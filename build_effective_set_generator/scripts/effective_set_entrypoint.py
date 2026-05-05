import os
import subprocess
from os import getenv

from envgenehelper import (
    decrypt_all_cred_files_for_env,
    copy_path,
    validate_creds,
    openJson,
    encrypt_all_cred_files_for_env,
    resolve_sd_path,
    logger,
    get_current_env_dir_from_env_vars,
    cleanup_dir,
    get_envgene_config_yaml,
    openYaml,
    ESGenerationContext,
    ES_MAPPING_FILE
)

from handle_effective_set_config import handle_effective_set_config
from sboms_retention_policy import sboms_retention_policy


def effective_set_entrypoint():
    full_env_name = getenv("FULL_ENV_NAME")
    ci_project_dir = getenv("CI_PROJECT_DIR")
    work_dir = os.path.join(ci_project_dir, "environments", full_env_name)

    decrypt_all_cred_files_for_env()

    artifact_app_defs_path = getenv("APP_DEFS_PATH")
    artifact_reg_defs_path = getenv("REG_DEFS_PATH")
    app_reg_defs_job = getenv("APP_REG_DEFS_JOB")

    # local app reg defs
    if artifact_app_defs_path and artifact_reg_defs_path and app_reg_defs_job:
        copy_path(artifact_app_defs_path, os.path.join(work_dir, "AppDefs"))
        copy_path(artifact_reg_defs_path, os.path.join(work_dir, "RegDefs"))

    validate_creds()
    sboms_retention_policy()

    effective_set_dir = get_current_env_dir_from_env_vars() / "effective-set"

    cmdb_cli_cmd_call = [
        "/module/scripts/utils/run_effective_set_cli.sh",
        f"--env-id={full_env_name}",
        "--envs-path=$CI_PROJECT_DIR/environments",
        f"--output={effective_set_dir}",
    ]

    sd_path = resolve_sd_path()
    if sd_path.is_file():
        cmdb_cli_cmd_call.extend([
            "--registries=${CI_PROJECT_DIR}/configuration/registry.yml",
            "--sboms-path=$sboms_path",
            "--sd-path=$sd_path",
        ])
        partial_gen = get_envgene_config_yaml().get("partial_effective_set_generation")
        if partial_gen:
            sd = openYaml(sd_path)
            apps = sd.get("applications", [])

            deploy_postfixes = {
                app.get("deployPostfix")
                for app in apps
                if app.get("deployPostfix")
            }
            # cleanup per namespace
            for ns in deploy_postfixes:
                cleanup_dir(effective_set_dir / ESGenerationContext.CLEANUP.value / ns)

            # cleanup per app
            for app in apps:
                app_name = app.get("version").split(":")[0]
                deploy_postfix = app.get("deployPostfix")
                cleanup_dir(effective_set_dir / ESGenerationContext.RUNTIME.value / deploy_postfix / app_name)
                cleanup_dir(effective_set_dir / ESGenerationContext.DEPLOYMENT.value / deploy_postfix / app_name)

            cleanup_dir(effective_set_dir / ESGenerationContext.TOPOLOGY.value)
            cleanup_dir(effective_set_dir / ESGenerationContext.PIPELINE.value)

        else:
            cleanup_dir(effective_set_dir)
    else:
        # for pipeline and topology context generation in no sd mode
        cleanup_dir(effective_set_dir)

    effective_set_config = getenv("EFFECTIVE_SET_CONFIG")
    if effective_set_config:
        handle_effective_set_config(effective_set_config)
        effective_set_output = openJson("/tmp/effective_set_output.json")
        extra_args = effective_set_output.get("extra_args") or []
        cmdb_cli_cmd_call.extend(extra_args)

    deployment_id = getenv("DEPLOYMENT_SESSION_ID")
    if deployment_id:
        cmdb_cli_cmd_call.append(f"--extra_params=DEPLOYMENT_SESSION_ID={deployment_id}")

    custom_params = getenv("CUSTOM_PARAMS")
    if custom_params:
        logger.info(f"custom_params: {custom_params}")
        cmdb_cli_cmd_call.append(f"--custom-params={custom_params}")

    cleanup_mapping = effective_set_dir / ESGenerationContext.CLEANUP.value / ES_MAPPING_FILE
    runtime_mapping = effective_set_dir / ESGenerationContext.RUNTIME.value / ES_MAPPING_FILE
    deployment_mapping = effective_set_dir / ESGenerationContext.DEPLOYMENT.value / ES_MAPPING_FILE

    # run java effective set cli
    subprocess.run(["sh", cmdb_cli_cmd_call], check=True)

    encrypt_all_cred_files_for_env()
