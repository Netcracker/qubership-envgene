import pytest
from click.testing import CliRunner

from envgene_linter.cli import main
from envgene_linter.engine import run_check


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8')
    return path


def test_template_only_checks_run_without_environment_bindings(tmp_path):
    write(tmp_path / 'templates/cloud.yml.j2', '{% include "missing.j2" %}')
    result = run_check(tmp_path)
    assert [item.rule for item in result.findings] == ['TPL-6']
    assert not {'TPL-4', 'TPL-6'} & set(result.not_applicable_rules)
    assert result.skipped == []


def test_descriptor_fields_are_checked_independently(tmp_path):
    path = write(tmp_path / 'templates/env_templates/example.yaml',
                 'tenant: "{{ templates_dir }}/tenant.yml.j2"\n'
                 'cloud: \'{% include "missing.j2" %}\'\n'
                 'namespaces:\n  - name: "{{ selector }}"\n'
                 '    template_path: "{{ templates_dir }}/namespace.yml.j2"\n'
                 'description: \'{% include "ignored.j2" %}\'\n')
    result = run_check(tmp_path)
    assert [(f.rule, f.path, f.line) for f in result.findings if f.rule in ('TPL-4', 'TPL-6')] == [
        ('TPL-6', path, 2),
    ]


@pytest.mark.parametrize('relative', ['templates/plain.yml', 'configuration/data.yml',
                                    'environments/cloud.yml.j2', 'README.md'])
def test_unrendered_files_are_outside_scope(tmp_path, relative):
    (tmp_path / 'templates').mkdir()
    write(tmp_path / relative, '{% include "missing.j2" %}')
    assert not [f for f in run_check(tmp_path).findings if f.rule in ('TPL-4', 'TPL-6')]


def test_invalid_template_does_not_hide_other_files_or_leak_source(tmp_path):
    write(tmp_path / 'templates/invalid.j2', '{{ synthetic_private_value + }}')
    write(tmp_path / 'templates/valid.j2', '{% include "missing.j2" %}')
    result = run_check(tmp_path)
    assert len([f for f in result.findings if f.rule == 'TPL-6']) == 1
    assert any('cannot parse Jinja' in note for note in result.skipped)
    assert 'synthetic_private_value' not in repr(result)


def test_templates_are_never_executed(tmp_path):
    write(tmp_path / 'templates/cloud.j2', '{{ 1 / 0 }}{% include "missing.j2" %}')
    result = run_check(tmp_path)
    assert len([f for f in result.findings if f.rule == 'TPL-6']) == 1
    assert result.skipped == []


def test_unsafe_links_and_physical_aliases(tmp_path):
    root = tmp_path / 'repository'
    path = write(root / 'templates/main.j2', '{% include "missing.j2" %}')
    (path.parent / 'alias.j2').symlink_to(path)
    external = write(tmp_path / 'outside.j2', '{% include "private.j2" %}')
    (path.parent / 'outside.j2').symlink_to(external)
    (path.parent / 'cycle.j2').symlink_to(path.parent / 'cycle.j2')
    result = run_check(root)
    assert len([f for f in result.findings if f.rule == 'TPL-6']) == 1


def test_disabled_template_rules_do_not_parse_or_appear_in_reports(tmp_path, monkeypatch):
    from envgene_linter import rule_config
    write(tmp_path / 'templates/invalid.j2', '{{ invalid + }}')
    for rule in ('TPL-4', 'TPL-6'):
        monkeypatch.setitem(rule_config.RULE_ENABLED, rule, False)
    result = CliRunner().invoke(main, ['check', str(tmp_path), '--console'])
    assert result.exit_code == 0, result.output
    assert 'cannot parse Jinja' not in result.output
    assert 'TPL-4' not in result.output and 'TPL-6' not in result.output
    report = (tmp_path / 'envgene-linter-report.html').read_text()
    assert 'TPL-4' not in report and 'TPL-6' not in report


@pytest.mark.parametrize('scalar', [
    '"{{ VALUE | default(\\"\\") | custom_filter }}"',
    "'{{ VALUE | default('''') | custom_filter }}'",
    '|\n  {{ VALUE | default(\'\') | custom_filter }}',
])
def test_descriptor_uses_decoded_yaml_scalar_and_reports_scalar_location(tmp_path, scalar):
    write(tmp_path / 'templates/env_templates/example.yaml',
          'tenant: tenant.yml.j2\ncloud: ' + scalar + '\nnamespaces: []\n')
    result = run_check(tmp_path)
    assert result.skipped == []
    assert [(f.rule, f.line) for f in result.findings if f.rule in ('TPL-4', 'TPL-6')] == [('TPL-6', 2)]
