from pytest_bdd import scenarios
from tests.shared_steps.sbom_retention_steps import *
from tests.shared_steps.common_steps import *

scenarios('../features/sbom-retention.feature')
