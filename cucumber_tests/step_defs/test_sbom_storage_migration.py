from pytest_bdd import scenarios
from cucumber_tests.shared_steps.common_steps import *
from cucumber_tests.shared_steps.unified_pipeline_steps import *
from cucumber_tests.shared_steps.sbom_migration_steps import *

scenarios('../features/sbom-storage-migration.feature')
