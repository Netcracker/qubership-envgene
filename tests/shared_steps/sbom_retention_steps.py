import pytest
from pytest_bdd import scenarios, given, when, then, parsers


@given('an Instance Repository exists with an "/sboms/" directory')
def instance_repo_with_sboms_dir(workspace):
    pass

@given(parsers.parse('SBOM files exist in "{path}"'))
def sbom_files_exist(workspace, path):
    app_name = path.strip('/').split('/')[-1]
    workspace.builder.create_mock_sboms(app_name, 5)

@given(parsers.parse('SBOM retention is disabled in "{path}"'))
def sbom_retention_disabled(workspace, path):
    workspace.config_data["sbom_retention"] = {"enabled": False}

@when('the Instance pipeline is started with GENERATE_EFFECTIVE_SET set to true')
def start_instance_pipeline(workspace):
    workspace.run_pipeline(extra_env={"GENERATE_EFFECTIVE_SET": "true"})


@then('no SBOM files are deleted')
def no_sbom_files_deleted(workspace):
    assert "Removing file:" not in workspace.stdout
    assert "Removing legacy SBOM file:" not in workspace.stdout

@given('SBOM files exist for multiple applications with the following counts:')
def sbom_files_multiple_apps_counts(workspace, datatable):
    for row in datatable[1:]:
        app = row[0]
        count = int(row[1])
        workspace.builder.create_mock_sboms(app, count)

@given(parsers.parse('SBOM retention is enabled with "keep_versions_per_app" set to {count:d}'))
def sbom_retention_enabled(workspace, count):
    workspace.config_data["sbom_retention"] = {
        "enabled": True,
        "keep_versions_per_app": count
    }

@given(parsers.parse('the total size of "/sboms/" is {size:d} MB, which is below the 1200 MB limit'))
def sbom_size_below_limit(workspace, size):
    app_dir = list(workspace.sboms_dir.iterdir())[0]
    workspace.builder.modify_first_sbom_size(app_dir.name, size)

@then(parsers.parse('{count:d} SBOM files are deleted in total'))
def sbom_files_deleted_total(workspace, count):
    output = workspace.stdout + "\n" + workspace.stderr
    deleted_count = sum(1 for line in output.splitlines() if "Removing legacy SBOM file:" in line or "Removing file:" in line)
    assert deleted_count == count, f"Expected {count} deleted files, but got {deleted_count}"

@then('the following SBOM files remain per application:')
def sbom_files_remain(workspace, datatable):
    for row in datatable[1:]:
        app = row[0]
        expected_kept = int(row[1])
        app_dir = workspace.sboms_dir / app
        actual_kept = len(list(app_dir.glob("*.sbom.json")))
        assert actual_kept == expected_kept, f"Expected {expected_kept} files for {app}, but found {actual_kept}"

@given(parsers.parse('{count:d} SBOM files exist for the application "{app}" under "{path}"'))
def sbom_files_exist_app(workspace, count, app, path):
    workspace.builder.create_mock_sboms(app, count)

@then(parsers.parse('the {count:d} most recently modified files are kept for "{app}"'))
def most_recent_kept(workspace, count, app):
    app_dir = workspace.sboms_dir / app
    actual_kept = len(list(app_dir.glob("*.sbom.json")))
    assert actual_kept == count, f"Expected {count} files for {app}, but found {actual_kept}"

@given('SBOM files exist for several applications with each containing 10 or fewer files')
def sbom_files_several_apps_10_or_fewer(workspace):
    workspace.builder.create_mock_sboms("app1", 8)
    workspace.builder.create_mock_sboms("app2", 5)
    workspace.builder.create_mock_sboms("app3", 10)

@given(parsers.parse('the total size of "/sboms/" is {size:d} MB, which is above the 1200 MB limit'))
def sbom_size_above_limit(workspace, size):
    workspace.builder.modify_first_sbom_size("app1", size)

@then('only the single most recent SBOM file remains under each application directory')
def single_most_recent_remains(workspace):
    for app_dir in workspace.sboms_dir.iterdir():
        if app_dir.is_dir():
            actual_kept = len(list(app_dir.glob("*.sbom.json")))
            assert actual_kept == 1, f"Expected exactly 1 file for {app_dir.name}, but found {actual_kept}"
