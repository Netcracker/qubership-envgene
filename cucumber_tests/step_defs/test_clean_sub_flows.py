import pytest
from pytest_bdd import scenarios
from cucumber_tests.shared_steps.calculator_cli_steps import _PRODUCTION_CLI
from cucumber_tests.step_defs.clean_sub_flows_steps import *  # noqa: F401,F403
from cucumber_tests.shared_steps.common_steps import *  # noqa: F401,F403
from cucumber_tests.shared_steps.unified_pipeline_steps import *  # noqa: F401,F403
from cucumber_tests.shared_steps.sbom_retention_steps import *  # noqa: F401,F403

scenarios('../features/clean-sub-flows.feature')


@pytest.fixture(autouse=True)
def use_production_cli(workspace):
    """Run against the real Effective Set CLI, as test_calculator_cli.py does.

    The .cleaned markers, cleanup/parameters.yaml, and cleanup/mapping.yaml assertions in
    clean-sub-flows.feature check genuine output of
    CliParameterParser.generateCleanedNamespacesOutput; the default mock (exit 0) never
    produces it. CLEAN never passes --deploy-plan-path/--registries/--sboms-path to the CLI
    (dp_path is always None, see effective_set_entrypoint._build_cli_cmd), so this has no
    registry/network dependency - only requires the production CLI to be on PATH, i.e.
    running inside the built envgene image (see devtools/cucumber/Dockerfile).
    """
    if not hasattr(workspace, "extra_env"):
        workspace.extra_env = {}
    workspace.extra_env["EFFECTIVE_SET_CLI_PATH"] = _PRODUCTION_CLI
