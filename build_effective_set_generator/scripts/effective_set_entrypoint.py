import os
import subprocess
from os import getenv

from envgenehelper import (
    decrypt_all_cred_files_for_env, copy_path, validate_creds,
    openJson, encrypt_all_cred_files_for_env, resolve_sd_path,
    logger, get_current_env_dir_from_env_vars, cleanup_dir,
    get_envgene_config_yaml, openYaml, ESGenerationContext,
    ES_MAPPING_FILE, writeYamlToFile, calculate_merge_mode,
    delete_dir, get_environment_name_from_full_name,
    get_sd_dir, SD_FILE_NAME, MergeType, DELTA_SD_FILE_NAME
)

from handle_effective_set_config import handle_effective_set_config
from sboms_retention_policy import sboms_retention_policy


def effective_set_entrypoint():
    ctx = _prepare_context()

    if ctx["is_partial"]:
        delta_sd_path = ctx["delta_sd_path"]
        sd_path = ctx["sd_path"].exists()
        if not ctx["delta_sd_path"].exists() and ctx["sd_path"].exists():
            raise ValueError(
                f"[Partial effective set generation] impossible without delta sd {delta_sd_path} and full sd {sd_path}")

        elif ctx["is_reverse"]:
            _run_reverse_merge(ctx)
        else:
            _run_forward_merge(ctx)
    else:
        _run_full_generation(ctx)


def _prepare_context():
    full_env_name = getenv("FULL_ENV_NAME")
    merge_mode = calculate_merge_mode(getenv("SD_REPO_MERGE_MODE"), getenv("SD_DELTA"))

    effective_set_dir = get_current_env_dir_from_env_vars() / "effective-set"
    sd_path = get_sd_dir().joinpath(SD_FILE_NAME)
    delta_sd_path = get_sd_dir().joinpath(DELTA_SD_FILE_NAME)

    is_partial = get_envgene_config_yaml().get(
        "partial_effective_set_generation") and merge_mode.name != MergeType.REPLACE
    is_reverse = is_partial and merge_mode.name == MergeType.BASIC_EXCLUSION

    return {
        "full_env_name": full_env_name,
        "effective_set_dir": effective_set_dir,
        "sd_path": sd_path,
        "delta_sd_path": delta_sd_path,
        "is_partial": is_partial,
        "is_reverse": is_reverse,
    }


def _run_full_generation(ctx):
    decrypt_all_cred_files_for_env()
    validate_creds()
    effective_set_dir = ctx["effective_set_dir"]
    cmd = _build_cli_cmd(ctx)
    cleanup_dir(effective_set_dir)
    subprocess.run(["sh", cmd], check=True)
    encrypt_all_cred_files_for_env()


def _run_forward_merge(ctx):
    effective_set_dir = ctx["effective_set_dir"]
    delta_sd_path = ctx["delta_sd_path"]
    decrypt_all_cred_files_for_env()
    validate_creds()

    cmd = _build_cli_cmd(ctx)

    delta_sd = openYaml(delta_sd_path)
    apps = delta_sd.get("applications", [])

    deploy_postfixes = {
        app.get("deployPostfix")
        for app in apps
        if app.get("deployPostfix")
    }

    for ns in deploy_postfixes:
        cleanup_dir(effective_set_dir / ESGenerationContext.CLEANUP.value / ns)

    for app in apps:
        app_name = app.get("version", "").split(":")[0]
        ns = app.get("deployPostfix")
        cleanup_dir(effective_set_dir / ESGenerationContext.RUNTIME.value / ns / app_name)
        cleanup_dir(effective_set_dir / ESGenerationContext.DEPLOYMENT.value / ns / app_name)

    cleanup_dir(effective_set_dir / ESGenerationContext.TOPOLOGY.value)
    cleanup_dir(effective_set_dir / ESGenerationContext.PIPELINE.value)

    cleanup_mapping_path = effective_set_dir / ESGenerationContext.CLEANUP.value / ES_MAPPING_FILE
    runtime_mapping_path = effective_set_dir / ESGenerationContext.RUNTIME.value / ES_MAPPING_FILE
    deployment_mapping_path = effective_set_dir / ESGenerationContext.DEPLOYMENT.value / ES_MAPPING_FILE

    cleanup_mapping = openYaml(cleanup_mapping_path)
    runtime_mapping = openYaml(runtime_mapping_path)
    deployment_mapping = openYaml(deployment_mapping_path)

    subprocess.run(["sh", cmd], check=True)

    new_cleanup_mapping = openYaml(cleanup_mapping_path)
    new_runtime_mapping = openYaml(runtime_mapping_path)
    new_deployment_mapping = openYaml(deployment_mapping_path)

    cleanup_mapping.update(new_cleanup_mapping)
    runtime_mapping.update(new_runtime_mapping)
    deployment_mapping.update(new_deployment_mapping)

    writeYamlToFile(cleanup_mapping_path, cleanup_mapping)
    writeYamlToFile(runtime_mapping_path, runtime_mapping)
    writeYamlToFile(deployment_mapping_path, deployment_mapping)

    encrypt_all_cred_files_for_env()


def _run_reverse_merge(ctx):
    effective_set_dir = ctx["effective_set_dir"]
    delta_sd_path = ctx["delta_sd_path"]

    apps = openYaml(delta_sd_path).get("applications", [])

    for app in apps:
        app_name = app.get("version", "").split(":")[0]
        dp = app.get("deployPostfix")

        runtime_dp = effective_set_dir / ESGenerationContext.RUNTIME.value / dp
        deployment_dp = effective_set_dir / ESGenerationContext.DEPLOYMENT.value / dp
        cleanup_dp = effective_set_dir / ESGenerationContext.CLEANUP.value / dp

        cleanup_dir(runtime_dp / app_name)
        cleanup_dir(deployment_dp / app_name)

        if not any(runtime_dp.iterdir()):
            delete_dir(runtime_dp)
            delete_dir(cleanup_dp)
            delete_dir(deployment_dp)

            ns = get_environment_name_from_full_name(ctx["full_env_name"])
            mapping_paths = [
                effective_set_dir / ESGenerationContext.CLEANUP.value / ES_MAPPING_FILE,
                effective_set_dir / ESGenerationContext.RUNTIME.value / ES_MAPPING_FILE,
                effective_set_dir / ESGenerationContext.DEPLOYMENT.value / ES_MAPPING_FILE,
            ]
            for path in mapping_paths:
                mapping = openYaml(path, allow_default=True)
                if ns in mapping:
                    mapping.pop(ns)
                    writeYamlToFile(path, mapping)


def _build_cli_cmd(ctx):
    effective_set_dir = ctx["effective_set_dir"]
    sd_path = ctx["sd_path"]

    cmd = [
        "/module/scripts/utils/run_effective_set_cli.sh",
        f"--env-id={ctx['full_env_name']}",
        "--envs-path=$CI_PROJECT_DIR/environments",
        f"--output={effective_set_dir}",
    ]

    if sd_path.is_file():
        cmd.extend([
            "--registries=${CI_PROJECT_DIR}/configuration/registry.yml",
            "--sboms-path=$sboms_path",
            "--sd-path=$sd_path",
        ])

    effective_set_config = getenv("EFFECTIVE_SET_CONFIG")
    if effective_set_config:
        handle_effective_set_config(effective_set_config)
        effective_set_output = openJson("/tmp/effective_set_output.json")
        extra_args = effective_set_output.get("extra_args") or []
        cmd.extend(extra_args)

    deployment_id = getenv("DEPLOYMENT_SESSION_ID")
    if deployment_id:
        cmd.append(f"--extra_params=DEPLOYMENT_SESSION_ID={deployment_id}")

    custom_params = getenv("CUSTOM_PARAMS")
    if custom_params:
        cmd.append(f"--custom-params={custom_params}")

    return cmd
