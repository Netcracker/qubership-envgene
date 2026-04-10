import os
from dataclasses import dataclass, asdict
from pathlib import Path

import pytest

# validations / gitlab_ci capture CI_PROJECT_DIR at import time; set it before loading main.
_REPO_ROOT = Path(__file__).resolve().parents[2]
os.environ["CI_PROJECT_DIR"] = str(_REPO_ROOT / "test_data" / "pipegene_ci_instance")
os.environ["CI_JOB_NAME"] = 'JOB_NAME_PLACEHOLDER'
os.environ.setdefault("JSON_SCHEMAS_DIR", str(_REPO_ROOT / "schemas"))

from main import perform_generation
from envgenehelper import openYaml, dump_as_yaml_format


@dataclass
class PipelineVars:
    env_names: str = "cluster-01/env-01"
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
    custom_params: str = ""

def convert_keys_to_uppercase(pairs):
    return {k.upper(): v for k, v in pairs}

build_pipeline_test_data = [
    (   # with all jobs
        PipelineVars(env_specific_params='{"params": "value"}'),
        [
            "trigger",
            "process_passport",
            "env_inventory_generation",
            "app_reg_def_render",
            "env_builder",
            "generate_effective_set",
            "git_commit",
        ],
    ),
    (   # new version template test
        PipelineVars(env_template_test="true", env_inventory_init="true"),
        [
            "trigger",
            "process_passport",
            "app_reg_def_render",
            "env_builder",
            "generate_effective_set",
        ],
    ),
    (   # wihtout passport discovery
        PipelineVars(get_passport="false"),
        ["app_reg_def_render", "env_builder", "generate_effective_set", "git_commit"],
    ),
    (   # effective set only
        PipelineVars(get_passport="false", env_builder="false", cmdb_import="false"),
        ["generate_effective_set", "git_commit"]
    ),
    (   # without passport and effective set
        PipelineVars(get_passport="false", generate_effective_set="false"),
        ["app_reg_def_render", "env_builder", "git_commit"],
    ),
    (   # custom_params with env_builder and effective set
        PipelineVars(get_passport="false", generate_effective_set="true", custom_params='{"params": "value"}'),
        ["app_reg_def_render", "env_builder", "generate_effective_set", "git_commit"],
    ),
]

@pytest.fixture(autouse=True)
def change_test_dir(request, monkeypatch):
    monkeypatch.chdir(request.fspath.dirname+"/../..")

@pytest.mark.parametrize("pipeline_vars, expected_sequence", build_pipeline_test_data)
def test_build_pipeline(pipeline_vars, expected_sequence):
    ci_commit_ref_name = "feature/test-generate"
    os.environ["CI_COMMIT_REF_NAME"] = ci_commit_ref_name
    pipeline_vars = asdict(pipeline_vars, dict_factory=convert_keys_to_uppercase)
    os.environ.update(pipeline_vars)

    perform_generation()

    result = openYaml("generated-config.yml")
    err_msg = f"Stages after generation should be: {dump_as_yaml_format(expected_sequence)}\nenv_template_version: {pipeline_vars['ENV_TEMPLATE_VERSION']}"
    assert result["stages"] == expected_sequence, err_msg
    # os.remove("generated-config.yml")
