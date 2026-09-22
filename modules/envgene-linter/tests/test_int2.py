import pytest
from ruamel.yaml import YAML

from envgene_linter.discovery import build_index
from envgene_linter.rules.int2 import check
from envgene_linter.report import render
from envgene_linter.html_report import render_html

ID = 'private-reference-id'
SECRET = 'private-secret-value'


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w') as stream:
        YAML().dump(value, stream)
    return path


def params(repo, value):
    repo.env('c', 'e', deploy={'cloud': ['service']})
    return write(repo.root / 'environments/parameters/service.yml', {'name': 'service', 'parameters': {'VALUE': value}})


def catalog(repo, value):
    return write(repo.root / 'environments/c/e/Credentials/credentials.yml', value)


def ref(identifier=ID):
    return '${creds.get("' + identifier + '").password}'


def findings(repo):
    return check(build_index(repo.root))


def assert_kind(result, kind):
    assert len(result) == 1
    expected = ('Information', 'Review') if kind == 'unknown' else ('Warning', 'Fix')
    assert (result[0].issue_type.value, result[0].action.value) == expected
    assert kind in result[0].message.lower()


@pytest.mark.parametrize('value', [ref(), '${creds.get("' + ID + '")}', {'$type': 'credRef', 'credId': ID}, 'prefix ' + ref() + ' suffix'])
def test_credential_reference_exists_or_missing(repo, value):
    source = params(repo, value)
    catalog(repo, {ID: {'type': 'secret', 'data': {'secret': SECRET}}})
    assert findings(repo) == []  # existence only, not type or property completeness
    catalog(repo, {})
    result = findings(repo)
    assert_kind(result, 'missing')
    assert result[0].path == source and result[0].line == 3
    for output in (repr(result), render(result), render_html(result, repo.root)):
        assert ID not in output and SECRET not in output


@pytest.mark.parametrize('value', ['${creds.get(DYNAMIC).password}', {'$type': 'credRef', 'credId': '${DYNAMIC}'}, '${creds.get("' + ID + '").password'])
def test_dynamic_or_malformed_credential_reference_is_unknown(repo, value):
    params(repo, value)
    catalog(repo, {})
    assert_kind(findings(repo), 'unknown')


def test_absent_generated_catalog_is_not_proof_of_missing_credential(repo):
    params(repo, ref())
    assert_kind(findings(repo), 'unknown')


def test_shared_connected_credential_can_resolve_without_generated_catalog(repo):
    params(repo, ref())
    path = repo.root / 'environments/c/e/Inventory/env_definition.yml'
    doc = YAML().load(path)
    doc['envTemplate']['sharedMasterCredentialFiles'] = ['shared']
    write(path, doc)
    write(repo.root / 'environments/credentials/shared.yml', {ID: {'type': 'secret'}})
    assert findings(repo) == []


def test_generated_catalog_takes_precedence_over_shared_input(repo):
    test_shared_connected_credential_can_resolve_without_generated_catalog(repo)
    catalog(repo, {})
    assert_kind(findings(repo), 'missing')


def test_unreadable_catalog_is_unknown_without_parser_leak(repo):
    params(repo, ref())
    path = catalog(repo, {})
    path.write_text('broken: [' + SECRET)
    result = findings(repo)
    assert_kind(result, 'unknown')
    assert SECRET not in repr(result)


def test_other_environment_and_unconnected_credential_cannot_resolve_reference(repo):
    params(repo, ref())
    catalog(repo, {})
    repo.env('c', 'other')
    write(repo.root / 'environments/c/other/Credentials/credentials.yml', {ID: {}})
    write(repo.root / 'environments/credentials/unused.yml', {ID: {}})
    assert_kind(findings(repo), 'missing')


def test_system_credential_reference_uses_root_catalog(repo):
    repo.env('c', 'e')
    write(repo.root / 'configuration/integration.yml', {'self_token': 'envgen.creds.get("' + ID + '").secret'})
    path = write(repo.root / 'configuration/credentials/credentials.yml', {ID: {}})
    assert findings(repo) == []
    write(path, {})
    assert_kind(findings(repo), 'missing')


def test_bare_credential_id_in_connected_artifact_is_checked(repo):
    repo.env('c', 'e', artifact='template:1')
    write(repo.root / 'configuration/artifact_definitions/template.yml', {'name': 'template', 'registry': {'credentialsId': ID}})
    catalog(repo, {})
    assert_kind(findings(repo), 'missing')


@pytest.mark.parametrize('category', ['deploy', 'e2e', 'technical'])
def test_missing_paramset_with_unavailable_template_is_unknown(repo, category):
    repo.env('c', 'e', **{category: {'cloud': ['missing']}})
    result = findings(repo)
    assert_kind(result, 'unknown')
    assert result[0].path.name == 'env_definition.yml'


def test_paramset_priority_is_not_ambiguity(repo):
    repo.env('c', 'e', deploy={'cloud': ['selected']})
    repo.site_paramset('selected', {})
    repo.cluster_paramset('c', 'selected', {})
    repo.env_paramset('c', 'e', 'selected', {})
    assert findings(repo) == []


def test_two_paramset_fragments_merge_deterministically(repo):
    repo.env('c', 'e', deploy={'cloud': ['selected']})
    repo.env_paramset('c', 'e', 'selected', {})
    write(repo.root / 'environments/c/e/Inventory/parameters/selected.yaml', {'name': 'selected'})
    assert findings(repo) == []


@pytest.mark.parametrize('name', ['{{ selected }}', 'selected'])
def test_dynamic_binding_or_jinja_target_is_unknown(repo, name):
    repo.env('c', 'e', deploy={'cloud': [name]})
    path = repo.root / 'environments/parameters/selected.yml.j2'
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text('name: {{ name }}')
    assert_kind(findings(repo), 'unknown')


def test_resource_profile_missing_and_existing(repo):
    repo.env('c', 'e')
    path = repo.root / 'environments/c/e/Inventory/env_definition.yml'
    doc = YAML().load(path)
    doc['envTemplate']['envSpecificResourceProfiles'] = {'cloud': 'selected'}
    write(path, doc)
    assert_kind(findings(repo), 'missing')
    write(repo.root / 'environments/resource_profiles/selected.yml', {'name': 'selected'})
    assert findings(repo) == []


def test_rendered_object_template_paramset_is_unknown_when_unavailable(repo):
    repo.env('c', 'e')
    write(repo.root / 'environments/c/e/cloud.yml', {'deployParameterSets': ['template-only']})
    assert_kind(findings(repo), 'unknown')


def test_unused_paramset_and_credential_definitions_are_not_scanned(repo):
    repo.env('c', 'e')
    write(repo.root / 'environments/parameters/unused.yml', {'parameters': {'VALUE': ref()}})
    catalog(repo, {'unused': {'data': {'secret': ref()}}})
    assert findings(repo) == []


def test_integration_with_engine_and_reports(repo):
    from envgene_linter.engine import run_check
    repo.env('c', 'e', deploy={'cloud': ['missing']})
    result = [f for f in run_check(repo.root).findings if f.rule == 'INT-2']
    assert result == findings(repo)
    assert 'INT-2: Every reference resolves' in render_html(result, repo.root)


def test_missing_paramset_without_template_source_is_definite(repo):
    repo.env('c', 'e', deploy={'cloud': ['missing']})
    path = repo.root / 'environments/c/e/Inventory/env_definition.yml'
    doc = YAML().load(path)
    del doc['envTemplate']['name']
    write(path, doc)
    assert_kind(findings(repo), 'missing')


def test_resource_profile_ambiguity_at_selected_scope(repo):
    repo.env('c', 'e')
    path = repo.root / 'environments/c/e/Inventory/env_definition.yml'
    doc = YAML().load(path)
    doc['envTemplate']['envSpecificResourceProfiles'] = {'cloud': 'selected'}
    write(path, doc)
    for name in ('selected.yml', 'selected.yaml'):
        write(repo.root / 'environments/resource_profiles' / name, {'name': 'selected'})
    assert_kind(findings(repo), 'ambiguous')


def test_resource_profile_alias_uses_reference_filename(repo):
    repo.env('c', 'e')
    path = repo.root / 'environments/c/e/Inventory/env_definition.yml'
    doc = YAML().load(path)
    doc['envTemplate']['envSpecificResourceProfiles'] = {'cloud': 'alias'}
    write(path, doc)
    target = write(repo.root / 'environments/resource_profiles/original.yml', {'name': 'original'})
    alias = repo.root / 'environments/c/e/Inventory/resource_profiles/alias.yml'
    alias.parent.mkdir(parents=True, exist_ok=True)
    alias.symlink_to(target)
    assert findings(repo) == []


def test_bare_runtime_id_can_use_connected_shared_catalog(repo):
    test_shared_connected_credential_can_resolve_without_generated_catalog(repo)
    write(repo.root / 'environments/c/e/cloud.yml', {'defaultCredentialsId': ID})
    assert findings(repo) == []


def test_rendered_profiles_use_generated_profile_files(repo):
    repo.env('c', 'e')
    write(repo.root / 'environments/c/e/cloud.yml', {'profile': {'name': 'selected', 'baseline': 'base'}})
    for name in ('selected', 'base'):
        write(repo.root / f'environments/c/e/Profiles/{name}.yml', {'name': name})
    assert findings(repo) == []


def test_unreadable_higher_priority_profile_does_not_fall_back(repo):
    test_resource_profile_missing_and_existing(repo)
    path = write(repo.root / 'environments/c/e/Inventory/resource_profiles/selected.yml', {})
    path.write_text('broken: [')
    assert_kind(findings(repo), 'unknown')


def test_profile_lower_priority_duplicate_is_not_ambiguous(repo):
    test_resource_profile_missing_and_existing(repo)
    write(repo.root / 'environments/c/e/Inventory/resource_profiles/selected.yml', {'name': 'selected'})
    assert findings(repo) == []


def test_mixed_references_report_missing_once_at_value(repo):
    params(repo, ref('present') + ref(ID) + ref(ID))
    catalog(repo, {'present': {}})
    assert_kind(findings(repo), 'missing')


def test_reference_cycle_and_nested_lists_are_bounded(repo):
    value = {'values': [ref()]}
    value['cycle'] = value
    params(repo, value)
    catalog(repo, {})
    assert_kind(findings(repo), 'missing')


def test_unsafe_catalog_never_reads_external_target(repo, tmp_path):
    params(repo, ref())
    external = tmp_path.parent / (tmp_path.name + '-outside.yml')
    write(external, {ID: {}})
    path = repo.root / 'environments/c/e/Credentials/credentials.yml'
    path.parent.mkdir(parents=True)
    path.symlink_to(external)
    assert_kind(findings(repo), 'unknown')


def test_later_shared_entry_overrides_earlier_entry(repo):
    test_shared_connected_credential_can_resolve_without_generated_catalog(repo)
    path = repo.root / 'environments/c/e/Inventory/env_definition.yml'
    doc = YAML().load(path)
    doc['envTemplate']['sharedMasterCredentialFiles'].append('later')
    write(path, doc)
    write(repo.root / 'environments/credentials/later.yml', {ID: None})
    assert_kind(findings(repo), 'unknown')


def test_paramset_staging_shadow_does_not_read_overwritten_lower_file(repo):
    repo.env('c', 'e', deploy={'cloud': ['selected']})
    repo.site_paramset('selected', {})
    (repo.root / 'environments/parameters/selected.yml').write_text('broken: [')
    repo.cluster_paramset('c', 'selected', {})
    assert findings(repo) == []


@pytest.mark.parametrize('lower_exists', [False, True])
def test_unsafe_profile_blocks_lower_priority_fallback(repo, tmp_path, lower_exists):
    repo.env('c', 'e')
    path = repo.root / 'environments/c/e/Inventory/env_definition.yml'
    doc = YAML().load(path)
    doc['envTemplate']['envSpecificResourceProfiles'] = {'cloud': 'selected'}
    write(path, doc)
    external = write(tmp_path.parent / (tmp_path.name + '-profile.yml'), {'name': 'selected'})
    alias = repo.root / 'environments/c/e/Inventory/resource_profiles/selected.yml'
    alias.parent.mkdir(parents=True)
    alias.symlink_to(external)
    if lower_exists:
        write(repo.root / 'environments/resource_profiles/selected.yml', {'name': 'selected'})
    assert_kind(findings(repo), 'unknown')


def test_explicit_namespace_binding_is_connected_without_local_template(repo):
    repo.env('c', 'e', deploy={'ns': ['template-only']})
    write(repo.root / 'environments/c/e/Namespaces/ns/namespace.yml', {
        'credentialsId': ID, 'deployParameters': {'VALUE': ref()},
    })
    catalog(repo, {})
    result = findings(repo)
    assert len(result) == 3
    assert sum(f.issue_type.value == 'Warning' for f in result) == 2


def test_unsafe_paramset_target_is_unknown(repo, tmp_path):
    repo.env('c', 'e', deploy={'cloud': ['selected']})
    path = repo.root / 'environments/c/e/Inventory/env_definition.yml'
    doc = YAML().load(path)
    del doc['envTemplate']['name']
    write(path, doc)
    external = write(tmp_path.parent / (tmp_path.name + '-paramset.yml'), {'name': 'selected'})
    alias = repo.root / 'environments/c/e/Inventory/parameters/selected.yml'
    alias.parent.mkdir(parents=True)
    alias.symlink_to(external)
    assert_kind(findings(repo), 'unknown')
