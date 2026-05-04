import json
import subprocess
from os import getenv
from pathlib import Path

from envgenehelper import decrypt_all_cred_files_for_env, copy_path, validate_creds, openJson, \
    encrypt_all_cred_files_for_env, resolve_sd_path, logger

from handle_effective_set_config import handle_effective_set_config
from sboms_retention_policy import sboms_retention_policy


def effective_set_entrypoint():
    full_env_name = getenv("FULL_ENV_NAME")
    ci_project_dir = getenv("CI_PROJECT_DIR")
    work_dir = ci_project_dir / "environments" / full_env_name

    decrypt_all_cred_files_for_env()

    artifact_app_defs_path = getenv("APP_DEFS_PATH")
    artifact_reg_defs_path = getenv("REG_DEFS_PATH")
    app_reg_defs_job = getenv("APP_REG_DEFS_JOB")
    is_local_app_def = artifact_app_defs_path and artifact_reg_defs_path and app_reg_defs_job
    if is_local_app_def:
        app_defs_path = work_dir / "AppDefs"
        reg_defs_path = work_dir / "RegDefs"
        copy_path(artifact_app_defs_path, app_defs_path)
        copy_path(artifact_reg_defs_path, reg_defs_path)

    validate_creds()
    sboms_retention_policy()

    cmdb_cli_cmd_call = [
        f"/module/scripts/utils/run_effective_set_cli.sh --env-id={full_env_name}",
        "--envs-path=$CI_PROJECT_DIR/environments",
        f"--output=$CI_PROJECT_DIR/environments/{full_env_name}/effective-set"
    ]
    sd_path = resolve_sd_path()
    if sd_path.is_file():
        cmdb_cli_cmd_call.extend([
            "--registries=${CI_PROJECT_DIR}/configuration/registry.yml",
            "--sboms-path=$sboms_path",
            "--sd-path=$sd_path",
        ])

    effective_set_config = getenv("EFFECTIVE_SET_CONFIG")
    if effective_set_config:
        effective_set_config_dict = json.loads(effective_set_config)
        # validate_topology_context_mode(effective_set_config_dict, full_env_name)

    if effective_set_config:
        handle_effective_set_config(effective_set_config)
        effective_set_output = openJson('/tmp/effective_set_output.json')
        extra_args = " ".join(effective_set_output.get("extra_args") or [])
        cmdb_cli_cmd_call.extend([extra_args])

    deployment_id = getenv("DEPLOYMENT_SESSION_ID")
    if deployment_id:
        cmdb_cli_cmd_call.append(f"--extra_params=DEPLOYMENT_SESSION_ID={deployment_id}")

    custom_params = getenv("CUSTOM_PARAMS")
    if custom_params:
        logger.info(f"custom_params : {custom_params}")
        cmdb_cli_cmd_call.append(f"--custom-params='{custom_params}'")

    # run java effective set cli
    subprocess.run(["sh", cmdb_cli_cmd_call], check=True)

    encrypt_all_cred_files_for_env()


def validate_topology_context_mode(effective_set_config_dict, full_env_name):
    effective_set_version = effective_set_config_dict.get("version") or "v2.0"
    sd = bool(getenv("SD_DATA")) or bool(getenv("SD_VERSION"))
    full_sd_path = Path(
        f'{getenv('CI_PROJECT_DIR')}/environments/{full_env_name}/Inventory/solution-descriptor/sd.yaml')
    # effective set generation in version 1.0 does not support no SBOMs mode
    if not (full_sd_path.exists() and sd) and effective_set_version.lower() == "v1.0":
        raise ValueError("Feature generation effective set for pipeline and topology context is not supported for v1.0")
