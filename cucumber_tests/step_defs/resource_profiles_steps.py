from pathlib import Path

import yaml
from pytest_bdd import given, then, parsers

from cucumber_tests.framework.workspace import EnvGeneWorkspace
from cucumber_tests.shared_steps.calculator_cli_steps import _MOCK_REGISTRY, _PRODUCTION_CLI
from build_env.deployment_profile import GENERATED_PROFILES_MAP_KEY, PROFILE_OVERRIDE_SUFFIX

# The name and the map the apply_deployment_profile step writes, expected here as a consumer does.
# The test data of these scenarios deploys with deployPostfix "bss".
GENERATED_PROFILE_NAME = f"bss{PROFILE_OVERRIDE_SUFFIX}"
GENERATED_MAP_KEY = GENERATED_PROFILES_MAP_KEY


def _env_dir(workspace: EnvGeneWorkspace) -> Path:
    return workspace.base_dir / "environments" / workspace.cluster_name / workspace.env_name


def _env_definition(workspace: EnvGeneWorkspace) -> dict:
    return workspace.get_yaml(_env_dir(workspace) / "Inventory" / "env_definition.yml")


def _generated_profile_file(workspace: EnvGeneWorkspace) -> Path:
    return _env_dir(workspace) / "Inventory" / "resource_profiles" / f"{GENERATED_PROFILE_NAME}.yml"


def _object_profile(workspace: EnvGeneWorkspace, object_file: Path) -> dict:
    return workspace.get_yaml(object_file).get("profile") or {}


def _resource_profile_file(workspace: EnvGeneWorkspace, name: str) -> Path | None:
    profiles_dir = _env_dir(workspace) / "Profiles"
    matches = [p for p in profiles_dir.glob("*.y*ml") if p.stem == name] if profiles_dir.exists() else []
    return matches[0] if matches else None


def _service_params(workspace: EnvGeneWorkspace, app: str, service: str) -> dict:
    deployment_dir = _env_dir(workspace) / "effective-set" / "deployment"
    # The directory under per-service-parameters carries the application's chart name, not the
    # service name - every service the application provides is a key inside the one file.
    matches = [p for p in deployment_dir.rglob("per-service-parameters/*/deployment-parameters.yaml")
               if app in p.parts]
    assert len(matches) == 1, f"Expected one per-service parameters file for {app}, found {matches}"
    params = yaml.safe_load(matches[0].read_text(encoding="utf-8")) or {}
    assert service in params, f"Service '{service}' missing from {matches[0]}, found {sorted(params)}"
    return params[service]


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


@then(parsers.parse('the namespace "{folder}" references resource profile "{name}"'))
def namespace_references_profile_by_name(workspace: EnvGeneWorkspace, folder: str, name: str):
    profile = _object_profile(workspace, _env_dir(workspace) / "Namespaces" / folder / "namespace.yml")
    assert profile == {"name": name}, profile


@then(parsers.parse('the run writes the generated resource profile with baseline "{baseline}"'))
def run_writes_generated_profile(workspace: EnvGeneWorkspace, baseline: str):
    profile_file = _generated_profile_file(workspace)
    assert profile_file.is_file(), f"{profile_file} is not written by the run"
    profile = workspace.get_yaml(profile_file)
    assert profile["name"] == GENERATED_PROFILE_NAME, profile
    assert {application["baseline"] for application in profile["applications"]} == {baseline}, profile


@then("the run leaves no generated resource profile")
def run_leaves_no_generated_profile(workspace: EnvGeneWorkspace):
    assert not _generated_profile_file(workspace).is_file()


@then(parsers.parse('the environment definition assigns the generated resource profile to "{key}"'))
def definition_assigns_generated_profile(workspace: EnvGeneWorkspace, key: str):
    generated = _env_definition(workspace)["envTemplate"].get(GENERATED_MAP_KEY) or {}
    assert generated.get(key) == GENERATED_PROFILE_NAME, generated


@then(parsers.parse('the environment definition has no generated resource profile for "{key}"'))
def definition_has_no_generated_profile(workspace: EnvGeneWorkspace, key: str):
    generated = _env_definition(workspace)["envTemplate"].get(GENERATED_MAP_KEY) or {}
    assert key not in generated, generated


@then(parsers.parse('the environment definition keeps resource profile "{name}" for "{key}"'))
def definition_keeps_resource_profile(workspace: EnvGeneWorkspace, name: str, key: str):
    profiles = _env_definition(workspace)["envTemplate"].get("envSpecificResourceProfiles") or {}
    assert profiles.get(key) == name, profiles
