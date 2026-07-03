import pytest
from pytest_bdd import scenarios
from tests.shared_steps.unified_pipeline_steps import *
from tests.shared_steps.common_steps import *

scenarios('../features/effective_set_generation/effective-set-deployment.feature')
