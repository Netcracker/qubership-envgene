from gcip import WhenStatement
from envgenehelper import logger
from pipeline_helper import job_instance

def prepare_env_build_job(pipeline, is_template_test, env_template_version, full_env, enviroment_name, cluster_name, group_id, artifact_id,tags):
  logger.info(f'prepare env_build job for {full_env}')
  # prepare script
  script = [
     'if [ -d "${CI_PROJECT_DIR}/configuration/certs" ]; then cert_path=$(ls -A "${CI_PROJECT_DIR}/configuration/certs"); for path in $cert_path; do . /module/scripts/update_ca_cert.sh ${CI_PROJECT_DIR}/configuration/certs/$path; done; fi',
  ]
  # adding update template version
  if env_template_version and env_template_version != "" and not is_template_test:
    script.append('/module/scripts/prepare.sh "set_template_version.yaml"')
    script.append('/module/scripts/prepare.sh "build_env.yaml"')
  else:
    script.append('/module/scripts/prepare.sh "build_env.yaml"')

  if is_template_test:
     script.append("env_name=$(cat set_variable.txt)")
     script.append('sed -i "s|\\\"envgeneNullValue\\\"|\\\"test_value\\\"|g" "$CI_PROJECT_DIR/environments/$env_name/Credentials/credentials.yml"')
  else:
     script.append("export env_name=$(echo $ENV_NAME | awk -F '/' '{print $NF}')")

  script.extend([
      'env_path=$(sudo find $CI_PROJECT_DIR/environments -type d -name "$env_name")',
      'for path in $env_path; do if [ -d "$path/Credentials" ]; then sudo chmod ugo+rw $path/Credentials/*; fi;  done'
  ])
  env_build_params = {
      "name":   f'env_builder.{full_env}',
      "image":  '${envgen_image}',
      "stage":  'env_builder',
      "script": script,
  }

  env_build_vars = {
      "ENV_NAME": full_env,
      "CLUSTER_NAME": cluster_name,
      "ENVIRONMENT_NAME": enviroment_name,
      "ENV_TEMPLATE_VERSION": env_template_version,
      "GROUP_ID": group_id,
      "ARTIFACT_ID": artifact_id,
      "ENV_TEMPLATE_TEST": "true" if is_template_test else "false",
      "INSTANCES_DIR": "${CI_PROJECT_DIR}/environments",
      "envgen_image": "$envgen_image",
      "envgen_args": " -vvv",
      "envgen_debug": "true",
      "module_ansible_dir": "/module/ansible",
      "module_inventory": "${CI_PROJECT_DIR}/configuration/inventory.yaml",
      "module_ansible_cfg": "/module/ansible/ansible.cfg",
      "module_config_default": "/module/templates/defaults.yaml",
      "GITLAB_RUNNER_TAG_NAME" : tags
  }

  env_build_job = job_instance(params=env_build_params, vars=env_build_vars)
  if is_template_test:
    env_build_job.artifacts.add_paths("${CI_PROJECT_DIR}/environments")
    env_build_job.artifacts.add_paths("${CI_PROJECT_DIR}/set_variable.txt")
  else:
    env_build_job.artifacts.add_paths("${CI_PROJECT_DIR}/environments/" + f"{full_env}")
    env_build_job.artifacts.add_paths("${CI_PROJECT_DIR}/configuration")
    env_build_job.artifacts.add_paths("${CI_PROJECT_DIR}/tmp")
  env_build_job.artifacts.when = WhenStatement.ALWAYS
  pipeline.add_children(env_build_job)
  return env_build_job

def prepare_generate_effective_set_job(pipeline, environment_name, cluster_name,tags):
  logger.info(f'Prepare generate_effective_set job for {cluster_name}/{environment_name}.')
  generate_effective_set_params = {
    "name":   f'generate_effective_set.{cluster_name}/{environment_name}',
    "image":  '${effective_set_generator_image}',
    "stage":  'generate_effective_set',
    "script": [ f'/module/scripts/prepare.sh "generate_effective_set.yaml"',
                "export env_name=$(echo $ENV_NAME | awk -F '/' '{print $NF}')",
                'env_path=$(sudo find $CI_PROJECT_DIR/environments -type d -name "$env_name")',
                'for path in $env_path; do if [ -d "$path/Credentials" ]; then sudo chmod ugo+rw $path/Credentials/*; fi;  done'
              ],
  }

  generate_effective_set_vars = {
    "CLUSTER_NAME": cluster_name,
    "ENVIRONMENT_NAME": environment_name,
    "INSTANCES_DIR": "${CI_PROJECT_DIR}/environments",
    "effective_set_generator_image": "$effective_set_generator_image",
    "envgen_args": " -vv",
    "envgen_debug": "true",
    "module_ansible_dir": "/module/ansible",
    "module_inventory": "${CI_PROJECT_DIR}/configuration/inventory.yaml",
    "module_ansible_cfg": "/module/ansible/ansible.cfg",
    "module_config_default": "/module/templates/defaults.yaml",
    "GITLAB_RUNNER_TAG_NAME" : tags
  }
  generate_effective_set_job = job_instance(params=generate_effective_set_params, vars=generate_effective_set_vars)
  generate_effective_set_job.artifacts.add_paths("${CI_PROJECT_DIR}/environments/" + f"{cluster_name}/{environment_name}")
  generate_effective_set_job.artifacts.when = WhenStatement.ALWAYS
  pipeline.add_children(generate_effective_set_job)
  return generate_effective_set_job


def prepare_git_commit_job(pipeline, full_env, enviroment_name, cluster_name, credential_rotation_job: None,tags):
  logger.info(f'prepare git_commit job for {full_env}.')
  git_commit_params = {
      "name":   f'git_commit.{full_env}',
      "image":  '${envgen_image}',
      "stage":  'git_commit',
      "script": [ 'if [ -d "${CI_PROJECT_DIR}/configuration/certs" ]; then cert_path=$(ls -A "${CI_PROJECT_DIR}/configuration/certs"); for path in $cert_path; do . /module/scripts/update_ca_cert.sh ${CI_PROJECT_DIR}/configuration/certs/$path; done; fi',
                  f'/module/scripts/prepare.sh "git_commit.yaml"',
                  "export env_name=$(echo $ENV_NAME | awk -F '/' '{print $NF}')",
                  'env_path=$(sudo find $CI_PROJECT_DIR/environments -type d -name "$env_name")',
                  'for path in $env_path; do if [ -d "$path/Credentials" ]; then sudo chmod ugo+rw $path/Credentials/*; fi;  done',
                  'cp -rf $CI_PROJECT_DIR/environments $CI_PROJECT_DIR/git_envs',
              ],
  }

  git_commit_vars = {
      "ENV_NAME": full_env,
      "CLUSTER_NAME": cluster_name,
      "ENVIRONMENT_NAME": enviroment_name,
      "envgen_image": "$envgen_image",
      "envgen_args": " -vv",
      "envgen_debug": "true",
      "module_ansible_dir": "/module/ansible",
      "module_inventory": "${CI_PROJECT_DIR}/configuration/inventory.yaml",
      "module_ansible_cfg": "/module/ansible/ansible.cfg",
      "module_config_default": "/module/templates/defaults.yaml",
      "GIT_STRATEGY": "none",
      "COMMIT_ENV": "true",
      "GITLAB_RUNNER_TAG_NAME" : tags
  }
  git_commit_job = job_instance(params=git_commit_params, vars=git_commit_vars)
  git_commit_job.artifacts.add_paths("${CI_PROJECT_DIR}/environments/" + f"{full_env}")
  git_commit_job.artifacts.add_paths("${CI_PROJECT_DIR}/git_envs")
  git_commit_job.artifacts.when = WhenStatement.ALWAYS
  if (credential_rotation_job is not None):
    git_commit_job.add_needs(credential_rotation_job)
  pipeline.add_children(git_commit_job)
  return git_commit_job

