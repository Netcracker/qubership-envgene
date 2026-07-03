import os
from pytest_bdd import scenarios, given, when, then
import pytest

scenarios('../features/gsf_maintenance/gsf-repository-maintenance.feature')

# -- GSF Template Tests --

@given('a new Template Repository exists without EnvGene-specific files')
def new_template_repo_exists():
    pass

@given('a Template Repository exists with a previous EnvGene template package version')
def template_repo_previous_version():
    pass

@given('a legacy Template Repository exists with a previous EnvGene template package version before 2.85.0')
def template_repo_legacy_version():
    pass

@given('a Template Repository exists with a later EnvGene template package version')
def template_repo_later_version():
    pass

@when('GSF install is run with a template package image and initialization parameters')
def run_gsf_install_template_init():
    pytest.xfail("GSF install requires external git-system-follower tooling not available in test env")

@when('GSF install is run with a target template package image')
def run_gsf_install_template_target():
    pytest.xfail("GSF install requires external git-system-follower tooling not available in test env")

@when('GSF install is run with a target template package image on the legacy repository')
def run_gsf_install_template_legacy():
    pytest.xfail("GSF install requires external git-system-follower tooling not available in test env")

@when('GSF install is run with an older template package image')
def run_gsf_install_template_older():
    pytest.xfail("GSF install requires external git-system-follower tooling not available in test env")

@then('the Template Repository is initialized with required files')
def verify_template_initialized():
    pass

@then('group_id and artifact_id are set in build_vars.sh')
def verify_group_id_artifact_id():
    pass

@then('the repository matches the reference structure')
def verify_reference_structure():
    pass

@then('the Template Repository is upgraded to the target version')
def verify_template_upgraded():
    pass

@then('restricted files are preserved according to policy')
def verify_restricted_files_preserved():
    pass

@then('the legacy repository is migrated to the current package format')
def verify_legacy_migrated():
    pass

@then('legacy formats are normalized')
def verify_legacy_normalized():
    pass

@then('the Template Repository is switched to the older version')
def verify_template_downgraded():
    pass

@then('files from the later version are removed')
def verify_later_files_removed():
    pass

# -- GSF Instance Tests --

@given('a new Instance Repository exists without EnvGene-specific files')
def new_instance_repo_exists():
    pass

@given('an Instance Repository exists with a previous EnvGene instance package version')
def instance_repo_previous_version():
    pass

@given('an Instance Repository exists with a later EnvGene instance package version')
def instance_repo_later_version():
    pass

@when('GSF install is run with an instance package image')
def run_gsf_install_instance_init():
    pytest.xfail("GSF install requires external git-system-follower tooling not available in test env")

@when('GSF install is run with a target instance package image')
def run_gsf_install_instance_target():
    pytest.xfail("GSF install requires external git-system-follower tooling not available in test env")

@when('GSF install is run with an older instance package image')
def run_gsf_install_instance_older():
    pytest.xfail("GSF install requires external git-system-follower tooling not available in test env")

@then('the Instance Repository is initialized with required files')
def verify_instance_initialized():
    pass

@then('the repository matches the reference instance structure')
def verify_instance_reference_structure():
    pass

@then('the Instance Repository is upgraded to the target version')
def verify_instance_upgraded():
    pass

@then('pipeline_vars are preserved according to policy')
def verify_pipeline_vars_preserved():
    pass

@then('the Instance Repository is switched to the older version')
def verify_instance_downgraded():
    pass

@then('files from the later instance version are removed')
def verify_later_instance_files_removed():
    pass
