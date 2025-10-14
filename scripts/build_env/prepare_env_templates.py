import os
from os import *

import ansible_runner
from envgenehelper import *

from main import merge_template_parameters

def prepare_env_templates()

    #Checking the workspace - GitLab or Github
    if os.getenv('CI_SERVER_NAME') == 'GitLab':
        base_dir = os.getenv('CI_PROJECT_DIR')
        branch = os.getenv('CI_PROJECT_NAME')
    elif os.getenv('GITHUB_ACTIONS') == 'true':
        base_dir = os.getenv('GITHUB_WORKSPACE')
        branch = os.getenv('GITHUB_REPOSITORY').split('/')[-1]
    else:
        raise EnvironmentError("Unsupported CI/CD environment")

    #Checking the info about project dir
    logger.info(f'Project path: {base_dir}')
    logger.info(f'Project branch: {branch}')

    #Deleting the existing folders
    delete_dir(f'{base_dir}/templates/env_templates')
    delete_dir(f'{base_dir}/templates/parameters')
    delete_dir(f'{base_dir}/templates/resource_profiles')

    #Creating the new ones
    check_dir_exist_and_create(f'{base_dir}/templates/env_templates')
    check_dir_exist_and_create(f'{base_dir}/templates/parameters')
    check_dir_exist_and_create(f'{base_dir}/templates/resource_profiles')

if __name__ == "__main__":
    prepare_env_templates()
