import shutil
from pathlib import Path
from pytest_bdd import given, parsers
import os

@given('the workspace is initialized for template testing')
def init_template_testing_workspace(workspace):
    project_root = Path(os.environ.get("CI_PROJECT_DIR", Path(__file__).parent.parent.parent.resolve()))
    
    # Copy environments
    src_env = project_root / "test_data" / "test_environments"
    dst_env = Path(workspace.base_dir) / "environments"
    if src_env.exists():
        shutil.copytree(src_env, dst_env, dirs_exist_ok=True)
    
    # Copy templates
    src_tpl = project_root / "test_data" / "test_templates"
    dst_tpl = Path(workspace.base_dir) / "templates"
    if src_tpl.exists():
        shutil.copytree(src_tpl, dst_tpl, dirs_exist_ok=True)

    # Copy configuration
    src_cfg = project_root / "test_data" / "configuration"
    dst_cfg = Path(workspace.base_dir) / "configuration"
    if src_cfg.exists():
        shutil.copytree(src_cfg, dst_cfg, dirs_exist_ok=True)
