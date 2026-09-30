from pathlib import Path

import yaml
from pytest_bdd import given, then, parsers

from cucumber_tests.framework.workspace import EnvGeneWorkspace
from cucumber_tests.shared_steps.calculator_cli_steps import _MOCK_REGISTRY, _PRODUCTION_CLI


def _env_dir(workspace: EnvGeneWorkspace) -> Path:
    return workspace.base_dir / "environments" / workspace.cluster_name / workspace.env_name


def _object_profile(workspace: EnvGeneWorkspace, object_file: Path) -> dict:
    return workspace.get_yaml(object_file).get("profile") or {}


def _resource_profile_file(workspace: EnvGeneWorkspace, name: str) -> Path | None:
    profiles_dir = _env_dir(workspace) / "Profiles"
    matches = [p for p in profiles_dir.glob("*.y*ml") if p.stem == name] if profiles_dir.exists() else []
    return matches[0] if matches else None


def _service_params(workspace: EnvGeneWorkspace, app: str, service: str) -> dict:
    deployment_dir = _env_dir(workspace) / "effective-set" / "deployment"
    matches = [p for p in deployment_dir.rglob(f"per-service-parameters/{service}/deployment-parameters.yaml")
               if app in p.parts]
    assert len(matches) == 1, f"Expected one per-service parameters file for {app}/{service}, found {matches}"
    return yaml.safe_load(matches[0].read_text(encoding="utf-8")) or {}


@given("the Calculator CLI generates the effective set")
def given_production_calculator_cli(workspace: EnvGeneWorkspace):
    registry_file = workspace.config_dir / "registry.yml"
    registries = yaml.safe_load(registry_file.read_text(encoding="utf-8")) or {}
    registries.update(_MOCK_REGISTRY)
    registry_file.write_text(yaml.dump(registries), encoding="utf-8")
    if not hasattr(workspace, "extra_env"):
        workspace.extra_env = {}
    workspace.extra_env["EFFECTIVE_SET_CLI_PATH"] = _PRODUCTION_CLI


@then(parsers.parse('the namespace "{folder}" references resource profile "{name}" with baseline "{baseline}"'))
def namespace_references_profile(workspace: EnvGeneWorkspace, folder: str, name: str, baseline: str):
    profile = _object_profile(workspace, _env_dir(workspace) / "Namespaces" / folder / "namespace.yml")
    assert profile == {"name": name, "baseline": baseline}, profile


@then(parsers.parse('the cloud references resource profile "{name}" with baseline "{baseline}"'))
def cloud_references_profile(workspace: EnvGeneWorkspace, name: str, baseline: str):
    profile = _object_profile(workspace, _env_dir(workspace) / "cloud.yml")
    assert profile == {"name": name, "baseline": baseline}, profile


@then(parsers.parse('the namespace "{folder}" has no resource profile'))
def namespace_has_no_profile(workspace: EnvGeneWorkspace, folder: str):
    profile = _object_profile(workspace, _env_dir(workspace) / "Namespaces" / folder / "namespace.yml")
    assert profile == {}, profile


@then(parsers.parse('the resource profile "{name}" in the environment instance has baseline "{baseline}"'))
def resource_profile_has_baseline(workspace: EnvGeneWorkspace, name: str, baseline: str):
    profile_file = _resource_profile_file(workspace, name)
    assert profile_file is not None, f"Resource profile {name} is not in {_env_dir(workspace) / 'Profiles'}"
    assert workspace.get_yaml(profile_file).get("baseline") == baseline


@then(parsers.parse('the environment instance has no resource profile "{name}"'))
def environment_has_no_resource_profile(workspace: EnvGeneWorkspace, name: str):
    assert _resource_profile_file(workspace, name) is None


@then(parsers.parse('the service "{service}" of application "{app}" receives "{param}" as "{value}"'))
def service_receives_param(workspace: EnvGeneWorkspace, service: str, app: str, param: str, value: str):
    params = _service_params(workspace, app, service)
    assert str(params.get(param)) == value, params


@then(parsers.parse('the service "{service}" of application "{app}" does not receive "{param}"'))
def service_does_not_receive_param(workspace: EnvGeneWorkspace, service: str, app: str, param: str):
    params = _service_params(workspace, app, service)
    assert param not in params, params
