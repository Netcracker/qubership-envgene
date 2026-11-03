"""Feature-specific step definitions for clean-sub-flows.feature.

Only steps that are genuinely specific to the CLEAN sub-flows scenarios live here;
everything else (pipeline params, orchestrator run, success/failure, log assertions,
workspace init from test data, pipeline step status, BG state files) is reused from
shared_steps/unified_pipeline_steps.py and shared_steps/common_steps.py.
"""
import re

import yaml
from git import Repo
from pytest_bdd import given, then, parsers

from cucumber_tests.framework.workspace import EnvGeneWorkspace


@given('the environment has deployed namespaces')
def given_deployed_namespaces(workspace: EnvGeneWorkspace):
    env_dir = workspace.builder.get_env_dir(workspace.cluster_name, workspace.env_name)
    entries = _load_deploy_plan(workspace)
    namespace_map = {}
    namespaces = {entry["namespace"] for entry in entries}
    for entry in entries:
        name, postfix = entry["namespace"], entry["deployPostfix"]
        role = next((role for role in ("origin", "peer") if name.endswith(f"-{role}")), None)
        if role:
            namespace_map.setdefault(postfix, {})[role] = name
        else:
            namespace_map[postfix] = name
    if any(isinstance(entry, dict) for entry in namespace_map.values()):
        namespace_map["controller"] = f"{workspace.env_name}-controller"
        namespaces.add(namespace_map["controller"])
    (env_dir / "Inventory" / "namespace-map.yml").write_text(yaml.safe_dump(namespace_map), encoding="utf-8")
    workspace.namespace_definitions_before = {}
    for namespace in namespaces:
        folder = namespace.removeprefix(f"{workspace.env_name}-")
        definition = env_dir / "Namespaces" / folder / "namespace.yml"
        definition.parent.mkdir(parents=True, exist_ok=True)
        definition.write_text(yaml.safe_dump({
            "name": namespace,
            "isServerSideMerge": False,
            "cleanInstallApprovalRequired": False,
            "mergeDeployParametersAndE2EParameters": False,
            "deployParameters": {},
            "deployParameterSets": [],
            "e2eParameters": {},
            "e2eParameterSets": [],
            "technicalConfigurationParameters": {},
            "technicalConfigurationParameterSets": [],
        }), encoding="utf-8")
        workspace.namespace_definitions_before[definition] = definition.read_bytes()
    es = _effective_set_dir(workspace)
    for context in ("deployment", "runtime"):
        mapping = {}
        for namespace in namespaces:
            folder = namespace.removeprefix(f"{workspace.env_name}-")
            application = es / context / folder / "app"
            application.mkdir(parents=True, exist_ok=True)
            (application / "parameters.yaml").write_text("parameter: value\n", encoding="utf-8")
            (application / "old-generation").mkdir(exist_ok=True)
            (application / "old-generation" / "parameters.yaml").write_text("old: value\n", encoding="utf-8")
            mapping[namespace] = f"/environments/{workspace.cluster_name}/{workspace.env_name}/effective-set/{context}/{folder}"
        (es / context / "mapping.yaml").write_text(yaml.safe_dump(mapping), encoding="utf-8")
    cleanup = es / "cleanup" / "core"
    cleanup.mkdir(parents=True, exist_ok=True)
    (cleanup / "parameters.yaml").write_text("old: context\n", encoding="utf-8")
    workspace.effective_set_before = _snapshot_effective_set(workspace)


@then('the namespace definitions are unchanged')
def then_namespace_definitions_unchanged(workspace: EnvGeneWorkspace):
    for path, content in workspace.namespace_definitions_before.items():
        assert path.read_bytes() == content, f"Namespace definition changed: {path}"


@then('the reduced deploy plan and namespace map are committed')
def then_cleanup_inputs_committed(workspace: EnvGeneWorkspace):
    match = re.search(r"Created hidden commit ([0-9a-f]+)", workspace.stdout + workspace.stderr)
    assert match, f"No inventory commit was created.\n{workspace.stdout}\n{workspace.stderr}"
    with Repo(workspace.base_dir) as repo:
        inventory = repo.commit(match[1]).tree / f"environments/{workspace.cluster_name}/{workspace.env_name}/Inventory"
        for name in ("deploy-plan.yml", "namespace-map.yml"):
            expected = workspace.get_yaml(workspace.environments_dir / workspace.cluster_name / workspace.env_name / "Inventory" / name)
            actual = yaml.safe_load((inventory / name).data_stream.read())
            assert actual == expected, f"Committed {name} differs from the cleanup result"


def _load_deploy_plan(workspace: EnvGeneWorkspace) -> list:
    env_dir = workspace.builder.get_env_dir(workspace.cluster_name, workspace.env_name)
    plan_path = env_dir / "Inventory" / "deploy-plan.yml"
    workspace.assert_file_exists(plan_path)
    return yaml.safe_load(plan_path.read_text(encoding="utf-8")) or []


@then('the deploy plan is empty')
def then_deploy_plan_is_empty(workspace: EnvGeneWorkspace):
    entries = _load_deploy_plan(workspace)
    assert entries == [], f"Expected an empty deploy plan, got: {entries}"


def _assert_deploy_plan_entry_count(workspace: EnvGeneWorkspace, count: int):
    entries = _load_deploy_plan(workspace)
    assert len(entries) == count, f"Expected {count} deploy plan entries, got {len(entries)}: {entries}"


@then(parsers.parse('the deploy plan contains {count:d} entry'))
def then_deploy_plan_entry_count_singular(workspace: EnvGeneWorkspace, count: int):
    _assert_deploy_plan_entry_count(workspace, count)


@then(parsers.parse('the deploy plan contains {count:d} entries'))
def then_deploy_plan_entry_count_plural(workspace: EnvGeneWorkspace, count: int):
    _assert_deploy_plan_entry_count(workspace, count)


@then(parsers.parse('the deploy plan does not contain an entry for namespace "{namespace}"'))
def then_deploy_plan_missing_namespace(workspace: EnvGeneWorkspace, namespace: str):
    entries = _load_deploy_plan(workspace)
    matches = [e for e in entries if e.get("namespace") == namespace]
    assert not matches, f"Expected no deploy-plan.yml entry for namespace='{namespace}', found: {matches}"


@then(parsers.parse('the deploy plan contains an entry for namespace "{namespace}"'))
def then_deploy_plan_has_namespace(workspace: EnvGeneWorkspace, namespace: str):
    entries = _load_deploy_plan(workspace)
    matches = [e for e in entries if e.get("namespace") == namespace]
    assert matches, f"Expected a deploy-plan.yml entry for namespace='{namespace}', found none. Entries: {entries}"


def _effective_set_dir(workspace: EnvGeneWorkspace):
    env_dir = workspace.builder.get_env_dir(workspace.cluster_name, workspace.env_name)
    return env_dir / "effective-set"


@then(parsers.parse('the effective set folder "{folder}" contains marker file "{marker}"'))
def then_effective_set_folder_contains_marker(workspace: EnvGeneWorkspace, folder: str, marker: str):
    marker_path = _effective_set_dir(workspace) / folder / marker
    workspace.assert_file_exists(marker_path)


@then(parsers.parse('the effective set folder "{folder}" contains file "{filename}"'))
def then_effective_set_folder_contains_file(workspace: EnvGeneWorkspace, folder: str, filename: str):
    file_path = _effective_set_dir(workspace) / folder / filename
    workspace.assert_file_exists(file_path)


@then(parsers.parse('the effective set folder "{folder}" does not exist'))
def then_effective_set_folder_does_not_exist(workspace: EnvGeneWorkspace, folder: str):
    folder_path = _effective_set_dir(workspace) / folder
    assert not folder_path.exists(), f"Expected effective-set/{folder} not to exist"


@then(parsers.parse('the effective set cleanup mapping contains namespace "{namespace}"'))
def then_effective_set_cleanup_mapping_contains_namespace(workspace: EnvGeneWorkspace, namespace: str):
    mapping_path = _effective_set_dir(workspace) / "cleanup" / "mapping.yaml"
    workspace.assert_file_exists(mapping_path)
    mapping = yaml.safe_load(mapping_path.read_text(encoding="utf-8")) or {}
    assert namespace in mapping, (
        f"Expected namespace '{namespace}' as a key in cleanup/mapping.yaml, got keys: {list(mapping)}"
    )


@given(parsers.parse('the namespaces "{first}" and "{second}" are selected with "{separator}"'))
def given_namespace_selection(workspace: EnvGeneWorkspace, first: str, second: str, separator: str):
    delimiters = {"semicolon": ";", "escaped newline": r"\n"}
    workspace.extra_env["NAMESPACE_NAMES"] = delimiters[separator].join((first, second))


def _snapshot_effective_set(workspace: EnvGeneWorkspace) -> dict:
    es = _effective_set_dir(workspace)
    return {str(path.relative_to(es)): path.read_bytes() for path in es.rglob("*") if path.is_file()}


@then('the existing effective set is unchanged')
def then_effective_set_unchanged(workspace: EnvGeneWorkspace):
    assert _snapshot_effective_set(workspace) == workspace.effective_set_before, (
        "The orchestrator must leave ES content for the separate argo-dpg cleanup invocation")
