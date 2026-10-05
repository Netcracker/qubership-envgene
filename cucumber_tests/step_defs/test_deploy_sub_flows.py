import pytest
from pytest_bdd import scenarios
from cucumber_tests.shared_steps.calculator_cli_steps import _PRODUCTION_CLI
from cucumber_tests.step_defs.deploy_sub_flows_steps import *  # noqa: F401,F403
from cucumber_tests.step_defs.bgd_sub_flows_steps import *  # noqa: F401,F403
from cucumber_tests.shared_steps.common_steps import *  # noqa: F401,F403
from cucumber_tests.shared_steps.unified_pipeline_steps import *  # noqa: F401,F403

scenarios('../features/deploy-sub-flows.feature')


@pytest.fixture(autouse=True)
def use_production_cli_for_legacy_flow(workspace, request):
    if "legacy" not in request.node.name:
        return

    cli_wrapper = workspace.base_dir / "run_cleanup_effective_set_cli.sh"
    cli_wrapper.write_text(
        f"""#!/bin/sh
filtered_args=""
for arg in "$@"; do
    case "$arg" in
        --deploy-plan-path=*|--registries=*|--sboms-path=*) ;;
        *) filtered_args="$filtered_args \"$arg\"" ;;
    esac
done
exec {_PRODUCTION_CLI} $filtered_args
""",
        encoding="utf-8",
    )
    cli_wrapper.chmod(0o755)

    if not hasattr(workspace, "extra_env"):
        workspace.extra_env = {}
    workspace.extra_env["EFFECTIVE_SET_CLI_PATH"] = str(cli_wrapper)
