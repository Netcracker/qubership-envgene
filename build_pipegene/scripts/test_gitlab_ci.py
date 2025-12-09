import pytest
from main import perform_generation
from envgenehelper import getAbsPath, openYaml, dump_as_yaml_format
import os
from dataclasses import dataclass, asdict

@dataclass
class PipelineVars:
    env_names: str = "sample-cloud-name/composite-full"
    env_template_version: str = "new-version:app_def"
    get_passport: str = "true"
    env_builder: str = "true"
    generate_effective_set: str = "true"
    cmdb_import: str = "true"
    env_template_test: str = "false"
    env_inventory_init: str = "false"
    sd_source_type: str = ""
    sd_data: str = ""
    sd_version: str = ""
    env_template_name: str = ""
    env_specific_params: str = ""

def convert_keys_to_uppercase(dictionary):
    return {k.upper(): v for k, v in dictionary}

build_pipeline_test_data = [
    (   # with all jobs
        PipelineVars(env_specific_params='{"params": "value"}'),
        ["trigger", "process_passport", "env_inventory_generation", "env_builder", "generate_effective_set", "git_commit", "cmdb_import" ]
    ),
    (   # new version template test
        PipelineVars(env_template_test="true", env_inventory_init="true"),
        ["trigger", "process_passport", "env_builder", "generate_effective_set", "cmdb_import" ]
    ),
    (   # wihtout passport discovery
        PipelineVars(get_passport="false"),
        ["env_builder", "generate_effective_set", "git_commit", "cmdb_import" ]
    ),
    (   # effective set only
        PipelineVars(get_passport="false", env_builder="false", cmdb_import="false"),
        ["generate_effective_set", "git_commit"]
    ),
    (   # without passport and effective set
        PipelineVars(get_passport="false", generate_effective_set="false"),
        ["env_builder", "git_commit", "cmdb_import" ]
    ),
    (   # with inventory generation and without env_build, passport discovery and effective set
        PipelineVars(get_passport="false", env_builder="false", generate_effective_set="false", sd_data='{"params": "value"}'),
        ["env_inventory_generation", "git_commit", "cmdb_import" ]
    ),
]

@pytest.fixture(autouse=True)
def change_test_dir(request, monkeypatch):
    monkeypatch.chdir(request.fspath.dirname+"/../..")

@pytest.mark.parametrize("pipeline_vars, expected_sequence", build_pipeline_test_data)
def test_build_pipeline(pipeline_vars, expected_sequence):
    os.environ["CI_PROJECT_DIR"] = getAbsPath("samples")
    os.environ["JSON_SCHEMAS_DIR"] = getAbsPath("schemas")

    ci_commit_ref_name = "feature/test-generate"
    os.environ["CI_COMMIT_REF_NAME"] = ci_commit_ref_name
    pipeline_vars = asdict(pipeline_vars, dict_factory=convert_keys_to_uppercase)
    os.environ.update(pipeline_vars)

    perform_generation()

    result = openYaml("generated-config.yml")
    err_msg = f"Stages after generation should be: {dump_as_yaml_format(expected_sequence)}\nenv_template_version: {pipeline_vars['ENV_TEMPLATE_VERSION']}"
    assert result["stages"] == expected_sequence, err_msg
    # os.remove("generated-config.yml")
