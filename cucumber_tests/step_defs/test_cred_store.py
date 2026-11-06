import yaml
import pytest
from pytest_bdd import scenarios
from cucumber_tests.shared_steps.calculator_cli_steps import _PRODUCTION_CLI, _MOCK_REGISTRY
from cucumber_tests.shared_steps.calculator_cli_steps import *
from cucumber_tests.shared_steps.common_steps import *
from cucumber_tests.shared_steps.unified_pipeline_steps import *
from cucumber_tests.shared_steps.credential_rotation_steps import *
from cucumber_tests.shared_steps.cred_file_steps import *
from cucumber_tests.step_defs.external_creds_steps import *
from cucumber_tests.step_defs.bgd_sub_flows_steps import *

scenarios('../features/cred-store.feature')


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
