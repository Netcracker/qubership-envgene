from pytest_bdd import scenarios
from tests.shared_steps.bg_deployment_steps import *
from tests.shared_steps.common_steps import *

scenarios('../features/blue-green-deployment.feature')
