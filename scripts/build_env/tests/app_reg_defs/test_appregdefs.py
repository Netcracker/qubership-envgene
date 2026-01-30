import os
import shutil
from jinja2.exceptions import TemplateSyntaxError
from pathlib import Path
import pytest
import yaml

from render_config_env import EnvGenerator
from envgenehelper.test_helpers import TestHelpers


class TestAppRegDefRendering:

    @pytest.fixture(scope="class", autouse=True)
    def setup_test_environment(self, request):
        cls = request.cls
        
        test_base = Path(__file__).parents[4] / "test_data" / "test_app_reg_defs"
        cls.test_data_dir = test_base
        cls.cluster_name = "cluster-01"
        cls.env_name = "env-01"
        
        cls.output_dir = Path("/tmp/appregdefs")
        cls.output_dir.mkdir(parents=True, exist_ok=True)
        
        os.environ["CLUSTER_NAME"] = cls.cluster_name
        os.environ["ENVIRONMENT_NAME"] = cls.env_name
        
        yield
        
        os.environ.pop("CLUSTER_NAME", None)
        os.environ.pop("ENVIRONMENT_NAME", None)

    def _get_test_case_dir(self, test_number: str) -> Path:
        return self.test_data_dir / test_number

    def _setup_render_dir(self) -> Path:
        render_dir = self.output_dir / "render" / self.env_name
        if render_dir.exists():
            shutil.rmtree(render_dir)
        render_dir.mkdir(parents=True, exist_ok=True)
        return render_dir

    def _get_render_context(self, test_number: str) -> dict:
        render_dir = self.output_dir / "render" / self.env_name
        
        test_case_dir = self._get_test_case_dir(test_number)
        
        env_dir = test_case_dir / "environments" / self.cluster_name / self.env_name
        templates_dir = test_case_dir / "templates"
        
        return {
            "cluster_name": self.cluster_name,
            "output_dir": str(test_case_dir / "environments"),
            "current_env_dir": str(render_dir),
            "templates_dir": str(templates_dir),
            "cloud_passport_file_path": "",
            "env_instances_dir": str(env_dir)
        }

    def _verify_rendered_files(self, test_number: str, render_dir: Path):
        """Verify rendered files match expected results"""
        test_case_dir = self._get_test_case_dir(test_number)
        expected_appdefs = test_case_dir / "expected" / "appdefs"
        expected_regdefs = test_case_dir / "expected" / "regdefs"
        
        TestHelpers.assert_dirs_content(expected_appdefs, render_dir / "AppDefs")
        TestHelpers.assert_dirs_content(expected_regdefs, render_dir / "RegDefs")
                    
    POSITIVE_CASES = [        
        "TC-001-001",
        "TC-001-002",
        "TC-001-003",
        "TC-001-004",
        "TC-001-005",
        "TC-001-006",
        "TC-001-008",
    ]

    @pytest.mark.parametrize("test_number", POSITIVE_CASES)                
    def test_positive_basic_appdef_rendering(self, test_number):
        self._setup_render_dir()
        
        render_context = EnvGenerator()
        context_vars = self._get_render_context(test_number)
        render_context.process_app_reg_defs(self.env_name, context_vars)
        
        render_dir = Path(context_vars["current_env_dir"])
        self._verify_rendered_files(test_number, render_dir)
        
    NEGATIVE_CASES = {
        "TC-001-010": TemplateSyntaxError,
        "TC-001-011": ValueError,
        "TC-001-012": ValueError,
    }
    
    @pytest.mark.parametrize("test_number,expected_exception", NEGATIVE_CASES.items())
    def test_negative_appregdef_rendering(self, test_number, expected_exception):
        self._setup_render_dir()
        
        render_context = EnvGenerator()
        context_vars = self._get_render_context(test_number)
        with pytest.raises(expected_exception):
            render_context.process_app_reg_defs(self.env_name, context_vars)
    