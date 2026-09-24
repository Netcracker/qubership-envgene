import pytest
from ruamel.yaml import YAML

from envgene_linter.connections import compute_connections
from envgene_linter.discovery import build_index
from envgene_linter.usage_candidates import collect_candidates
from test_usage_candidates import write


def analyze(repo):
    from envgene_linter.usage_references import analyze_usage
    index = build_index(repo.root)
    connections = compute_connections(index)
    return analyze_usage(index, connections, collect_candidates(index, connections))


def bind(repo, **bindings):
    path = repo.root / 'environments/c/e/Inventory/env_definition.yml'
    doc = YAML().load(path)
    doc['envTemplate'].update(bindings)
    write(path, doc)


def shared(repo, name='shared', ids=('used', 'orphan')):
    return write(repo.root / f'environments/credentials/{name}.yml',
                 {identifier: {'type': 'secret', 'data': {'secret': 'synthetic'}} for identifier in ids})


def test_same_name_in_sibling_environment_is_not_protected(repo):
    repo.env('c', 'one', deploy={'cloud': ['service']})
    repo.env('c', 'two')
    repo.env_paramset('c', 'one', 'service', {'VALUE': 1})
    repo.env_paramset('c', 'two', 'service', {'VALUE': 2})
    assert {x.candidate.environments: bool(x.references) for x in analyze(repo)} == {
        ('c/one',): True, ('c/two',): False}


def test_shadowed_files_are_referenced(repo):
    repo.env('c', 'e', deploy={'cloud': ['service']})
    repo.site_paramset('service', {'VALUE': 1})
    repo.cluster_paramset('c', 'service', {'VALUE': 2})
    assert all(x.references for x in analyze(repo))


@pytest.mark.parametrize('expression,used', [
    ('${creds.get("used").password}', {'used'}),
    ('before ${creds.get("used")} and ${creds.get("orphan")}', {'used', 'orphan'}),
    ({'$type': 'credRef', 'credId': 'used'}, {'used'}),
    ('${creds.get(DYNAMIC).password}', set()),
    ({'$type': 'credRef', 'credId': '${DYNAMIC}'}, set()),
])
def test_credential_entry_references(repo, expression, used):
    repo.env('c', 'e', deploy={'cloud': ['service']})
    bind(repo, sharedMasterCredentialFiles=['shared'])
    shared(repo)
    write(repo.root / 'environments/parameters/service.yml', {'parameters': {'VALUE': expression}})
    entries = [x for x in analyze(repo) if x.candidate.kind == 'Credential']
    assert {x.candidate.name for x in entries if x.references} == used
    if not used:
        assert all(any(g.reason == 'dynamic' for g in x.gaps) for x in entries)


def test_catalog_binding_alone_does_not_consume_entries(repo):
    repo.env('c', 'e')
    bind(repo, sharedMasterCredentialFiles=['shared'])
    shared(repo)
    assert not any(x.references for x in analyze(repo))


def test_unconnected_parameter_set_supplies_direct_reference(repo):
    repo.env('c', 'e')
    bind(repo, sharedMasterCredentialFiles=['shared'])
    shared(repo)
    write(repo.root / 'environments/parameters/orphan.yml', {'parameters': {'VALUE': '${creds.get("used")}'}})
    result = analyze(repo)
    assert {x.candidate.name for x in result if x.references} == {'used'}


def test_unbound_namespace_supplies_consumers(repo):
    repo.env('c', 'e')
    bind(repo, sharedMasterCredentialFiles=['shared'])
    shared(repo)
    repo.site_paramset('service', {'VALUE': 1})
    write(repo.root / 'environments/c/e/Namespaces/unbound/namespace.yml',
          {'credentialsId': 'used', 'deployParameterSets': ['service']})
    assert {x.candidate.name for x in analyze(repo) if x.references} == {'used', 'service'}


def test_generated_catalog_protects_only_connected_authored_catalog(repo):
    repo.env('c', 'e')
    bind(repo, sharedMasterCredentialFiles=['shared'])
    shared(repo)
    shared(repo, name='unconnected', ids=('used',))
    write(repo.root / 'environments/c/e/Credentials/credentials.yml', {'used': {'type': 'secret'}})
    write(repo.root / 'environments/c/e/cloud.yml', {'defaultCredentialsId': 'used'})
    result = [x for x in analyze(repo) if x.references]
    assert [(x.candidate.path.name, x.candidate.name) for x in result] == [('shared.yml', 'used')]


def test_template_baseline_does_not_select_override(repo):
    repo.env('c', 'e')
    write(repo.root / 'environments/resource_profiles/small.yml', {'baseline': 'small'})
    write(repo.root / 'environments/c/e/cloud.yml', {'profile': {'baseline': 'small'}})
    assert not analyze(repo)[0].references


def test_no_environment_has_explicit_gap(repo):
    repo.site_paramset('orphan', {'VALUE': 1})
    assert [g.reason for g in analyze(repo)[0].gaps] == ['no-environment']


def test_unreadable_definition_adds_gap(repo):
    repo.env('c', 'e')
    repo.site_paramset('orphan', {'VALUE': 1})
    (repo.root / 'environments/c/e/Inventory/env_definition.yml').write_text('broken: [')
    assert any(g.reason == 'unreadable' for g in analyze(repo)[0].gaps)


def test_cyclic_yaml_alias_and_secret_payload_are_not_consumers(repo):
    repo.env('c', 'e')
    bind(repo, sharedMasterCredentialFiles=['shared'])
    path = shared(repo)
    write(path, {'used': {'type': 'secret', 'data': {'secret': '${creds.get("orphan")}' }},
                 'orphan': {'type': 'secret'}})
    parameters = repo.root / 'environments/parameters/cyclic.yml'
    parameters.parent.mkdir()
    parameters.write_text('parameters: &loop\n  SELF: *loop\n')
    assert not any(x.references for x in analyze(repo))


@pytest.mark.parametrize('field,directory', [('sharedTemplateVariables', 'configuration'),
                                           ('envSpecificResourceProfiles', 'resource_profiles')])
def test_other_file_references(repo, field, directory):
    repo.env('c', 'e')
    bind(repo, **{field: {'cloud': 'selected'} if 'Profiles' in field else ['selected']})
    write(repo.root / f'environments/{directory}/selected.yml', {'baseline': 'small'})
    assert len(analyze(repo)) == 1
    assert analyze(repo)[0].references


@pytest.mark.parametrize('consumer', ['integration', 'registry', 'deployer', 'passport', 'artifact'])
def test_system_consumers_protect_exact_catalog_entries(repo, consumer):
    repo.env('c', 'e')
    identifier = 'system-used'
    catalog = repo.root / 'configuration/credentials/credentials.yml'
    if consumer == 'integration':
        write(repo.root / 'configuration/integration.yml', {'self_token': 'envgen.creds.get("system-used").secret'})
    elif consumer == 'registry':
        bind(repo, templateArtifact={'registry': 'selected'})
        write(repo.root / 'configuration/registry.yml', {'selected': {'password': 'envgen.creds.get("system-used").secret'}})
    elif consumer == 'deployer':
        path = repo.root / 'environments/c/e/Inventory/env_definition.yml'
        doc = YAML().load(path)
        doc['inventory']['deployer'] = 'selected'
        write(path, doc)
        write(repo.root / 'configuration/deployer.yml', {'selected': {'token': 'envgen.creds.get("system-used").secret'}})
    elif consumer == 'passport':
        repo.env('c', 'e', cloud_passport='passport')
        repo.passport('passport', {'cloud': {'password': '${creds.get("system-used").secret}'}})
        catalog = repo.root / 'environments/cloud-passport/credentials/passport.yml'
    else:
        repo.env('c', 'e', artifact='template:1')
        bind(repo, sharedMasterCredentialFiles=['shared'])
        catalog = shared(repo, ids=(identifier, 'orphan'))
        write(repo.root / 'configuration/artifact_definitions/template.yml',
              {'name': 'template', 'registry': {'credentialsId': identifier}})
    write(catalog, {identifier: {'type': 'secret'}, 'orphan': {'type': 'secret'}})
    shared(repo, name='unrelated', ids=(identifier,))
    result = analyze(repo)
    assert [(x.candidate.path, x.candidate.name) for x in result if x.references] == [(catalog, identifier)]


def test_alias_name_from_other_environment_does_not_match(repo):
    repo.env('c', 'one', deploy={'cloud': ['alias']})
    repo.env('c', 'two')
    repo.env_paramset('c', 'one', 'actual', {'VALUE': 1})
    source = repo.root / 'environments/c/one/Inventory/parameters/actual.yml'
    alias = repo.root / 'environments/c/two/Inventory/parameters/alias.yml'
    alias.parent.mkdir()
    alias.symlink_to(source)
    assert not analyze(repo)[0].references


def test_unreadable_unconnected_parameter_consumer_adds_credential_gap(repo):
    repo.env('c', 'e')
    shared(repo)
    path = repo.root / 'environments/parameters/broken.yml'
    path.parent.mkdir()
    path.write_text('parameters: [broken')
    entries = [x for x in analyze(repo) if x.candidate.kind == 'Credential']
    assert all(any(g.reason == 'unreadable' for g in x.gaps) for x in entries)


def test_jinja_parameter_consumer_adds_dynamic_gap(repo):
    repo.env('c', 'e')
    shared(repo)
    path = repo.root / 'environments/parameters/template.yml.j2'
    path.parent.mkdir()
    path.write_text('parameters: {{ reference }}')
    assert all(any(g.reason == 'dynamic' for g in x.gaps) for x in analyze(repo))


@pytest.mark.parametrize('consumer', ['registry', 'generated'])
def test_unavailable_authoritative_catalog_does_not_fall_back(repo, consumer):
    repo.env('c', 'e', deploy={'cloud': ['service']})
    bind(repo, sharedMasterCredentialFiles=['shared'])
    shared(repo)
    if consumer == 'registry':
        bind(repo, templateArtifact={'registry': 'selected'})
        write(repo.root / 'configuration/registry.yml', {'selected': {'password': 'envgen.creds.get("used").secret'}})
    else:
        write(repo.root / 'environments/parameters/service.yml', {'parameters': {'VALUE': '${creds.get("used").secret}'}})
        path = repo.root / 'environments/c/e/Credentials/credentials.yml'
        path.parent.mkdir()
        path.write_text('broken: [')
    entries = [x for x in analyze(repo) if x.candidate.kind == 'Credential']
    assert not any(x.references for x in entries)
    assert all(any(g.reason in ('unreadable', 'provenance') for g in x.gaps) for x in entries)


@pytest.mark.parametrize('bag', [['${creds.get("used").secret}'], '${creds.get("used").secret}'])
@pytest.mark.parametrize('source', ['parameter', 'application', 'cloud', 'namespace'])
def test_invalid_parameter_bags_are_uncertain_not_reference_evidence(repo, bag, source):
    repo.env('c', 'e')
    bind(repo, sharedMasterCredentialFiles=['shared'])
    shared(repo)
    if source == 'parameter':
        path, doc = 'environments/parameters/orphan.yml', {'parameters': bag}
    elif source == 'application':
        path, doc = 'environments/parameters/orphan.yml', {'applications': [{'appName': 'app', 'parameters': bag}]}
    elif source == 'cloud':
        path, doc = 'environments/c/e/cloud.yml', {'deployParameters': bag}
    else:
        path, doc = 'environments/c/e/Namespaces/ns/namespace.yml', {'deployParameters': bag}
    write(repo.root / path, doc)
    entries = [x for x in analyze(repo) if x.candidate.kind == 'Credential']
    assert not any(x.references for x in entries)
    assert all(any(g.reason == 'unreadable' for g in x.gaps) for x in entries)


@pytest.mark.parametrize('linked', ['catalog', 'consumer'])
def test_resolved_system_paths_do_not_bypass_directory_symlink_guard(repo, linked):
    repo.env('c', 'e')
    bind(repo, templateArtifact={'registry': 'selected'})
    if linked == 'catalog':
        write(repo.root / 'configuration/registry.yml', {'selected': {'password': 'envgen.creds.get("used").secret'}})
        write(repo.root / 'payload/credentials.yml', {'used': {'type': 'secret'}, 'orphan': {'type': 'secret'}})
        (repo.root / 'configuration/credentials').symlink_to(repo.root / 'payload', target_is_directory=True)
        assert analyze(repo) == []
    else:
        write(repo.root / 'payload/registry.yml', {'selected': {'password': 'envgen.creds.get("used").secret'}})
        write(repo.root / 'payload/credentials/credentials.yml', {'used': {'type': 'secret'}})
        (repo.root / 'configuration').symlink_to(repo.root / 'payload', target_is_directory=True)
        assert analyze(repo) == []
