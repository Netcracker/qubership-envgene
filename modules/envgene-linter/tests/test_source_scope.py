"""Generated outputs must not become configuration finding targets."""

import json

import pytest
from click.testing import CliRunner

from envgene_linter.cli import main
from envgene_linter.discovery import build_index
from envgene_linter.engine import run_check
from envgene_linter.model import Action
from envgene_linter.rules.int2 import check as check_int2
from envgene_linter.rules.tpl1 import check as check_tpl1


def write(repo, relative, text):
    path = repo.root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8')
    return path


OUTPUTS = (
    'Namespaces/App_Ns/namespace.yml',
    'Namespaces/App_Ns/Applications/application.yml',
    'Applications/application.yml',
    'Profiles/profile.yml',
    'Credentials/credentials.yml',
    'effective-set/deployment/app/values.yml',
    'cloud.yml',
    'tenant.yml',
    'bg_domain.yml',
    'composite_structure.yml',
    'Inventory/namespace-map.yml',
    'Inventory/deploy-plan.yml',
    'Inventory/deploy-plan-calculated.yml',
    'Inventory/deploy-plan-mapped.yml',
)

OUTPUT_TEXT = '''deployParameters:
  DB_PASSWORD: example-generated-value
technicalConfigurationParameters:
  VALUE: '${creds.get("absent").secret}'
deployParameterSets: [absent]
value: "{{ lookup('unconfirmed', 'example') }}"
'''


@pytest.mark.parametrize('relative', OUTPUTS)
def test_generated_output_does_not_change_authored_findings(repo, all_rules_enabled, relative):
    repo.env('c', 'e', deploy={'cloud': ['p'], 'App_Ns': ['p']})
    repo.env_paramset('c', 'e', 'p', {'DB_PASSWORD': 'example-authored-value'})
    before = run_check(repo.root)
    assert any(f.rule == 'SEC-1' for f in before.findings)
    write(repo, 'environments/c/e/' + relative, OUTPUT_TEXT)
    after = run_check(repo.root)
    assert after.findings == before.findings
    assert after.skipped == before.skipped
    assert after.skipped_checks == before.skipped_checks


@pytest.mark.parametrize('relative', (
    'templates/Namespaces/source.yml',
    'environments/c/Profiles/source.yml',
    'environments/c/e/Inventory/Profiles/source.yml',
    'environments/c/e/Inventory/Credentials/source.yml',
    'environments/c/e/Inventory/parameters/Namespaces/source.yml',
    'environments/c/e/Inventory/parameters/deploy-plan.yml',
    'environments/parameters/Namespaces/source.yml',
    'environments/c/e/Inventory/custom/source.yml',
))
def test_generated_names_inside_authored_paths_remain_checked(repo, relative):
    repo.env('c', 'e')
    path = write(repo, relative, 'value: "{{ example }}"\n')
    findings = check_tpl1(build_index(repo.root))
    assert [(f.path, f.line, f.column) for f in findings] == [(path, 1, 9)]


def test_generated_header_does_not_hide_an_authored_file(repo):
    repo.env('c', 'e')
    path = write(repo, 'environments/c/e/Inventory/custom/source.yml',
                 '# The contents of this file is generated from template artifact: example.\n'
                 'value: "{{ example }}"\n')
    findings = check_tpl1(build_index(repo.root))
    assert [(f.path, f.line) for f in findings] == [(path, 2)]


def test_authored_alias_cannot_expose_generated_output(repo):
    repo.env('c', 'e')
    output = write(repo, 'environments/c/e/Namespaces/app/namespace.yml', 'value: "{{ example }}"\n')
    alias = repo.root / 'environments/c/e/Inventory/alias.yml'
    alias.symlink_to(output)
    assert check_tpl1(build_index(repo.root)) == []


def test_generated_catalog_still_resolves_an_authored_reference(repo):
    repo.env('c', 'e', deploy={'cloud': ['p']})
    repo.env_paramset('c', 'e', 'p', {'VALUE': "'${creds.get(\"example\").secret}'"})
    before = check_int2(build_index(repo.root))
    assert len(before) == 1 and before[0].action is Action.REVIEW
    write(repo, 'environments/c/e/Credentials/credentials.yml',
          'example:\n  type: secret\n  data:\n    secret: example-generated-value\n')
    assert check_int2(build_index(repo.root)) == []
    assert not any('/Credentials/' in f.path.as_posix() for f in run_check(repo.root).findings)


def test_broken_generated_catalog_keeps_review_on_authored_consumer(repo):
    repo.env('c', 'e', deploy={'cloud': ['p']})
    repo.env_paramset('c', 'e', 'p', {'VALUE': "'${creds.get(\"example\").secret}'"})
    output = write(repo, 'environments/c/e/Credentials/credentials.yml', 'example: [malformed\n')
    result = run_check(repo.root)
    integrity = [f for f in result.findings if f.rule == 'INT-2']
    assert len(integrity) == 1 and integrity[0].action is Action.REVIEW
    assert integrity[0].path.name == 'p.yml'
    assert all(f.path != output for f in result.findings)
    assert all(skip.path != output for skip in result.skipped_checks)
    assert all('Credentials/credentials.yml' not in note for note in result.skipped)


@pytest.mark.parametrize('relative', ('cloud.yml', 'Namespaces/app/namespace.yml', 'Inventory/namespace-map.yml'))
def test_broken_generated_yaml_is_silently_excluded(repo, relative):
    repo.env('c', 'e')
    output = write(repo, 'environments/c/e/' + relative, 'value: "{{ example }}"\n')
    output.write_bytes(b'\xff')
    result = run_check(repo.root)
    assert result.findings == []
    assert result.skipped == []
    assert result.skipped_checks == []


def test_generated_paths_are_absent_from_console_html_and_json(repo, all_rules_enabled):
    repo.env('c', 'e', deploy={'cloud': ['p'], 'App_Ns': ['p']})
    repo.env_paramset('c', 'e', 'p', {'DB_PASSWORD': 'example-authored-value'})
    for relative in OUTPUTS:
        write(repo, 'environments/c/e/' + relative, OUTPUT_TEXT)
    result = CliRunner().invoke(main, ['check', str(repo.root), '--console'])
    assert result.exit_code == 0, result.output
    records = json.loads((repo.root / 'envgene-linter-report.json').read_text())
    assert any(record['rule_id'] == 'SEC-1' for record in records)
    html = (repo.root / 'envgene-linter-report.html').read_text()
    for relative in OUTPUTS:
        target = 'environments/c/e/' + relative
        assert target not in result.output
        assert target not in html
        assert all(target not in location for record in records for location in record['files'])


def catalog_alias(repo, text):
    target = write(repo, 'data/catalog.yml', text)
    catalog = repo.root / 'environments/c/e/Credentials/credentials.yml'
    catalog.parent.mkdir(parents=True, exist_ok=True)
    catalog.symlink_to(target)
    return target


def test_generated_catalog_alias_keeps_its_context_only_role(repo):
    repo.env('c', 'e', deploy={'cloud': ['p']})
    repo.env_paramset('c', 'e', 'p', {'VALUE': "'${creds.get(\"example\").secret}'"})
    target = catalog_alias(repo, 'example:\n  type: secret\n  data:\n    secret: example-generated-value\n')
    result = run_check(repo.root)
    assert not any(f.path == target for f in result.findings)
    assert not any(f.rule == 'INT-2' for f in result.findings)


def test_invalid_generated_catalog_alias_has_no_physical_path_diagnostics(repo):
    repo.env('c', 'e', deploy={'cloud': ['p']})
    repo.env_paramset('c', 'e', 'p', {'VALUE': "'${creds.get(\"example\").secret}'"})
    target = catalog_alias(repo, 'example: [malformed\n')
    result = run_check(repo.root)
    integrity = [f for f in result.findings if f.rule == 'INT-2']
    assert len(integrity) == 1 and integrity[0].path.name == 'p.yml'
    assert integrity[0].action is Action.REVIEW
    assert not any(f.path == target for f in result.findings)
    assert not any(skip.path == target for skip in result.skipped_checks)
    assert not any('data/catalog.yml' in note for note in result.skipped)


def test_generated_parameter_alias_cannot_suppress_authored_group(repo, all_rules_enabled):
    repo.env('c', 'e', deploy={'cloud': ['p', 'q']})
    repo.env_paramset('c', 'e', 'p', {'FIRST': 'same-value', 'SECOND': 'same-value'})
    before = [f for f in run_check(repo.root).findings if f.rule == 'NAME-1']
    assert len(before) == 1 and len(before[0].file_locations()) == 2
    output = write(repo, 'environments/c/e/Profiles/q.yml', 'name: q\nparameters:\n  THIRD: same-value\n')
    (repo.root / 'environments/c/e/Inventory/parameters/q.yml').symlink_to(output)
    after = [f for f in run_check(repo.root).findings if f.rule == 'NAME-1']
    assert after == before


def test_invalid_generated_parameter_alias_has_no_legacy_skip_notes(repo):
    repo.env('c', 'e', deploy={'cloud': ['p']})
    output = write(repo, 'environments/c/e/Profiles/p.yml', 'parameters: [malformed\n')
    alias = repo.root / 'environments/c/e/Inventory/parameters/p.yml'
    alias.parent.mkdir(parents=True, exist_ok=True)
    alias.symlink_to(output)
    result = run_check(repo.root)
    assert not any('parameters/p.yml' in note or 'Profiles/p.yml' in note for note in result.skipped)
    assert all(skip.path not in {alias, output} for skip in result.skipped_checks)
    integrity = [f for f in result.findings if f.rule == 'INT-2']
    assert len(integrity) == 1 and integrity[0].action is Action.REVIEW
    assert integrity[0].path.name == 'env_definition.yml'


def test_generated_catalog_alias_preserves_independent_authored_selection(repo):
    repo.env('c', 'e', deploy={'cloud': ['p']})
    repo.env_paramset('c', 'e', 'p', {'VALUE': "'${creds.get(\"example\").username}'"})
    definition = repo.root / 'environments/c/e/Inventory/env_definition.yml'
    definition.write_text(definition.read_text() + '  sharedMasterCredentialFiles: [shared]\n')
    target = catalog_alias(repo, 'example:\n  type: usernamePassword\n  data:\n'
                           '    username: example-authored-username\n    password: envgeneNullValue\n')
    authored = repo.root / 'environments/c/e/Inventory/credentials/shared.yml'
    authored.parent.mkdir(parents=True, exist_ok=True)
    authored.symlink_to(target)
    result = [f for f in run_check(repo.root).findings if f.rule == 'SEC-5']
    assert len(result) == 1 and result[0].action is Action.FIX
    assert result[0].path.resolve() == target



@pytest.mark.parametrize('cloud', (
    {'maasConfig': {'credentialsId': 'example'}},
    {'vaultConfig': {'credentialsId': 'example'}},
    {'consulConfig': {'tokenSecret': 'example'}},
    {'dbaasConfigs': [{'credentialsId': 'example'}]},
))
def test_nested_generated_cloud_credential_ids_remain_usage_evidence(repo, cloud):
    repo.env('c', 'e')
    definition = repo.root / 'environments/c/e/Inventory/env_definition.yml'
    definition.write_text(definition.read_text() + '  sharedMasterCredentialFiles: [shared]\n')
    source = write(repo, 'environments/c/e/Inventory/credentials/shared.yml',
                   'example:\n  type: secret\n  data:\n    secret: envgeneNullValue\n')
    write(repo, 'environments/c/e/Credentials/credentials.yml',
          'example:\n  type: secret\n  data:\n    secret: envgeneNullValue\n')
    write(repo, 'environments/c/e/cloud.yml', json.dumps(cloud))
    result = run_check(repo.root)
    assert not any(f.rule == 'INT-4' and f.path == source for f in result.findings)


def test_unknown_nested_cloud_field_does_not_establish_credential_usage(repo):
    repo.env('c', 'e')
    definition = repo.root / 'environments/c/e/Inventory/env_definition.yml'
    definition.write_text(definition.read_text() + '  sharedMasterCredentialFiles: [shared]\n')
    source = write(repo, 'environments/c/e/Inventory/credentials/shared.yml',
                   'example:\n  type: secret\n  data:\n    secret: envgeneNullValue\n')
    write(repo, 'environments/c/e/cloud.yml', json.dumps({'customConfig': {'credentialsId': 'example'}}))
    findings = [f for f in run_check(repo.root).findings if f.rule == 'INT-4' and f.path == source]
    assert len(findings) == 1 and findings[0].action is Action.REVIEW
