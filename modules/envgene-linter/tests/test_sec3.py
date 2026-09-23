import pytest
from click.testing import CliRunner
from ruamel.yaml import YAML

from envgene_linter.cli import main
from envgene_linter.discovery import build_index
from envgene_linter.engine import run_check
from envgene_linter.html_report import render_html
from envgene_linter.report import render

REFERENCE = '${creds.get("synthetic-private-id").password}'


def write(path, doc):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w') as stream:
        YAML().dump(doc, stream)
    return path


def paramset(repo, value=REFERENCE, category='technical'):
    repo.env('c', 'e', **{category: {'cloud': ['service-runtime']}})
    return write(repo.root / 'environments/parameters/service-runtime.yml',
                 {'name': 'service-runtime', 'parameters': {'VALUE': value}})


def findings(repo):
    return [f for f in run_check(repo.root).findings if f.rule == 'SEC-3']


@pytest.mark.parametrize('value', [REFERENCE, "${creds.get('id').username}",
    'prefix ${creds.get("id").secret} suffix', '${ creds . get ("id").password }',
    {'$type': 'credRef', 'credId': 'synthetic-private-id', 'property': 'password'}])
def test_technical_reference_independent_of_parameter_name(repo, value):
    path = paramset(repo, value)
    result = findings(repo)
    assert len(result) == 1
    f = result[0]
    assert (f.path, f.key, f.line, f.column) == (path, 'parameters.VALUE', 3, 3)
    assert (f.issue_type.value, f.action.value) == ('Warning', 'Fix')
    assert 'synthetic-private-id' not in repr(result)
    assert REFERENCE not in render(result)
    assert 'synthetic-private-id' not in render_html(result, repo.root)


@pytest.mark.parametrize('category', ['deploy', 'e2e'])
def test_nonruntime_parameter_set_is_not_reported(repo, category):
    paramset(repo, category=category)
    assert findings(repo) == []


@pytest.mark.parametrize('value', ['', None, 42, 'literal', '${OTHER_PARAM}',
    'creds.get("id").password', '${mycreds.get("id").password}',
    {'$type': 'other', 'credId': 'id'}, '{{ secret }}'])
def test_noncredential_values_are_not_reported(repo, value):
    paramset(repo, value)
    assert findings(repo) == []


def test_nested_and_application_parameters(repo):
    path = paramset(repo)
    write(path, {'parameters': {'outer': [{'VALUE': REFERENCE}]},
                 'applications': [{'name': 'app', 'parameters': {'VALUE': {'$type': 'credRef', 'credId': 'id'}}}]})
    assert {f.key for f in findings(repo)} == {'parameters.outer.0.VALUE', 'applications.0.parameters.VALUE'}


def test_one_finding_per_parameter_even_with_two_references(repo):
    paramset(repo, REFERENCE + REFERENCE)
    assert len(findings(repo)) == 1


def test_shared_file_checked_once_for_multiple_technical_consumers(repo):
    paramset(repo)
    repo.env('c', 'other', technical={'cloud': ['service-runtime']})
    repo.env('other', 'e', deploy={'cloud': ['service-runtime']})
    assert len(findings(repo)) == 1


def test_unused_and_shadowed_technical_files(repo):
    repo.env('c', 'e', technical={'cloud': ['shared', 'missing']})
    repo.site_paramset('unused', {'VALUE': REFERENCE})
    repo.site_paramset('shared', {'VALUE': REFERENCE})
    repo.cluster_paramset('c', 'shared', {'VALUE': 'safe'})
    assert findings(repo) == []


def test_cloud_namespace_only_runtime_sections_and_connected_objects(repo):
    repo.env('c', 'e', deploy={'app': ['used'], 'missing': ['absent']})
    repo.site_paramset('used', {'VALUE': 'safe'})
    env = repo.root / 'environments/c/e'
    document = {s: {'VALUE': REFERENCE} for s in ('deployParameters', 'e2eParameters', 'technicalConfigurationParameters')}
    cloud = write(env / 'cloud.yml', document)
    namespace = write(env / 'Namespaces/app/namespace.yml', document)
    write(env / 'Namespaces/unused/namespace.yml', document)
    write(env / 'Namespaces/missing/namespace.yml', document)
    write(repo.root / 'environments/c/orphan/cloud.yml', document)
    result = findings(repo)
    assert {f.path for f in result} == {cloud, namespace}
    assert all(f.key == 'technicalConfigurationParameters.VALUE' for f in result)


def test_direct_call_and_cli_html(repo):
    paramset(repo)
    from envgene_linter.rules.sec3 import check
    assert check(build_index(repo.root)) == findings(repo)
    result = CliRunner().invoke(main, ['check', str(repo.root), '--html'])
    assert result.exit_code == 0
    assert result.output.index('SEC-1') < result.output.index('SEC-3') < result.output.index('NAME-1')
    assert 'SEC-3: No credentials in runtime parameters' in (repo.root / 'envgene-linter-report.html').read_text()
    assert 'synthetic-private-id' not in result.output


def test_invalid_cloud_and_git_target_skipped(repo):
    repo.env('c', 'e')
    env = repo.root / 'environments/c/e'
    (env / 'cloud.yml').write_text('technicalConfigurationParameters: [synthetic-private-id\n')
    result = CliRunner().invoke(main, ['check', str(repo.root)])
    assert result.exit_code == 0 and 'synthetic-private-id' not in result.output
    (env / 'cloud.yml').unlink()
    hidden = write(repo.root / '.git/hidden.yml', {'technicalConfigurationParameters': {'VALUE': REFERENCE}})
    (env / 'cloud.yml').symlink_to(hidden)
    assert findings(repo) == []


def test_technical_reference_does_not_select_unrelated_deploy_file(repo):
    repo.env('c', 'e', deploy={'cloud': ['service']}, technical={'cloud': ['missing']})
    repo.site_paramset('service', {'VALUE': REFERENCE})
    assert findings(repo) == []


def test_profile_binding_selects_namespace(repo):
    repo.env('c', 'e')
    env = repo.root / 'environments/c/e'
    with (env / 'Inventory/env_definition.yml').open('a') as stream:
        stream.write('  envSpecificResourceProfiles:\n    app: profile\n')
    write(repo.root / 'environments/resource_profiles/profile.yml', {'name': 'profile'})
    path = write(env / 'Namespaces/app/namespace.yml', {'technicalConfigurationParameters': {'VALUE': REFERENCE}})
    assert [f.path for f in findings(repo)] == [path]


def test_external_cloud_not_read(repo, tmp_path):
    repo.env('c', 'e')
    external = tmp_path.parent / (tmp_path.name + '-sec3.yml')
    try:
        write(external, {'technicalConfigurationParameters': {'VALUE': REFERENCE}})
        (repo.root / 'environments/c/e/cloud.yml').symlink_to(external)
        assert findings(repo) == []
    finally:
        external.unlink(missing_ok=True)


def test_quoted_credential_text_inside_other_macro_is_not_reference(repo):
    paramset(repo, '${"creds.get(example)"}')
    assert findings(repo) == []


pytestmark = pytest.mark.usefixtures("all_rules_enabled")
