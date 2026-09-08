"""Feature-specific step definitions for bgd-sub-flows.feature.

Only steps that are genuinely specific to the BGD sub-flows scenarios live
here; everything else (pipeline params, orchestrator run, success/failure,
log assertions, workspace init from test data) is reused from
shared_steps/unified_pipeline_steps.py and shared_steps/common_steps.py.
"""
import json
import re

import yaml
from pytest_bdd import given, then, parsers

from cucumber_tests.framework.workspace import EnvGeneWorkspace


@given(parsers.parse('the BG state files are origin "{origin_state}" and peer "{peer_state}"'))
def given_bg_state_files(workspace: EnvGeneWorkspace, origin_state: str, peer_state: str):
    workspace.builder.set_bg_state_files(origin_state, peer_state, workspace.cluster_name, workspace.env_name)


@given(parsers.parse('the pipeline parameter "BG_STATE" targets origin "{origin_state}" and peer "{peer_state}"'))
def given_bg_state_pipeline_parameter(workspace: EnvGeneWorkspace, origin_state: str, peer_state: str):
    if not hasattr(workspace, "extra_env"):
        workspace.extra_env = {}
    payload = {
        "BGState": {
            "controllerNamespace": "test-env-bg-controller",
            "originNamespace": {"name": "test-env-bss-origin", "state": origin_state, "version": "v1"},
            "peerNamespace": {"name": "test-env-bss-peer", "state": peer_state, "version": "v1"},
            "updateTime": "2026-08-20T00:00:00Z",
        }
    }
    workspace.extra_env["BG_STATE"] = json.dumps(payload)


@then(parsers.parse('the BG state files are origin "{origin_state}" and peer "{peer_state}"'))
def then_bg_state_files(workspace: EnvGeneWorkspace, origin_state: str, peer_state: str):
    env_dir = workspace.builder.get_env_dir(workspace.cluster_name, workspace.env_name)
    dotfiles = {p.name for p in env_dir.iterdir() if p.is_file() and p.name.startswith(".")}
    expected = {f".origin-{origin_state}", f".peer-{peer_state}"}
    assert dotfiles == expected, (
        f"Expected BG state files {expected}, found {dotfiles}.\n"
        f"STDOUT: {workspace.stdout}\nSTDERR: {workspace.stderr}"
    )


@given('the deploy plan is recorded as a baseline')
def given_deploy_plan_baseline(workspace: EnvGeneWorkspace):
    env_dir = workspace.builder.get_env_dir(workspace.cluster_name, workspace.env_name)
    plan_path = env_dir / "Inventory" / "deploy-plan.yml"
    workspace.assert_file_exists(plan_path)
    workspace.deploy_plan_baseline = plan_path.read_text(encoding="utf-8")


@then('the deploy plan file is unchanged')
def then_deploy_plan_unchanged(workspace: EnvGeneWorkspace):
    env_dir = workspace.builder.get_env_dir(workspace.cluster_name, workspace.env_name)
    plan_path = env_dir / "Inventory" / "deploy-plan.yml"
    workspace.assert_file_exists(plan_path)
    baseline = getattr(workspace, "deploy_plan_baseline", None)
    assert baseline is not None, "No baseline recorded — call 'the deploy plan is recorded as a baseline' first"
    before = yaml.safe_load(baseline)
    after = yaml.safe_load(plan_path.read_text(encoding="utf-8"))
    assert before == after, (
        f"deploy-plan.yml changed unexpectedly.\nBefore: {before}\nAfter: {after}\n"
        f"STDOUT: {workspace.stdout}\nSTDERR: {workspace.stderr}"
    )


@then(parsers.parse('the environment inventory field "envTemplate.bgNsArtifacts.{role}" equals "{value}"'))
def then_bg_ns_artifacts_field(workspace: EnvGeneWorkspace, role: str, value: str):
    env_dir = workspace.builder.get_env_dir(workspace.cluster_name, workspace.env_name)
    env_def_path = env_dir / "Inventory" / "env_definition.yml"
    workspace.assert_file_exists(env_def_path)
    content = yaml.safe_load(env_def_path.read_text(encoding="utf-8"))
    actual = content.get("envTemplate", {}).get("bgNsArtifacts", {}).get(role)
    assert actual == value, (
        f"Expected envTemplate.bgNsArtifacts.{role} == '{value}', got '{actual}'.\n"
        f"Full env_definition.yml: {content}"
    )


@then(parsers.parse(
    'the namespace directories "{origin_ns}" and "{peer_ns}" have identical content except the namespace name'))
def then_namespace_dirs_identical(workspace: EnvGeneWorkspace, origin_ns: str, peer_ns: str):
    env_dir = workspace.builder.get_env_dir(workspace.cluster_name, workspace.env_name)
    origin_dir = env_dir / "Namespaces" / origin_ns
    peer_dir = env_dir / "Namespaces" / peer_ns
    workspace.assert_file_exists(origin_dir)
    workspace.assert_file_exists(peer_dir)

    def snapshot(root):
        result = {}
        for path in sorted(root.rglob("*")):
            if not path.is_file():
                continue
            rel = str(path.relative_to(root))
            content = path.read_text(encoding="utf-8")
            if path.name == "namespace.yml":
                data = yaml.safe_load(content) or {}
                data.pop("name", None)
                content = yaml.dump(data, sort_keys=True)
            result[rel] = content
        return result

    origin_snapshot = snapshot(origin_dir)
    peer_snapshot = snapshot(peer_dir)
    assert origin_snapshot.keys() == peer_snapshot.keys(), (
        f"File sets differ between '{origin_ns}' and '{peer_ns}': "
        f"only in origin: {origin_snapshot.keys() - peer_snapshot.keys()}, "
        f"only in peer: {peer_snapshot.keys() - origin_snapshot.keys()}"
    )
    mismatches = {
        rel: (origin_snapshot[rel], peer_snapshot[rel])
        for rel in origin_snapshot
        if origin_snapshot[rel] != peer_snapshot[rel]
    }
    assert not mismatches, f"Content differs (excluding the namespace name) for: {mismatches}"


_ANSI_ESCAPE_RE = re.compile(r"\x1b\[[0-9;]*m")


@then(parsers.parse('the pipeline step "{step_name}" has status "{status}"'))
def then_pipeline_step_status(workspace: EnvGeneWorkspace, step_name: str, status: str):
    output = _ANSI_ESCAPE_RE.sub("", workspace.stdout + "\n" + workspace.stderr)
    pattern = rf"^{re.escape(step_name)}\s+{re.escape(status)}\b"
    found = re.search(pattern, output, re.MULTILINE)
    assert found, (
        f"Expected pipeline step '{step_name}' to have status '{status}' in the PIPELINE SUMMARY, "
        f"but it was not found.\nOutput:\n{output}"
    )


@then(parsers.parse(
    'the namespace map contains "{deploy_postfix}" with origin "{origin_ns}" and peer "{peer_ns}"'))
def then_namespace_map_has_both_sides(workspace: EnvGeneWorkspace, deploy_postfix: str, origin_ns: str, peer_ns: str):
    # Per docs/technical-design/instance-pipeline/deploy-postfix-namespace-map.md: a BG deployPostfix
    # always maps to an object holding both origin and peer namespace names; BG_NS_TARGET does not
    # affect this file at all.
    env_dir = workspace.builder.get_env_dir(workspace.cluster_name, workspace.env_name)
    map_path = env_dir / "Inventory" / "namespace-map.yml"
    workspace.assert_file_exists(map_path)
    namespace_map = yaml.safe_load(map_path.read_text(encoding="utf-8"))
    expected = {"origin": origin_ns, "peer": peer_ns}
    assert namespace_map.get(deploy_postfix) == expected, (
        f"Expected namespace-map.yml['{deploy_postfix}'] == {expected}, got {namespace_map}"
    )


def _assert_deploy_plan_has_entry(workspace: EnvGeneWorkspace, namespace: str, version: str):
    env_dir = workspace.builder.get_env_dir(workspace.cluster_name, workspace.env_name)
    plan_path = env_dir / "Inventory" / "deploy-plan.yml"
    workspace.assert_file_exists(plan_path)
    entries = yaml.safe_load(plan_path.read_text(encoding="utf-8")) or []
    matches = [e for e in entries if e.get("namespace") == namespace and e.get("version") == version]
    assert matches, f"No deploy-plan.yml entry for namespace='{namespace}' version='{version}'. Entries: {entries}"


@then(parsers.parse('the deploy plan contains an entry for namespace "{namespace}" with version "{version}"'))
def then_deploy_plan_has_entry(workspace: EnvGeneWorkspace, namespace: str, version: str):
    _assert_deploy_plan_has_entry(workspace, namespace, version)


@given(parsers.parse('the deploy plan contains an entry for namespace "{namespace}" with version "{version}"'))
def given_deploy_plan_has_entry(workspace: EnvGeneWorkspace, namespace: str, version: str):
    # Precondition, not an outcome: warmup's create_dp_for_warmup fails when no deploy-plan.yml
    # entry names the active namespace (see process-deployment-plan.md's warmup delta rules), so
    # scenarios that rely on this fixture data document the dependency explicitly here.
    _assert_deploy_plan_has_entry(workspace, namespace, version)


@given('the environment AppDefs and RegDefs paths are resolved for the deploy')
def given_local_appdefs_regdefs_resolved(workspace: EnvGeneWorkspace):
    # LOCAL_APPDEFS_PATH/LOCAL_REGDEFS_PATH are not pipeline parameters a caller sets - in a real
    # pipeline run they are derived by scripts/pipeline/resolve_env_names.py from CI_PROJECT_DIR
    # and ENV_NAMES before the orchestrator ever starts, and consumed as plain env vars by
    # modules/dpg's LocalClient. The BDD harness invokes the orchestrator directly and skips that
    # dotenv step, so this step reproduces the same derivation instead of modelling the paths as
    # externally-supplied pipeline input.
    if not hasattr(workspace, "extra_env"):
        workspace.extra_env = {}
    env_dir = f"environments/{workspace.cluster_name}/{workspace.env_name}"
    workspace.extra_env["LOCAL_APPDEFS_PATH"] = f"{env_dir}/AppDefs"
    workspace.extra_env["LOCAL_REGDEFS_PATH"] = f"{env_dir}/RegDefs"


@given(parsers.parse(
    'the pipeline parameter "APPLICATION_VERSIONS" is set to a Solution Descriptor with '
    'deployPostfix "{deploy_postfix}" for "{app_version}"'))
def given_application_versions_as_solution_descriptor(workspace: EnvGeneWorkspace, deploy_postfix: str, app_version: str):
    # A bare deployPostfix entry (process-deployment-plan.md 5.1-5.5, the path BG_NS_TARGET
    # gates) only arises from an actual Solution Descriptor - dpg.DeploymentPlanCalculator only
    # ever produces a populated `deployPostfix` field via SolutionDescriptor_2_x.collect_waves().
    # APPLICATION_VERSIONS is pointed at a local SD file (type: solutionDeploy) so dpg reads it
    # straight off disk (utils.is_file_path) instead of resolving an AppDef + fetching an
    # artifact over the network.
    sd_dir = workspace.base_dir / "solution_descriptors"
    sd_dir.mkdir(parents=True, exist_ok=True)
    sd_path = sd_dir / "bgd-sd.yml"
    sd_path.write_text(yaml.dump({
        "version": 2.2,
        "type": "solutionDeploy",
        "applications": [{"version": app_version, "deployPostfix": deploy_postfix}],
    }))
    if not hasattr(workspace, "extra_env"):
        workspace.extra_env = {}
    workspace.extra_env["APPLICATION_VERSIONS"] = str(sd_path)


@then(parsers.parse(
    'the namespace "{ns_dir}" application "{app}" deploy parameter "{param}" equals "{value}"'))
def then_namespace_application_param_equals(workspace: EnvGeneWorkspace, ns_dir: str, app: str, param: str, value: str):
    env_dir = workspace.builder.get_env_dir(workspace.cluster_name, workspace.env_name)
    app_path = env_dir / "Namespaces" / ns_dir / "Applications" / f"{app}.yml"
    workspace.assert_file_exists(app_path)
    content = yaml.safe_load(app_path.read_text(encoding="utf-8"))
    actual = content.get("deployParameters", {}).get(param)
    assert actual == value, f"Expected {app_path}.deployParameters.{param} == '{value}', got '{actual}'"


@then(parsers.parse('the rendered namespace.yml for "{ns_dir}" has deploy parameter "{param}" equal to "{value}"'))
def then_namespace_deploy_parameter_equals(workspace: EnvGeneWorkspace, ns_dir: str, param: str, value: str):
    env_dir = workspace.builder.get_env_dir(workspace.cluster_name, workspace.env_name)
    ns_path = env_dir / "Namespaces" / ns_dir / "namespace.yml"
    workspace.assert_file_exists(ns_path)
    content = yaml.safe_load(ns_path.read_text(encoding="utf-8"))
    actual = content.get("deployParameters", {}).get(param)
    assert actual == value, (
        f"Expected {ns_path}.deployParameters.{param} == '{value}', got '{actual}'.\n"
        f"Full namespace.yml: {content}"
    )
