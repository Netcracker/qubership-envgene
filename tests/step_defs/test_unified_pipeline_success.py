import pytest
from pytest_bdd import scenarios, scenario
from tests.shared_steps.unified_pipeline_steps import *

# Explicitly declare xfail for ME-1 before loading all others
@pytest.mark.xfail(reason="Currently the orchestrator does not support multiple environments")
@scenario('../features/unified_pipeline_success/environment-instance-generation.feature', 'UC-EIG-ME-1: Parallel Environment Instance Generation for Multiple Environments')
def test_uceigme1_parallel_environment_instance_generation_for_multiple_environments():
    pass

# Load all scenarios from the unified_pipeline_success directory
scenarios('../features/unified_pipeline_success/')