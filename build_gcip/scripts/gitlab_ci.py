from os import getenv, listdir
import os

from plugin_engine import PluginEngine
from envgenehelper import logger, get_cluster_name_from_full_name, get_environment_name_from_full_name, getEnvDefinition, get_env_instances_dir
from gcip import JobFilter, Pipeline
import pipeline_helper
from pipeline_helper import get_gav_coordinates_from_build, find_predecessor_job

from passport_jobs import prepare_trigger_passport_job, prepare_passport_job, prepare_decryption_mode_job
from env_build_jobs import prepare_env_build_job, prepare_generate_effective_set_job, prepare_git_commit_job
from inventory_generation_job import prepare_inventory_generation_job, is_inventory_generation_needed


def build_pipeline(env_names, env_build, get_passport, cmdb_import, generate_effective_set, env_template_version, is_template_test, is_offsite, ci_commit_ref_name, env_inventory_init, env_inventory_generation_params, params: dict):
  # if we are in template testing during template build
  if is_template_test:
    logger.info("We are generating jobs in template test mode.")
    templates_dir = f"{getenv('CI_PROJECT_DIR')}/templates/env_templates"
    # getting build artifact
    build_artifact = get_gav_coordinates_from_build()
    group_id = build_artifact["group_id"]
    artifact_id = build_artifact["artifact_id"]
    env_template_version = build_artifact["version"]
    # get env_names for all templates types
    templateFiles = [os.path.splitext(f)[0] for f in listdir(templates_dir) if os.path.isfile(os.path.join(templates_dir, f)) and (f.endswith('.yaml') or f.endswith('.yml'))]
    env_names = '\n'.join(templateFiles)
  else:
     group_id = ""
     artifact_id = ""
  
  pipeline = Pipeline()
  sorted_pipeline = Pipeline()
  get_passport_jobs = {}
  jobs_map = {}

  for env in env_names.split("\n"):
    logger.info(f'----------------start processing for {env}---------------------')
    ci_project_dir = getenv("CI_PROJECT_DIR")

    if is_template_test:
      cluster_name = ""
      environment_name = env
      env_definition = {}
    else: 
      cluster_name = get_cluster_name_from_full_name(env)
      environment_name = get_environment_name_from_full_name(env)
      if env_inventory_init:
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
                    "env_build_job", "generate_effective_set_job", "git_commit_job"]
    
    # get passport job if it is not already added for cluster
    if get_passport and cluster_name not in get_passport_jobs:
      jobs_map["trigger_passport_job"] = prepare_trigger_passport_job(pipeline, env)
      jobs_map["get_passport_job"] = prepare_passport_job(pipeline, env, environment_name, cluster_name, need_commit=not is_offsite)
      get_passport_jobs[cluster_name] = True
      ## process_decryption_mode job is for offsite only
      if is_offsite:
        jobs_map["process_decryption_mode_job"] = prepare_decryption_mode_job(pipeline, env, cluster_name)
    else:
       logger.info(f"Generation of cloud passport for environment '{env}' is skipped")

    if is_inventory_generation_needed(is_template_test, env_inventory_generation_params):
      jobs_map["env_inventory_generation_job"] = prepare_inventory_generation_job(pipeline, env, environment_name, cluster_name, env_inventory_generation_params)
    else:
      logger.info(f'Preparing of env inventory generation job for {env} is skipped because we are in template test mode.')

    if env_build:
      if env_definition == None:
        try:
            env_definition = getEnvDefinition(get_env_instances_dir(environment_name, cluster_name, f"{ci_project_dir}/environments"))
        except ReferenceError:
            pass

      # env_builder job
      jobs_map["env_build_job"] = prepare_env_build_job(pipeline, is_template_test, env_template_version, env, environment_name, cluster_name, group_id, artifact_id)
    else:
       logger.info(f'Preparing of env_build job for {env} is skipped.')
    
    # generate_effective_set job
    if generate_effective_set:
      jobs_map["generate_effective_set_job"] = prepare_generate_effective_set_job(pipeline, environment_name, cluster_name)
    else:
       logger.info(f'Preparing of generate_effective_set job for {cluster_name}/{environment_name} is skipped.')
    
    ## git_commit job
    jobs_requiring_git_commit = ("env_build_job", "generate_effective_set_job", "env_inventory_generation_job")
    if any(job in jobs_map for job in jobs_requiring_git_commit) and not is_template_test:
      jobs_map["git_commit_job"] = prepare_git_commit_job(pipeline, env, environment_name, cluster_name)
    else:
      logger.info(f'Preparing of git commit job for {env} is skipped.')
    

    params['jobs_map'] = jobs_map
    params['job_sequence'] = job_sequence
    params['env_name'] = environment_name
    params['cluster_name'] = cluster_name
    params['full_env'] = env
    plugin_engine = PluginEngine(plugins_dir='/module/scripts/pipegene_plugins/per_env', params=params, pipeline_helper=pipeline_helper, pipeline=pipeline)
    plugin_engine.start()

    for job in job_sequence:
        if not job in jobs_map.keys():
            continue
        job_instance = jobs_map[job]
        sorted_pipeline.add_children(job_instance)
        job_instance.set_needs(find_predecessor_job(job, jobs_map, job_sequence))

    logger.info(f'----------------end processing for {env}---------------------')


  sorted_pipeline.write_yaml()
