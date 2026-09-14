"""Step definitions for Cloud Passport association BDD scenarios (UC-01..UC-09), per
docs/use-cases/cloud-passport.md. Cloud Passport association/merge (process_cloud_passport in
scripts/cloud_passport/cloud_passport.py) runs unconditionally as part of env_build's cloud
processing - it never needs the real Effective Set CLI, only ENV_BUILDER=true to trigger
env_build itself, so these scenarios run entirely against the local mock.
"""
import re

from pytest_bdd import then, parsers

from cucumber_tests.framework.workspace import EnvGeneWorkspace


def _cloud_yaml_path(workspace: EnvGeneWorkspace):
    env_dir = workspace.builder.get_env_dir(workspace.cluster_name, workspace.env_name)
    return env_dir / "cloud.yml"


def _cloud_yaml_text(workspace: EnvGeneWorkspace) -> str:
    path = _cloud_yaml_path(workspace)
    workspace.assert_file_exists(path)
    return path.read_text(encoding="utf-8")


@then(parsers.parse('the cloud.yml contains "{key_value}"'))
def cloud_yaml_contains(workspace: EnvGeneWorkspace, key_value: str) -> None:
    # Quote-insensitive: ruyaml wraps most scalar string values in double quotes when it
    # writes cloud.yml, but not consistently for every value shape, so strip quotes from both
    # sides before comparing rather than requiring the scenario text to guess the exact quoting.
    content = _cloud_yaml_text(workspace)
    assert key_value.replace('"', '') in content.replace('"', ''), (
        f"'{key_value}' not found in cloud.yml.\nContent:\n{content}"
    )


@then(parsers.parse('the cloud.yml does not contain "{key}"'))
def cloud_yaml_does_not_contain(workspace: EnvGeneWorkspace, key: str) -> None:
    content = _cloud_yaml_text(workspace)
    assert key not in content, f"'{key}' unexpectedly found in cloud.yml.\nContent:\n{content}"


@then(parsers.parse('the cloud.yml parameter "{key}" has traceability comment "{comment}"'))
def cloud_yaml_param_has_traceability_comment(workspace: EnvGeneWorkspace, key: str, comment: str) -> None:
    content = _cloud_yaml_text(workspace)
    pattern = re.compile(rf'^\s*{re.escape(key)}\s*:.*$', re.MULTILINE)
    match = pattern.search(content)
    assert match, f"Key '{key}' not found in cloud.yml.\nContent:\n{content}"
    line = match.group(0)
    assert "#" in line and comment in line.split("#", 1)[1], (
        f"Expected traceability comment '{comment}' on the '{key}' line, got: {line!r}"
    )
