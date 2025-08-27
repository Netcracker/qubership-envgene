import ansible_runner
from envgenehelper import *

from main import merge_template_parameters


def build_ci_jobs():

    if os.getenv('CI_SERVER_NAME') == 'GitLab':
        base_dir = os.getenv('CI_PROJECT_DIR')
        branch = os.getenv('CI_PROJECT_NAME')
    elif os.getenv('GITHUB_ACTIONS') == 'true':
        base_dir = os.getenv('GITHUB_WORKSPACE')
        branch = os.getenv('GITHUB_REPOSITORY').split('/')[-1]
    else:
        raise EnvironmentError("Unsupported CI/CD environment")

    logger.info(f'path {base_dir}')

    parameter_set = set()

    all_templates = findAllYamlsInDir(f'{base_dir}/templates/env_templates')
    logger.info(f'all_templates {all_templates}')
    artifact_definition = openYaml('/build_env/scripts/build_template/template/artifact_definition.yml')

    delete_dir(f'{base_dir}/templates/parameters_containers/source')
    delete_dir(f'{base_dir}/templates/parameters_containers/merge')
    check_dir_exist_and_create(f'{base_dir}/templates/parameters_containers/source')
    check_dir_exist_and_create(f'{base_dir}/templates/parameters_containers/merge')

    for template_path in all_templates:
        template_yml = openYaml(template_path)
        logger.info(f'template_yml {template_yml}')
        if "namespaces" in template_yml:
            download_source_files(artifact_definition, base_dir, parameter_set, template_yml)
            merge_template_parameters(template_yml, f'{base_dir}/templates')
        else:
            logger.warning(f'No namespaces found in template: {template_path}')

    all_parameters = findAllYamlsInDir(f'{base_dir}/templates/parameters_containers/merge')
    logger.info(f'all_parameters {all_parameters}')
    all_parameters = sorted(set(all_parameters))

    delete_dir(f'{base_dir}/gitlab-ci/prefix_build')
    check_dir_exist_and_create(f'{base_dir}/gitlab-ci/prefix_build')
    copy_path('/build_env/scripts/build_template/template/parameters_containers_empty.yaml', f'{base_dir}/gitlab-ci/parameters_containers.yaml')

    build_sh = openFileAsString('/build_env/scripts/build_template/template/build.sh')
    description = openFileAsString('/build_env/scripts/build_template/template/description.yaml')
    parameters_containers = openFileAsString('/build_env/scripts/build_template/template/parameters_containers.yaml')

    logger.info(f"files = {all_parameters}")

    for parameter_path in all_parameters:
        logger.info(f'parameter_path {parameter_path}')
        parameter_name = extractNameFromFile(parameter_path)
        check_dir_exist_and_create(f'{base_dir}/gitlab-ci/prefix_build/{parameter_name}')
        copy_path(parameter_path, f'{base_dir}/gitlab-ci/prefix_build/{parameter_name}/{parameter_name}.yml')
        new_build_sh = build_sh.replace("@paramater-name", f'{parameter_name}')
        writeToFile(f'{base_dir}/gitlab-ci/prefix_build/{parameter_name}/build.sh', new_build_sh)
        new_description = description.replace("@paramater-name", f'{parameter_name}')
        new_description = new_description.replace("@branch-name", f'{branch}')
        writeToFile(f'{base_dir}/gitlab-ci/prefix_build/{parameter_name}/description.yaml', new_description)

        new_parameters_containers = parameters_containers.replace("@paramater-name", f'{parameter_name}')

        jobs = openFileAsString(f'{base_dir}/gitlab-ci/parameters_containers.yaml')
        writeToFile(f'{base_dir}/gitlab-ci/parameters_containers.yaml', jobs + new_parameters_containers + '\n\n')

    delete_dir(f'{base_dir}/templates/parameters_containers/merge')


def download_source_files(artifact_definition, base_dir, parameter_set, template_yml):
    namespaces = template_yml["namespaces"]
    for namespace in namespaces:
        if "parameterContainer" in namespace:
            for parameterContainer in namespace["parameterContainer"]:
                source_name = parameterContainer["source"]["name"]
                if not source_name in parameter_set:
                    parameter_set.add(source_name)
                    logger.info(f'source_name = {source_name}')
                    ansible_vars = {}

                    if ":" in source_name:
                        ansible_vars["version"] = source_name.split(":")[1]
                        artifact_definition['artifactId'] = source_name.split(":")[0]
                        ansible_vars["artifact_definition"] = artifact_definition

                        logger.info(f"Starting download parameterContainer {source_name}")
                        r = ansible_runner.run(playbook='/module/ansible/download_parameters.yaml',envvars=ansible_vars, verbosity=2)
                        if (r.rc != 0):
                            logger.error(
                                f"Error during ansible execution. Result code is: {r.rc}. Status is: {r.status}")
                            raise ReferenceError(f"Error during ansible execution. See logs above.")
                        else:
                            logger.info(f"Ansible execution status is: {r.status}. Stats is: {r.stats}")

                        addHeaderToYaml(f'{base_dir}/templates/parameters_containers/source/{artifact_definition["artifactId"]}.yml', f'# The contents of this file is generated from Parameter Container artifact: {source_name}\n# Contents will be overwritten by next generation.\n# Please do not modify this content')

                        move_path(
                            f'{base_dir}/templates/parameters_containers/source/{artifact_definition["artifactId"]}.yml',
                            f'{base_dir}/templates/parameters_containers/source/{artifact_definition["artifactId"]}-{ansible_vars["version"]}.yml')


if __name__ == "__main__":
    build_ci_jobs()
