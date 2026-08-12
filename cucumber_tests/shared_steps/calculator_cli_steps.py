"""Step definitions for Calculator CLI BDD scenarios (UC-CC-DP-*, UC-CC-MR-*, UC-CC-HR-*, UC-CC-CR-*,
UC-CC-PM-*, UC-CC-GI-*, UC-CC-CP-*).

All generic Given/When/Then steps come from shared_steps and are imported in test_calculator_cli.py.
This file wires the real effective-set-generator CLI into the BDD runner.
"""
import re
import yaml
from pathlib import Path

from pytest_bdd import given, then, parsers

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


def _install_cli_wrapper(workspace: EnvGeneWorkspace) -> None:
    """Point EFFECTIVE_SET_CLI_PATH at the production CLI script already present in the image."""
    # Add mock-reg to workspace registry.yml so the CLI resolves SBOM purl entries.
    registry_file = workspace.config_dir / "registry.yml"
    existing = {}
    if registry_file.exists():
        existing = yaml.safe_load(registry_file.read_text(encoding="utf-8")) or {}
    existing.update(_MOCK_REGISTRY)
    registry_file.write_text(yaml.dump(existing), encoding="utf-8")

    if not hasattr(workspace, "extra_env"):
        workspace.extra_env = {}
    workspace.extra_env["EFFECTIVE_SET_CLI_PATH"] = _PRODUCTION_CLI


@given("the Calculator CLI mock validates rules")
def install_real_cli(workspace: EnvGeneWorkspace) -> None:
    """Install a wrapper that invokes the real effective-set-generator JAR.

    This step is present in the Background of calculator-cli.feature, so every
    scenario automatically uses the real JAR — enabling both success and failure
    assertions against real CLI behaviour.
    """
    _install_cli_wrapper(workspace)


@given("the Calculator CLI uses the real JAR")
def calculator_cli_uses_real_jar(workspace: EnvGeneWorkspace) -> None:
    """Explicit alias for _install_cli_wrapper — used in scenarios that need the real JAR
    but are NOT covered by the Background (e.g. scenarios in other feature files)."""
    _install_cli_wrapper(workspace)


@then(parsers.parse('the effective set deployment parameters contain "{key_value}"'))
def effective_set_deployment_params_contain(workspace: EnvGeneWorkspace, key_value: str) -> None:
    """Assert that any *.yaml under effective-set/deployment/ contains the given string.

    Searches deployment-parameters.yaml and custom-params.yaml (CLI writes CUSTOM_PARAMS
    overrides to custom-params.yaml, not deployment-parameters.yaml).
    """
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
    """Assert that the app output directory has a UUID-named subdirectory (UniqForRun)."""
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
    """Assert that the app output has a version-named subdirectory (UniqForVersion)."""
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
