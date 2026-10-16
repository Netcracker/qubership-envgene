import json

import pytest
from click.testing import CliRunner

from envgene_linter import rule_config
from envgene_linter.cli import main
from envgene_linter.engine import run_check
from envgene_linter.model import Action


def write(root, relative, text):
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8')
    return path


def reviews(root):
    return [item for item in run_check(root).findings
            if item.rule == 'TPL-6' and item.key == 'ansible_compatibility']


@pytest.mark.parametrize('relative', [
    'templates/cloud.yml.j2',
    'templates/cloud.yaml.j2',
    'templates/regdefs/example.yml',
    'templates/appdefs/example.yaml',
])
def test_full_renderer_accepts_supported_ansible_replacements(tmp_path, relative):
    write(tmp_path, relative,
          "{{ lookup('ansible.builtin.env', 'EXAMPLE') | default('') }}\n"
          "{{ value | default({}) | ansible.builtin.to_nice_yaml }}")
    assert reviews(tmp_path) == []


@pytest.mark.parametrize('relative', [
    'templates/parameters/example.j2',
    'templates/env_templates/example.j2',
    'templates/parameters/example.yml',
    'environments/c/e/Inventory/parameters/example.yml',
    'configuration/example.yaml',
])
def test_legacy_lookup_without_confirmed_full_renderer_gets_review(tmp_path, relative):
    (tmp_path / 'templates').mkdir()
    path = write(tmp_path, relative, "{{ lookup('ansible.builtin.env', 'PRIVATE_NAME') | default('') }}")
    result = reviews(tmp_path)
    assert [(item.path, item.line, item.action) for item in result] == [(path, 1, Action.REVIEW)]
    assert 'PRIVATE_NAME' not in repr(result)


def test_descriptor_path_does_not_inherit_full_renderer_filters(tmp_path):
    path = write(tmp_path, 'templates/env_templates/example.yaml',
                 'tenant: tenant.yml.j2\n'
                 'cloud: "{{ value | default({}) | to_nice_yaml }}"\n'
                 'namespaces: []\n')
    assert [(item.path, item.line) for item in reviews(tmp_path)] == [(path, 2)]


def test_descriptor_override_uses_registered_filters_and_compatibility_processing(tmp_path):
    write(tmp_path, 'templates/env_templates/example.yaml',
          'tenant: tenant.yml.j2\ncloud:\n  template_path: cloud.yml.j2\n  template_override:\n'
          '    value: "{{ value | default({}) | ansible.builtin.to_nice_yaml }}"\nnamespaces: []\n')
    assert reviews(tmp_path) == []


@pytest.mark.parametrize('expression', [
    "{{ lookup('ansible.builtin.env', 'EXAMPLE') | default('') }}",
    '{{ value | default({}) | ansible.builtin.to_nice_yaml }}',
    '{% raw %}{{ _tenant }}{% endraw %}',
])
def test_namespace_override_must_support_both_rendering_stages(tmp_path, expression):
    path = write(tmp_path, 'templates/env_templates/example.yaml',
                 'tenant: tenant.yml.j2\ncloud: cloud.yml.j2\nnamespaces:\n'
                 '  - template_path: namespace.yml.j2\n    template_override:\n'
                 '      value: ' + json.dumps(expression) + '\n')
    assert [(item.path, item.line) for item in reviews(tmp_path)] == [(path, 6)]


def test_namespace_override_accepts_filters_registered_in_both_stages(tmp_path):
    write(tmp_path, 'templates/env_templates/example.yaml',
          'tenant: tenant.yml.j2\ncloud: cloud.yml.j2\nnamespaces:\n'
          '  - template_path: namespace.yml.j2\n    template_override:\n'
          '      value: "{{ value | default({}) | to_nice_yaml }}"\n')
    assert reviews(tmp_path) == []


@pytest.mark.parametrize('relative', ['templates/regdefs/example.yml', 'templates/appdefs/example.yaml'])
@pytest.mark.parametrize('expression', [
    '{% raw %}{{ _tenant }}{% endraw %}',
    '{{ value | default({}) | private_custom_filter }}',
])
def test_full_renderer_yaml_checks_expressions_without_legacy_markers(tmp_path, relative, expression):
    path = write(tmp_path, relative, 'value: ' + json.dumps(expression) + '\n')
    assert [(item.path, item.line) for item in reviews(tmp_path)] == [(path, 1)]


@pytest.mark.parametrize('filename', ['description_template.yaml', 'description_template_manifest.yml'])
def test_gsf_metadata_is_outside_envgene_compatibility_scope(tmp_path, filename):
    (tmp_path / 'templates').mkdir()
    write(tmp_path, filename, '# metadata\nvalue: "{{ lookup(\'env\', \'PRIVATE_NAME\') }}"\n')
    assert reviews(tmp_path) == []


def test_compatibility_does_not_expand_tpl4_or_statement_checks_to_metadata(tmp_path):
    (tmp_path / 'templates').mkdir()
    write(tmp_path, 'description_template.yaml',
          "{{ lookup('env', 'PRIVATE_NAME') }}\n{% include 'example.j2' %}")
    result = run_check(tmp_path)
    assert result.findings == []


def test_compatibility_is_visible_in_html_json_and_console_without_source(tmp_path):
    path = write(tmp_path, 'templates/example.yml.j2', '{{ value | default({}) | private_custom_filter }}')
    result = CliRunner().invoke(main, ['check', str(tmp_path), '--console'])
    assert result.exit_code == 0, result.output
    data = json.loads((tmp_path / 'envgene-linter-report.json').read_text())
    assert len(data) == 1 and data[0]['rule_id'] == 'TPL-6' and data[0]['action'] == 'Review'
    assert data[0]['files'] == ['templates/example.yml.j2:1:1']
    html = (tmp_path / 'envgene-linter-report.html').read_text()
    for output in (result.output, json.dumps(data), html):
        assert 'private_custom_filter' not in output
    assert reviews(tmp_path)[0].path == path


def test_disabled_tpl6_does_not_collect_additional_legacy_sources(tmp_path, monkeypatch):
    (tmp_path / 'templates').mkdir()
    write(tmp_path, 'configuration/example.yaml', "{{ lookup('env', 'PRIVATE_NAME') }}")
    monkeypatch.setitem(rule_config.RULE_ENABLED, 'TPL-6', False)
    monkeypatch.setitem(rule_config.RULE_ENABLED, 'TPL-1', False)
    result = run_check(tmp_path)
    assert not result.findings and not result.skipped_checks


def test_compatibility_deduplicates_aliases_and_rejects_external_and_git_targets(tmp_path):
    root = tmp_path / 'repository'
    path = write(root, 'templates/example.yml.j2', '{{ value | default({}) | private_custom_filter }}')
    (path.parent / 'alias.yml.j2').symlink_to(path)
    external = write(tmp_path, 'outside.yml', "{{ lookup('env', 'PRIVATE_NAME') }}")
    (root / 'configuration').mkdir()
    (root / 'configuration/outside.yaml').symlink_to(external)
    hidden = write(root, '.git/private.yml', "{{ lookup('env', 'PRIVATE_NAME') }}")
    (root / 'configuration/hidden.yaml').symlink_to(hidden)
    result = reviews(root)
    assert len(result) == 1
    assert result[0].path.resolve() == path.resolve()


def test_alias_with_a_different_consumer_does_not_inherit_template_compatibility(tmp_path):
    target = write(tmp_path, 'templates/example.yml.j2',
                   'VALUE: "{{ lookup(\'ansible.builtin.env\', \'EXAMPLE\') | default(\'\') }}"')
    consumer = tmp_path / 'configuration/example.yaml'
    consumer.parent.mkdir()
    consumer.symlink_to(target)
    result = reviews(tmp_path)
    assert [(item.path, item.line) for item in result] == [(consumer, 1)]


@pytest.mark.parametrize(('kind', 'count'), [('ok', 0), ('not-ok', 3)])
def test_public_compatibility_examples(kind, count):
    from pathlib import Path

    root = Path(__file__).resolve().parents[1] / 'testdata/compatibility/ansible' / kind
    assert len(reviews(root)) == count
