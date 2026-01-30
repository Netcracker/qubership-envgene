import os
from pathlib import Path


class BaseTest:
    base_dir = Path(__file__).resolve().parents[3]
    test_data_dir = base_dir / "test_data"
    ci_project_dir = test_data_dir
    os.environ['CI_PROJECT_DIR'] = str(test_data_dir)
    os.environ['JSON_SCHEMAS_DIR'] = str(base_dir / "schemas")

    def set_project_dir(self, *subdirs) -> Path:
        self.ci_project_dir = self.ci_project_dir.joinpath(*subdirs)
        os.environ['CI_PROJECT_DIR'] = str(self.ci_project_dir)
        return self.ci_project_dir
