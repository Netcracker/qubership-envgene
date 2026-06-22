import os
from pathlib import Path

from envgenehelper import business_helper


class BaseTest:
    base_dir = Path(__file__).resolve().parents[2]
    schemas_dir = business_helper.get_schema_dir(2)
    test_data_dir = base_dir / "test_data"
    output_dir = base_dir / "tmp"

    ci_project_dir = test_data_dir
    os.environ['CI_PROJECT_DIR'] = str(test_data_dir)

    def set_ci_project_dir(self, *subdirs) -> Path:
        self.ci_project_dir = self.ci_project_dir.joinpath(*subdirs)
        os.environ['CI_PROJECT_DIR'] = str(self.ci_project_dir)
        return self.ci_project_dir
