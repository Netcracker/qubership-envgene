import click
from envgenehelper import logger, get_env_instances_dir, check_dir_exists, delete_dir, check_dir_exist_and_create, encrypt_all_cred_files_for_env, decrypt_all_cred_files_for_env, openYaml
from os import getenv
from effective_set_generator import generate_effective_set, get_application_dict_from_sd, get_and_check_env_creds_or_fail

EFFECTIVE_SET_FOLDER = "effective-set"

@click.group(chain=True)
def effective_set_generator():
    pass

@effective_set_generator.command("generate")
@click.option('--cluster_name', '-c', 'cluster_name', default = getenv('CLUSTER_NAME', ''), help="Cluster (CLUSTER_NAME)")
@click.option('--environment_name', '-e', 'environment_name', default = getenv('ENVIRONMENT_NAME', ''), help="Environment name (ENVIRONMENT_NAME)")
@click.option('--instances_dir', '-i', 'instances_dir', default = getenv('INSTANCES_DIR', 'instance_dir'), help="Directory with inventory for all environments")
def generate(cluster_name ,environment_name, instances_dir):
    logger.info(f"Starting to generate effective set. ENVIRONMENT_NAME: {environment_name}. CLUSTER_NAME: {cluster_name} INSTANCES_DIR: {instances_dir}")
    generate_effective_set_for_env(cluster_name, environment_name, instances_dir)


def generate_effective_set_for_env(cluster_name ,environment_name, instances_dir):
    decrypt_all_cred_files_for_env()
    full_env_name = f"{cluster_name}/{environment_name}"
    env_dir = get_env_instances_dir(environment_name, cluster_name, instances_dir)
    logger.info(f"Env dir is: {env_dir}")
    env_creds = get_and_check_env_creds_or_fail(env_dir)
    # clearing effective set folder in env env
    output_dir = f"{env_dir}/{EFFECTIVE_SET_FOLDER}"
    if check_dir_exists(output_dir):
        logger.info(f"Clearing folder for effective set calculation: {output_dir}")
        delete_dir(output_dir)
    check_dir_exist_and_create(output_dir)
    # get list of apps from solution descriptor
    apps_dict = get_application_dict_from_sd(full_env_name, env_dir)
    # generating effective set
    generate_effective_set(full_env_name, env_dir, output_dir, apps_dict, env_creds)
    encrypt_all_cred_files_for_env()

if __name__ == "__main__":
    effective_set_generator()

