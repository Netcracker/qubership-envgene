import yaml
import pytest
from pytest_bdd import scenarios
from cucumber_tests.shared_steps.calculator_cli_steps import _PRODUCTION_CLI, _MOCK_REGISTRY
from cucumber_tests.shared_steps.calculator_cli_steps import *    # noqa: F401,F403
from cucumber_tests.shared_steps.common_steps import *             # noqa: F401,F403
from cucumber_tests.shared_steps.unified_pipeline_steps import *  # noqa: F401,F403

scenarios('../features/calculator-cli.feature')


@pytest.fixture(autouse=True)
def use_production_cli(workspace):
    registry_file = workspace.config_dir / "registry.yml"
    existing = {}
    if registry_file.exists():
        existing = yaml.safe_load(registry_file.read_text(encoding="utf-8")) or {}
    existing.update(_MOCK_REGISTRY)
    registry_file.write_text(yaml.dump(existing), encoding="utf-8")

    if not hasattr(workspace, "extra_env"):
        workspace.extra_env = {}
    workspace.extra_env["EFFECTIVE_SET_CLI_PATH"] = _PRODUCTION_CLI
