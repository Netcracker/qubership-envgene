from pytest_bdd import scenarios
from tests.shared_steps.unified_pipeline_steps import *

# Load all scenarios from the feature file
scenarios('../features/unified_pipeline_success/app_reg_defs_template_rendering.feature')
