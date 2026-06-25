import os
os.environ['ENVGENE_AGE_PRIVATE_KEY'] = 'dummy'
os.environ['PUBLIC_AGE_KEYS'] = 'dummy'
from pytest_bdd import scenarios
from tests.shared_steps.unified_pipeline_steps import *

scenarios('../features/unified_pipeline_success/credential-rotation.feature')

