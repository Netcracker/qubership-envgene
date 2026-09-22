"""Feature-specific step definitions for deploy-sub-flows.feature."""
from pytest_bdd import given, parsers, then
from cucumber_tests.framework.workspace import EnvGeneWorkspace
import yaml


@given(parsers.parse(
    'the pipeline parameter "SD_DATA" is set to a Solution Descriptor with '
    'deployPostfix "{deploy_postfix}" for "{app_version}"'))
def given_sd_data_as_solution_descriptor(
    workspace: EnvGeneWorkspace, deploy_postfix: str, app_version: str
):
    # Deliberately hardcodes SD_DATA (not a generic {param} placeholder) so this step's Gherkin
    # text cannot overlap with bgd_sub_flows_steps.given_application_versions_as_solution_descriptor,
    # which matches the same "... is set to a Solution Descriptor ..." phrasing for
    # APPLICATION_VERSIONS. process_sd.py's handle_sd() accepts inline SD content via SD_DATA,
    # parsed with load_json_or_yaml() - unlike APPLICATION_VERSIONS, which dpg resolves as a file
    # path (utils.is_file_path), so SD_DATA is written as inline YAML, not a file.
    sd_content = yaml.dump({
        "version": 2.2,
        "type": "solutionDeploy",
        "applications": [{"version": app_version, "deployPostfix": deploy_postfix}],
    })
    if not hasattr(workspace, "extra_env"):
        workspace.extra_env = {}
    workspace.extra_env["SD_DATA"] = sd_content


@then(parsers.parse('the effective set folder "{folder}" contains file "{filename}"'))
def then_effective_set_folder_contains_file(
    workspace: EnvGeneWorkspace, folder: str, filename: str
):
    file_path = (
        workspace.builder.get_env_dir(workspace.cluster_name, workspace.env_name)
        / "effective-set"
        / folder
        / filename
    )
    workspace.assert_file_exists(file_path)


@then(parsers.parse('the effective set cleanup mapping contains namespace "{namespace}"'))
def then_effective_set_cleanup_mapping_contains_namespace(
    workspace: EnvGeneWorkspace, namespace: str
):
    mapping_path = (
        workspace.builder.get_env_dir(workspace.cluster_name, workspace.env_name)
        / "effective-set"
        / "cleanup"
        / "mapping.yaml"
    )
    assert mapping_path.exists(), (
        f"Expected cleanup mapping at {mapping_path}.\n"
        f"STDOUT:\n{workspace.stdout}\nSTDERR:\n{workspace.stderr}"
    )
    mapping = yaml.safe_load(mapping_path.read_text(encoding="utf-8")) or {}
    assert namespace in mapping, (
        f"Expected namespace '{namespace}' as a key in cleanup/mapping.yaml, "
        f"got keys: {list(mapping)}.\n"
        f"STDOUT:\n{workspace.stdout}\nSTDERR:\n{workspace.stderr}"
    )
