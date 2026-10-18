"""ParameterSet inputs must agree across resolution, merging, and content checks."""

import json

import pytest
from click.testing import CliRunner
from ruamel.yaml import YAML

from envgene_linter.cli import main
from envgene_linter.connections import compute_connections
from envgene_linter.discovery import build_index
from envgene_linter.effective import SITE_LAYERS, compute, compute_values, resolve_reference
from envgene_linter.engine import run_check
from envgene_linter.model import Action, Category, Scope

pytestmark = pytest.mark.usefixtures('all_rules_enabled')


def write(root, relative, params=None, *, applications=None):
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    document = {'name': 'shared', 'parameters': params or {}}
    if applications is not None:
        document['applications'] = applications
    if path.suffix == '.json':
        path.write_text(json.dumps(document, indent=2) + '\n', encoding='utf-8')
    else:
        with path.open('w', encoding='utf-8') as stream:
            YAML().dump(document, stream)
    return path


def findings(repo, rule):
    return [item for item in run_check(repo.root).findings if item.rule == rule]


@pytest.mark.parametrize('directory', [
    'environments/parameters', 'environments/c/parameters', 'environments/c/e/Inventory/parameters',
])
@pytest.mark.parametrize('filename', ['shared.yml', 'nested/shared.yaml', 'nested/shared.json'])
def test_selected_formats_reach_resolution_merging_and_content_rules(repo, directory, filename):
    repo.env('c', 'e', deploy={'cloud': ['shared']})
    path = write(repo.root, f'{directory}/{filename}', {'CONFIG': '[1, 2]'})
    index = build_index(repo.root)
    env = index.environments[0]
    assert [entry.file.path for entry in resolve_reference(index, env, 'shared')] == [path]
    assert compute_connections(index).parameter_sets == {path.resolve()}
    assert compute_values(index, env) == {Scope('cloud', Category.DEPLOY): {'CONFIG': '[1, 2]'}}
    assert findings(repo, 'INT-2') == []
    result = findings(repo, 'VAL-4')
    assert len(result) == 1
    assert result[0].path == path
    assert result[0].key == 'parameters.CONFIG'


def test_distinct_nested_paths_survive_and_merge_in_staged_path_order(repo):
    repo.env('c', 'e', deploy={'cloud': ['shared']})
    site = write(repo.root, 'environments/parameters/z/shared.yml', {'WIN': 'site', 'KEEP_SITE': 1})
    cluster = write(repo.root, 'environments/c/parameters/a/shared.yml', {'WIN': 'cluster', 'KEEP_CLUSTER': 2})
    index = build_index(repo.root)
    env = index.environments[0]
    assert [entry.file.path for entry in resolve_reference(index, env, 'shared')] == [cluster, site]
    assert compute_values(index, env) == {
        Scope('cloud', Category.DEPLOY): {'WIN': 'site', 'KEEP_SITE': 1, 'KEEP_CLUSTER': 2}}


def test_exact_nested_path_replaces_invalid_repository_file_before_projection(repo):
    repo.env('c', 'e', deploy={'cloud': ['shared']})
    site = write(repo.root, 'environments/parameters/nested/shared.yml', {'CONFIG': '[1]'})
    site.write_text('invalid: [', encoding='utf-8')
    cluster = write(repo.root, 'environments/c/parameters/nested/shared.yml', {'WIN': 'cluster'})
    index = build_index(repo.root)
    env = index.environments[0]
    assert [entry.file.path for entry in resolve_reference(index, env, 'shared')] == [cluster]
    assert resolve_reference(index, env, 'shared', SITE_LAYERS) == []
    assert compute(index, env, SITE_LAYERS).scopes == {}
    assert findings(repo, 'INT-2') == []
    assert findings(repo, 'VAL-4') == []


def test_environment_copy_replaces_same_staged_from_instance_path(repo):
    repo.env('c', 'e', deploy={'cloud': ['shared']})
    write(repo.root, 'environments/c/parameters/from_instance/shared.yml', {'CONFIG': '[1]', 'OLD': 1})
    env_file = write(repo.root, 'environments/c/e/Inventory/parameters/shared.yml', {'WIN': 'env'})
    index = build_index(repo.root)
    env = index.environments[0]
    assert [entry.file.path for entry in resolve_reference(index, env, 'shared')] == [env_file]
    assert compute_values(index, env) == {Scope('cloud', Category.DEPLOY): {'WIN': 'env'}}
    assert findings(repo, 'VAL-4') == []


def test_from_instance_substring_changes_application_order(repo):
    repo.env('c', 'e', deploy={'cloud': ['shared']})
    early = write(repo.root, 'environments/parameters/z/shared.yml', {'WIN': 'ordinary'})
    late = write(repo.root, 'environments/parameters/a_from_instance/shared.yml', {'WIN': 'instance'})
    index = build_index(repo.root)
    assert [entry.file.path for entry in resolve_reference(index, index.environments[0], 'shared')] == [early, late]
    assert compute_values(index, index.environments[0])[Scope('cloud', Category.DEPLOY)]['WIN'] == 'instance'


@pytest.mark.parametrize('folder', ['from_template', 'from_origin_template', 'from_peer_template'])
def test_role_specific_paths_require_review_without_template_context(repo, folder):
    repo.env('c', 'e', deploy={'cloud': ['shared']})
    write(repo.root, f'environments/parameters/{folder}/shared.yml', {'CONFIG': '[1]'})
    result = findings(repo, 'INT-2')
    assert len(result) == 1 and result[0].action is Action.REVIEW
    assert findings(repo, 'VAL-4') == []


def test_incomplete_environment_remains_a_potential_consumer_of_shared_source(repo):
    repo.env('c', 'a', deploy={'cloud': ['base', 'shared']})
    repo.env('c', 'b', deploy={'cloud': ['shared']})
    repo.site_paramset('base', {'VALUE': 1})
    repo.cluster_paramset('c', 'shared', {'VALUE': 1})
    unknown = repo.root / 'environments/c/b/Inventory/parameters/nested'
    unknown.parent.mkdir(parents=True, exist_ok=True)
    unknown.symlink_to(repo.root / 'environments/parameters', target_is_directory=True)
    result = findings(repo, 'PLACE-2')
    assert len(result) == 1
    assert result[0].path == repo.root / 'environments/c/parameters/shared.yml'
    assert result[0].action is Action.REVIEW


def test_conditional_common_template_source_cannot_prove_removal(repo):
    repo.env('c', 'e', deploy={'cloud': ['base', 'shared']})
    write(repo.root, 'environments/parameters/from_template/base.yml', {'VALUE': 1})
    repo.cluster_paramset('c', 'shared', {'VALUE': 1})
    result = findings(repo, 'PLACE-2')
    assert not any(item.action is Action.FIX for item in result)
    assert any(item.action is Action.REVIEW for item in findings(repo, 'INT-2'))


@pytest.mark.parametrize('collision', ['file-to-directory', 'directory-to-file', 'unsupported-ancestor', 'environment-root'])
def test_structural_staging_collisions_prevent_connected_selection(repo, collision):
    repo.env('c', 'e', deploy={'cloud': ['shared']})
    if collision == 'file-to-directory':
        repo.site_paramset('shared', {'CONFIG': '[1]'})
        (repo.root / 'environments/c/parameters/shared.yml').mkdir(parents=True)
    elif collision == 'directory-to-file':
        write(repo.root, 'environments/parameters/shared.yml/nested.yml', {'VALUE': 1})
        repo.cluster_paramset('c', 'shared', {'CONFIG': '[1]'})
    elif collision == 'unsupported-ancestor':
        write(repo.root, 'environments/parameters/nested/shared.yml', {'CONFIG': '[1]'})
        blocker = repo.root / 'environments/c/parameters/nested'
        blocker.parent.mkdir(parents=True)
        blocker.write_text('synthetic non-ParameterSet', encoding='utf-8')
    else:
        blocker = repo.root / 'environments/parameters/from_instance'
        blocker.parent.mkdir(parents=True)
        blocker.write_text('synthetic non-ParameterSet', encoding='utf-8')
        repo.env_paramset('c', 'e', 'shared', {'CONFIG': '"[1]"'})
    index = build_index(repo.root)
    assert compute_values(index, index.environments[0]) == {}
    assert findings(repo, 'VAL-4') == []
    result = findings(repo, 'INT-2')
    assert len(result) == 1 and result[0].action is Action.REVIEW


def test_noncolliding_unsupported_files_do_not_block_sources(repo):
    repo.env('c', 'e', deploy={'cloud': ['shared']})
    path = write(repo.root, 'environments/parameters/nested/shared.yml', {'CONFIG': '[1]'})
    note = repo.root / 'environments/c/parameters/README.txt'
    note.parent.mkdir(parents=True)
    note.write_text('synthetic note', encoding='utf-8')
    result = findings(repo, 'VAL-4')
    assert len(result) == 1 and result[0].path == path
    assert findings(repo, 'INT-2') == []


@pytest.mark.parametrize('filename', ['nested/orphan.yml', 'nested/orphan.json'])
def test_unbound_inputs_remain_outside_connected_checks(repo, filename):
    repo.env('c', 'e')
    path = write(repo.root, f'environments/parameters/{filename}', {'CONFIG': '[1]', 'PASSWORD': 'synthetic'})
    index = build_index(repo.root)
    assert compute_connections(index).parameter_sets == set()
    assert compute_values(index, index.environments[0]) == {}
    assert findings(repo, 'VAL-4') == [] and findings(repo, 'SEC-1') == []
    assert any(item.path == path for item in findings(repo, 'INT-4'))


def test_unsafe_higher_layer_file_blocks_repository_fallback(repo, tmp_path):
    repo.env('c', 'e', deploy={'cloud': ['shared']})
    write(repo.root, 'environments/parameters/shared.yml', {'CONFIG': '[1]'})
    outside = tmp_path.parent / f'{tmp_path.name}-external.json'
    outside.write_text('{"parameters":{"CONFIG":"[2]"}}', encoding='utf-8')
    alias = repo.root / 'environments/c/parameters/shared.yml'
    alias.parent.mkdir(parents=True, exist_ok=True)
    alias.symlink_to(outside)
    index = build_index(repo.root)
    assert compute_values(index, index.environments[0]) == {}
    assert findings(repo, 'VAL-4') == []
    result = findings(repo, 'INT-2')
    assert len(result) == 1 and result[0].action is Action.REVIEW


def test_unscanned_directory_prevents_fallback_and_removal_confirmation(repo):
    repo.env('c', 'e', deploy={'cloud': ['shared']})
    repo.site_paramset('shared', {'VALUE': 1})
    repo.env_paramset('c', 'e', 'shared', {'VALUE': 1})
    unknown = repo.root / 'environments/c/parameters/nested'
    unknown.parent.mkdir(parents=True, exist_ok=True)
    unknown.symlink_to(repo.root / 'environments/parameters', target_is_directory=True)
    index = build_index(repo.root)
    assert compute_values(index, index.environments[0]) == {}
    result = findings(repo, 'INT-2')
    assert len(result) == 1 and result[0].action is Action.REVIEW
    assert not any(item.action is Action.FIX for item in findings(repo, 'PLACE-2'))


def test_nested_jinja_is_unrendered_and_requires_review(repo):
    repo.env('c', 'e', deploy={'cloud': ['shared']})
    path = repo.root / 'environments/parameters/nested/shared.yml.j2'
    path.parent.mkdir(parents=True)
    path.write_text('parameters:\n  VALUE: {{ unsafe_call() }}\n', encoding='utf-8')
    index = build_index(repo.root)
    assert len(index.site_paramsets) == 1
    assert index.site_paramsets[0].is_jinja and index.site_paramsets[0].loaded is None
    assert compute_values(index, index.environments[0]) == {}
    result = findings(repo, 'INT-2')
    assert len(result) == 1 and result[0].action is Action.REVIEW


def test_nested_orphan_inventory_candidate_is_preserved(repo):
    path = write(repo.root, 'environments/c/orphan/Inventory/parameters/nested/shared.json', {'VALUE': 1})
    index = build_index(repo.root)
    assert index.environments == []
    result = findings(repo, 'INT-4')
    assert len(result) == 1 and result[0].path == path
    assert 'No consuming environment' in result[0].hint


def test_json_duplicate_keys_drive_checks_and_effective_values(repo):
    repo.env('c', 'e', deploy={'cloud': ['shared']})
    path = write(repo.root, 'environments/parameters/nested/shared.json')
    path.write_text('''{
  "name": "shared",
  "parameters": {
    "CONFIG": "native",
    "CONFIG": "[1, 2]"
  }
}''', encoding='utf-8')
    index = build_index(repo.root)
    assert compute_values(index, index.environments[0]) == {Scope('cloud', Category.DEPLOY): {'CONFIG': '[1, 2]'}}
    assert findings(repo, 'INT-2') == []
    result = findings(repo, 'VAL-4')
    assert len(result) == 1
    assert (result[0].path, result[0].line, result[0].column) == (path, 5, 5)


def test_invalid_json_is_unavailable_even_when_it_is_valid_yaml(repo):
    repo.env('c', 'e', deploy={'cloud': ['shared']})
    path = write(repo.root, 'environments/parameters/shared.json')
    path.write_text('parameters:\n  CONFIG: "[1]"\n', encoding='utf-8')
    result = findings(repo, 'INT-2')
    assert len(result) == 1 and result[0].action is Action.REVIEW
    assert findings(repo, 'VAL-4') == []


def test_json_application_checks_keep_distinct_locations_in_reports(repo):
    repo.env('c', 'e', deploy={'cloud': ['shared']})
    path = write(repo.root, 'environments/parameters/nested/shared.json', {'CONFIG': '[1]'},
                 applications=[{'appName': 'app', 'parameters': {'PASSWORD': 'synthetic'}}])
    val = findings(repo, 'VAL-4')
    sec = findings(repo, 'SEC-1')
    assert len(val) == len(sec) == 1
    assert (val[0].line, val[0].column) == (4, 5)
    assert (sec[0].line, sec[0].column) == (10, 9)
    assert sec[0].key == 'applications.0.parameters.PASSWORD'
    original = path.read_bytes()
    result = CliRunner().invoke(main, ['check', str(repo.root), '--console'])
    assert result.exit_code == 0, result.output
    assert 'VAL-4' in result.output and 'SEC-1' in result.output
    assert 'HTML report saved here:' in result.output and 'JSON report saved here:' in result.output
    html = (repo.root / 'envgene-linter-report.html').read_text(encoding='utf-8')
    assert 'VAL-4' in html and 'SEC-1' in html and 'nested/shared.json' in html
    data = json.loads((repo.root / 'envgene-linter-report.json').read_text(encoding='utf-8'))
    relevant = {item['rule_id']: item for item in data if item['rule_id'] in {'VAL-4', 'SEC-1'}}
    assert relevant['VAL-4']['files'] == ['environments/parameters/nested/shared.json:4:5']
    assert relevant['SEC-1']['files'] == ['environments/parameters/nested/shared.json:10:9']
    assert all('type' not in item for item in data)
    assert path.read_bytes() == original


@pytest.mark.parametrize('filename', ['nested/orphan.yml', 'nested/orphan.json'])
def test_authored_unbound_nested_input_protects_referenced_credential(repo, filename):
    from envgene_linter.usage_candidates import collect_candidates
    from envgene_linter.usage_references import analyze_usage

    repo.env('c', 'e')
    definition = repo.root / 'environments/c/e/Inventory/env_definition.yml'
    document = YAML().load(definition)
    document['envTemplate']['sharedMasterCredentialFiles'] = ['shared']
    with definition.open('w', encoding='utf-8') as stream:
        YAML().dump(document, stream)
    catalog = repo.root / 'environments/credentials/shared.yml'
    catalog.parent.mkdir(parents=True)
    catalog.write_text('used:\n  type: secret\n', encoding='utf-8')
    write(repo.root, f'environments/parameters/{filename}', {'VALUE': '${creds.get("used").secret}'})
    index = build_index(repo.root)
    connections = compute_connections(index)
    usages = analyze_usage(index, connections, collect_candidates(index, connections))
    credentials = [usage for usage in usages if usage.candidate.kind == 'Credential']
    assert len(credentials) == 1 and credentials[0].references
    assert connections.parameter_sets == set()
