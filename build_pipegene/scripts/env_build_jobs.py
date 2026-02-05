from gcip import WhenStatement
from envgenehelper import logger
from pipeline_helper import job_instance


def prepare_env_build_job(pipeline, is_template_test, full_env, enviroment_name, cluster_name, group_id, artifact_id, tags):
    logger.info(f'prepare env_build job for {full_env}')

    script = [
        '/module/scripts/handle_certs.sh',
    ]
    script.append('cd /build_env; python3 /build_env/scripts/build_env/main.py')

    if is_template_test:
        script.append('env_name=$(cat "$CI_PROJECT_DIR/set_variable.txt")')
        script.append(
            'sed -i "s|\\\"envgeneNullValue\\\"|\\\"test_value\\\"|g" "$CI_PROJECT_DIR/environments/$env_name/Credentials/credentials.yml"')
        
    env_build_params = {
        "name": f'env_builder.{full_env}',
        "image": '${envgen_image}',
        "stage": 'env_builder',
        "script": script
    }

    env_build_vars = {
        "ENV_NAME": full_env,
        "FULL_ENV_NAME": full_env,
        "CLUSTER_NAME": cluster_name,
        "ENVIRONMENT_NAME": enviroment_name,
        "GROUP_ID": group_id,
        "ARTIFACT_ID": artifact_id,
        "ENV_TEMPLATE_TEST": "true" if is_template_test else "false",
        "INSTANCES_DIR": "${CI_PROJECT_DIR}/environments",
        "envgen_image": "$envgen_image",
        "envgen_args": " -vvv",
        "envgen_debug": "true",
        "module_config_default": "/module/templates/defaults.yaml",
        "GITLAB_RUNNER_TAG_NAME": tags,
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


def prepare_git_commit_job(pipeline, full_env, enviroment_name, cluster_name, deployment_session_id, tags,
                           credential_rotation_job: object = None):
    logger.info(f'prepare git_commit job for {full_env}.')
    logger.info(f'Deployment session id is {deployment_session_id}.')
    git_commit_params = {
        "name": f'git_commit.{full_env}',
        "image": '${envgen_image}',
        "stage": 'git_commit',
        "script": [
            '/module/scripts/handle_certs.sh',
            '/module/scripts/git_commit.sh',
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
        "module_config_default": "/module/templates/defaults.yaml",
        "GIT_STRATEGY": "none",
        "COMMIT_ENV": "true",
        "GITLAB_RUNNER_TAG_NAME": tags,
        "DEPLOY_SESSION_ID": deployment_session_id
    }
    git_commit_job = job_instance(params=git_commit_params, vars=git_commit_vars)
    git_commit_job.artifacts.add_paths("${CI_PROJECT_DIR}/environments/" + f"{full_env}")
    git_commit_job.artifacts.add_paths("${CI_PROJECT_DIR}/git_envs")
    git_commit_job.artifacts.add_paths('${CI_PROJECT_DIR}/sboms')
    git_commit_job.artifacts.when = WhenStatement.ALWAYS
    if (credential_rotation_job is not None):
        git_commit_job.add_needs(credential_rotation_job)
    pipeline.add_children(git_commit_job)
    return git_commit_job
