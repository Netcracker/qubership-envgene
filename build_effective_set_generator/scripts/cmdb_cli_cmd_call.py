import json
import subprocess
from os import getenv
from pathlib import Path

from envgenehelper import logger, getenv_with_error

from handle_effective_set_config import handle_effective_set_config


def cmdb_cli_cmd_call():
    sd_version = getenv("SD_VERSION")
    sd_data = getenv("SD_DATA")
    deployment_id = getenv("DEPLOYMENT_SESSION_ID")
    effective_set_config = getenv("EFFECTIVE_SET_CONFIG")
    custom_params = getenv("CUSTOM_PARAMS")
    full_env_name = getenv_with_error("FULL_ENV_NAME")
    base_dir = getenv_with_error('CI_PROJECT_DIR')

    cmdb_cli_cmd = [
        "/module/scripts/utils/entrypoint.sh",
        f"--env-id={full_env_name}",
        f"--envs-path={base_dir}/environments",
        f"--output={base_dir}/environments/{full_env_name}/effective-set"
    ]

    effective_set_config_dict = {}
    if effective_set_config:
        effective_set_config_dict = json.loads(effective_set_config)

    sd_path = Path(f'{base_dir}/environments/{full_env_name}/Inventory/solution-descriptor/sd.yaml')
    full_sd_exists = sd_path.is_file()
    sd_data = bool(sd_data) or bool(sd_version)

    effective_set_version = effective_set_config_dict.get("version") or "v2.0"
    if not (full_sd_exists and sd_data) and effective_set_version.lower() == "v1.0":
        raise ValueError("Feature generation effective set for pipeline and topology context is not supported for v1.0")

    if full_sd_exists or sd_data:
        cmdb_cli_cmd.extend([
            f"--registries={base_dir}/configuration/registry.yml",
            f"--sboms-path={base_dir}/sboms",
            f"--sd-path={sd_path}",
        ])

    logger.info(f'Prepare generate_effective_set job for {full_env_name}.')
    if effective_set_config:
        extra_args = handle_effective_set_config(effective_set_config)
        logger.info(f"Resolved Extra args: {extra_args}")
        extra_args = extra_args.get("extra_args", [])

        if extra_args:
            cmdb_cli_cmd.extend(extra_args)

    if deployment_id:
        cmdb_cli_cmd.extend([f"--extra_params=DEPLOYMENT_SESSION_ID={deployment_id}"])

    if custom_params:
        logger.info(f"custom_params : {custom_params}")
        cmdb_cli_cmd.extend([f"--custom-params={custom_params}"])

    subprocess.run(cmdb_cli_cmd, check=True)


if __name__ == "__main__":
    cmdb_cli_cmd_call()
