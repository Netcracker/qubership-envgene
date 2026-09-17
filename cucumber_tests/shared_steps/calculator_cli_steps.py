"""Step definitions for Calculator CLI BDD scenarios (UC-CC-DP-*, UC-CC-MR-*, UC-CC-HR-*, UC-CC-CR-*,
UC-CC-PM-*, UC-CC-GI-*, UC-CC-CP-*).

All generic Given/When/Then steps come from shared_steps and are imported in test_calculator_cli.py.
"""
from pathlib import Path
import re
import yaml

from pytest_bdd import then, parsers

from cucumber_tests.framework.workspace import EnvGeneWorkspace

# Production CLI entry point — present in the envgene Docker image under /module/
_PRODUCTION_CLI = "/module/scripts/utils/run_effective_set_cli.sh"

# mock-reg registry definition matching the purl in test SBOM files
_MOCK_REGISTRY = {
    "mock-reg": {
        "name": "mock-reg",
        "mavenConfig": {
            "targetSnapshot": "snapshot",
            "targetStaging": "staging",
            "targetRelease": "release",
            "repositoryDomainName": "http://localhost:8000/",
        },
    }
}


def _get_effective_set_dir(workspace):
    es_dir = (
        workspace.base_dir
        / "environments" / workspace.cluster_name / workspace.env_name
        / "effective-set" / "deployment"
    )
    assert es_dir.exists(), f"effective-set/deployment directory does not exist at {es_dir}"
    return es_dir


@then(parsers.parse('the effective set deployment parameters contain "{key_value}"'))
def effective_set_deployment_params_contain(workspace: EnvGeneWorkspace, key_value: str) -> None:
    es_dir = _get_effective_set_dir(workspace)
    found = False
    for params_file in es_dir.rglob("*.yaml"):
        if key_value in params_file.read_text(encoding="utf-8"):
            found = True
            break
    assert found, (
        f"'{key_value}' not found in any *.yaml under {es_dir}.\n"
        f"YAML files: {[str(p) for p in es_dir.rglob('*.yaml')]}"
    )


@then(parsers.parse('the effective set contains a generation id subdirectory for "{app_name}"'))
def effective_set_contains_generation_id_subdir(workspace: EnvGeneWorkspace, app_name: str) -> None:
    es_dir = _get_effective_set_dir(workspace)
    uuid_pattern = re.compile(
        r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', re.IGNORECASE
    )
    found = any(
        child.is_dir() and uuid_pattern.match(child.name)
        for app_dir in es_dir.rglob(app_name)
        if app_dir.is_dir()
        for child in app_dir.iterdir()
    )
    assert found, f"No UUID-named generation subdirectory found for app '{app_name}' under {es_dir}"


@then(parsers.parse('the effective set deployment parameters for "{app_name}" exist under version "{version}"'))
def effective_set_params_exist_under_version(workspace: EnvGeneWorkspace, app_name: str, version: str) -> None:
    es_dir = _get_effective_set_dir(workspace)
    found = any(
        (app_dir / version / "values").exists()
        for app_dir in es_dir.rglob(app_name)
        if app_dir.is_dir()
    )
    assert found, f"No version directory '{version}/values' found for app '{app_name}' under {es_dir}"


def _find_deployment_file(workspace: EnvGeneWorkspace, app_name: str, filename: str = "custom-params.yaml") -> Path:
    es_dir = _get_effective_set_dir(workspace)
    candidates = [
        path for path in es_dir.rglob(filename)
        if app_name in path.parts
    ]
    assert candidates, (
        f"'{filename}' not found under '{app_name}' in {es_dir}.\n"
        f"Files present: {[str(p) for p in es_dir.rglob('*.yaml')]}\n"
        f"STDOUT: {workspace.stdout}\nSTDERR: {workspace.stderr}"
    )
    return candidates[0]


@then(parsers.parse('the "{app_name}" custom-params.yaml has "{key_value}" at root, under global, and per-service'))
def custom_params_yaml_has_key_at_root_global_per_service(workspace: EnvGeneWorkspace, app_name: str, key_value: str):
    path = _find_deployment_file(workspace, app_name, "custom-params.yaml")
    content = path.read_text(encoding="utf-8")
    data = yaml.safe_load(content) or {}
    key, _, value = key_value.partition(":")
    key = key.strip()
    expected = value.strip()

    assert key in data, (f"Key '{key}' not found at root of {path}")
    assert data.get(key) == expected, (f"Expected '{key}: {expected}' at root, got {data.get(key)!r}")

    global_data = data.get("global")
    assert isinstance(global_data, dict), (f"'global' is missing or not a mapping in {path}")
    assert global_data.get(key) == expected, (
        f"Expected '{key}: {expected}' under global, got {global_data.get(key)!r}"
    )

    # Services = mappings appearing after global
    items = list(data.items())
    global_index = next(i for i, (name, _) in enumerate(items) if name == "global")
    services = {
        name: params for name, params in items[global_index + 1:]
        if isinstance(params, dict)
    }
    assert services, f"No per-service blocks found after 'global' in {path}"
    missing = [
        name for name, params in services.items()
        if params.get(key) != expected
    ]
    assert not missing, (
        f"Expected '{key}: {expected}' in every per-service block, but missing/wrong in: {missing}"
    )


@then(parsers.parse('the "{app_name}" collision-credentials.yaml contains "{key_value}"'))
def collision_credentials_yaml_contains(workspace: EnvGeneWorkspace, app_name: str, key_value: str) -> None:
    collision_path = _find_deployment_file(workspace, app_name, "collision-credentials.yaml")
    data = yaml.safe_load(collision_path.read_text(encoding="utf-8")) or {}
    key, _, raw_val = key_value.partition(": ")
    key = key.strip()
    raw_val = raw_val.strip()
    expected_val = yaml.safe_load(raw_val)
    assert key in data, (
        f"Key '{key}' not found in {collision_path}.\nFull content:\n{collision_path.read_text()}"
    )
    assert data[key] == expected_val, (
        f"'{key}' = {data[key]!r} in {collision_path}, expected {expected_val!r}"
    )


@then(parsers.parse('the "{app_name}" custom-params.yaml keeps the per-service entry for "{service}"'))
def custom_params_yaml_keeps_per_service_entry(workspace: EnvGeneWorkspace, app_name: str, service: str) -> None:
    custom_params_path = _find_deployment_file(workspace, app_name, "custom-params.yaml")
    data = yaml.safe_load(custom_params_path.read_text(encoding="utf-8")) or {}
    assert service in data and isinstance(data[service], dict), (
        f"Per-service key '{service}' missing or not a mapping in {custom_params_path}.\n"
        f"Top-level keys: {list(data.keys())}"
    )