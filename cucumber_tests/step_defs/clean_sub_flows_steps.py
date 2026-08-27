"""Feature-specific step definitions for clean-sub-flows.feature.

Only steps that are genuinely specific to the CLEAN sub-flows scenarios live here;
everything else (pipeline params, orchestrator run, success/failure, log assertions,
workspace init from test data, pipeline step status, BG state files) is reused from
shared_steps/unified_pipeline_steps.py and shared_steps/common_steps.py.
"""
import yaml
from pytest_bdd import then, parsers

from cucumber_tests.framework.workspace import EnvGeneWorkspace


def _load_namespace_yaml(workspace: EnvGeneWorkspace, name: str) -> dict:
    env_dir = workspace.builder.get_env_dir(workspace.cluster_name, workspace.env_name)
    ns_path = env_dir / "Namespaces" / name / "namespace.yml"
    workspace.assert_file_exists(ns_path)
    return yaml.safe_load(ns_path.read_text(encoding="utf-8")) or {}


@then(parsers.parse('the namespace "{name}" is marked as cleaned'))
def then_namespace_is_cleaned(workspace: EnvGeneWorkspace, name: str):
    content = _load_namespace_yaml(workspace, name)
    assert content.get("cleaned") is True, (
        f"Expected namespace '{name}' to have cleaned: true, got: {content.get('cleaned')!r}.\n"
        f"Full namespace.yml: {content}"
    )


@then(parsers.parse('the namespace "{name}" is not marked as cleaned'))
def then_namespace_is_not_cleaned(workspace: EnvGeneWorkspace, name: str):
    content = _load_namespace_yaml(workspace, name)
    assert "cleaned" not in content, (
        f"Expected namespace '{name}' to have no 'cleaned' attribute, got: {content.get('cleaned')!r}.\n"
        f"Full namespace.yml: {content}"
    )


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
