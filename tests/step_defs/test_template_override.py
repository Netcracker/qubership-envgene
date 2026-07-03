from pytest_bdd import scenarios
from tests.shared_steps.unified_pipeline_steps import *
from tests.shared_steps.template_macros_steps import *

scenarios('../features/template_override/template-override.feature')
