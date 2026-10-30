from pathlib import Path
from types import SimpleNamespace

import pytest

from deployment_plan.process_deployment_plan import reduce_deployment_plan
from envgene_shared.utils.logger import logger
from envgene_shared.utils.yaml_utils import openYaml, writeYamlToFile
from envgenehelper.deploy_plan_adapter import DeployPlanEntity, EnvgeneDeployPlan


@pytest.fixture
def cleanup_context(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("CLUSTER_NAME", "cluster-01")
    monkeypatch.setenv("ENVIRONMENT_NAME", "env-01")
    monkeypatch.setenv("FULL_ENV_NAME", "cluster-01/env-01")
    inventory = tmp_path / "environments" / "cluster-01" / "env-01" / "Inventory"
    inventory.mkdir(parents=True)
    writeYamlToFile(inventory / "namespace-map.yml", {
        "core": "env-core",
        "bss": {"origin": "env-origin", "peer": "env-peer"},
        "controller": "env-controller",
    })
    plan = EnvgeneDeployPlan(entities=[
        DeployPlanEntity(version="app:1.0", namespace=namespace, deployPostfix=postfix)
        for namespace, postfix in (("env-core", "core"), ("env-origin", "bss"), ("env-peer", "bss"))
    ])
    plan.write()
    return SimpleNamespace(params={}, deploy_plan=plan)


@pytest.mark.parametrize("names, remaining", [
    (None, []),
    ("", []),
    ("env-core", ["env-origin", "env-peer"]),
    ("env-origin;env-peer", ["env-core"]),
])
def test_reduce_plan_preserves_only_unselected_namespaces(cleanup_context, names, remaining):
    cleanup_context.params["NAMESPACE_NAMES"] = names

    reduce_deployment_plan(cleanup_context)

    assert [entry["namespace"] for entry in openYaml(EnvgeneDeployPlan.path())] == remaining
    assert [entry.namespace for entry in cleanup_context.deploy_plan.entities] == remaining
    assert not EnvgeneDeployPlan.delta_path().exists()
    assert not Path("deploy-plan.yaml").exists()


def test_unknown_namespace_fails_before_any_plan_is_changed(cleanup_context):
    cleanup_context.params["NAMESPACE_NAMES"] = "env-core;does-not-exist"
    initial_plan = EnvgeneDeployPlan.path().read_bytes()
    initial_entities = cleanup_context.deploy_plan.to_dict()

    with pytest.raises(ValueError, match="does-not-exist.*namespace-map.yml"):
        reduce_deployment_plan(cleanup_context)

    assert EnvgeneDeployPlan.path().read_bytes() == initial_plan
    assert cleanup_context.deploy_plan.to_dict() == initial_entities


def test_namespace_without_plan_entry_warns_and_preserves_plan(cleanup_context, monkeypatch):
    cleanup_context.params["NAMESPACE_NAMES"] = "env-controller"
    initial_entities = cleanup_context.deploy_plan.to_dict()
    warnings = []
    monkeypatch.setattr(logger, "warning", warnings.append)

    reduce_deployment_plan(cleanup_context)

    assert warnings == ["Namespace 'env-controller' is absent from deploy-plan.yml"]
    assert openYaml(EnvgeneDeployPlan.path()) == initial_entities


def test_empty_namespace_map_reports_the_requested_namespace(cleanup_context):
    cleanup_context.params["NAMESPACE_NAMES"] = "env-core"
    (EnvgeneDeployPlan.path().parent / "namespace-map.yml").write_text("")

    with pytest.raises(ValueError, match="env-core.*namespace-map.yml"):
        reduce_deployment_plan(cleanup_context)
