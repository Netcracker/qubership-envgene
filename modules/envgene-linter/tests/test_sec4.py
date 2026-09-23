import pytest
from ruamel.yaml import YAML

from envgene_linter.discovery import build_index
from envgene_linter.rules.sec4 import check
from envgene_linter.report import render
from envgene_linter.html_report import render_html

ID = 'private-credential-id'
OTHER = 'private-other-id'
VALUE = 'private-test-value'
TOKEN = 'ENC[AES256_GCM,data:YWJj,iv:YWJj,tag:YWJj,type:str]'
META = {'mac': TOKEN, 'age': [{'recipient': 'age1synthetic', 'enc': 'envelope'}], 'version': '3.8.1'}


def write(path, doc):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w') as stream:
        YAML().dump(doc, stream)
    return path


def pair(external=False):
    if external:
        return {'type': 'external', 'properties': [{'name': 'username'}, {'name': 'password'}]}
    return {'type': 'usernamePassword', 'data': {'username': VALUE, 'password': VALUE}}


def ref(field, identifier=ID, external=False, system=False):
    if external:
        return {'$type': 'credRef', 'credId': identifier, 'property': field}
    call = f'creds.get("{identifier}").{field}'
    return 'envgen.' + call if system else '${' + call + '}'


def setup(repo, params=None, definitions=None, generated=True, env='e'):
    repo.env('c', env, deploy={'cloud': ['service']})
    if params is None:
        params = {'DB_USERNAME': ref('username'), 'DB_PASSWORD': ref('password')}
    source = write(repo.root / f'environments/c/{env}/Inventory/parameters/service.yml', {'name': 'service', 'parameters': params})
    if generated:
        catalog = repo.root / f'environments/c/{env}/Credentials/credentials.yml'
    else:
        definition = repo.root / f'environments/c/{env}/Inventory/env_definition.yml'
        doc = YAML().load(definition.read_text())
        doc['envTemplate']['sharedMasterCredentialFiles'] = ['shared']
        write(definition, doc)
        catalog = repo.root / 'environments/credentials/shared.yml'
    write(catalog, {ID: pair()} if definitions is None else definitions)
    return source, catalog


def findings(repo):
    return check(build_index(repo.root))


KEYS = [
    ('DEFAULT_TENANT_ADMIN_LOGIN', 'DEFAULT_TENANT_ADMIN_PASSWORD'),
    ('STORAGE_USERNAME', 'STORAGE_PASSWORD'),
    ('CSE_GRAYLOG_USER', 'CSE_GRAYLOG_PASSWORD'),
    ('OPENSEARCH_CLIENT_USER_NAME', 'OPENSEARCH_CLIENT_PASSWORD'),
    ('DUMPS_MONGO_USER', 'DUMPS_MONGO_PASSWD'),
    ('DB_USER', 'DB_PASS'), ('db_user', 'db_pwd'),
    ('kafkaAuthUsername', 'kafkaAuthPassword'), ('sasl.username', 'sasl.password'),
]


@pytest.mark.parametrize('keys', KEYS)
@pytest.mark.parametrize('same_id', [False, True])
def test_obvious_pairs_compare_ids_without_catalog(repo, keys, same_id):
    source, catalog = setup(repo, {keys[0]: ref('username'), keys[1]: ref('password', ID if same_id else OTHER)})
    catalog.unlink()
    result = findings(repo)
    if same_id:
        assert result == []
    else:
        assert len(result) == 1 and result[0].path == source
        assert len(result[0].locations) == 2
        assert 'same Credential ID' in result[0].message
        assert (result[0].issue_type.value, result[0].action.value) == ('Information', 'Review')
        for output in (repr(result), render(result), render_html(result, repo.root)):
            assert ID not in output and OTHER not in output and VALUE not in output


@pytest.mark.parametrize('definitions', [{}, {ID: {'type': 'secret'}}, {ID: {'type': 'usernamePassword', 'data': {'password': VALUE}}}])
def test_definition_existence_and_shape_are_outside_sec4(repo, definitions):
    setup(repo, definitions=definitions)
    assert findings(repo) == []


@pytest.mark.parametrize('params', [
    {'DB_USERNAME': ref('username')},
    {'DB_PASSWORD': ref('password')},
    {'VALUE': ref('username'), 'OTHER': ref('password', OTHER)},
    {'DB_USERNAME': VALUE, 'DB_PASSWORD': ref('password')},
    {'DB_USERNAME': VALUE, 'DB_PASSWORD': VALUE},
    {'DB_USERNAME': ref('username'), 'DB_PASSWORD': '${creds.get(DYNAMIC).password}'},
    {'DB_USERNAME': ref('username'), 'DB_PASSWORD': ref('password', OTHER) + ' suffix'},
])
def test_missing_pair_or_unparseable_id_is_skipped(repo, params):
    setup(repo, params, definitions={})
    assert findings(repo) == []


@pytest.mark.parametrize('keys', [
    ('SSM_CMDB_USER', 'SSM_CMDB_TOKEN'), ('AUTH_CLIENT_ID', 'AUTH_CLIENT_SECRET'),
    ('accessKey', 'accessSecret'), ('principal', 'credentials'),
    ('DB_USER', 'OTHER_PASSWORD'), ('DBSUPERUSER', 'DBPASSWORD'),
    ('IDP_ADMIN_USER_NAME', 'IDP_ADMIN_USER_PASSWORD'),
])
def test_unapproved_or_different_prefix_pairs_are_skipped(repo, keys):
    setup(repo, {keys[0]: ref('username'), keys[1]: ref('password', OTHER)}, definitions={})
    assert findings(repo) == []


@pytest.mark.parametrize('external', [False, True])
def test_existing_unprefixed_pairs_and_structured_references(repo, external):
    setup(repo, {'username': ref('username', external=external), 'password': ref('password', OTHER, external)}, definitions={})
    assert len(findings(repo)) == 1


def test_id_comparison_does_not_validate_referenced_fields(repo):
    setup(repo, {'DB_USER': ref('secret'), 'DB_PASS': ref('secret')}, definitions={})
    assert findings(repo) == []
    setup(repo, {'DB_USER': ref('secret'), 'DB_PASS': ref('secret', OTHER)}, definitions={})
    assert len(findings(repo)) == 1


def test_nested_mappings_lists_and_applications_do_not_form_cross_pairs(repo):
    source, _ = setup(repo, {'a': {'DB_USER': ref('username')}, 'b': {'DB_PASSWORD': ref('password', OTHER)},
                           'items': [{'DB_USER': ref('username')}, {'DB_PASSWORD': ref('password', OTHER)}]}, definitions={})
    assert findings(repo) == []
    write(source, {'applications': [
        {'name': 'a', 'parameters': {'DB_USER': ref('username')}},
        {'name': 'b', 'parameters': {'DB_PASSWORD': ref('password', OTHER)}},
        {'name': 'c', 'parameters': {'DB_USER': ref('username'), 'DB_PASSWORD': ref('password', OTHER)}},
    ]})
    assert len(findings(repo)) == 1


def test_disconnected_pair_is_ignored(repo):
    setup(repo, {}, definitions={})
    write(repo.root / 'environments/parameters/unused.yml', {'parameters': {'DB_USER': ref('username'), 'DB_PASS': ref('password', OTHER)}})
    assert findings(repo) == []


def test_environments_do_not_form_cross_pairs(repo):
    setup(repo, {'DB_USER': ref('username')}, definitions={})
    setup(repo, {'DB_PASSWORD': ref('password', OTHER)}, definitions={}, env='other')
    assert findings(repo) == []


def test_system_pair_compares_ids_without_root_catalog(repo):
    repo.env('c', 'e')
    definition = repo.root / 'environments/c/e/Inventory/env_definition.yml'
    doc = YAML().load(definition.read_text())
    doc['envTemplate']['templateArtifact'] = {'registry': 'active'}
    write(definition, doc)
    source = write(repo.root / 'configuration/registry.yml', {'active': {'username': ref('username', system=True), 'password': ref('password', OTHER, system=True)}})
    result = findings(repo)
    assert len(result) == 1 and result[0].path == source


def test_recursive_alias_is_bounded(repo):
    values = {'DB_USER': ref('username'), 'DB_PASS': ref('password', OTHER)}
    values['recursive'] = values
    setup(repo, values, definitions={})
    assert len(findings(repo)) == 1


def test_direct_engine_and_html_integration(repo):
    from envgene_linter.engine import run_check
    setup(repo, {'DB_USER': ref('username'), 'DB_PASS': ref('password', OTHER)}, definitions={})
    result = [f for f in run_check(repo.root).findings if f.rule == 'SEC-4']
    assert result == findings(repo)
    assert 'SEC-4: Credential pairs reference the same ID' in render_html(result, repo.root)


def test_unparseable_outer_pair_does_not_hide_nested_pair(repo):
    setup(repo, {'DB_USER': {'username': ref('username'), 'password': ref('password', OTHER)}, 'DB_PASS': VALUE}, definitions={})
    assert len(findings(repo)) == 1


def test_multiple_user_aliases_compare_only_against_password(repo):
    setup(repo, {'DB_USER': ref('username'), 'DB_LOGIN': ref('username', OTHER), 'DB_PASS': ref('password')}, definitions={})
    result = findings(repo)
    assert len(result) == 1 and len(result[0].locations) == 2
    setup(repo, {'DB_USER': ref('username'), 'DB_LOGIN': ref('username', OTHER), 'DB_PASS': VALUE}, definitions={})
    assert findings(repo) == []


def test_names_ignore_case_but_ids_do_not(repo):
    setup(repo, {'db_User': ref('username', 'Example'), 'DB_PASSWORD': ref('password', 'example')}, definitions={})
    assert len(findings(repo)) == 1


pytestmark = pytest.mark.usefixtures("all_rules_enabled")
