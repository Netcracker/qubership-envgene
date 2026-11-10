from pytest_bdd import scenarios
from cucumber_tests.shared_steps.common_steps import *  # noqa: F401,F403
from cucumber_tests.shared_steps.unified_pipeline_steps import *  # noqa: F401,F403
from cucumber_tests.shared_steps.inventory_gen_steps import *  # noqa: F401,F403
from cucumber_tests.shared_steps.envgene_null_value_steps import *  # noqa: F401,F403

scenarios('../features/envgene-null-value.feature')
