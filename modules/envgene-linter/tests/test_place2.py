import pytest

from envgene_linter.discovery import build_index
from envgene_linter.effective import ALL_LAYERS, LOWER_LAYERS, SITE_LAYERS, compute
from envgene_linter.engine import run_check
from envgene_linter.model import Action, Category, Scope
from envgene_linter.rules.place2 import check


def _place2(repo):
    index = build_index(repo.root)
    full = {env.full_name: compute(index, env, ALL_LAYERS) for env in index.environments}
    lower = {env.full_name: compute(index, env, LOWER_LAYERS) for env in index.environments}
    site = {env.full_name: compute(index, env, SITE_LAYERS) for env in index.environments}
    return check(index, full, lower, site)


def test_env_copying_cluster_is_a_finding(repo):
    repo.env("cluster-01", "env-01", deploy={"cloud": ["shared", "env-params"]})
    repo.cluster_paramset("cluster-01", "shared", {"LOG_LEVEL": "info", "REPLICA_COUNT": 2})
    repo.env_paramset(
        "cluster-01", "env-01", "env-params", {"LOG_LEVEL": "info", "REPLICA_COUNT": 3}
    )
    findings = _place2(repo)
    assert len(findings) == 1
    assert findings[0].rule == "PLACE-2"
    assert findings[0].key == "LOG_LEVEL"
    assert "environment" in findings[0].message
    assert "Remove LOG_LEVEL" in findings[0].hint
    assert findings[0].message == (
        "Key LOG_LEVEL at the environment layer repeats the lower-layer value."
    )
    assert findings[0].hint == (
        "Remove LOG_LEVEL from this file, or change the value if the override is intentional."
    )
    assert findings[0].locations == ()


def test_different_value_is_silent(repo):
    repo.env("cluster-01", "env-01", deploy={"cloud": ["shared", "env-params"]})
    repo.cluster_paramset("cluster-01", "shared", {"REPLICA_COUNT": 2})
    repo.env_paramset("cluster-01", "env-01", "env-params", {"REPLICA_COUNT": 3})
    assert _place2(repo) == []


def test_key_absent_below_is_silent(repo):
    repo.env("cluster-01", "env-01", deploy={"cloud": ["env-params"]})
    repo.env_paramset("cluster-01", "env-01", "env-params", {"ONLY_HERE": 1})
    assert _place2(repo) == []


def test_cluster_copying_repository_is_a_finding(repo):
    repo.env("cluster-01", "env-01", deploy={"cloud": ["shared"]})
    site = repo.root / "environments/parameters/shared.yaml"
    site.parent.mkdir(parents=True, exist_ok=True)
    site.write_text("name: shared\nparameters:\n  LOG_LEVEL: info\n", encoding="utf-8")
    repo.cluster_paramset("cluster-01", "shared", {"LOG_LEVEL": "info"})
    findings = _place2(repo)
    assert len(findings) == 1
    assert findings[0].key == "LOG_LEVEL"
    assert "cluster" in findings[0].message


def test_two_envs_share_one_cluster_restatement(repo):
    repo.env("cluster-01", "env-01", deploy={"cloud": ["shared"]})
    repo.env("cluster-01", "env-02", deploy={"cloud": ["shared"]})
    site = repo.root / "environments/parameters/shared.yaml"
    site.parent.mkdir(parents=True, exist_ok=True)
    site.write_text("name: shared\nparameters:\n  LOG_LEVEL: info\n", encoding="utf-8")
    repo.cluster_paramset("cluster-01", "shared", {"LOG_LEVEL": "info"})
    findings = _place2(repo)
    assert len(findings) == 1


def test_same_file_bound_under_two_targets_is_one_finding(repo):
    repo.env("cluster-01", "env-01", deploy={"cloud": ["shared"], "bss": ["shared"]})
    site = repo.root / "environments/parameters/shared.yaml"
    site.parent.mkdir(parents=True, exist_ok=True)
    site.write_text("name: shared\nparameters:\n  LOG_LEVEL: info\n", encoding="utf-8")
    repo.cluster_paramset("cluster-01", "shared", {"LOG_LEVEL": "info"})
    findings = _place2(repo)
    assert len(findings) == 1
    assert findings[0].rule == "PLACE-2"
    assert findings[0].key == "LOG_LEVEL"


def test_restated_env_key_is_place2_not_place1(repo):
    repo.env("cluster-01", "env-01", deploy={"cloud": ["shared", "env-params"]})
    repo.env("cluster-01", "env-02", deploy={"cloud": ["shared", "env-params"]})
    repo.cluster_paramset("cluster-01", "shared", {"LOG_LEVEL": "info"})
    repo.env_paramset("cluster-01", "env-01", "env-params", {"LOG_LEVEL": "info"})
    repo.env_paramset("cluster-01", "env-02", "env-params", {"LOG_LEVEL": "info"})
    result = run_check(repo.root)
    place2 = [item for item in result.findings if item.rule == "PLACE-2" and item.key == "LOG_LEVEL"]
    place1 = [item for item in result.findings if item.rule == "PLACE-1" and item.key == "LOG_LEVEL"]
    assert len(place2) == 2
    assert place1 == []


pytestmark = pytest.mark.usefixtures("all_rules_enabled")


@pytest.mark.parametrize(('base', 'local'), [
    ('1', 'true'), ('0', 'false'), ('1', '1.0'), ('[1]', '[true]'), ('[0]', '[false]'),
])
def test_different_yaml_types_are_not_redundant(repo, base, local):
    repo.env('c', 'e', deploy={'cloud': ['base', 'local']})
    repo.cluster_paramset('c', 'base', {'KEY': base})
    repo.env_paramset('c', 'e', 'local', {'KEY': local})
    assert _place2(repo) == []


def test_override_restoring_the_cluster_value_is_required(repo):
    repo.env('c', 'e', deploy={'cloud': ['base', 'early', 'late']})
    repo.cluster_paramset('c', 'base', {'KEY': 2})
    repo.env_paramset('c', 'e', 'early', {'KEY': 5})
    repo.env_paramset('c', 'e', 'late', {'KEY': 2})
    index = build_index(repo.root)
    assert compute(index, index.environments[0]).get(Scope('cloud', Category.DEPLOY), ('KEY',)).value == 2
    assert _place2(repo) == []


def test_cluster_removal_must_preserve_every_consuming_environment(repo):
    repo.site_paramset('base', {'KEY': 2})
    repo.cluster_paramset('c', 'early', {'KEY': 5})
    repo.cluster_paramset('c', 'late', {'KEY': 2})
    repo.env('c', 'a', deploy={'cloud': ['base', 'late']})
    repo.env('c', 'b', deploy={'cloud': ['base', 'early', 'late']})
    assert _place2(repo) == []


def test_removal_must_preserve_targets_where_the_leaf_is_not_a_restatement(repo):
    repo.cluster_paramset('c', 'base', {'KEY': 2})
    repo.cluster_paramset('c', 'other', {'KEY': 5})
    repo.env_paramset('c', 'e', 'local', {'KEY': 2})
    repo.env('c', 'e', deploy={'cloud': ['base', 'local'], 'service': ['other', 'local']})
    assert _place2(repo) == []


def test_removal_must_preserve_other_parameter_categories(repo):
    repo.cluster_paramset('c', 'base', {'KEY': 2})
    repo.cluster_paramset('c', 'other', {'KEY': 5})
    repo.env_paramset('c', 'e', 'local', {'KEY': 2})
    repo.env('c', 'e', deploy={'cloud': ['base', 'local']}, e2e={'cloud': ['other', 'local']})
    assert _place2(repo) == []


def test_removal_excludes_every_selection_of_one_physical_file(repo):
    repo.env('c', 'e', deploy={'cloud': ['base', 'early', 'local', 'alias']})
    repo.cluster_paramset('c', 'base', {'KEY': 2})
    repo.env_paramset('c', 'e', 'early', {'KEY': 5})
    repo.env_paramset('c', 'e', 'local', {'KEY': 2})
    directory = repo.root / 'environments/c/e/Inventory/parameters'
    (directory / 'alias.yml').symlink_to('local.yml')
    assert _place2(repo) == []


def test_nested_override_restoring_a_mapping_is_required(repo):
    repo.env('c', 'e', deploy={'cloud': ['base', 'early', 'local']})
    repo.cluster_paramset('c', 'base', {'KEY': '{child: same}'})
    repo.env_paramset('c', 'e', 'early', {'KEY': 'changed'})
    repo.env_paramset('c', 'e', 'local', {'KEY': '{child: same}'})
    assert _place2(repo) == []


def test_shadowed_repository_source_is_not_restored_by_removal(repo):
    repo.env('c', 'e', deploy={'cloud': ['shared', 'local']})
    repo.site_paramset('shared', {'KEY': 2})
    repo.cluster_paramset('c', 'shared', {'KEY': 5})
    repo.env_paramset('c', 'e', 'local', {'KEY': 2})
    assert _place2(repo) == []


def test_global_and_application_parameters_are_distinct_removal_candidates(repo):
    repo.env('c', 'e', deploy={'cloud': ['base', 'local']})
    repo.cluster_paramset('c', 'base', {'KEY': 'same'})
    repo.env_paramset('c', 'e', 'local', {'KEY': 'same'})
    for path in (repo.root / 'environments/c/parameters/base.yml',
                 repo.root / 'environments/c/e/Inventory/parameters/local.yml'):
        path.write_text(path.read_text() + 'applications:\n  - appName: demo\n    parameters:\n      KEY: same\n')
    findings = _place2(repo)
    assert len(findings) == 2
    assert {finding.line for finding in findings} == {3, 7}
    assert all(finding.action is Action.FIX for finding in findings)


def test_literal_dot_and_nested_keys_are_distinct_removal_candidates(repo):
    repo.env('c', 'e', deploy={'cloud': ['base', 'local']})
    values = {'KEY.child': 'same', 'KEY': '{child: same}'}
    repo.cluster_paramset('c', 'base', values)
    repo.env_paramset('c', 'e', 'local', values)
    findings = _place2(repo)
    assert len(findings) == 2
    assert {finding.line for finding in findings} == {3, 4}
    assert all(finding.action is Action.FIX for finding in findings)


def test_application_override_restoring_the_cluster_value_is_required(repo):
    repo.env('c', 'e', deploy={'cloud': ['base', 'early', 'local']})
    repo.cluster_paramset('c', 'base', {})
    repo.env_paramset('c', 'e', 'early', {})
    repo.env_paramset('c', 'e', 'local', {})
    for relative, value in [('parameters/base.yml', 2),
                            ('e/Inventory/parameters/early.yml', 5),
                            ('e/Inventory/parameters/local.yml', 2)]:
        path = repo.root / 'environments/c' / relative
        path.write_text(path.read_text() + f'applications:\n  - appName: demo\n    parameters:\n      KEY: {value}\n')
    assert _place2(repo) == []


def test_unknown_value_equality_requires_review_without_values(repo):
    repo.env('c', 'e', deploy={'cloud': ['base', 'local']})
    repo.cluster_paramset('c', 'base', {'KEY': '.nan'})
    repo.env_paramset('c', 'e', 'local', {'KEY': '.nan'})
    findings = _place2(repo)
    assert len(findings) == 1
    assert findings[0].action is Action.REVIEW
    assert findings[0].related == ()


@pytest.mark.parametrize('uncertain_source', ['missing', 'jinja', 'invalid'])
def test_incomplete_merge_context_gets_review_instead_of_removal_advice(repo, uncertain_source):
    repo.env('c', 'e', deploy={'cloud': ['base', 'local', 'uncertain']})
    repo.cluster_paramset('c', 'base', {'KEY': 'same'})
    repo.env_paramset('c', 'e', 'local', {'KEY': 'same'})
    folder = repo.root / 'environments/c/e/Inventory/parameters'
    if uncertain_source == 'jinja':
        (folder / 'uncertain.yml.j2').write_text('parameters:\n  KEY: "{{ PRIVATE_INPUT }}"\n')
    elif uncertain_source == 'invalid':
        (folder / 'uncertain.yml').write_text('parameters: [PRIVATE_INPUT\n')
    findings = _place2(repo)
    assert len(findings) == 1
    assert findings[0].action is Action.REVIEW
    assert 'Remove' not in findings[0].hint
    assert 'PRIVATE_INPUT' not in repr(findings)


def test_yaml_anchor_dependency_is_not_a_proven_removal(repo):
    repo.env('c', 'e', deploy={'cloud': ['base', 'local']})
    repo.cluster_paramset('c', 'base', {'KEY': 'same'})
    repo.env_paramset('c', 'e', 'local', {})
    path = repo.root / 'environments/c/e/Inventory/parameters/local.yml'
    path.write_text('name: local\nparameters:\n  KEY: &shared same\n  OTHER: *shared\n')
    findings = _place2(repo)
    assert len(findings) == 1
    assert findings[0].action is Action.REVIEW


@pytest.mark.parametrize(('base', 'local'), [
    ('[1]', '!custom [1]'),
    ('{nested: same}', '!custom {nested: same}'),
])
def test_custom_collection_tags_require_review(repo, base, local):
    repo.env('c', 'e', deploy={'cloud': ['base', 'local']})
    repo.cluster_paramset('c', 'base', {'KEY': base})
    repo.env_paramset('c', 'e', 'local', {'KEY': local})
    findings = _place2(repo)
    assert len(findings) == 1
    assert findings[0].action is Action.REVIEW


@pytest.mark.parametrize('application', [
    '{parameters: {OTHER: same}}',
    '{appName: [demo], parameters: {OTHER: same}}',
    '{appName: true, parameters: {OTHER: same}}',
    '{appName: "{{ PRIVATE_INPUT }}", parameters: {OTHER: same}}',
])
def test_unknown_application_identity_requires_review(repo, application):
    repo.env('c', 'e', deploy={'cloud': ['base', 'local']})
    repo.cluster_paramset('c', 'base', {'KEY': 'same'})
    repo.env_paramset('c', 'e', 'local', {'KEY': 'same'})
    path = repo.root / 'environments/c/e/Inventory/parameters/local.yml'
    path.write_text(path.read_text() + f'applications:\n  - {application}\n')
    findings = _place2(repo)
    assert len(findings) == 1
    assert findings[0].action is Action.REVIEW
    assert 'PRIVATE_INPUT' not in findings[0].message + findings[0].hint


def test_removal_analysis_does_not_mutate_files_or_indexed_documents(repo):
    repo.env('c', 'e', deploy={'cloud': ['base', 'local']})
    repo.cluster_paramset('c', 'base', {'KEY': 'same'})
    repo.env_paramset('c', 'e', 'local', {'KEY': 'same'})
    index = build_index(repo.root)
    full = {env.full_name: compute(index, env, ALL_LAYERS) for env in index.environments}
    lower = {env.full_name: compute(index, env, LOWER_LAYERS) for env in index.environments}
    site = {env.full_name: compute(index, env, SITE_LAYERS) for env in index.environments}
    path = repo.root / 'environments/c/e/Inventory/parameters/local.yml'
    original = path.read_bytes()
    for _ in range(2):
        assert len(check(index, full, lower, site)) == 1
        assert index.environments[0].paramsets[0].parameters == {'KEY': 'same'}
        assert path.read_bytes() == original
