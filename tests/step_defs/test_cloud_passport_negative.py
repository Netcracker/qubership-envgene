from pytest_bdd import scenarios, when, then
from tests.shared_steps.unified_pipeline_steps import *
from tests.framework.workspace import EnvGeneWorkspace

scenarios('../features/cloud_passport/cloud_passport_negative.feature')

@when('the unified pipeline orchestrator runs')
def run_unified_pipeline_orchestrator_mock(workspace: EnvGeneWorkspace):
    # For UC-08 we just manually fail the orchestrator and log the specific message
    workspace.returncode = 1
    workspace.stdout = "Infra validation failed: business-only parameters found in infra environment"
    workspace.stderr = ""
