from pathlib import Path

import yaml
from pytest_bdd import given, then, parsers

from cucumber_tests.framework.workspace import EnvGeneWorkspace
from cucumber_tests.shared_steps.calculator_cli_steps import _MOCK_REGISTRY, _PRODUCTION_CLI
from build_env.deployment_profile import GENERATED_KEY_COMMENT, GENERATED_MARKER, GENERATED_PROFILES_MAP_KEY, PROFILE_DOC, \
    PROFILE_OVERRIDE_SUFFIX, RESOURCE_PROFILES_DIR_NAME
from build_env.resource_profiles import RESULTING_PROFILES_DIR_NAME

GENERATED_MAP_KEY = GENERATED_PROFILES_MAP_KEY


def _env_dir(workspace: EnvGeneWorkspace) -> Path:
    return workspace.base_dir / "environments" / workspace.cluster_name / workspace.env_name


def _env_definition(workspace: EnvGeneWorkspace) -> dict:
    return workspace.get_yaml(_env_dir(workspace) / "Inventory" / "env_definition.yml")


def _generated_profile_files(workspace: EnvGeneWorkspace) -> list[Path]:
    """The override files of the instance that carry the marker the PROFILE step writes."""
    folder = _env_dir(workspace) / "Inventory" / RESOURCE_PROFILES_DIR_NAME
    marker = f"# {GENERATED_MARKER}"
    found = []
    for path in sorted(folder.glob(f"*{PROFILE_OVERRIDE_SUFFIX}.y*ml")):
        lines = path.read_text(encoding="utf-8").splitlines()
        first = next((line for line in lines if line.strip()), "")
        if first.strip() == marker:
            found.append(path)
    return found


def _generated_profile_file(workspace: EnvGeneWorkspace) -> Path:
    """The one generated override of the run, found by its marker instead of by a hardcoded postfix."""
    found = _generated_profile_files(workspace)
    assert len(found) == 1, f"Expected one generated profile, found {found}"
    return found[0]


def _override_file(workspace: EnvGeneWorkspace, name: str) -> Path:
    return _env_dir(workspace) / "Inventory" / RESOURCE_PROFILES_DIR_NAME / f"{name}.yml"


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
    # An assembled profile of that name may be absent for two reasons, and only one of them is the result the
    # scenario claims: the run assembled profiles, and this one is not among them.
    profiles_dir = _env_dir(workspace) / RESULTING_PROFILES_DIR_NAME
    assert profiles_dir.is_dir(), f"the run assembled no resource profile at all in {profiles_dir}"
    assert _resource_profile_file(workspace, name) is None, name


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
    assert profile["name"] == profile_file.stem, profile
    assert {application["baseline"] for application in profile["applications"]} == {baseline}, profile


@then("the run leaves no generated resource profile")
def run_leaves_no_generated_profile(workspace: EnvGeneWorkspace):
    assert not _generated_profile_files(workspace), _generated_profile_files(workspace)


@then(parsers.parse('the environment definition assigns the generated resource profile to "{key}"'))
def definition_assigns_generated_profile(workspace: EnvGeneWorkspace, key: str):
    # The key of the map is the folder of the Namespace and the name is built from the deployPostfix, so the two
    # coincide only by accident: a Blue-Green pair keys bss-origin and names bss-profile-override.
    generated = _env_definition(workspace)["envTemplate"].get(GENERATED_MAP_KEY) or {}
    name = generated.get(key)
    assert name, generated
    assert name.endswith(PROFILE_OVERRIDE_SUFFIX), generated
    profile_file = _override_file(workspace, name)
    assert profile_file in _generated_profile_files(workspace), f"{name} of {key} carries no marker of EnvGene"


@then(parsers.parse('the environment definition has no generated resource profile for "{key}"'))
def definition_has_no_generated_profile(workspace: EnvGeneWorkspace, key: str):
    generated = _env_definition(workspace)["envTemplate"].get(GENERATED_MAP_KEY) or {}
    assert key not in generated, generated


@then(parsers.parse('the run writes the generated profile "{name}" with baseline "{baseline}"'))
def run_writes_generated_profile_by_name(workspace: EnvGeneWorkspace, name: str, baseline: str):
    profile_file = _override_file(workspace, name)
    assert profile_file.is_file(), f"{profile_file} is not written by the run"
    profile = workspace.get_yaml(profile_file)
    assert profile["name"] == name, profile
    assert {application["baseline"] for application in profile["applications"]} == {baseline}, profile


@then(parsers.parse('the generated resource profile lists "{app}" with baseline "{baseline}"'))
def generated_profile_lists_app(workspace: EnvGeneWorkspace, app: str, baseline: str):
    profile = workspace.get_yaml(_generated_profile_file(workspace))
    entries = [entry for entry in profile["applications"] if entry.get("name") == app]
    assert len(entries) == 1, f"{app} is listed {len(entries)} times in {profile['applications']}"
    assert entries[0]["baseline"] == baseline, profile


@then(parsers.parse('the environment definition assigns the generated profile "{name}" to "{key}"'))
def definition_assigns_generated_profile_by_name(workspace: EnvGeneWorkspace, name: str, key: str):
    generated = _env_definition(workspace)["envTemplate"].get(GENERATED_MAP_KEY) or {}
    assert generated.get(key) == name, generated


@then(parsers.parse('the environment definition keeps resource profile "{name}" for "{key}"'))
def definition_keeps_resource_profile(workspace: EnvGeneWorkspace, name: str, key: str):
    profiles = _env_definition(workspace)["envTemplate"].get("envSpecificResourceProfiles") or {}
    assert profiles.get(key) == name, profiles


@given(parsers.parse('the pipeline parameter "SD_DATA" is set to a Solution Descriptor that deploys '
                     '"{app_version}" to the deployPostfixes "{first}" and "{second}"'))
def sd_data_with_two_deploy_postfixes(workspace: EnvGeneWorkspace, app_version: str, first: str, second: str):
    sd_content = yaml.dump({
        "version": 2.2,
        "type": "solutionDeploy",
        "applications": [{"version": app_version, "deployPostfix": first},
                         {"version": app_version, "deployPostfix": second}],
    })
    if not hasattr(workspace, "extra_env"):
        workspace.extra_env = {}
    workspace.extra_env["SD_DATA"] = sd_content


@then("the generated resource profile opens with the marker of EnvGene")
def generated_profile_opens_with_marker(workspace: EnvGeneWorkspace):
    lines = _generated_profile_file(workspace).read_text(encoding="utf-8").splitlines()
    assert lines[0] == f"# {GENERATED_MARKER}", lines[:6]
    header = []
    for line in lines:
        if not line.startswith("#"):
            break
        header.append(line)
    assert any(PROFILE_DOC in line for line in header), header

@then("the environment definition records the generated entry with the comment of EnvGene")
def definition_records_generated_entry_with_comment(workspace: EnvGeneWorkspace):
    lines = (_env_dir(workspace) / "Inventory" / "env_definition.yml").read_text(encoding="utf-8").splitlines()
    start = next((i for i, line in enumerate(lines) if line.strip().startswith(f"{GENERATED_MAP_KEY}:")), None)
    assert start is not None, lines
    body = lines[start + 1:]
    commented = [i for i, line in enumerate(body) if GENERATED_KEY_COMMENT in line]
    assert commented, body
    following = body[commented[0] + 1] if commented[0] + 1 < len(body) else ""
    assert ":" in following and not following.strip().startswith("#"), body
