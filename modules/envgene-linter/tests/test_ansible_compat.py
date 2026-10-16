"""Static renderer compatibility, including transformations before parsing."""

from pathlib import Path

import pytest


def analyze(text, rendering='envgene', offset=0, descriptor=False):
    from envgene_linter.ansible_compat import CompatibilitySource, analyze_compatibility

    return analyze_compatibility(CompatibilitySource(
        Path('templates/example.yml.j2'), text, rendering, offset, descriptor,
    ))


@pytest.mark.parametrize('text', [
    "{{ lookup('ansible.builtin.env', 'TOKEN') }}",
    "{{ lookup( 'ansible.builtin.env' , 'TOKEN' ) }}",
    '{{ data | ansible.builtin.to_nice_yaml }}',
    '{{ data | ansible.builtin.to_nice_yaml() }}',
    '{{ _tenant }}',
    '{{ data | to_nice_yaml }}',
    '{{ data | urlsplit }}',
    "{{ data | urlsplit('hostname') }}",
    "{{ data | urlsplit(part='hostname') }}",
    '{{ data | default([]) | join(",") | upper }}',
    '{{ data | indent(2, true) }}',
    '{% filter to_nice_yaml %}text{% endfilter %}',
])
def test_supported_envgene_expressions_need_no_review(text):
    assert analyze(text) == {}


@pytest.mark.parametrize('text', [
    '{{ lookup("ansible.builtin.env", "TOKEN") }}',
    "{{ lookup('ansible.builtin.env', 'TOKEN', default='secret') }}",
    "{{ lookup('ansible.builtin.env') }}",
    "{{ lookup('ansible.builtin.env', '') }}",
    "{{ lookup('ansible.builtin.env', 'NOT-AN-IDENTIFIER') }}",
    "{{ lookup('ansible.builtin.env', 'NESTED.KEY') }}",
    "{{ lookup('ansible.builtin.env', variable) }}",
    "{{ lookup('file', 'private-file') }}",
    "{{ query('ansible.builtin.env', 'TOKEN') }}",
    "{{ q('ansible.builtin.env', 'TOKEN') }}",
    '{{ ansible.builtin.lookup("env", "TOKEN") }}',
    '{{ data | ansible.builtin.combine(other) }}',
    '{{ data | private_filter }}',
    '{% filter private_filter %}text{% endfilter %}',
    '{% filter ansible.builtin.to_nice_yaml %}text{% endfilter %}',
    '{{ data | to_nice_yaml(2) }}',
    '{{ data | to_nice_yaml(indent=2) }}',
    '{{ data | ansible.builtin.to_nice_yaml(indent=2) }}',
    '{{ data | urlsplit("host", "scheme") }}',
    '{{ data | urlsplit(unknown="host") }}',
    '{{ data | urlsplit("host", part="scheme") }}',
    '{{ data | to_nice_yaml(*arguments) }}',
    '{{ data | urlsplit(**arguments) }}',
    '{{ data | urlsplit(1) }}',
    '{{ data | urlsplit(-1) }}',
    '{{ data | urlsplit(+1) }}',
    '{{ data | urlsplit(-0.5) }}',
    '{{ data | urlsplit(part=true) }}',
    '{{ data | urlsplit(["host"]) }}',
    '{{ data | urlsplit({"part": "host"}) }}',
    '{{ data | urlsplit(("host",)) }}',
])
def test_unsupported_or_unconfirmed_expressions_need_review(text):
    assert set(analyze(text)) == {1}


@pytest.mark.parametrize(('rendering', 'text', 'lines'), [
    ('custom_jinja', '{{ data | to_nice_yaml }}', set()),
    ('custom_jinja', '{{ data | urlsplit(part="host") }}', set()),
    ('custom_jinja', '{{ data | ansible.builtin.to_nice_yaml }}', {1}),
    ('custom_jinja', "{{ lookup('ansible.builtin.env', 'TOKEN') }}", {1}),
    ('jinja', '{{ data | to_nice_yaml }}', {1}),
    ('jinja', '{{ data | urlsplit }}', {1}),
    ('jinja', '{{ data | default([]) | join(",") }}', set()),
    ('unknown', '{{ data | ansible.builtin.to_nice_yaml }}', {1}),
    ('unknown', "{{ lookup('ansible.builtin.env', 'TOKEN') }}", {1}),
    ('unknown', '{{ data | to_nice_yaml }}', {1}),
    ('unknown', '{{ data | private_filter }}', {1}),
    ('unknown', '{{ data | default([]) }}', set()),
])
def test_rendering_contract_controls_compatibility(rendering, text, lines):
    assert set(analyze(text, rendering)) == lines


@pytest.mark.parametrize('text', [
    'Plain text mentioning ansible.builtin.env and lookup and urlsplit',
    '{{ "ansible.builtin.env" }}',
    '{{ "lookup" }}',
    '{# {{ data | ansible.builtin.to_nice_yaml }} #}',
    "{# {{ lookup('ansible.builtin.env', 'TOKEN') }} #}",
    '{% raw %}{{ data | ansible.builtin.combine(other) }}{% endraw %}',
    '{% raw %}{{ lookup("ansible.builtin.env", "TOKEN") }}{% endraw %}',
    '{% raw %}{{ data | private_filter }}{% endraw %}',
    '{% raw %}{{ broken + }}{% endraw %}',
])
def test_literal_mentions_comments_and_unmodified_raw_are_allowed(text):
    assert analyze(text) == {}


@pytest.mark.parametrize('text', [
    "literal lookup('ansible.builtin.env', 'TOKEN')",
    'literal | ansible.builtin.to_nice_yaml',
    '{% raw %}{{ _tenant }}{% endraw %}',
    '{% raw %}{{ data | ansible.builtin.to_nice_yaml }}{% endraw %}',
    "{% raw %}{{ lookup('ansible.builtin.env', 'TOKEN') }}{% endraw %}",
    '{{ "literal | ansible.builtin.to_nice_yaml" }}',
    '{{ "{{ _tenant }}" }}',
    '{{ "lookup(\'ansible.builtin.env\', \'TOKEN\')" }}',
    "{{ object.lookup('ansible.builtin.env', 'TOKEN') }}",
    "{{ object . lookup('ansible.builtin.env', 'TOKEN') }}",
    "{{ mylookup('ansible.builtin.env', 'TOKEN') }}",
])
def test_preparse_replacements_changing_literal_or_other_calls_need_review(text):
    assert set(analyze(text)) == {1}


def test_yaml_comment_is_rendered_before_yaml_parsing():
    assert set(analyze('# {{ data | ansible.builtin.combine(other) }}')) == {1}


def test_multiline_replacement_preserves_later_original_positions():
    text = "---\n{{ lookup(\n'ansible.builtin.env',\n'TOKEN') }}\n{{ data | private_filter }}"
    assert set(analyze(text)) == {5}


def test_positions_use_offsets_and_descriptor_opening_line():
    text = '\n{{ data | private_filter }}\n{{ data | other_filter }}'
    assert set(analyze(text, offset=7)) == {9, 10}
    assert set(analyze(text, offset=7, descriptor=True)) == {8}


def test_same_line_compatibility_issues_produce_one_review():
    assert set(analyze('{{ data | private_filter }} {{ data | to_nice_yaml(2) }}')) == {1}


@pytest.mark.parametrize('argument', ['0', '+0', '-0', '-0.0', 'false', 'none', '[]', '{}', '()'])
def test_false_constant_urlsplit_part_is_supported(argument):
    assert analyze('{{ data | urlsplit(' + argument + ') }}') == {}


def test_deep_flat_expression_does_not_create_spurious_review():
    text = '{{ ' + ' + '.join(['1'] * 1100) + ' }}\n{% include "shared.j2" %}'
    assert analyze(text) == {}


def test_parser_failure_reports_generic_original_position():
    assert set(analyze('---\n{{ data + }}')) == {2}


def test_reasons_redact_values_names_and_parser_exception_details():
    text = '{{ private_variable | private_filter("private-secret") }}\n{{ "private-broken" + }}'
    reasons = '\n'.join(analyze(text).values())
    assert reasons
    assert 'private' not in reasons
    assert 'unexpected' not in reasons
    assert 'TOKEN' not in reasons


def test_unknown_rendering_reason_identifies_uncertainty():
    reasons = analyze("{{ lookup('ansible.builtin.env', 'TOKEN') }}", 'unknown')
    assert any('unknown' in reason.lower() or 'unconfirmed' in reason.lower()
               for reason in reasons.values())


def test_analysis_never_compiles_renders_or_reads_lookup_targets(tmp_path, monkeypatch):
    from jinja2 import Environment

    def forbidden(*args, **kwargs):
        pytest.fail('compatibility analysis executed a template or read a target')

    marker = tmp_path / 'must-not-exist'
    monkeypatch.setattr(Environment, 'compile', forbidden)
    monkeypatch.setattr(Environment, 'from_string', forbidden)
    monkeypatch.setattr(Path, 'read_text', forbidden)
    text = '{{ cycler.__init__.__globals__.os.system("touch ' + str(marker) + '") }}'
    assert analyze(text) == {}
    assert set(analyze('{{ data | private_filter }}')) == {1}
    assert set(analyze("{{ lookup('file', 'private-target') }}")) == {1}
    assert not marker.exists()
