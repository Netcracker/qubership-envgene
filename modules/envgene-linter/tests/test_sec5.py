import pytest
from ruamel.yaml import YAML

from envgene_linter.discovery import build_index
from envgene_linter.rules.sec5 import check
from envgene_linter.report import render
from envgene_linter.html_report import render_html

TOKEN = 'ENC[AES256_GCM,data:YWJj,iv:YWJj,tag:YWJj,type:str]'
META = {'mac': TOKEN, 'age': [{'recipient': 'age1synthetic', 'enc': 'synthetic-envelope'}], 'version': '3.8.1'}
ID = 'private-credential-identifier'
SECRET = 'private-test-secret-value'


def write(path, doc):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w') as stream:
        YAML().dump(doc, stream)
    return path


def cred(value=SECRET, kind='secret'):
    return {'type': kind, 'data': {'secret': value}}


def setup(repo, value=SECRET, metadata=False):
    repo.env('c', 'e')
    doc = {ID: cred(value)}
    if metadata:
        doc['sops'] = META
    return write(repo.root / 'environments/c/e/Credentials/credentials.yml', doc)


def findings(repo):
    return check(build_index(repo.root))


@pytest.mark.parametrize('value,metadata,reason', [
    (SECRET, False, 'literal'), (TOKEN, True, None),
    (TOKEN, False, 'source'), ('${CI_SECRET}', False, 'source'),
    ('[encrypted:AES256_Fernet]synthetic', False, 'SOPS'),
    ('', False, None), (None, False, None),
])
def test_generated_credential_classification(repo, value, metadata, reason):
    path = setup(repo, value, metadata)
    result = findings(repo)
    if reason is None:
        assert result == []
    else:
        assert len(result) == 1
        assert result[0].path == path
        assert reason in result[0].message
        assert (result[0].issue_type.value, result[0].action.value) == ('Information', 'Review')
        for output in (repr(result), render(result), render_html(result, repo.root)):
            assert SECRET not in output and ID not in output and 'CI_SECRET' not in output


def test_partial_sops_document_and_encrypted_type(repo):
    path = setup(repo, TOKEN, True)
    write(path, {ID: {'type': TOKEN, 'data': {'username': TOKEN, 'password': SECRET}}, 'sops': META})
    result = findings(repo)
    assert len(result) == 1 and 'literal' in result[0].message
    assert result[0].line == 5


@pytest.mark.parametrize('external,expected', [
    ({'type': 'external', 'secretStore': 'store'}, 0),
    ({'type': 'external', 'secretStore': 'store', 'properties': [{'name': 'password'}]}, 0),
    ({'type': 'external'}, 0),
    ({'type': 'external', 'secretStore': 'store', 'data': {'password': SECRET}}, 2),
])
def test_external_shapes(repo, external, expected):
    path = setup(repo)
    write(path, {ID: external})
    assert len(findings(repo)) == expected


def test_unconnected_file_is_not_checked(repo):
    repo.env('c', 'e')
    write(repo.root / 'environments/credentials/unused.yml', {ID: cred()})
    write(repo.root / 'configuration/credentials/credentials.yml', {ID: cred()})
    assert findings(repo) == []


def params(repo, value, key='DB_PASSWORD'):
    repo.env('c', 'e', deploy={'cloud': ['service']})
    return write(repo.root / 'environments/parameters/service.yml', {'name': 'service', 'parameters': {key: value}})


def test_parameter_reference_uses_generated_catalog_and_deduplicates(repo):
    path = setup(repo)
    params(repo, '${creds.get("' + ID + '").secret}', key='VALUE')
    result = findings(repo)
    assert len(result) == 1 and result[0].path == path


def test_unresolved_reference_is_not_a_secret_protection_finding(repo):
    params(repo, '${creds.get("' + ID + '").secret}', key='VALUE')
    result = findings(repo)
    assert result == []


def test_parameter_unknown_expression_and_composite_are_reviewed(repo):
    params(repo, '{{ hidden_source }}')
    assert len(findings(repo)) == 1
    params(repo, '${creds.get("' + ID + '").secret} suffix', key='VALUE')
    assert len(findings(repo)) == 1


def test_apps_lists_and_cycles_are_bounded(repo):
    path = params(repo, SECRET)
    bag = {'DB_PASSWORD': [SECRET, '${UNVERIFIED}']}
    bag['recursive'] = bag
    write(path, {'name': 'service', 'applications': [{'name': 'app', 'parameters': bag}]})
    result = findings(repo)
    assert len(result) == 2  # ruamel resolves this recursive alias to None; both scalar leaves remain


def test_selected_bad_yaml_reports_without_parser_text(repo):
    path = setup(repo)
    path.write_text('broken: [' + SECRET)
    result = findings(repo)
    assert len(result) == 1 and result[0].line == 1 and SECRET not in repr(result)


def test_reference_cycle_is_reviewed(repo):
    path = setup(repo)
    write(path, {ID: cred('${creds.get("' + ID + '").secret}')})
    result = findings(repo)
    assert len(result) == 1 and 'source' in result[0].message


def test_integration_fallback_and_explicit_override(repo):
    repo.env('c', 'e')
    path = write(repo.root / 'configuration/integration.yml', {'gitlab': {'url': 'https://example.invalid'}})
    assert findings(repo) == []
    write(path, {'self_token': SECRET})
    result = findings(repo)
    assert len(result) == 1 and result[0].path == path


def test_system_catalog_only_referenced_entries(repo):
    repo.env('c', 'e')
    write(repo.root / 'configuration/integration.yml', {'self_token': "envgen.creds.get('" + ID + "').secret"})
    path = write(repo.root / 'configuration/credentials/credentials.yml', {ID: cred(TOKEN), 'unused': cred(), 'sops': META})
    assert findings(repo) == []
    write(path, {ID: cred(), 'unused': cred()})
    result = findings(repo)
    assert len(result) == 1 and result[0].path == path


def test_reference_wrong_kind_and_missing_property_are_unknown(repo):
    path = setup(repo)
    write(path, {ID: {'type': 'external', 'secretStore': 'store'}})
    params(repo, '${creds.get("' + ID + '").secret}')
    assert len(findings(repo)) == 1
    write(path, {ID: cred(TOKEN), 'sops': META})
    params(repo, '${creds.get("' + ID + '").missing}')
    assert len(findings(repo)) == 1


def test_reference_to_external_definition_is_accepted(repo):
    path = setup(repo)
    write(path, {ID: {'type': 'external', 'secretStore': 'store'}})
    params(repo, {'$type': 'credRef', 'credId': ID})
    assert findings(repo) == []


def test_bare_credential_id_accepts_external_without_local_data(repo):
    path = setup(repo)
    write(path, {ID: {'type': 'external', 'secretStore': 'store'}})
    write(repo.root / 'environments/c/e/cloud.yml', {'defaultCredentialsId': ID})
    assert findings(repo) == []


def test_bare_missing_credential_id_is_not_a_secret(repo):
    repo.env('c', 'e')
    path = write(repo.root / 'environments/c/e/cloud.yml', {'defaultCredentialsId': ID})
    result = findings(repo)
    assert result == []


def test_invalid_external_cycle_cannot_recurse_forever(repo, monkeypatch):
    from envgene_linter.rules.sec5 import _Scanner
    original = _Scanner.reference
    calls = []
    def bounded(self, *args):
        calls.append(1)
        assert len(calls) < 5, "reference recursion was not bounded"
        return original(self, *args)
    monkeypatch.setattr(_Scanner, "reference", bounded)
    path = setup(repo)
    write(path, {ID: {'type': 'external', 'secretStore': 'store',
                     'data': {'secret': {'$type': 'credRef', 'credId': ID}}}})
    result = findings(repo)
    assert 1 <= len(result) <= 2


def test_invalid_external_inline_material_is_not_hidden_by_reference(repo):
    path = setup(repo)
    write(path, {ID: {'type': 'external', 'secretStore': 'store', 'data': {'password': SECRET}}})
    params(repo, {'$type': 'credRef', 'credId': ID})
    result = findings(repo)
    assert any('literal' in f.message for f in result)


def test_full_cli_integration_does_not_print_credential_values(repo):
    from click.testing import CliRunner
    from envgene_linter.cli import main
    setup(repo)
    result = CliRunner().invoke(main, ['check', str(repo.root), '--console'])
    assert result.exit_code == 0
    assert 'SEC-5\nNo findings' not in result.output
    assert result.output.index('SEC-4') < result.output.index('SEC-5') < result.output.index('NAME-1')
    output = (repo.root / 'envgene-linter-report.html').read_text()
    assert 'SEC-5: Review protection of connected secrets' in output
    assert SECRET not in output and ID not in output


def test_runtime_macro_in_system_consumer_is_not_assumed_evaluated(repo):
    repo.env('c', 'e')
    path = write(repo.root / 'configuration/integration.yml', {'self_token': '${creds.get("' + ID + '").secret}'})
    write(repo.root / 'configuration/credentials/credentials.yml', {ID: cred(TOKEN), 'sops': META})
    result = findings(repo)
    assert len(result) == 1 and result[0].path == path and 'source' in result[0].message


def test_system_macro_in_runtime_consumer_is_unknown(repo):
    setup(repo, TOKEN, True)
    path = params(repo, "envgen.creds.get('" + ID + "').secret", key='VALUE')
    result = findings(repo)
    assert len(result) == 1 and result[0].path == path


def test_credential_data_is_not_evaluated_a_second_time(repo):
    path = setup(repo)
    write(path, {ID: cred('${creds.get("other").secret}'), 'other': cred(TOKEN), 'sops': META})
    result = findings(repo)
    assert len(result) == 1 and result[0].path == path and 'source' in result[0].message


def test_structured_reference_in_bare_id_field_is_unknown(repo):
    path = setup(repo)
    write(path, {ID: {'type': 'external'}})
    cloud = write(repo.root / 'environments/c/e/cloud.yml', {'defaultCredentialsId': {'$type': 'credRef', 'credId': ID}})
    result = findings(repo)
    assert len(result) == 1 and result[0].path == cloud and 'source' in result[0].message


@pytest.mark.parametrize('catalog_state', ['absent', 'empty', 'other', 'protected', 'literal'])
def test_artifact_credential_id_checks_only_available_secret_content(repo, catalog_state):
    repo.env('c', 'e', artifact='template:1')
    artifact = write(repo.root / 'configuration/artifact_definitions/template.yml', {
        'name': 'template', 'groupId': 'example', 'artifactId': 'template',
        'registry': {'name': 'registry', 'credentialsId': ID,
                     'mavenConfig': {'repositoryDomainName': 'https://example.invalid'}},
    })
    catalog = repo.root / 'environments/c/e/Credentials/credentials.yml'
    if catalog_state == 'empty':
        write(catalog, {})
    elif catalog_state == 'other':
        write(catalog, {'another': cred(TOKEN), 'sops': META})
    elif catalog_state in ('protected', 'literal'):
        write(catalog, {ID: cred(TOKEN if catalog_state == 'protected' else SECRET), 'sops': META})
    result = findings(repo)
    assert all(f.path != artifact for f in result)
    if catalog_state == 'literal':
        assert len(result) == 1 and result[0].path == catalog
        assert 'literal' in result[0].message
    else:
        assert result == []


@pytest.mark.parametrize('reference', ["envgen.creds.get('missing').secret", 'external'])
def test_unavailable_system_or_external_target_is_skipped(repo, reference):
    repo.env('c', 'e')
    if reference == 'external':
        params(repo, {'$type': 'credRef', 'credId': ID})
    else:
        write(repo.root / 'configuration/integration.yml', {'self_token': reference})
    assert findings(repo) == []


pytestmark = pytest.mark.usefixtures("all_rules_enabled")
