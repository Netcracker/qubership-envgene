import os
from pathlib import Path


class BaseTest:
    base_dir = Path(__file__).resolve().parents[3]
    test_data_dir = base_dir / "test_data"
    ci_project_dir = test_data_dir
    expected_dir = test_data_dir
    os.environ['CI_PROJECT_DIR'] = str(test_data_dir)
    os.environ['JSON_SCHEMAS_DIR'] = str(base_dir / "schemas")

    def set_ci_project_dir(self, *subdirs) -> Path:
        self.ci_project_dir = self.ci_project_dir.joinpath(*subdirs)
        os.environ['CI_PROJECT_DIR'] = str(self.ci_project_dir)
        return self.ci_project_dir

    def teardown_method(self):
        for var in ("ENVIRONMENT_NAME", "CLUSTER_NAME", "FULL_ENV_NAME",
                    "ENV_INVENTORY_CONTENT", "ENV_TEMPLATE_VERSION"):
            os.environ.pop(var, None)
