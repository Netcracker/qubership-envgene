from gcip import WhenStatement
from envgenehelper import logger
from pipeline_helper import job_instance

def prepare_credential_rotation_job(pipeline, full_env, environment_name, cluster_name):
  logger.info(f'Prepare credential_rotation_job job for {full_env}.')
  credential_rotation_params = {
    "name":   f'credential_rotation.{full_env}',
    "image":  '${envgen_image}',
    "stage":  'credential_rotation',
    "script": [
            "python3 /module/creds_rotation_scripts/creds_rotation_handler.py",
        ],
  }

  credential_rotation_vars = {
    "CLUSTER_NAME": cluster_name,
    "ENV_NAME": environment_name,
    "envgen_args": " -vv",
    "envgen_debug": "true"
  }
  credential_rotation_job = job_instance(params=credential_rotation_params, vars=credential_rotation_vars)
  credential_rotation_job.artifacts.add_paths("${CI_PROJECT_DIR}/environments")
  credential_rotation_job.artifacts.add_paths("${CI_PROJECT_DIR}/affected-sensitive-parameters.yaml")
  credential_rotation_job.artifacts.when = WhenStatement.ALWAYS
  pipeline.add_children(credential_rotation_job)
  return credential_rotation_job
