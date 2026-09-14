from pytest_bdd import scenarios
from cucumber_tests.shared_steps.cloud_passport_steps import *  # noqa: F401,F403
from cucumber_tests.shared_steps.inventory_gen_steps import *  # noqa: F401,F403
from cucumber_tests.shared_steps.common_steps import *  # noqa: F401,F403
from cucumber_tests.shared_steps.unified_pipeline_steps import *  # noqa: F401,F403
from cucumber_tests.step_defs.bgd_sub_flows_steps import *  # noqa: F401,F403 (the pipeline step ... status ... step)

scenarios('../features/cloud-passport.feature')
