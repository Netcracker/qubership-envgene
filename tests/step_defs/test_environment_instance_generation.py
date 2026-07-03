import pytest
from pytest_bdd import scenario, scenarios
from tests.shared_steps.unified_pipeline_steps import *

@pytest.mark.xfail(reason="Unified pipeline does not support multiple environments in a single run")
@scenario('../features/unified_pipeline_success/environment-instance-generation.feature', 'UC-EIG-ME-1: Parallel Environment Instance Generation for Multiple Environments')
def test_uceigme1_parallel_environment_instance_generation_for_multiple_environments():
    """UC-EIG-ME-1: Parallel Environment Instance Generation for Multiple Environments."""
    pass

scenarios('../features/unified_pipeline_success/environment-instance-generation.feature')
