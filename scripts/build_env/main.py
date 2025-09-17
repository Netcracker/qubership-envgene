import argparse
import pathlib
import os
from build_env import build_env, process_additional_template_parameters
from create_credentials import create_credentials
from cloud_passport import update_env_definition_with_cloud_name
from resource_profiles import get_env_specific_resource_profiles
from envgenehelper import *
from envgenehelper.deployer import *
import ansible_runner

# const
INVENTORY_DIR_NAME = "Inventory"
ENV_DEFINITION_FILE_NAME = "env_definition.yml"
PARAMSET_SCHEMA = "schemas/paramset.schema.json"
CLOUD_SCHEMA = "schemas/cloud.schema.json"
NAMESPACE_SCHEMA = "schemas/namespace.schema.json"
ENV_SPECIFIC_RESOURCE_PROFILE_SCHEMA = "schemas/resource-profile.schema.json"

def clear_output_folder(dir) :
    delete_dir(f"{dir}/Namespaces")
    delete_dir(f"{dir}/Applications")
    delete_dir(f"{dir}/Profiles")


def prepare_folders_for_rendering(env_name, cluster_name, source_env_dir, templates_dir, render_dir, render_parameters_dir, render_profiles_dir, output_dir):
    # clearing folders
    delete_dir(render_dir)
    delete_dir(render_parameters_dir)
    delete_dir(render_profiles_dir)
    render_env_dir = f"{render_dir}/{env_name}"
    copy_path(f'{source_env_dir}/{INVENTORY_DIR_NAME}', f"{render_env_dir}/{INVENTORY_DIR_NAME}")
    # clearing instances dir
    clear_output_folder(f'{output_dir}/{cluster_name}/{env_name}')
    # copying parameters from templates and instances
    check_dir_exist_and_create(f'{render_parameters_dir}/from_template')
    copy_path(f'{templates_dir}/parameters', f'{render_parameters_dir}/from_template')
    cluster_path = getDirName(source_env_dir)
    instances_dir = getDirName(cluster_path)
    check_dir_exist_and_create(f'{render_parameters_dir}/from_instance')
    copy_path(f'{instances_dir}/parameters', render_parameters_dir)
    copy_path(f'{cluster_path}/parameters', render_parameters_dir)
    copy_path(f'{source_env_dir}/{INVENTORY_DIR_NAME}/parameters', f'{render_parameters_dir}/from_instance')
    # copying all template resource profiles
    copy_path(f'{templates_dir}/resource_profiles', render_profiles_dir)
    return render_env_dir


def pre_process_env_before_rendering(render_env_dir, source_env_dir, all_instances_dir):
    process_additional_template_parameters(render_env_dir, source_env_dir, all_instances_dir)
    update_env_definition_with_cloud_name(render_env_dir, source_env_dir, all_instances_dir)
    copy_path(f"{source_env_dir}/Credentials", f"{render_env_dir}")


def post_process_env_after_rendering(env_name, render_env_dir, source_env_dir, all_instances_dir, output_dir):
    check_dir_exist_and_create(output_dir)
    # copying results to output_dir
    env_instances_relative_dir = str(pathlib.Path(source_env_dir).relative_to(pathlib.Path(all_instances_dir)))
    logger.info(f"Relative path of {env_name} in instances dir is: {env_instances_relative_dir}")
    resulting_dir = f'{output_dir}/{env_instances_relative_dir}'
    check_dir_exist_and_create(resulting_dir)
    # overwrite env definition from instances, as it can mutate during generation
    copy_path(f'{source_env_dir}/{INVENTORY_DIR_NAME}/{ENV_DEFINITION_FILE_NAME}', f"{render_env_dir}/{INVENTORY_DIR_NAME}")
    # pushing all to output dir
    copy_path(f'{render_env_dir}/*', resulting_dir)
    return resulting_dir


def handle_template_override(render_dir):
    logger.info(f'start handle_template_override')
    logger.info('Starting handle_template_override')

    all_files = findAllFilesInDir(render_dir, "ml_override")

    for file in all_files:
        template_path = file.replace("_override", "")
        logger.info(f"Processing override file: {file}")

        yaml_to_override = openYaml(template_path)
        
        stream_before = io.StringIO()
        yaml.dump(yaml_to_override, stream_before)   # <-- yaml is your YAML() instance
        logger.info(f"YAML BEFORE override:\n{stream_before.getvalue()}")

        src = openYaml(file)
        merge_yaml_into_target(yaml_to_override, '', src)

        stream_after = io.StringIO()
        yaml.dump(yaml_to_override, stream_after)
        logger.info(f"YAML AFTER merge (before writeYamlToFile):\n{stream_after.getvalue()}")

        # First write
        writeYamlToFile(template_path, yaml_to_override)

        # Read file after first write to inspect formatting
        with open(template_path, 'r') as f:
            written_yaml = f.read()
        logger.info(f"YAML ON DISK after writeYamlToFile:\n{written_yaml}")

        template_path_stem = pathlib.Path(template_path).stem
        schema_path = ""
        if template_path_stem == 'cloud':
            schema_path = CLOUD_SCHEMA
        if template_path_stem == 'namespace':
            schema_path = NAMESPACE_SCHEMA

        # Beautify
        beautifyYaml(template_path, schema_path)

        with open(template_path, 'r') as f:
            beautified_yaml = f.read()
        logger.info(f"YAML ON DISK after beautifyYaml:\n{beautified_yaml}")

        deleteFile(file)


def build_environment(env_name, cluster_name, templates_dir, source_env_dir, all_instances_dir, output_dir, g_template_version, work_dir) :
    # defining folders that will be used during generation
    render_dir = getAbsPath('tmp/render')
    render_parameters_dir = getAbsPath('tmp/parameters_templates')
    render_profiles_dir = getAbsPath('tmp/resource_profiles')
    # preparing folders for generation
    render_env_dir = prepare_folders_for_rendering(env_name, cluster_name, source_env_dir, templates_dir, render_dir, render_parameters_dir, render_profiles_dir, output_dir)
    pre_process_env_before_rendering(render_env_dir, source_env_dir, all_instances_dir)
    # get deployer parameters
    cmdb_url, _, _ = get_deployer_config(f"{cluster_name}/{env_name}", work_dir, all_instances_dir, None, None, False)
    # perform rendering with Jinja2
    # Load environment definition and ensure auto-derived environmentName is available
    env_def_path = os.path.join(render_env_dir, "Inventory", "env_definition.yml")
    try:
        env_definition = openYaml(env_def_path) if os.path.exists(env_def_path) else {}
    except Exception as e:
        logger.warning(f"Failed to load environment definition from {env_def_path}: {str(e)}. Using empty definition.")
        env_definition = {}
    
    # Ensure environmentName is set (auto-derive if missing)
    # Handle missing inventory section
    if "inventory" not in env_definition:
        env_definition["inventory"] = {}
        logger.debug(f"Created missing inventory section in environment definition")
    
    if not env_definition["inventory"].get("environmentName"):
        env_definition["inventory"]["environmentName"] = env_name
        logger.info(f"Auto-derived environment name '{env_name}' for environment definition")
        # Write the updated definition back to file so Ansible can access it
        try:
            writeYamlToFile(env_def_path, env_definition)
            logger.debug(f"Successfully updated environment definition with auto-derived name: {env_def_path}")
        except Exception as e:
            logger.error(f"Failed to write updated environment definition to {env_def_path}: {str(e)}")
            # Continue execution - the in-memory definition still has the environmentName
    
    # Create current_env object with environmentName for Jinja2 template compatibility
    # This is used by templates that expect current_env.environmentName (like composite_structure.yml.j2)
    derived_env_name = env_definition.get("inventory", {}).get("environmentName", env_name)
    
    # Validate environment name
    if not derived_env_name or not isinstance(derived_env_name, str):
        logger.warning(f"Invalid environment name '{derived_env_name}', falling back to folder name '{env_name}'")
        derived_env_name = env_name
    
    current_env = {
        "name": env_name,  # Always use folder name for consistency
        "environmentName": derived_env_name  # Use derived or explicit name
    }
    
    logger.debug(f"Created environment context: name='{current_env['name']}', environmentName='{current_env['environmentName']}'")
    
    ansible_vars = {}
    ansible_vars["env"] = env_name  # Keep as string for file paths
    ansible_vars["current_env"] = current_env  # Object for Jinja2 templates that need current_env.environmentName
    ansible_vars["cluster_name"] = cluster_name
    ansible_vars["templates_dir"] = templates_dir
    ansible_vars["env_instances_dir"] = getAbsPath(render_env_dir)
    ansible_vars["render_dir"] = getAbsPath(render_dir)
    ansible_vars["render_parameters_dir"] = getAbsPath(render_parameters_dir)
    ansible_vars["template_version"] = g_template_version
    ansible_vars["cloud_passport_file_path"] = find_cloud_passport_definition(source_env_dir, all_instances_dir)
    ansible_vars["cmdb_url"] = cmdb_url
    ansible_vars["output_dir"] = output_dir
    logger.info(f"Starting rendering environment {env_name} with ansible. Input params are:\n{dump_as_yaml_format(ansible_vars)}")
    r = ansible_runner.run(playbook=getAbsPath('env-builder/main.yaml'), envvars=ansible_vars, verbosity=2)
    if (r.rc != 0):
        logger.error(f"Error during ansible execution. Result code is: {r.rc}. Status is: {r.status}")
        raise ReferenceError(f"Error during ansible execution. See logs above.")
    else:
        logger.info(f"Ansible execution status is: {r.status}. Stats is: {r.stats}")

    handle_template_override(render_dir)
    env_specific_resource_profile_map = get_env_specific_resource_profiles(source_env_dir, all_instances_dir, ENV_SPECIFIC_RESOURCE_PROFILE_SCHEMA)
    # building env
    handle_parameter_container(env_name, cluster_name, templates_dir, all_instances_dir, getAbsPath(render_dir))
    build_env(env_name, source_env_dir, render_parameters_dir, render_dir, render_profiles_dir, env_specific_resource_profile_map, all_instances_dir)
    resulting_dir = post_process_env_after_rendering(env_name, render_env_dir, source_env_dir, all_instances_dir, output_dir)
    validate_appregdefs(render_dir, env_name)

    return resulting_dir


def get_duplicate_names(param_files):
    file_names = list(map(extractNameFromFile, param_files))
    return set([x for x in file_names if file_names.count(x) > 1])


def validate_parameters(templates_dir, all_instances_dir, cluster_name=None, env_name=None):
    errors = []
    logger.info(f'Validate {templates_dir}/parameters dir')
    param_files = findAllYamlsInDir(f'{templates_dir}/parameters')

    names = get_duplicate_names(param_files)

    if len(names) > 0:
        errors.append(f'duplicate Paramset names {names}')

    errors = errors + validate_parameter_files(param_files)

    logger.info(f'Validate {all_instances_dir}/parameters dir')
    param_files = findAllYamlsInDir(f'{all_instances_dir}/parameters')
    # all_param_files = param_files
    errors = errors + validate_parameter_files(param_files)

    # Only validate the specific cluster if provided
    if cluster_name:
        if os.path.exists(f'{all_instances_dir}/{cluster_name}/parameters'):
            logger.info(f'Validate {all_instances_dir}/{cluster_name}/parameters')
            param_files = findAllYamlsInDir(f'{all_instances_dir}/{cluster_name}/parameters')
            errors = errors + validate_parameter_files(param_files)

            # Only validate the specific environment if provided
            if env_name:
                env_base_path = f'{all_instances_dir}/{cluster_name}/{env_name}'
                if os.path.exists(env_base_path):
                    # Now traverse through all subdirectories to find other parameter directories
                    for root, dirs, files in os.walk(env_base_path):
                        for dir_name in dirs:
                            if dir_name == "parameters":
                                param_path = os.path.join(root, dir_name)
                                logger.info(f'Validate {param_path}')
                                param_files = findAllYamlsInDir(param_path)
                                errors = errors + validate_parameter_files(param_files)
    else:
        # If no specific cluster/env provided, validate all (original behavior)
        sub_dirs = find_all_sub_dir(all_instances_dir)

        for sub_dir in next(sub_dirs)[1]:
            if sub_dir != "parameters":
                logger.info(f'Validate {all_instances_dir}/{sub_dir}/parameters')
                param_files = findAllYamlsInDir(f'{all_instances_dir}/{sub_dir}/parameters')
                errors = errors + validate_parameter_files(param_files)

                env_dirs = find_all_sub_dir(f'{all_instances_dir}/{sub_dir}')
                for env_dir in next(env_dirs)[1]:
                    if env_dir not in ["parameters", "cloud-passport"]:
                        logger.info(f'Validate {all_instances_dir}/{sub_dir}/{env_dir}/Inventory/parameters')
                        param_files = findAllYamlsInDir(f'{all_instances_dir}/{sub_dir}/{env_dir}/Inventory/parameters')
                        errors = errors + validate_parameter_files(param_files)

    # all_param_names = get_duplicate_names(all_param_files)
    # if len(all_param_names) > 0:
    #     errors.append(f'duplicate Env-specific Paramset names {all_param_names}')
    if len(errors) > 0:
        raise ReferenceError("\n" + "\n".join(errors))


def validate_parameter_files(param_files):
    errors = []
    for param_file_path in param_files:
        rel_param_file_path = os.path.relpath(param_file_path, os.getenv('CI_PROJECT_DIR'))
        try:
            validate_yaml_by_scheme_or_fail(param_file_path, PARAMSET_SCHEMA)
        except ValueError:
            errors.append(f'Parameter file at {rel_param_file_path} is invalid, look for details above')
        file_name = extractNameFromFile(param_file_path)
        param_file = openYaml(param_file_path)

        name = param_file["name"]
        if file_name != name:
            errors.append(f'Parameter "name" must be equal to filename without extension in file {rel_param_file_path}')
    return errors


def handle_parameter_container(env_name, cluster_name, templates_dir, all_instances_dir, render_dir):
    logger.info(f'start handle_parameter_container')
    env_dir = get_env_instances_dir(env_name, cluster_name, all_instances_dir)
    env_definition_yaml = getEnvDefinition(env_dir)
    template_name = env_definition_yaml["envTemplate"]["name"]
    logger.info(f'handle "{template_name}" template')
    template_file = findYamls(f'{templates_dir}/env_templates', f'{template_name}.y')

    for file in template_file:
        template_yml = openYaml(file)
        merge_template_parameters(template_yml, templates_dir, True)
        namespaces = template_yml["namespaces"]
        for namespace in namespaces:
            if "parameterContainer" in namespace:
                namespace_path_name = namespace["template_path"].split("/")[-1]
                namespace_path_name = namespace_path_name.split(".")[0]
                namespace_path = f'{render_dir}/{env_name}/Namespaces/{namespace_path_name}/namespace.yml'
                namespaces_yml = openYaml(namespace_path)
                deployment_parameters = namespaces_yml["deployParameters"]

                for parameterContainer in namespace["parameterContainer"]:
                    if parameterContainer["source"]["name"] == "":
                        source_parameters_path = findYamls(f'{templates_dir}/parameters_containers/',
                                                           f'source/{parameterContainer["override"]["name"]}.y')
                        source_file_name = extractNameFromFile(source_parameters_path[0])
                    else:
                        source_file_name = parameterContainer["source"]["name"].split(":")[0]
                        source_file_version = parameterContainer["source"]["name"].split(":")[1]
                        source_parameters_path = findYamls(f'{templates_dir}/parameters_containers/',f'source/{source_file_name}-{source_file_version}.y')
                    source_parameters_yaml = openYaml(source_parameters_path[0])

                    if "base" in source_parameters_yaml:
                        for key in source_parameters_yaml["base"]["parameters"]:
                            merge_dict_key_with_comment(key, deployment_parameters, "value", source_parameters_yaml["base"]["parameters"][key], f'# parameterContainer "{source_file_name}", base')

                    if "features" in parameterContainer:
                        for features in parameterContainer["features"]:
                            for key in source_parameters_yaml["features"][features]["parameters"]:
                                merge_dict_key_with_comment(key, deployment_parameters, "value", source_parameters_yaml["features"][features]["parameters"][key], f'# parameterContainer "{source_file_name}", feature "{features}"')

                writeYamlToFile(namespace_path, namespaces_yml)


def merge_template_parameters(template_yml, templates_dir, override_source=False):
    namespaces = template_yml["namespaces"]
    for namespace in namespaces:
        if "parameterContainer" in namespace:
            for parameterContainer in namespace["parameterContainer"]:
                logger.info(f'handle {parameterContainer["source"]["name"]}')
                if not ":" in parameterContainer["source"]["name"]:
                    override_parameters_path = findYamls(f'{templates_dir}/parameters_containers/',
                                                         f'override/{parameterContainer["override"]["name"]}.y')
                    if override_source:
                        copy_path(override_parameters_path[0],f'{templates_dir}/parameters_containers/source/{extractNameWithExtensionFromFile(override_parameters_path[0])}')
                    else:
                        copy_path(override_parameters_path[0],f'{templates_dir}/parameters_containers/merge/{extractNameWithExtensionFromFile(override_parameters_path[0])}')
                else:
                    source_file_name = parameterContainer["source"]["name"].split(":")[0]
                    source_file_version = parameterContainer["source"]["name"].split(":")[1]
                    source_parameters_path = findYamls(f'{templates_dir}/parameters_containers/',   f'source/{source_file_name}-{source_file_version}.y')
                    if "override" in parameterContainer:
                        override_parameters_path = findYamls(f'{templates_dir}/parameters_containers/',
                                                             f'override/{parameterContainer["override"]["name"]}.y')
                        logger.info(f'merge parameters from {override_parameters_path} to {source_parameters_path}')

                        yaml_to_override = openYaml(source_parameters_path)
                        src = openYaml(override_parameters_path)
                        merge_yaml_into_target(yaml_to_override, '', src)

                        source_parameters_path = source_parameters_path[0]
                        if not override_source:
                            merged_yaml['name'] = parameterContainer["override"]["artifact_name"]
                            source_parameters_path = source_parameters_path.replace("/source/", "/merge/")
                            source_parameters_path = source_parameters_path.replace(f'/{source_file_name}-{source_file_version}.', f'/{parameterContainer["override"]["artifact_name"]}.')

                        writeYamlToFile(source_parameters_path, yaml_to_override)

def validate_appregdefs(render_dir, env_name):
    appdef_dir = f"{render_dir}/{env_name}/AppDefs"
    regdef_dir = f"{render_dir}/{env_name}/RegDefs"

    if os.path.exists(appdef_dir):
        appdef_files = findAllYamlsInDir(appdef_dir)
        if not appdef_files:
            print(f"[INFO] No AppDef YAMLs found in {appdef_dir}")
        for file in appdef_files:
            print(f"[VALIDATING] AppDef file: {file}")
            validate_yaml_by_scheme_or_fail(file, "schemas/appdef.schema.json")

    if os.path.exists(regdef_dir):
        regdef_files = findAllYamlsInDir(regdef_dir)
        if not regdef_files:
            print(f"[INFO] No RegDef YAMLs found in {regdef_dir}")
        for file in regdef_files:
            print(f"[VALIDATING] RegDef file: {file}")
            validate_yaml_by_scheme_or_fail(file, "schemas/regdef.schema.json")


def render_environment(env_name, cluster_name, templates_dir, all_instances_dir, output_dir, g_template_version, work_dir):
    logger.info(f'env: {env_name}')
    logger.info(f'cluster_name: {cluster_name}')
    logger.info(f'templates_dir: {templates_dir}')
    logger.info(f'instances_dir: {all_instances_dir}')
    logger.info(f'output_dir: {output_dir}')
    logger.info(f'template_version: {g_template_version}')
    logger.info(f'work_dir: {work_dir}')
    # checking that directory is valid
    check_environment_is_valid_or_fail(env_name, cluster_name, all_instances_dir, validate_env_definition_by_schema=True)
    # searching for env directory in instances
    validate_parameters(templates_dir, all_instances_dir, cluster_name, env_name)
    env_dir = get_env_instances_dir(env_name, cluster_name, all_instances_dir)
    logger.info(f"Environment {env_name} directory is {env_dir}")
    # build env
    resulting_env_dir = build_environment(env_name, cluster_name, templates_dir, env_dir, all_instances_dir, output_dir, g_template_version, work_dir)
    # create credentials
    create_credentials(resulting_env_dir, env_dir, all_instances_dir)
    # update versions
    update_generated_versions(resulting_env_dir, BUILD_ENV_TAG, g_template_version)


if __name__ == "__main__":
    # Initialize parser
    parser = argparse.ArgumentParser()
    # Adding optional argument
    parser.add_argument("-e", "--env_name", help = "Environment name is not set with -e argument")
    parser.add_argument("-c", "--cluster", help = "Cluster name is not set with -c argument")
    parser.add_argument("-t", "--templates_dir", help="Templates directory is not set with -t argument", default="environment_templates")
    parser.add_argument("-i", "--instances_dir", help="Environment instances directory is not set with -i argument")
    parser.add_argument("-k", "--template_version", help="Artifact version is not set with -k argument")
    parser.add_argument("-o", "--output_dir", help="Output directory is not set with -o argument")
    # Read arguments from command line
    args = parser.parse_args()
    g_input_env_name = args.env_name
    g_input_cluster_name = args.cluster
    g_templates_dir = args.templates_dir
    g_all_instances_dir = args.instances_dir
    g_template_version = args.template_version
    g_output_dir = args.output_dir
    g_work_dir = get_parent_dir_for_dir(g_all_instances_dir)

    decrypt_all_cred_files_for_env()
    render_environment(g_input_env_name, g_input_cluster_name, g_templates_dir, g_all_instances_dir, g_output_dir, g_template_version, g_work_dir)
    encrypt_all_cred_files_for_env()
