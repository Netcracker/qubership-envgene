import pytest

from envgene_linter.engine import run_check
from envgene_linter.model import Action, Severity


def findings(tmp_path, source):
    path = tmp_path / 'templates/cloud.yml.j2'
    path.parent.mkdir(exist_ok=True)
    path.write_text(source, encoding='utf-8')
    return [item for item in run_check(tmp_path).findings if item.rule == 'TPL-4']


@pytest.mark.parametrize('source', [
    '{{ VALUE }}',
    "{% if FEATURE_A == 'on' %}true{% else %}false{% endif %}",
    '{{ current_env.additionalTemplateVariables.mode }}',
    '{{ VALUE + 1 }}',
    "{{ (VALUE + 1) | default('') }}",
    "{{ VALUE | upper | default('') }}",
    '{{ VALUE | default(FALLBACK) }}',
    "{{ values[INDEX] | default('') }}",
    '{% if value is defined %}{{ value.child }}{% endif %}',
    '{% if value is defined or value == "on" %}yes{% endif %}',
    '{% if value is defined %}yes{% else %}{{ value }}{% endif %}',
    '{% for item in items | default([]) %}{{ item.name }}{% endfor %}',
    '{% set item = 1 %}{{ item.name }}',
    '{% if flag | default(false) %}{% set item = 1 %}{% endif %}{{ item }}',
    '{% for item in items | default([]) %}{{ item }}{% endfor %}{{ item }}',
    '{% set current_env = {} %}{{ current_env.name }}',
    '{{ templates_dir }}',
    '{{ function(VALUE) | default(0) }}',
])
def test_unprotected_references_are_review_candidates(tmp_path, source):
    result = findings(tmp_path, '# template\n' + source)
    assert len(result) == 1
    assert (result[0].severity, result[0].action, result[0].line) == (Severity.INFORMATION, Action.REVIEW, 2)
    assert 'VALUE' not in repr(result)
    assert 'FEATURE_A' not in repr(result)


@pytest.mark.parametrize('source', [
    "{{ VALUE | default('') }}",
    "{{ VALUE | d('') }}",
    "{{ current_env.additionalTemplateVariables.mode | default('') }}",
    "{{ (VALUE | default(0)) + 1 }}",
    "{{ VALUE | default('') | upper }}",
    '{% if value is defined %}{{ value }}{% endif %}',
    '{% if value is not defined %}missing{% else %}{{ value }}{% endif %}',
    '{% if value is undefined %}missing{% else %}{{ value }}{% endif %}',
    '{% if value is defined and value == "on" %}{{ value }}{% endif %}',
    '{% if value is undefined or value == "on" %}yes{% endif %}',
    '{{ value if value is defined else "fallback" }}',
    '{% if value is defined %}yes{% elif other is defined %}{{ other }}{% endif %}',
    '{% if current_env["custom"] is defined %}{{ current_env.custom }}{% endif %}',
    '{% for item in items | default([]) %}{{ item }}: {{ loop.index }}{% endfor %}',
    '{% for key, value in items | default([]) %}{{ key }} {{ value }}{% endfor %}',
    '{% set item = "constant" %}{{ item }}',
    '{{ current_env.name }} {{ current_env.environmentName }}',
    '{# {{ ignored }} #}{% raw %}{{ .Release.Name }}{% endraw %}',
    '{% macro helper(value) %}{{ value }}{% endmacro %}',
])
def test_protected_references_and_bound_locals_are_silent(tmp_path, source):
    assert findings(tmp_path, source) == []


def test_report_deduplicates_lines_without_exposing_input_names(tmp_path):
    source = '{{ synthetic_private_name }} {{ another_private_name }}\n{{ synthetic_private_name }}'
    result = findings(tmp_path, source)
    assert [(item.line, item.column) for item in result] == [(1, 1), (2, 1)]
    assert 'private_name' not in repr(result)


@pytest.mark.parametrize('source,line', [
    ('{% if value.child is defined %}\n{% if true %}{% set value = {} %}{% endif %}\n'
     '{{ value.child }}\n{% endif %}', 3),
    ('{% if true %}{% set current_env = {} %}{% endif %}\n{{ current_env.name }}', 2),
    ('{% macro outer() %}{{ caller(1) }}{% endmacro %}\n{% if value.child is defined %}\n'
     '{% call(value) outer() %}\n{{ value.child }}\n{% endcall %}\n{% endif %}', 4),
])
def test_rebinding_invalidates_outer_presence_guards(tmp_path, source, line):
    assert [f.line for f in findings(tmp_path, source)] == [line]


def test_filter_block_has_sequential_local_bindings(tmp_path):
    assert findings(tmp_path, '{% filter upper %}\n{% set local = 1 %}\n{{ local }}\n{% endfilter %}') == []


def test_loop_filter_cannot_read_its_own_loop_metadata(tmp_path):
    result = findings(tmp_path, '{% for item in [1, 2] if loop.index %}{{ item }}{% endfor %}')
    assert [f.line for f in result] == [1]


def test_nested_loop_filter_can_read_outer_loop_metadata(tmp_path):
    assert findings(tmp_path, '{% for outer in [1, 2] %}\n'
                    '{% for item in [1, 2] if loop.index %}{{ item }}{% endfor %}\n{% endfor %}') == []


def test_macro_parameter_named_loop_shadows_outer_metadata(tmp_path):
    result = findings(tmp_path, '{% for item in [1, 2] %}\n'
                      '{% macro helper(loop) %}{{ loop.index }}{% endmacro %}\n{% endfor %}')
    assert [f.line for f in result] == [2]
