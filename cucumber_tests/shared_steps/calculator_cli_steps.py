"""Step definitions for Calculator CLI BDD scenarios (UC-CC-DP-*, UC-CC-MR-*, UC-CC-HR-*, UC-CC-CR-*,
UC-CC-PM-*, UC-CC-GI-*, UC-CC-CP-*).

All generic Given/When/Then steps come from shared_steps and are imported in test_calculator_cli.py.
"""
import re
import yaml
from pathlib import Path

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


@then(parsers.parse('the effective set deployment parameters contain "{key_value}"'))
def effective_set_deployment_params_contain(workspace: EnvGeneWorkspace, key_value: str) -> None:
    es_dir = (
        workspace.base_dir
        / "environments" / workspace.cluster_name / workspace.env_name
        / "effective-set" / "deployment"
    )
    assert es_dir.exists(), f"effective-set/deployment directory does not exist at {es_dir}"
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
    es_dir = (
        workspace.base_dir
        / "environments" / workspace.cluster_name / workspace.env_name
        / "effective-set" / "deployment"
    )
    assert es_dir.exists(), f"effective-set/deployment directory does not exist at {es_dir}"
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
    es_dir = (
        workspace.base_dir
        / "environments" / workspace.cluster_name / workspace.env_name
        / "effective-set" / "deployment"
    )
    assert es_dir.exists(), f"effective-set/deployment directory does not exist at {es_dir}"
    found = any(
        (app_dir / version / "values").exists()
        for app_dir in es_dir.rglob(app_name)
        if app_dir.is_dir()
    )
    assert found, f"No version directory '{version}/values' found for app '{app_name}' under {es_dir}"


def _find_custom_params_yaml(workspace: EnvGeneWorkspace, app_name: str, filename: str = "custom-params.yaml") -> Path:
    """Locate ``filename`` under the deployment effective-set for ``app_name``."""
    es_dir = (
        workspace.base_dir
        / "environments" / workspace.cluster_name / workspace.env_name
        / "effective-set" / "deployment"
    )
    assert es_dir.exists(), (
        f"effective-set/deployment directory does not exist at {es_dir}\n"
        f"STDOUT: {workspace.stdout}\nSTDERR: {workspace.stderr}"
    )
    candidates = [
        p for p in es_dir.rglob(filename)
        if any(part == app_name for part in p.parts)
    ]
    assert candidates, (
        f"'{filename}' not found under any '{app_name}' directory in {es_dir}.\n"
        f"Files present: {[str(p) for p in es_dir.rglob('*.yaml')]}\n"
        f"STDOUT: {workspace.stdout}\nSTDERR: {workspace.stderr}"
    )
    return candidates[0]


@then(parsers.parse('the "{app_name}" custom-params.yaml has "{key_value}" at root, under global, and per-service'))
def custom_params_yaml_has_key_at_root_global_per_service(
    workspace: EnvGeneWorkspace, app_name: str, key_value: str
) -> None:
    """Assert that key_value (e.g. 'LOG_LEVEL: DEBUG') appears at the root of the YAML mapping,
    inside the ``global`` sub-map, and inside at least one per-service sub-map.
    """
    custom_params_path = _find_custom_params_yaml(workspace, app_name)
    data = yaml.safe_load(custom_params_path.read_text(encoding="utf-8")) or {}

    key, _, raw_val = key_value.partition(": ")
    key = key.strip()
    raw_val = raw_val.strip()

    def _parse_val(s: str):
        return yaml.safe_load(s)

    expected_val = _parse_val(raw_val)

    assert key in data, (
        f"Key '{key}' not found at root of {custom_params_path}.\nFull content:\n{custom_params_path.read_text()}"
    )
    assert data[key] == expected_val, (
        f"Root key '{key}' = {data[key]!r}, expected {expected_val!r} in {custom_params_path}"
    )

    global_map = data.get("global")
    assert isinstance(global_map, dict), (
        f"'global' key missing or not a mapping in {custom_params_path}.\nFull content:\n{custom_params_path.read_text()}"
    )
    assert key in global_map and global_map[key] == expected_val, (
        f"Key '{key}' not present or wrong value in 'global' block of {custom_params_path}.\n"
        f"global block: {global_map}"
    )

    reserved = {"global"}
    per_service_hits = [
        svc for svc, svc_val in data.items()
        if svc not in reserved and isinstance(svc_val, dict) and svc_val.get(key) == expected_val
    ]
    assert per_service_hits, (
        f"Key '{key}' not found in any per-service block of {custom_params_path}.\n"
        f"Non-global mapping keys: {[k for k, v in data.items() if k not in reserved and isinstance(v, dict)]}"
    )


@then(parsers.parse('the "{app_name}" collision-custom-params.yaml contains "{key_value}"'))
def collision_custom_params_yaml_contains(
    workspace: EnvGeneWorkspace, app_name: str, key_value: str
) -> None:
    """Assert that key_value (e.g. 'web: collision-value') is present in collision-custom-params.yaml."""
    collision_path = _find_custom_params_yaml(workspace, app_name, "collision-custom-params.yaml")
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
def custom_params_yaml_keeps_per_service_entry(
    workspace: EnvGeneWorkspace, app_name: str, service: str
) -> None:
    """Assert that the named service has its own sub-map in custom-params.yaml (collision did not evict it)."""
    custom_params_path = _find_custom_params_yaml(workspace, app_name)
    data = yaml.safe_load(custom_params_path.read_text(encoding="utf-8")) or {}

    assert service in data and isinstance(data[service], dict), (
        f"Per-service key '{service}' missing or not a mapping in {custom_params_path}.\n"
        f"Top-level keys: {list(data.keys())}"
    )
