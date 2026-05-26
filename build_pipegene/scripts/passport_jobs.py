from gcip import TriggerJob, TriggerStrategy, WhenStatement
from envgenehelper import logger, openYaml
from integration_loader.loader import IntergrationConfigLoader
from pipeline_helper import job_instance
from os import getenv


def prepare_trigger_passport_job(pipeline, full_env_name):
    # trigger get_passport
    logger.info(f'prepare trigger_discovery_passport job for {full_env_name}')
    integration_path = f"{getenv('CI_PROJECT_DIR')}/configuration/integration.yml"
    integration_data = openYaml(integration_path, safe_load=True)
    integration = IntergrationConfigLoader(integration_data)
    discovery_branch_name = integration.cp_discovery['gitlab']['branch']
    discovery_project_name = integration.cp_discovery['gitlab']['project']
    discovery_trigger_job = {
        "name": f'trigger_discovery_passport.{full_env_name}',
        "stage": 'trigger',
        "project": discovery_project_name,
        "branch": discovery_branch_name,
    }
    trigger_job = TriggerJob(
        name=discovery_trigger_job["name"],
        stage=discovery_trigger_job["stage"],
        project=discovery_trigger_job["project"],
        branch=discovery_trigger_job["branch"],
        strategy=TriggerStrategy.DEPEND,
    )
    trigger_job.add_variables(ENV_NAME=full_env_name, GET_PASSPORT="true")
    pipeline.add_children(trigger_job)
    return trigger_job


def prepare_passport_job(pipeline, full_env_name, cluster_name):
    logger.info(f'prepare get_passport job for {full_env_name}')

    get_passport_params = {
        "name": f'get_passport.{full_env_name}',
        "image": '${envgen_image}',
        "stage": 'process_passport',
        "script": [
                    'python3 /cloud_passport/scripts/main.py --env_name "$ENV_NAME",',
                    "export env_name=$(echo $ENV_NAME | awk -F '/' '{print $NF}')",
                    'env_path=$(sudo find $CI_PROJECT_DIR/environments -type d -name "$env_name")',
                    'for path in $env_path; do if [ -d "$path/Credentials" ]; then sudo chmod ugo+rw $path/Credentials/*; fi;  done'
                  ],
    }
    get_passport_params['script'].append('/module/scripts/git_commit.sh')
    get_passport_vars = {
        "ENV_NAME": full_env_name,
        "CLUSTER_NAME": cluster_name,
    }
    get_passport_job = job_instance(params=get_passport_params, vars=get_passport_vars)
    base = "${CI_PROJECT_DIR}/environments"
    get_passport_job.artifacts.add_paths(f"{base}/{cluster_name}/cloud-passport")
    get_passport_job.artifacts.when = WhenStatement.ALWAYS
    pipeline.add_children(get_passport_job)
    return get_passport_job
