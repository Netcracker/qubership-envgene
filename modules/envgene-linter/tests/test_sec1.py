from pathlib import Path

import pytest
from click.testing import CliRunner
from ruamel.yaml import YAML

from envgene_linter.cli import main
from envgene_linter.discovery import build_index
from envgene_linter.engine import run_check
from envgene_linter.html_report import render_html
from envgene_linter.report import render


SECRET = 'synthetic-secret-for-sec1-tests'


def write(path, doc):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w') as stream:
        YAML().dump(doc, stream)
    return path


def bound(repo, params):
    repo.env('c', 'e', deploy={'cloud': ['service-deploy']})
    return write(repo.root / 'environments/c/e/Inventory/parameters/service-deploy.yml',
                 {'name': 'service-deploy', 'parameters': params})


def findings(repo):
    return [f for f in run_check(repo.root).findings if f.rule == 'SEC-1']


@pytest.mark.parametrize('key', ['DB_PASSWORD', 'admin_password', 'password', 'apiKey',
                                     'accessToken', 'APIKey', 'DBPassword', 'PaSsWoRd', 'DB_PaSsWoRd', 'client.secret', 'private_key', 'db.passwd', 'DB_PASS'])
def test_literal_secret_parameter(repo, key):
    path = bound(repo, {key: SECRET})
    result = findings(repo)
    assert len(result) == 1
    assert result[0].path == path
    assert result[0].line == 3
    assert result[0].key == 'parameters.' + key
    assert result[0].issue_type.value == 'Warning'
    assert result[0].action.value == 'Fix'
    assert SECRET not in repr(result)
    assert SECRET not in render(result)
    assert SECRET not in render_html(result, repo.root)


@pytest.mark.parametrize('value', ['', None, '${creds.get("db-cred").password}',
                                  "${creds.get('db-cred').secret}", '${OTHER_PASSWORD}',
                                  '{{ password }}', {'$type': 'credRef', 'credId': 'db', 'property': 'password'}])
def test_nonliteral_or_empty_value_is_not_reported(repo, value):
    bound(repo, {'DB_PASSWORD': value})
    assert findings(repo) == []


@pytest.mark.parametrize('key', ['LOG_LEVEL', 'token.path', 'TOKEN_TTL', 'PASSWORD_LENGTH',
                                     'secretName', 'credentialsId', 'SECRET_FLOW'])
def test_nonsecret_parameter_names(repo, key):
    bound(repo, {key: 'example'})
    assert findings(repo) == []


def test_nested_lists_and_application_parameters(repo):
    path = bound(repo, {'db': {'instances': [{'password': SECRET}]}})
    write(path, {'parameters': {'db': {'instances': [{'password': SECRET}]}},
                 'applications': [{'name': 'app', 'parameters': {'api_key': SECRET}}]})
    result = findings(repo)
    assert {f.key for f in result} == {'parameters.db.instances.0.password',
                                     'applications.0.parameters.api_key'}


@pytest.mark.parametrize('value', [123456, False, 'changeme', 'ENC[synthetic]'])
def test_literal_does_not_need_to_be_complex_or_string(repo, value):
    bound(repo, {'DB_PASSWORD': value})
    assert len(findings(repo)) == 1


def test_unbound_and_shadowed_files_are_ignored(repo):
    repo.env('c', 'e', deploy={'cloud': ['shared']})
    repo.site_paramset('unused', {'DB_PASSWORD': SECRET})
    repo.site_paramset('shared', {'DB_PASSWORD': SECRET})
    repo.cluster_paramset('c', 'shared', {'LOG_LEVEL': 'info'})
    assert findings(repo) == []


def test_cloud_and_connected_namespace_only(repo):
    repo.env('c', 'e', deploy={'app': ['service-deploy'], 'missing': ['absent']})
    repo.site_paramset('service-deploy', {'LOG_LEVEL': 'info'})
    env = repo.root / 'environments/c/e'
    cloud = write(env / 'cloud.yml', {'deployParameters': {'DB_PASSWORD': SECRET}})
    ns = write(env / 'Namespaces/app/namespace.yml', {'technicalConfigurationParameters': {'API_KEY': SECRET}})
    write(env / 'Namespaces/unused/namespace.yml', {'deployParameters': {'DB_PASSWORD': SECRET}})
    write(env / 'Namespaces/missing/namespace.yml', {'deployParameters': {'DB_PASSWORD': SECRET}})
    write(repo.root / 'environments/c/orphan/cloud.yml', {'deployParameters': {'DB_PASSWORD': SECRET}})
    assert {f.path for f in findings(repo)} == {cloud, ns}


def test_credentials_are_not_parameter_bags(repo):
    bound(repo, {'LOG_LEVEL': 'info'})
    write(repo.root / 'environments/c/e/Inventory/credentials/inventory_generation_creds.yml',
          {'db': {'type': 'usernamePassword', 'data': {'password': SECRET}}})
    assert findings(repo) == []


def test_direct_rule_matches_engine(repo):
    bound(repo, {'DB_PASSWORD': SECRET})
    from envgene_linter.rules.sec1 import check
    assert check(build_index(repo.root)) == findings(repo)


def test_malformed_cloud_does_not_disclose_source(repo):
    bound(repo, {'LOG_LEVEL': 'info'})
    cloud = repo.root / 'environments/c/e/cloud.yml'
    cloud.write_text('deployParameters: [' + SECRET + '\n')
    result = CliRunner().invoke(main, ['check', str(repo.root)])
    assert result.exit_code == 0
    assert SECRET not in result.output


def test_external_cloud_is_not_loaded(repo, tmp_path):
    bound(repo, {'LOG_LEVEL': 'info'})
    external = tmp_path.parent / (tmp_path.name + '-external.yml')
    try:
        write(external, {'deployParameters': {'DB_PASSWORD': SECRET}})
        (repo.root / 'environments/c/e/cloud.yml').symlink_to(external)
        assert findings(repo) == []
    finally:
        external.unlink(missing_ok=True)


def test_list_of_literal_secrets(repo):
    bound(repo, {'password': [SECRET, '${creds.get("db").password}']})
    result = findings(repo)
    assert [f.key for f in result] == ['parameters.password.0']


def test_profile_binding_selects_namespace(repo):
    repo.env('c', 'e')
    definition = repo.root / 'environments/c/e/Inventory/env_definition.yml'
    with definition.open('a') as stream:
        stream.write('  envSpecificResourceProfiles:\n    app: profile\n')
    write(repo.root / 'environments/resource_profiles/profile.yml', {'name': 'profile'})
    path = write(repo.root / 'environments/c/e/Namespaces/app/namespace.yml',
                 {'e2eParameters': {'DB_PASSWORD': SECRET}})
    assert [f.path for f in findings(repo)] == [path]


def test_git_target_cloud_is_not_checked(repo):
    bound(repo, {'LOG_LEVEL': 'info'})
    hidden = write(repo.root / '.git/hidden.yml', {'deployParameters': {'DB_PASSWORD': SECRET}})
    (repo.root / 'environments/c/e/cloud.yml').symlink_to(hidden)
    assert findings(repo) == []


def test_engine_and_cli_report_integration(repo):
    bound(repo, {'DB_PASSWORD': SECRET})
    result = CliRunner().invoke(main, ['check', str(repo.root), '--console'])
    assert result.exit_code == 0
    assert result.output.index('PLACE-10') < result.output.index('SEC-1') < result.output.index('NAME-1')
    assert SECRET not in result.output
    html = (repo.root / 'envgene-linter-report.html').read_text()
    assert 'SEC-1: No literal secrets in parameters' in html
    assert SECRET not in html


pytestmark = pytest.mark.usefixtures("all_rules_enabled")
