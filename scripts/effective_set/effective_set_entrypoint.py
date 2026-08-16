import shlex
import shutil
import subprocess
import tempfile
from os import getenv
from pathlib import Path

from envgenehelper.business_helper import get_current_env_dir_from_env_vars
from envgenehelper.deploy_plan_adapter import DeployPlanEntity, EnvgeneDeployPlan, GenerationType
from envgenehelper.effective_set_helper import ES_DIR_NAME, ES_MAPPING_FILE, ESGenerationContext, GenerationMode, \
    PartialMergeMode
from envgenehelper.file_helper import delete_dir, delete_dir_if_exists, deleteFileIfExists
from envgenehelper.logger import logger
from envgenehelper.sd_helper import get_sd_dir, DELTA_SD_FILE_NAME
from envgenehelper.yaml_helper import writeYamlToFile, openYaml

from effective_set.handle_effective_set_config import handle_effective_set_config


def run_gitlab_deploy_effective_set(ctx):
    full_env_name = getenv("FULL_ENV_NAME")
    effective_set_dir = get_current_env_dir_from_env_vars() / ES_DIR_NAME

    if ctx.is_clean():
        cmd = _build_cli_cmd(effective_set_dir, full_env_name, dp_path=None)
        subprocess.run(cmd, shell=True, check=True)
    else:
        _run_deploy_plan_full(effective_set_dir, full_env_name, ctx.deploy_plan_delta)

    _cleanup_delta_artifacts()


def run_legacy_sd_effective_set(ctx):
    full_env_name = getenv("FULL_ENV_NAME")
    effective_set_dir = get_current_env_dir_from_env_vars() / ES_DIR_NAME

    if ctx.es_generation_mode == GenerationMode.FULL:
        _run_deploy_plan_full(effective_set_dir, full_env_name, ctx.deploy_plan)
    elif ctx.partial_merge_mode == PartialMergeMode.FORWARD:
        _run_deploy_plan_partial(effective_set_dir, full_env_name, ctx.deploy_plan_delta)
    elif ctx.partial_merge_mode == PartialMergeMode.REVERSE:
        _run_reverse_merge(effective_set_dir, ctx.deploy_plan, ctx.deploy_plan_delta)

    _cleanup_delta_artifacts()


def _cleanup_delta_artifacts():
    deleteFileIfExists(get_sd_dir().joinpath(DELTA_SD_FILE_NAME))
    deleteFileIfExists(EnvgeneDeployPlan.delta_path())


def _run_deploy_plan_full(effective_set_dir, full_env_name, deploy_plan: EnvgeneDeployPlan):
    entries = deploy_plan.entities
    tmp_root, saved = _save_es_app_dirs(effective_set_dir, entries)
    delete_dir(effective_set_dir)
    _restore_saved_dirs(tmp_root, saved)
    _clear_uniq_for_version_dirs(effective_set_dir, entries)

    cmd = _build_cli_cmd(effective_set_dir, full_env_name, deploy_plan.dp_path)
    subprocess.run(cmd, shell=True, check=True)


def _run_deploy_plan_partial(effective_set_dir, full_env_name, deploy_plan_delta: EnvgeneDeployPlan):
    entries = deploy_plan_delta.entities
    for ns in {e.namespace for e in entries}:
        delete_dir_if_exists(effective_set_dir / ESGenerationContext.CLEANUP.value / ns)
    for entry in entries:
        app = entry.version.split(":")[0]
        delete_dir_if_exists(effective_set_dir / ESGenerationContext.RUNTIME.value / entry.namespace / app)
        delete_dir_if_exists(effective_set_dir / ESGenerationContext.DEPLOYMENT.value / entry.namespace / app)
    delete_dir_if_exists(effective_set_dir / ESGenerationContext.TOPOLOGY.value)
    delete_dir_if_exists(effective_set_dir / ESGenerationContext.PIPELINE.value)

    cleanup_mapping_path = effective_set_dir / ESGenerationContext.CLEANUP.value / ES_MAPPING_FILE
    runtime_mapping_path = effective_set_dir / ESGenerationContext.RUNTIME.value / ES_MAPPING_FILE
    deployment_mapping_path = effective_set_dir / ESGenerationContext.DEPLOYMENT.value / ES_MAPPING_FILE
    cleanup_mapping = openYaml(cleanup_mapping_path, allow_default=True)
    runtime_mapping = openYaml(runtime_mapping_path, allow_default=True)
    deployment_mapping = openYaml(deployment_mapping_path, allow_default=True)

    cmd = _build_cli_cmd(effective_set_dir, full_env_name, deploy_plan_delta.dp_path)
    subprocess.run(cmd, shell=True, check=True)

    cleanup_mapping.update(openYaml(cleanup_mapping_path, allow_default=True))
    runtime_mapping.update(openYaml(runtime_mapping_path, allow_default=True))
    deployment_mapping.update(openYaml(deployment_mapping_path, allow_default=True))
    writeYamlToFile(cleanup_mapping_path, cleanup_mapping)
    writeYamlToFile(runtime_mapping_path, runtime_mapping)
    writeYamlToFile(deployment_mapping_path, deployment_mapping)


def _run_reverse_merge(effective_set_dir, deploy_plan: EnvgeneDeployPlan, deploy_plan_delta: EnvgeneDeployPlan):
    entries = deploy_plan.entities
    delta_entries = deploy_plan_delta.entities
    remaining_namespaces = {e.namespace for e in entries}
    deleted_namespaces = set()

    mapping_paths = [
        effective_set_dir / ESGenerationContext.CLEANUP.value / ES_MAPPING_FILE,
        effective_set_dir / ESGenerationContext.RUNTIME.value / ES_MAPPING_FILE,
        effective_set_dir / ESGenerationContext.DEPLOYMENT.value / ES_MAPPING_FILE,
    ]

    for entry in delta_entries:
        app = entry.version.split(":")[0]
        ns = entry.namespace

        runtime_ns = effective_set_dir / ESGenerationContext.RUNTIME.value / ns
        deployment_ns = effective_set_dir / ESGenerationContext.DEPLOYMENT.value / ns
        cleanup_ns = effective_set_dir / ESGenerationContext.CLEANUP.value / ns

        delete_dir_if_exists(runtime_ns / app)
        delete_dir_if_exists(deployment_ns / app)

        if ns in deleted_namespaces:
            continue

        if ns not in remaining_namespaces:
            delete_dir_if_exists(runtime_ns)
            delete_dir_if_exists(deployment_ns)
            delete_dir_if_exists(cleanup_ns)
            deleted_namespaces.add(ns)

            for path in mapping_paths:
                if not path.exists():
                    logger.warning(f"Mapping file not found, skipping: {path}")
                    continue
                mapping = openYaml(path, allow_default=True) or {}
                mapping_key = next((key for key in mapping if ns in key), None)
                if mapping_key is None:
                    logger.warning(f"Namespace substring '{ns}' not found in mapping file {path}, skipping removing")
                    continue
                mapping.pop(mapping_key)
                writeYamlToFile(path, mapping)


def _resolve_generation_id(entry: DeployPlanEntity):
    if entry.generation_type == GenerationType.UNIQ_FOR_RUN:
        return str(entry.generation_id) if entry.generation_id else None
    if entry.generation_type == GenerationType.UNIQ_FOR_VERSION:
        return entry.version.split(":", 1)[1]
    return None


def _clear_uniq_for_version_dirs(effective_set_dir, entries: list[DeployPlanEntity]):
    for entry in entries:
        if entry.generation_type != GenerationType.UNIQ_FOR_VERSION:
            continue
        app = entry.version.split(":")[0]
        generation_id = _resolve_generation_id(entry)
        delete_dir_if_exists(effective_set_dir / ESGenerationContext.RUNTIME.value / entry.namespace / app / generation_id)
        delete_dir_if_exists(effective_set_dir / ESGenerationContext.DEPLOYMENT.value / entry.namespace / app / generation_id)


def _save_es_app_dirs(effective_set_dir, entries: list[DeployPlanEntity]):
    tmp_root = None
    saved = []
    for entry in entries:
        if _resolve_generation_id(entry) is None:
            continue
        ns, app = entry.namespace, entry.version.split(":")[0]
        for ctx in (ESGenerationContext.DEPLOYMENT, ESGenerationContext.RUNTIME):
            src = effective_set_dir / ctx.value / ns / app
            if not src.is_dir():
                continue
            if tmp_root is None:
                tmp_root = Path(tempfile.mkdtemp(prefix="es-save-"))
            dest = tmp_root / ctx.value / ns / app
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), str(dest))
            saved.append((src, dest))
    return tmp_root, saved


def _restore_saved_dirs(tmp_root, saved):
    for src, dest in saved:
        src.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(dest), str(src))
    if tmp_root is not None:
        shutil.rmtree(tmp_root, ignore_errors=True)


def _build_cli_cmd(effective_set_dir, full_env_name, dp_path):
    cmd = [
        getenv("EFFECTIVE_SET_CLI_PATH", "/module/scripts/utils/run_effective_set_cli.sh"),
        f"--env-id={full_env_name}",
        "--envs-path=$CI_PROJECT_DIR/environments",
        f"--output={effective_set_dir}",
    ]

    if dp_path is not None and dp_path.is_file():
        cmd.extend([
            "--registries=${CI_PROJECT_DIR}/configuration/registry.yml",
            "--sboms-path=$CI_PROJECT_DIR/sboms",
            f"--deploy-plan-path={dp_path}",
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
        cmd.append(f"--custom-params={shlex.quote(custom_params)}")
    return " ".join(cmd)
