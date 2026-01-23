import os
from os import listdir

from gcip import JobFilter, Pipeline

import pipeline_helper
from pipeline_helper import get_gav_coordinates_from_build, find_predecessor_job
from envgenehelper.plugin_engine import PluginEngine
from envgenehelper import logger, get_cluster_name_from_full_name, get_environment_name_from_full_name, getEnvDefinition, get_env_instances_dir
from passport_jobs import prepare_trigger_passport_job, prepare_passport_job
from env_build_jobs import prepare_env_build_job, prepare_generate_effective_set_job, prepare_git_commit_job
from inventory_generation_job import prepare_inventory_generation_job, is_inventory_generation_needed
from credential_rotation_job import prepare_credential_rotation_job
from appregdef_render_job import prepare_appregdef_render_job

PROJECT_DIR = os.getenv('CI_PROJECT_DIR') or os.getenv('GITHUB_WORKSPACE')
IS_GITLAB = bool(os.getenv('CI_PROJECT_DIR')) and not bool(os.getenv('GITHUB_ACTIONS'))
IS_GITHUB = bool(os.getenv('GITHUB_WORKSPACE')) or bool(os.getenv('GITHUB_ACTIONS'))

logger.info(f"Detected environment - GitLab: {IS_GITLAB}, GitHub: {IS_GITHUB}")


def build_pipeline(params: dict) -> None:
    tags=params['GITLAB_RUNNER_TAG_NAME']

    artifact_url = None
    if params['IS_TEMPLATE_TEST']:
        logger.info("Generating jobs in template test mode.")
        artifact_url = os.getenv("artifact_url")
        templates_dir = f"{PROJECT_DIR}/templates/env_templates"
        # getting build artifact
        build_artifact = get_gav_coordinates_from_build()
        group_id = build_artifact["group_id"]
        artifact_id = build_artifact["artifact_id"]
        params['ENV_TEMPLATE_VERSION'] = f"{artifact_id}:{build_artifact["version"]}"
        # get env_names for all templates types
        templateFiles = [
            os.path.splitext(f)[0]
            for f in listdir(templates_dir)
            if os.path.isfile(os.path.join(templates_dir, f))
            and (f.endswith(".yaml") or f.endswith(".yml"))
        ]
        params['ENV_NAMES'] = "\n".join(templateFiles)
    else:
        group_id = ""
        artifact_id = ""

    pipeline = Pipeline()
    sorted_pipeline = Pipeline()
    get_passport_jobs = {}
    jobs_map = {}
    queued_job_names = []

    per_env_plugin_engine = PluginEngine(plugins_dir='/module/scripts/pipegene_plugins/per_env')

    for env in params['ENV_NAMES'].split("\n"):
        logger.info(f'----------------start processing for {env}---------------------')

        if params['IS_TEMPLATE_TEST']:
            cluster_name = ""
            environment_name = env
            env_definition = {}
        else:
            cluster_name = get_cluster_name_from_full_name(env)
            environment_name = get_environment_name_from_full_name(env)
            env_definition = None
            if not params['ENV_INVENTORY_INIT']:
                env_definition = getEnvDefinition(get_env_instances_dir(environment_name, cluster_name, f"{PROJECT_DIR}/environments"))
                

        job_sequence = [
            "trigger_passport_job",
            "get_passport_job",
            "env_inventory_generation_job",
            "credential_rotation_job",
            "appregdef_render_job",
            "env_build_job",
            "generate_effective_set_job",
            "git_commit_job"
        ]

        # get passport job if it is not already added for cluster
        if params['GET_PASSPORT'] and cluster_name not in get_passport_jobs:
            jobs_map["trigger_passport_job"] = prepare_trigger_passport_job(pipeline, env)
            jobs_map["get_passport_job"] = prepare_passport_job(pipeline, env, environment_name, cluster_name, tags)
            get_passport_jobs[cluster_name] = True
        else:
            logger.info(f"Generation of cloud passport for environment '{env}' is skipped")

        if is_inventory_generation_needed(params['IS_TEMPLATE_TEST'], params):
            jobs_map["env_inventory_generation_job"] = prepare_inventory_generation_job(pipeline, env, environment_name, cluster_name, params, tags)
        else:
            logger.info(f'Preparing of env inventory generation job for {env} is skipped because we are in template test mode.')
            
        if env_definition is None:
            try:
                env_definition = getEnvDefinition(get_env_instances_dir(environment_name, cluster_name, f"{PROJECT_DIR}/environments"))
            except ReferenceError:
                pass

        credential_rotation_job = None
        if params['CRED_ROTATION_PAYLOAD']:
            credential_rotation_job = prepare_credential_rotation_job(pipeline, env, environment_name, cluster_name, tags)
            jobs_map["credential_rotation_job"] = credential_rotation_job
        else:
            logger.info(f'Credential rotation job for {env} is skipped because CRED_ROTATION_PAYLOAD is empty.')
            
        if params['ENV_BUILD'] or (params["SD_SOURCE_TYPE"].lower() == "json" and params["SD_DATA"] or params["SD_SOURCE_TYPE"].lower() == "artifact" and params["SD_VERSION"]):
            jobs_map["appregdef_render_job"] = prepare_appregdef_render_job(pipeline, params['IS_TEMPLATE_TEST'], params['ENV_TEMPLATE_VERSION'], env, environment_name, cluster_name, tags)
        else:
            logger.info(f'Preparing of appregdef_render_job {env} is skipped.')

        if params['ENV_BUILD']:     
            jobs_map["env_build_job"] = prepare_env_build_job(pipeline, params['IS_TEMPLATE_TEST'], params['ENV_TEMPLATE_VERSION'], env, environment_name, cluster_name, group_id, artifact_id, artifact_url, tags)
        else:
            logger.info(f'Preparing of env_build job for {env} is skipped.')

        if params['GENERATE_EFFECTIVE_SET']:
            jobs_map["generate_effective_set_job"] = prepare_generate_effective_set_job(pipeline, environment_name, cluster_name, tags)
        else:
            logger.info(f'Preparing of generate_effective_set job for {cluster_name}/{environment_name} is skipped.')

        jobs_requiring_git_commit = ["appregdef_render_job", "env_build_job", "generate_effective_set_job", "env_inventory_generation_job", "credential_rotation_job"]

        plugin_params = params
        plugin_params['jobs_map'] = jobs_map
        plugin_params['job_sequence'] = job_sequence
        plugin_params['jobs_requiring_git_commit'] = jobs_requiring_git_commit
        plugin_params['env_name'] = environment_name
        plugin_params['cluster_name'] = cluster_name
        plugin_params['full_env'] = env
        per_env_plugin_engine.run(params=plugin_params, pipeline=pipeline, pipeline_helper=pipeline_helper)

        if any(job in jobs_map for job in plugin_params['jobs_requiring_git_commit']) and not params['IS_TEMPLATE_TEST']:
            jobs_map["git_commit_job"] = prepare_git_commit_job(pipeline, env, environment_name, cluster_name, params['DEPLOYMENT_SESSION_ID'], tags, credential_rotation_job)
        else:
            logger.info(f'Preparing of git commit job for {env} is skipped.')

        for job in job_sequence:
            if job not in jobs_map.keys():
                continue
            job_instance = jobs_map[job]
            if job_instance.name in queued_job_names:
                continue
            queued_job_names.append(job_instance.name)
            sorted_pipeline.add_children(job_instance)
            job_instance.add_needs(*find_predecessor_job(job, jobs_map, job_sequence))

        logger.info(f'----------------end processing for {env}---------------------')

    # check out repo only once in the first job of the generated pipeline, later jobs get it through artifacts from each other
    # purpose: avoid later jobs restoring files that were removed by previous jobs, so git commit job can commit those deletions
    for job in sorted_pipeline.find_jobs(JobFilter()): # gets all jobs in pipeline
        job.artifacts.add_paths('./')
        is_first_job = job.needs is None or len(job.needs) == 0
        if not is_first_job:
            job.add_variables(GIT_CHECKOUT="false")


    sorted_pipeline.write_yaml()

