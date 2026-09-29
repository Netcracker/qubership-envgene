import pytest

from envgene_linter.engine import run_check
from envgene_linter.model import Action, Severity


def findings(tmp_path, source):
    path = tmp_path / 'templates/cloud.yml.j2'
    path.parent.mkdir(exist_ok=True)
    path.write_text(source, encoding='utf-8')
    return [item for item in run_check(tmp_path).findings if item.rule == 'TPL-6']


@pytest.mark.parametrize('source', [
    '{% macro url(h) %}{{ h }}{% endmacro %}',
    '{% include "shared.j2" %}',
    '{% import "shared.j2" as helper %}',
    '{% from "shared.j2" import helper %}',
    '{% extends "base.j2" %}',
    '{% block body %}value{% endblock %}',
    '{{ value | custom_filter }}',
    '{{ value | to_nice_yaml }}',
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
    '{% raw %}literal text{% endraw %}',
    '{% raw %}{{ unknown }}{% endraw %}',
    '{% raw %}{{ .Release.Name }} {{ unknown }}{% endraw %}',
    '{{ value | replace("a", "b") }}',
    '{% set value = "fixed" %}',
    '{% for item in items recursive %}{{ item }}{% endfor %}',
])
def test_uncertain_logic_is_reviewed(tmp_path, source):
    result = findings(tmp_path, source)
    assert len(result) == 1
    assert (result[0].severity, result[0].action) == (Severity.INFORMATION, Action.REVIEW)


def test_raw_body_is_not_executable_jinja(tmp_path):
    result = findings(tmp_path, '{% raw %}{% include "secret-name.j2" %}{% endraw %}')
    assert len(result) == 1
    assert result[0].action == Action.REVIEW
    assert 'secret-name' not in repr(result)


@pytest.mark.parametrize('expression', [
    '{{ value | custom_filter | replace("a", "b") }}',
    '{{ value | replace("a", "b") | custom_filter }}',
])
def test_custom_filter_fix_is_not_hidden_by_review_on_same_line(tmp_path, expression):
    result = findings(tmp_path, expression)
    assert len(result) == 1
    assert result[0].action == Action.FIX


@pytest.mark.parametrize('expression', ['tpl (value)', 'include ("x")'])
def test_ambiguous_calls_inside_raw_need_review(tmp_path, expression):
    result = findings(tmp_path, '{% raw %}{{ ' + expression + ' }}{% endraw %}')
    assert len(result) == 1
    assert result[0].action == Action.REVIEW


def test_deep_expression_does_not_abort_other_template_checks(tmp_path):
    result = findings(tmp_path, '{{ ' + ' + '.join(['1'] * 1100) + ' }}\n{% include "shared.j2" %}')
    assert len(result) == 1
    assert result[0].line == 2
