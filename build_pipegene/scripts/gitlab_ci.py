import os
from os import listdir

from envgenehelper.plugin_engine import PluginEngine
from envgenehelper import logger, get_cluster_name_from_full_name, get_environment_name_from_full_name, getEnvDefinition, get_env_instances_dir
from gcip import JobFilter, Pipeline
import pipeline_helper
from pipeline_helper import get_gav_coordinates_from_build, find_predecessor_job

from passport_jobs import prepare_trigger_passport_job, prepare_passport_job, prepare_decryption_mode_job
from env_build_jobs import prepare_env_build_job, prepare_generate_effective_set_job, prepare_git_commit_job
from inventory_generation_job import prepare_inventory_generation_job, is_inventory_generation_needed
from credential_rotation_job import prepare_credential_rotation_job

project_dir = os.getenv('CI_PROJECT_DIR') or os.getenv('GITHUB_WORKSPACE')

is_gitlab = bool(os.getenv('CI_PROJECT_DIR')) and not bool(os.getenv('GITHUB_ACTIONS'))
is_github = bool(os.getenv('GITHUB_WORKSPACE')) or bool(os.getenv('GITHUB_ACTIONS'))

logger.info(f"Detected environment - GitLab: {is_gitlab}, GitHub: {is_github}")

def build_pipeline(params: dict):
    # if we are in template testing during template build
    tags=params['GITLAB_RUNNER_TAG_NAME']

    if params['IS_TEMPLATE_TEST']:
        logger.info("We are generating jobs in template test mode.")
        templates_dir = f"{project_dir}/templates/env_templates"
        # getting build artifact
        build_artifact = get_gav_coordinates_from_build()
        group_id = build_artifact["group_id"]
        artifact_id = build_artifact["artifact_id"]
        params['ENV_TEMPLATE_VERSION'] = build_artifact["version"]
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
        ci_project_dir = project_dir

        if params['IS_TEMPLATE_TEST']:
            cluster_name = ""
            environment_name = env
            env_definition = {}
        else:
            cluster_name = get_cluster_name_from_full_name(env)
            environment_name = get_environment_name_from_full_name(env)
            if params['ENV_INVENTORY_GENERATION_PARAMS']['ENV_INVENTORY_INIT']:
                env_definition = None
            else:
                env_definition = getEnvDefinition(get_env_instances_dir(environment_name, cluster_name, f"{ci_project_dir}/environments"))

        # trigger_passport_job ->
        # get_passport_job (commit if not is_offsite) ->
        # process_decryption_mode_job (commit) ->
        # env_inventory_generation_job ->
        # env_build_job ->
        # generate_effective_set_job ->
        # git_commit_job (commit) ->
        job_sequence = ["trigger_passport_job", "get_passport_job", "process_decryption_mode_job", "env_inventory_generation_job",
                    "credential_rotation_job", "env_build_job", "generate_effective_set_job", "git_commit_job"]

        # get passport job if it is not already added for cluster
        if params['GET_PASSPORT'] and cluster_name not in get_passport_jobs:
            jobs_map["trigger_passport_job"] = prepare_trigger_passport_job(pipeline, env)
            jobs_map["get_passport_job"] = prepare_passport_job(pipeline, env, environment_name, cluster_name, tags, need_commit=not params['IS_OFFSITE'])
            get_passport_jobs[cluster_name] = True
            ## process_decryption_mode job is for offsite only
            if params['IS_OFFSITE']:
                jobs_map["process_decryption_mode_job"] = prepare_decryption_mode_job(pipeline, env, cluster_name,tags)
        else:
            logger.info(f"Generation of cloud passport for environment '{env}' is skipped")

        if is_inventory_generation_needed(params['IS_TEMPLATE_TEST'], params['ENV_INVENTORY_GENERATION_PARAMS']):
            jobs_map["env_inventory_generation_job"] = prepare_inventory_generation_job(pipeline, env, environment_name, cluster_name, params['ENV_INVENTORY_GENERATION_PARAMS'], tags)
        else:
            logger.info(f'Preparing of env inventory generation job for {env} is skipped because we are in template test mode.')

        credential_rotation_job = None
        if params['CRED_ROTATION_PAYLOAD']:
            credential_rotation_job = prepare_credential_rotation_job(pipeline, env, environment_name, cluster_name, tags)
            jobs_map["credential_rotation_job"] = credential_rotation_job
        else:
            logger.info(f'Credential rotation job for {env} is skipped because CRED_ROTATION_PAYLOAD is empty.')
        if params['ENV_BUILD']:
            if env_definition is None:
                try:
                    env_definition = getEnvDefinition(get_env_instances_dir(environment_name, cluster_name, f"{ci_project_dir}/environments"))
                except ReferenceError:
                    pass

            # env_builder job
            jobs_map["env_build_job"] = prepare_env_build_job(pipeline, params['IS_TEMPLATE_TEST'], params['ENV_TEMPLATE_VERSION'], env, environment_name, cluster_name, group_id, artifact_id, tags)
        else:
            logger.info(f'Preparing of env_build job for {env} is skipped.')

        # generate_effective_set job
        if params['GENERATE_EFFECTIVE_SET']:
            jobs_map["generate_effective_set_job"] = prepare_generate_effective_set_job(pipeline, environment_name, cluster_name, tags)
        else:
            logger.info(f'Preparing of generate_effective_set job for {cluster_name}/{environment_name} is skipped.')

        jobs_requiring_git_commit = ["env_build_job", "generate_effective_set_job", "env_inventory_generation_job", "credential_rotation_job"]

        plugin_params = params
        plugin_params['jobs_map'] = jobs_map
        plugin_params['job_sequence'] = job_sequence
        plugin_params['jobs_requiring_git_commit'] = jobs_requiring_git_commit
        plugin_params['env_name'] = environment_name
        plugin_params['cluster_name'] = cluster_name
        plugin_params['full_env'] = env
        per_env_plugin_engine.run(params=plugin_params, pipeline=pipeline, pipeline_helper=pipeline_helper)

        ## git_commit job
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
        job.artifacts.add_paths("${CI_PROJECT_DIR}")
        if job.needs is None or len(job.needs) == 0:
            job.add_variables(GIT_STRATEGY="fetch")
        else:
            job.add_variables(GIT_STRATEGY="empty")

    sorted_pipeline.write_yaml()
