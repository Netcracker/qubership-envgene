import importlib.util
import sys
import types
from pathlib import Path

import pytest
import yaml

from envgene_shared.utils.yaml_utils import validate_yaml_by_scheme_or_fail

ROOT = Path(__file__).resolve().parents[2]
INIT = ROOT / "gsf_packages/envgene_instance_project/git-system-follower-package/scripts/init.py"


@pytest.fixture
def init_module(monkeypatch):
    for name in ("git_system_follower", "git_system_follower.develop", "git_system_follower.develop.api",
                 "git_system_follower.develop.api.types", "git_system_follower.develop.api.templates",
                 "git_system_follower.develop.api.cicd_variables"):
        monkeypatch.setitem(sys.modules, name, types.ModuleType(name))
    api = sys.modules
    api["git_system_follower.develop.api.types"].Parameters = object
    api["git_system_follower.develop.api.templates"].create_template = None
    api["git_system_follower.develop.api.templates"].get_template_names = None
    api["git_system_follower.develop.api.cicd_variables"].CICDVariable = None
    api["git_system_follower.develop.api.cicd_variables"].create_variable = None
    spec = importlib.util.spec_from_file_location("gsf_instance_init", INIT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("line", [
    "crypt_backend: Fernet\n",
    "crypt_backend: 'Fernet'\n",
    'crypt_backend: "Fernet"  # legacy\r\n',
    "crypt_backend: Fernet",
])
def test_drop_fernet_backend_makes_config_valid(init_module, line):
    content = f"crypt: false\nsbom_retention:\n  enabled: false\n{line}".encode()

    migrated = init_module._drop_fernet_backend(content)

    config = yaml.safe_load(migrated)
    assert "crypt_backend" not in config
    assert config["sbom_retention"] == {"enabled": False}
    validate_yaml_by_scheme_or_fail(input_yaml_content=config, schema_name="config.schema.json",
                                    schemas_dir=ROOT / "schemas")


@pytest.mark.parametrize("content", [
    b"crypt: true\ncrypt_backend: SOPS\n",
    b"crypt: false\n# crypt_backend: Fernet\n",
    b"crypt: false\n",
])
def test_drop_fernet_backend_keeps_other_configs(init_module, content):
    assert init_module._drop_fernet_backend(content) == content
