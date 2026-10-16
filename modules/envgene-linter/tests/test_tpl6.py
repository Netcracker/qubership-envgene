import json

import pytest
from click.testing import CliRunner

from envgene_linter.cli import main
from envgene_linter.engine import run_check
from envgene_linter.model import Action, Severity


def findings(tmp_path, source, relative='templates/cloud.yml.j2'):
    path = tmp_path / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(source, encoding='utf-8')
    return [item for item in run_check(tmp_path).findings if item.rule == 'TPL-6']


@pytest.mark.parametrize('source', [
    '{% macro url(h) %}{{ h }}{% endmacro %}',
    '{% include "shared.j2" %}',
    '{% import "shared.j2" as helper %}',
    '{% from "shared.j2" import helper %}',
    '{% extends "base.j2" %}',
    '{% block body %}value{% endblock %}',
    '{% for item in [1, 2] %}{{ item }}{% endfor %}',
    '{% for item in range(3) %}{{ item }}{% endfor %}',
])
def test_prohibited_logic_produces_fix(tmp_path, source):
    result = findings(tmp_path, '# template\n' + source)
    assert len(result) == 1
    assert (result[0].severity, result[0].action, result[0].line) == (Severity.WARNING, Action.FIX, 2)


@pytest.mark.parametrize('source', [
    '{% if flag | default(false) %}yes{% elif other | d(false) %}other{% else %}no{% endif %}',
    '{{ value | default([]) | join(",") | upper | lower }}',
    '{% for item in items | default([]) %}{{ item }}{% else %}empty{% endfor %}',
    '{# {% include "shared.j2" %} {{ value | custom_filter }} #}',
    '{% raw %}{{ .Release.Name }}{% endraw %}',
    '{%- raw -%}{{- if .Values.enabled }}{{ .Values.name | quote }}{{ else }}none{{ end }}{%- endraw -%}',
    '{% raw %}{{ include "chart.labels" . }}{% endraw %}',
    '{% raw %}{{ tpl .Values.config . }}{% endraw %}',
])
def test_simple_logic_and_helm_passthrough_are_allowed(tmp_path, source):
    assert findings(tmp_path, source) == []


@pytest.mark.parametrize('source', [
    '{% set value = "fixed" %}',
    '{% for item in items recursive %}{{ item }}{% endfor %}',
])
def test_uncertain_logic_is_reviewed(tmp_path, source):
    result = findings(tmp_path, source)
    assert len(result) == 1
    assert (result[0].severity, result[0].action) == (Severity.INFORMATION, Action.REVIEW)


def test_raw_body_is_not_executable_jinja(tmp_path):
    assert findings(tmp_path, '{% raw %}{% include "secret-name.j2" %}{% endraw %}') == []


@pytest.mark.parametrize('expression', [
    '{{ value | custom_filter | replace("a", "b") }}',
    '{{ value | replace("a", "b") | custom_filter }}',
])
def test_unregistered_filter_chains_require_compatibility_review(tmp_path, expression):
    result = findings(tmp_path, expression)
    assert len(result) == 1 and result[0].action == Action.REVIEW
    assert result[0].key == 'ansible_compatibility'


@pytest.mark.parametrize('source', [
    '{{ value | to_nice_yaml }}',
    '{{ value | ansible.builtin.to_nice_yaml }}',
    '{{ value | urlsplit }}',
    '{{ value | replace("a", "b") }}',
    '{{ value | length }}',
    '{{ value | indent(2, true) }}',
    '{% filter to_nice_yaml %}literal text{% endfilter %}',
    '{% filter to_nice_yaml | indent(2) %}literal text{% endfilter %}',
])
def test_compatible_filters_are_allowed_without_a_style_allowlist(tmp_path, source):
    assert findings(tmp_path, source) == []


def test_allowed_filter_block_does_not_hide_prohibited_statements(tmp_path):
    source = '{% filter to_nice_yaml %}\n{% include "shared.j2" %}\n{% endfilter %}'
    assert [(item.line, item.action) for item in findings(tmp_path, source)] == [(2, Action.FIX)]


def test_builtin_filter_is_allowed_in_a_rendered_descriptor_scalar(tmp_path):
    source = 'tenant: tenant.yml.j2\ncloud: "{{ value | default(\'\') | upper }}"\nnamespaces: []\n'
    assert findings(tmp_path, source, 'templates/env_templates/example.yaml') == []


def test_cli_registered_custom_filter_does_not_create_findings_or_skips(tmp_path):
    findings(tmp_path, "{{ value | default('') | to_nice_yaml }}")
    result = CliRunner().invoke(main, ['check', str(tmp_path)])
    assert result.exit_code == 0, result.output
    assert json.loads((tmp_path / 'envgene-linter-report.json').read_text()) == []
    html = (tmp_path / 'envgene-linter-report.html').read_text()
    assert 'No findings' in html
    assert 'Incomplete checks' not in html


@pytest.mark.parametrize('expression', ['tpl (value)', 'include ("x")'])
def test_ambiguous_calls_inside_raw_are_allowed(tmp_path, expression):
    assert findings(tmp_path, '{% raw %}{{ ' + expression + ' }}{% endraw %}') == []


@pytest.mark.parametrize('source', [
    '{% raw %}literal text{% endraw %}',
    '{% raw %}{{ id }}{% endraw %}',
    '{% raw %}{{ .Release.Name }} {{ unknown }}{% endraw %}',
    '{% raw %}{{ value | custom_filter }}{% endraw %}',
    '{% raw %}{{ broken + }}{% endraw %}',
    '{% raw %}{% set value = "fixed" %}{% endraw %}',
    '{% raw %}{% endraw %}',
    '{%- raw -%}\n{{ id }}\n{%- endraw -%}',
    '{% raw %}{{ first }}{% endraw %}\n{% raw %}{{ second }}{% endraw %}',
])
def test_raw_passthrough_does_not_require_helm_syntax(tmp_path, source):
    assert findings(tmp_path, source) == []


def test_raw_does_not_hide_executable_logic_outside_the_block(tmp_path):
    source = '{% raw %}{% include "ignored.j2" %}{% endraw %}\n{% include "active.j2" %}'
    result = findings(tmp_path, source)
    assert [(item.line, item.action) for item in result] == [(2, Action.FIX)]


def test_raw_passthrough_is_allowed_in_a_rendered_descriptor_scalar(tmp_path):
    source = 'tenant: tenant.yml.j2\ncloud: "{% raw %}{{ id }}{% endraw %}"\nnamespaces: []\n'
    assert findings(tmp_path, source, 'templates/env_templates/example.yaml') == []


def test_unclosed_raw_block_remains_an_incomplete_check(tmp_path):
    findings(tmp_path, '{% raw %}{{ id }}')
    result = run_check(tmp_path)
    assert any(check.rule == 'TPL-6' and check.reason == 'cannot parse Jinja source'
               for check in result.skipped_checks)


def test_cli_raw_passthrough_does_not_create_review_entries(tmp_path):
    findings(tmp_path, '{% raw %}{{ id }}{% endraw %}')
    result = CliRunner().invoke(main, ['check', str(tmp_path)])
    assert result.exit_code == 0, result.output
    assert json.loads((tmp_path / 'envgene-linter-report.json').read_text()) == []
    assert 'No findings' in (tmp_path / 'envgene-linter-report.html').read_text()


def test_deep_expression_does_not_abort_other_template_checks(tmp_path):
    result = findings(tmp_path, '{{ ' + ' + '.join(['1'] * 1100) + ' }}\n{% include "shared.j2" %}')
    assert len(result) == 1
    assert result[0].line == 2
