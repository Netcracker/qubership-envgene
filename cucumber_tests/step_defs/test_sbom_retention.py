from pytest_bdd import scenarios
from cucumber_tests.shared_steps.sbom_retention_steps import *  # noqa: F401,F403
from cucumber_tests.shared_steps.common_steps import *  # noqa: F401,F403
from cucumber_tests.shared_steps.unified_pipeline_steps import *  # noqa: F401,F403

scenarios('../features/sbom-retention.feature')
