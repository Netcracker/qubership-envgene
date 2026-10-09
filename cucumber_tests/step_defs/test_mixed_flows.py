import pytest
from pytest_bdd import scenarios
from cucumber_tests.shared_steps.calculator_cli_steps import _PRODUCTION_CLI
from cucumber_tests.step_defs.clean_sub_flows_steps import *
from cucumber_tests.shared_steps.common_steps import *
from cucumber_tests.shared_steps.unified_pipeline_steps import *

scenarios('../features/mixed-flows.feature')


@pytest.fixture(autouse=True)
def use_production_cli(workspace):
    if not hasattr(workspace, "extra_env"):
        workspace.extra_env = {}
    workspace.extra_env["EFFECTIVE_SET_CLI_PATH"] = _PRODUCTION_CLI
