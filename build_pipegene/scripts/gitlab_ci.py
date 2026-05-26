import os
from os import listdir

from envgenehelper import logger, get_cluster_name_from_full_name, get_environment_name_from_full_name
from envgenehelper.plugin_engine import PluginEngine
from gcip import JobFilter, Pipeline, TriggerJob

import pipeline_helper
from appregdef_render_job import prepare_appregdef_render_job
from bg_manage_job import prepare_bg_manage_job
from credential_rotation_job import prepare_credential_rotation_job
from env_build_jobs import prepare_env_build_job, prepare_git_commit_job
from inventory_generation_job import prepare_inventory_generation_job, is_inventory_generation_needed
from passport_jobs import prepare_trigger_passport_job, prepare_passport_job
from process_sd_job import prepare_process_sd
from effective_set_job import prepare_generate_effective_set_job
from pipeline_helper import get_gav_coordinates_from_build, find_predecessor_job
from envgenehelper.collections_helper import split_multi_value_param


PROJECT_DIR = os.getenv('CI_PROJECT_DIR') or os.getenv('GITHUB_WORKSPACE')
IS_GITLAB = bool(os.getenv('CI_PROJECT_DIR')) and not bool(os.getenv('GITHUB_ACTIONS'))
IS_GITHUB = bool(os.getenv('GITHUB_WORKSPACE')) or bool(os.getenv('GITHUB_ACTIONS'))

logger.info(f"Detected environment - GitLab: {IS_GITLAB}, GitHub: {IS_GITHUB}")


def build_pipeline(params: dict, sensitive_params: list) -> None:
    artifact_url = None
    group_id = ""
    artifact_id = ""

    if params['IS_TEMPLATE_TEST']:
        logger.info("Generating jobs in template test mode.")
        artifact_url = os.getenv("artifact_url")
        templates_dir = f"{PROJECT_DIR}/templates/env_templates"
        build_artifact = get_gav_coordinates_from_build()
        group_id = build_artifact["group_id"]
        artifact_id = build_artifact["artifact_id"]
        params['ENV_TEMPLATE_VERSION'] = f"{artifact_id}:{build_artifact['version']}"
        template_files = [
            os.path.splitext(f)[0]
            for f in listdir(templates_dir)
            if os.path.isfile(os.path.join(templates_dir, f)) and (f.endswith(".yaml") or f.endswith(".yml"))
        ]
        params['ENV_NAMES'] = "\n".join(template_files)

    pipeline = Pipeline()
    sorted_pipeline = Pipeline()
    get_passport_jobs = {}
    jobs_map = {}
    queued_job_names = []

    per_env_plugin_engine = PluginEngine(plugins_dir='/module/scripts/pipegene_plugins/per_env')

    env_names = split_multi_value_param(params['ENV_NAMES'])
    if len(env_names) > 1 and is_inventory_generation_needed(params['IS_TEMPLATE_TEST'], params):
        raise ValueError(
            f"Generating Inventories for multiple Environments in single pipeline is not supported. "
            f"ENV_NAMES: {env_names}"
        )

    for full_env_name in env_names:
        logger.info(f'----------------start processing for {full_env_name}---------------------')

        if params['IS_TEMPLATE_TEST']:
            env_template_art_vers = params["ENV_TEMPLATE_VERSION"]
            env_template_vers_split = env_template_art_vers.split(':')[1].replace('.', '_')
            env_template_version_normalized = f"{env_template_vers_split.replace('-', '_')}"

            project_name = os.getenv("CI_PROJECT_NAME")
            cluster_name = f"template_testing_{project_name}_{full_env_name}"
            environment_name = f"{cluster_name}_{env_template_version_normalized}"
        else:
            cluster_name = get_cluster_name_from_full_name(full_env_name)
            environment_name = get_environment_name_from_full_name(full_env_name)

        job_sequence = [
            "trigger_passport_job", "get_passport_job", "bg_manage_job", "env_inventory_generation_job",
            "credential_rotation_job", "appregdef_render_job", "process_sd_job", "env_build_job",
            "generate_effective_set_job", "git_commit_job"
        ]

        if params['GET_PASSPORT'] and cluster_name not in get_passport_jobs:
            jobs_map["trigger_passport_job"] = prepare_trigger_passport_job(pipeline, full_env_name)
            jobs_map["get_passport_job"] = prepare_passport_job(pipeline, full_env_name, environment_name, cluster_name)
            get_passport_jobs[cluster_name] = True
        else:
            logger.info(f"Generation of cloud passport for environment '{full_env_name}' is skipped")

        if params.get('BG_MANAGE'):
            jobs_map['bg_manage_job'] = prepare_bg_manage_job(pipeline, full_env_name)
        else:
            logger.info(f'Preparing of bg_manage job for environment {full_env_name} is skipped.')

        if is_inventory_generation_needed(params['IS_TEMPLATE_TEST'], params):
            jobs_map["env_inventory_generation_job"] = prepare_inventory_generation_job(
                pipeline, full_env_name, environment_name, cluster_name
            )
        else:
            logger.info(f'Preparing of inventory generation job for {full_env_name} is skipped.')

        credential_rotation_job = None
        if params['CRED_ROTATION_PAYLOAD']:
            credential_rotation_job = prepare_credential_rotation_job(
                pipeline, full_env_name, environment_name, cluster_name
            )
            jobs_map["credential_rotation_job"] = credential_rotation_job
        else:
            logger.info(f'Credential rotation job for {full_env_name} is skipped.')

        if params['ENV_BUILD']:
            jobs_map["appregdef_render_job"] = prepare_appregdef_render_job(
                pipeline, params, full_env_name, environment_name, cluster_name, group_id, artifact_id, artifact_url
            )
        else:
            logger.info(f'Preparing of appregdef_render_job for {full_env_name} is skipped.')

        source_type = (params.get("SD_SOURCE_TYPE", "artifact")).lower()
        if (source_type == "json" and params.get("SD_DATA")) or \
           (source_type == "artifact" and params.get("SD_VERSION")):
            jobs_map["process_sd_job"] = prepare_process_sd(pipeline, full_env_name, environment_name, cluster_name)
        else:
            logger.info(f'Preparing of process_sd_job for {full_env_name} is skipped')

        if params['ENV_BUILD']:
            jobs_map["env_build_job"] = prepare_env_build_job(
                pipeline, params['IS_TEMPLATE_TEST'], full_env_name, environment_name, cluster_name, group_id, artifact_id
            )
        else:
            logger.info(f'Preparing of env_build job for {full_env_name} is skipped.')

        if params['GENERATE_EFFECTIVE_SET']:
            jobs_map["generate_effective_set_job"] = prepare_generate_effective_set_job(
                pipeline, full_env_name, environment_name, cluster_name, params
            )
        else:
            logger.info(f'Preparing of generate_effective_set job for {full_env_name} is skipped.')

        jobs_requiring_git_commit = [
            "appregdef_render_job", "process_sd_job", "env_build_job", "generate_effective_set_job",
            "env_inventory_generation_job", "credential_rotation_job", "bg_manage_job"
        ]

        plugin_params = {
            **params,
            'jobs_map': jobs_map,
            'job_sequence': job_sequence,
            'jobs_requiring_git_commit': jobs_requiring_git_commit,
            'env_name': environment_name,
            'cluster_name': cluster_name,
            'full_env': full_env_name
        }
        per_env_plugin_engine.run(params=plugin_params, pipeline=pipeline, pipeline_helper=pipeline_helper)

        if any(job in jobs_map for job in plugin_params['jobs_requiring_git_commit']) and not params['IS_TEMPLATE_TEST']:
            jobs_map["git_commit_job"] = prepare_git_commit_job(
                pipeline, full_env_name, environment_name, cluster_name, credential_rotation_job
            )
        else:
            logger.info(f'Preparing of git commit job for {full_env_name} is skipped.')

        for job_name in job_sequence:
            if job_name in jobs_map and jobs_map[job_name].name not in queued_job_names:
                job_instance = jobs_map[job_name]
                queued_job_names.append(job_instance.name)
                sorted_pipeline.add_children(job_instance)
                job_instance.add_needs(*find_predecessor_job(job_name, jobs_map, job_sequence))

        logger.info(f'----------------end processing for {full_env_name}---------------------')

    for key, value in params.items():
        if key not in sensitive_params and value:
            sorted_pipeline.add_variables(**{key: value})
    sorted_pipeline.add_tags(params["GITLAB_RUNNER_TAG_NAME"])

    for job in sorted_pipeline.find_jobs(JobFilter()):
        job.artifacts.add_paths('environments/', 'configuration/', 'sboms/', 'templates/', 'tmp/')
        if not do_checkout(job):
            job.add_variables(GIT_STRATEGY="empty")

    sorted_pipeline.write_yaml()


def is_trigger_job(job):
    return isinstance(job, TriggerJob)


def do_checkout(job):
    is_first_job = not job.needs
    if is_first_job or any(is_trigger_job(need) for need in job.needs):
        logger.info(f"Enabling checkout for {job.name} (Stage: {job.stage}, Needs: {job.needs})")
        return True
    return False
