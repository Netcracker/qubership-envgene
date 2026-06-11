import subprocess
from os import getenv

from envgenehelper.business_helper import get_current_env_dir_from_env_vars
from envgenehelper.effective_set_helper import GenerationMode, PartialMergeMode, \
    resolve_partial_merge_mode, ES_MAPPING_FILE, ESGenerationContext, ES_DIR_NAME, get_es_generation_mode
from envgenehelper.file_helper import delete_dir, deleteFileIfExists, delete_dir_if_exists
from envgenehelper.logger import logger
from envgenehelper.sd_helper import get_sd_dir, DELTA_SD_FILE_NAME, SD_FILE_NAME
from envgenehelper.yaml_helper import writeYamlToFile, openYaml

from effective_set.handle_effective_set_config import handle_effective_set_config  # noqa: E402


def effective_set_entrypoint():
    full_env_name = getenv("FULL_ENV_NAME")
    effective_set_dir = get_current_env_dir_from_env_vars() / ES_DIR_NAME
    sd_path = get_sd_dir().joinpath(SD_FILE_NAME)
    delta_sd_path = get_sd_dir().joinpath(DELTA_SD_FILE_NAME)

    if get_es_generation_mode() == GenerationMode.PARTIAL:
        if resolve_partial_merge_mode() == PartialMergeMode.REVERSE:
            _run_reverse_merge(effective_set_dir, delta_sd_path, sd_path)
        else:
            _run_forward_merge(effective_set_dir, full_env_name, delta_sd_path)
    else:
        _run_full_generation(effective_set_dir, full_env_name, sd_path)

    # do not commit delta sd to repo
    deleteFileIfExists(delta_sd_path)


def _run_full_generation(effective_set_dir, full_env_name, sd_path):
    cmd = _build_cli_cmd(effective_set_dir, full_env_name, sd_path)
    delete_dir(effective_set_dir)
    subprocess.run(cmd, shell=True, check=True)


def _run_forward_merge(effective_set_dir, full_env_name, delta_sd_path):
    cmd = _build_cli_cmd(effective_set_dir, full_env_name, delta_sd_path)

    delta_sd = openYaml(delta_sd_path)
    apps = delta_sd.get("applications", [])

    deploy_postfixes = {
        app.get("deployPostfix")
        for app in apps
        if app.get("deployPostfix")
    }

    for ns in deploy_postfixes:
        delete_dir_if_exists(effective_set_dir / ESGenerationContext.CLEANUP.value / ns)

    for app in apps:
        app_name = app.get("version", "").split(":")[0]
        ns = app.get("deployPostfix")
        delete_dir_if_exists(effective_set_dir / ESGenerationContext.RUNTIME.value / ns / app_name)
        delete_dir_if_exists(effective_set_dir / ESGenerationContext.DEPLOYMENT.value / ns / app_name)

    delete_dir_if_exists(effective_set_dir / ESGenerationContext.TOPOLOGY.value)
    delete_dir_if_exists(effective_set_dir / ESGenerationContext.PIPELINE.value)

    cleanup_mapping_path = effective_set_dir / ESGenerationContext.CLEANUP.value / ES_MAPPING_FILE
    runtime_mapping_path = effective_set_dir / ESGenerationContext.RUNTIME.value / ES_MAPPING_FILE
    deployment_mapping_path = effective_set_dir / ESGenerationContext.DEPLOYMENT.value / ES_MAPPING_FILE

    cleanup_mapping = openYaml(cleanup_mapping_path, allow_default=True)
    runtime_mapping = openYaml(runtime_mapping_path, allow_default=True)
    deployment_mapping = openYaml(deployment_mapping_path, allow_default=True)

    subprocess.run(cmd, shell=True, check=True)

    new_cleanup_mapping = openYaml(cleanup_mapping_path, allow_default=True)
    new_runtime_mapping = openYaml(runtime_mapping_path, allow_default=True)
    new_deployment_mapping = openYaml(deployment_mapping_path, allow_default=True)

    cleanup_mapping.update(new_cleanup_mapping)
    runtime_mapping.update(new_runtime_mapping)
    deployment_mapping.update(new_deployment_mapping)

    writeYamlToFile(cleanup_mapping_path, cleanup_mapping)
    writeYamlToFile(runtime_mapping_path, runtime_mapping)
    writeYamlToFile(deployment_mapping_path, deployment_mapping)


def _run_reverse_merge(effective_set_dir, delta_sd_path, sd_path):
    sd_apps = openYaml(sd_path).get("applications", [])
    sd_postfixes = {app.get("deployPostfix") for app in sd_apps if app.get("deployPostfix")}
    delta_sd_apps = openYaml(delta_sd_path).get("applications", [])

    deleted_postfixes = set()
    for app in delta_sd_apps:
        app_name = app.get("version", "").split(":")[0]
        dp = app.get("deployPostfix")

        runtime_dp = effective_set_dir / ESGenerationContext.RUNTIME.value / dp
        deployment_dp = effective_set_dir / ESGenerationContext.DEPLOYMENT.value / dp
        cleanup_dp = effective_set_dir / ESGenerationContext.CLEANUP.value / dp

        delete_dir_if_exists(runtime_dp / app_name)
        delete_dir_if_exists(deployment_dp / app_name)

        if dp in deleted_postfixes:
            continue

        mapping_paths = [
            effective_set_dir / ESGenerationContext.CLEANUP.value / ES_MAPPING_FILE,
            effective_set_dir / ESGenerationContext.RUNTIME.value / ES_MAPPING_FILE,
            effective_set_dir / ESGenerationContext.DEPLOYMENT.value / ES_MAPPING_FILE,
        ]
        if dp not in sd_postfixes:
            delete_dir_if_exists(runtime_dp)
            delete_dir_if_exists(deployment_dp)
            delete_dir_if_exists(cleanup_dp)
            deleted_postfixes.add(dp)

            for path in mapping_paths:
                if not path.exists():
                    logger.warning(f"Mapping file not found, skipping: {path}")
                    continue
                mapping = openYaml(path, allow_default=True) or {}
                mapping_key = next((key for key in mapping if dp in key), None)

                if mapping_key is None:
                    logger.warning(f"Namespace substring '{dp}' not found in mapping file {path}, skipping removing")
                    continue

                mapping.pop(mapping_key)
                writeYamlToFile(path, mapping)


def _build_cli_cmd(effective_set_dir, full_env_name, sd_path):
    cmd = [
        "/module/scripts/utils/run_effective_set_cli.sh",
        f"--env-id={full_env_name}",
        "--envs-path=$CI_PROJECT_DIR/environments",
        f"--output={effective_set_dir}",
    ]

    if sd_path.is_file():
        cmd.extend([
            "--registries=${CI_PROJECT_DIR}/configuration/registry.yml",
            "--sboms-path=$CI_PROJECT_DIR/sboms",
            f"--sd-path={sd_path}",
        ])

    effective_set_config = getenv("EFFECTIVE_SET_CONFIG")
    if effective_set_config:
        effective_set_output = handle_effective_set_config(effective_set_config)
        extra_args = effective_set_output.get("extra_args") or []
        cmd.extend(extra_args)

    deployment_id = getenv("DEPLOYMENT_SESSION_ID")
    if deployment_id:
        cmd.append(f"--extra_params=DEPLOYMENT_SESSION_ID={deployment_id}")

    custom_params = getenv("CUSTOM_PARAMS")
    if custom_params:
        cmd.append(f"--custom-params={custom_params}")
    return " ".join(cmd)


if __name__ == "__main__":
    effective_set_entrypoint()
