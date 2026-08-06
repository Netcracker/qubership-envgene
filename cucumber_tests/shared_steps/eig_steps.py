"""Step definitions for Environment Instance Generation scenarios."""
from pathlib import Path
from pytest_bdd import then, parsers

from cucumber_tests.framework.workspace import EnvGeneWorkspace


@then(parsers.parse('the namespace folder "{folder_name}" exists in the environment instance'))
def namespace_folder_exists(workspace: EnvGeneWorkspace, folder_name: str) -> None:
    ns_dir = (
        workspace.base_dir
        / "environments"
        / workspace.cluster_name
        / workspace.env_name
        / "Namespaces"
        / folder_name
    )
    assert ns_dir.exists(), (
        f"Namespace folder {folder_name!r} not found at {ns_dir}.\n"
        f"STDOUT: {workspace.stdout}\nSTDERR: {workspace.stderr}"
    )


@then(parsers.parse('the namespace folder "{folder_name}" exists in environment "{cluster}/{env}"'))
def namespace_folder_exists_in_env(
    workspace: EnvGeneWorkspace, folder_name: str, cluster: str, env: str
) -> None:
    ns_dir = (
        workspace.base_dir
        / "environments"
        / cluster
        / env
        / "Namespaces"
        / folder_name
    )
    assert ns_dir.exists(), (
        f"Namespace folder {folder_name!r} not found in {cluster}/{env} at {ns_dir}.\n"
        f"STDOUT: {workspace.stdout}\nSTDERR: {workspace.stderr}"
    )
