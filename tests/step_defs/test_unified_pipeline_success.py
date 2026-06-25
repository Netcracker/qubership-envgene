from pytest_bdd import scenarios
from tests.shared_steps.unified_pipeline_steps import *

# Load all scenarios from the unified_pipeline_success directory
scenarios('../features/unified_pipeline_success/')
