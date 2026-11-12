import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

from envgene_shared.utils.yaml_utils import get_schema, validate_yaml_by_scheme_or_fail


ROOT = Path(__file__).resolve().parents[2]
GSF_TEMPLATE = ROOT / "gsf_packages/envgene_instance_project/git-system-follower-package/scripts/templates/default/{{ cookiecutter.gsf_repository_name }}"


@pytest.fixture
def shell():
    executable = shutil.which("sh")
    if not executable:
        git = shutil.which("git")
        candidate = Path(git).resolve().parents[1] / "bin/bash.exe" if git else None
        if candidate and candidate.is_file():
            executable = str(candidate)
    if not executable:
        pytest.skip("A POSIX shell is required to test schema packaging")
    return executable


def test_gsf_action_stages_required_schemas_and_retains_cleanup_history(tmp_path, shell):
    source = tmp_path / "schemas"
    source.mkdir()
    for name in ("config.schema.json", "credential.schema.json"):
        shutil.copyfile(ROOT / "schemas" / name, source / name)
    action = yaml.safe_load((ROOT / ".github/actions/build-gsf-instance/action.yml").read_text())
    step = next(step for step in action["runs"]["steps"] if step["name"] == "Copy schemas to git_hooks")

    subprocess.run([shell, "-c", step["run"]], cwd=tmp_path, check=True, capture_output=True, text=True)

    staged = tmp_path / GSF_TEMPLATE.relative_to(ROOT) / "git_hooks/schemas"
    assert {path.name for path in staged.iterdir()} == {"config.schema.json", "credential.schema.json"}
    for name in ("config.schema.json", "credential.schema.json"):
        assert get_schema(name, staged) == get_schema(name, ROOT / "schemas")
    validate_yaml_by_scheme_or_fail(
        input_yaml_content={"token": {"type": "secret", "data": {"secret": "value"}}},
        schema_name="credential.schema.json", schemas_dir=staged,
    )
    history = set((GSF_TEMPLATE / "history.log").read_text().splitlines())
    assert {
        "git_hooks/config.schema.json",
        "git_hooks/envgene_shared/schemas/config.schema.json",
        "git_hooks/envgene_shared/schemas/credential.schema.json",
        "git_hooks/schemas/config.schema.json",
        "git_hooks/schemas/credential.schema.json",
    } <= history
