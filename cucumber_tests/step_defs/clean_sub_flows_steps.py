"""Feature-specific step definitions for clean-sub-flows.feature.

Only steps that are genuinely specific to the CLEAN sub-flows scenarios live here;
everything else (pipeline params, orchestrator run, success/failure, log assertions,
workspace init from test data, pipeline step status, BG state files) is reused from
shared_steps/unified_pipeline_steps.py and shared_steps/common_steps.py.
"""
import re
import shutil
from pathlib import Path

import yaml
from git import Actor, Repo
from pytest_bdd import given, then, parsers

from cucumber_tests.framework.workspace import EnvGeneWorkspace


@then(parsers.parse('the namespace "{name}" is marked as cleaned'))
def then_namespace_is_cleaned(workspace: EnvGeneWorkspace, name: str):
    with Repo(workspace.es_remote) as remote:
        tree = remote.commit("refs/heads/main").tree / workspace.es_relative_path
        for context in ("deployment", "runtime"):
            namespace = tree / context / name
            assert (namespace / ".cleaned").data_stream.read() == b"", f"Missing marker for {context}/{name}"
            app = namespace / "app"
            assert [entry.name for entry in app] == [".gitkeep"], f"Application content remains in {context}/{name}"


@then(parsers.parse('the namespace "{name}" is not marked as cleaned'))
def then_namespace_is_not_cleaned(workspace: EnvGeneWorkspace, name: str):
    with Repo(workspace.es_remote) as remote:
        tree = remote.commit("refs/heads/main").tree / workspace.es_relative_path
        for context in ("deployment", "runtime"):
            namespace = tree / context / name
            actual = {item.path: item.data_stream.read() for item in namespace.traverse() if item.type == "blob"}
            expected = {path: data for path, data in workspace.es_before.items()
                        if path.startswith(f"{workspace.es_relative_path}/{context}/{name}/")}
            assert actual == expected, f"Untargeted namespace {context}/{name} changed: {actual}"


@given('the environment has a deployed effective set in its ES repository')
def given_deployed_effective_set(workspace: EnvGeneWorkspace):
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
        definition.write_text(yaml.safe_dump({"name": namespace, "deployPostfix": folder}), encoding="utf-8")
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
    workspace.es_relative_path = f"environments/{workspace.cluster_name}/{workspace.env_name}/effective-set"
    workspace.es_remote = workspace.base_dir / "es-remote.git"
    with Repo.init(workspace.es_remote, bare=True), \
            Repo.init(workspace.base_dir / "es-seed", initial_branch="main") as seed:
        shutil.copytree(es, Path(seed.working_tree_dir) / workspace.es_relative_path)
        seed.git.add(".")
        actor = Actor("Test", "test@example.com")
        seed.index.commit("Seed effective set", author=actor, committer=actor)
        workspace.es_before = {blob.path: blob.data_stream.read() for blob in seed.head.commit.tree.traverse()
                               if blob.type == "blob"}
        seed.create_remote("origin", str(workspace.es_remote)).push("HEAD:refs/heads/main").raise_if_error()
    pipeline = es / "pipeline"
    pipeline.mkdir(exist_ok=True)
    (pipeline / "parameters.yaml").write_text(yaml.safe_dump({
        "DCL_GIT_URL": str(workspace.es_remote), "DCL_GIT_BRANCH": "main"}), encoding="utf-8")


@given('the ES repository contains an old cleanup context')
def given_old_cleanup_context(workspace: EnvGeneWorkspace):
    with Repo.clone_from(str(workspace.es_remote), workspace.base_dir / "old-cleanup", branch="main") as checkout:
        cleanup = Path(checkout.working_tree_dir) / workspace.es_relative_path / "cleanup" / "core"
        cleanup.mkdir(parents=True)
        (cleanup / "parameters.yaml").write_text("old: context\n", encoding="utf-8")
        checkout.git.add(".")
        actor = Actor("Test", "test@example.com")
        checkout.index.commit("Add old cleanup context", author=actor, committer=actor)
        checkout.remote().push("HEAD:refs/heads/main").raise_if_error()
    local_cleanup = _effective_set_dir(workspace) / "cleanup"
    local_cleanup.mkdir()
    (local_cleanup / "mapping.yaml").write_text("old: mapping\n", encoding="utf-8")


@then('the ES repository contains no cleanup context')
def then_no_remote_cleanup_context(workspace: EnvGeneWorkspace):
    with Repo(workspace.es_remote) as remote:
        effective_set = remote.commit("refs/heads/main").tree / workspace.es_relative_path
        assert "cleanup" not in [entry.name for entry in effective_set], "Old cleanup context remains in ES repository"


@then('the ES repository keeps its namespace mappings')
def then_es_mappings_unchanged(workspace: EnvGeneWorkspace):
    with Repo(workspace.es_remote) as remote:
        tree = remote.commit("refs/heads/main").tree
        for context in ("deployment", "runtime"):
            path = f"{workspace.es_relative_path}/{context}/mapping.yaml"
            assert (tree / path).data_stream.read() == workspace.es_before[path], f"Mapping changed: {path}"


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
