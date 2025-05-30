from envgenehelper import *
import copy
import re

# const
GENERATED_HEADER = "The contents of this file is generated from template artifact: %s.\nContents will be overwritten by next generation.\nPlease modify this contents only for development purposes or as workaround."
EFFECTIVE_SET_SCHEMA_PATH="schemas/effectiveset.schema.json"
EFFECTIVE_SET_MAPPING_SCHEMA_PATH="schemas/effectiveset_mapping.schema.json"

def get_app_name_from_app_vers(app_vers):
    logger.debug(f"Getting application name from {app_vers}")
    #getting the first element of splitting
    return app_vers.split(':')[0]

def get_application_dict_from_sd(env_name, env_dir):
    result = {}
    sd_path = f"{env_dir}/Inventory/solution-descriptor/sd.yaml"
    logger.info(f"Getting the list of applications for {env_name} from SD: {sd_path}")
    if not check_file_exists(sd_path):
        logger.error(f"File with solution descriptor does not exist in path: {sd_path}")
        raise ReferenceError(f"Can't generate effective set. Solution Descriptor file is not found. See logs above.")
    sd = openYaml(sd_path)
    for app in sd["applications"]:
        logger.info(f"Processin application from sd: \n{dump_as_yaml_format(app)}")
        app_vers = app["version"]
        app_name = get_app_name_from_app_vers(app_vers)
        if not "deployPostfix" in app:
            logger.error(f"Solution descriptor file should contain deploy postfix for each app. No deploy postfix found in {sd_path} for application {app_name}")
            raise ReferenceError(f"Solution descriptor version must be 2.1 or higher. See logs above")
        deploy_postfix = app["deployPostfix"]
        # if this deploy postfix doesn't exist yet, than adding it
        if not deploy_postfix in result:
            result[deploy_postfix] = []
        result[deploy_postfix].append(app_name)
    logger.info(f"List of applications got from SD {sd_path} is:\n{dump_as_yaml_format(result)}")
    return result

def get_and_check_env_creds_or_fail(env_dir):
    envCredPath = getEnvCredentialsPath(env_dir)
    envCreds = getEnvCredentials(env_dir)
    logger.info(f"Checking environment credentials values in file: {envCredPath}")
    errorMsg = ""
    for credId in envCreds:
        credValue = envCreds[credId]
        type = credValue["type"]
        data = credValue["data"]
        match type:
            case "usernamePassword":
                if data["username"] is None or data["password"] is None:
                    errorMsg += f"\ncredId: {credId} - username or password is empty"
            case "secret":
                if data["secret"] is None:
                    errorMsg += f"\ncredId: {credId} - secret is empty"
            case _:
                logger.warn(f"Unsupported credential type for {credId}: {type}. Skipping...")
    if errorMsg:
        logger.error(f"Error while validating credentials in file {envCredPath}: " + errorMsg)
        raise ReferenceError(f"Error while validating credentials in file {envCredPath}. See logs above.")
    return envCreds

def check_is_cred_and_update_cred_yaml(key: str, value: object, credentials_yaml: dict, env_creds: dict, comment: str) -> bool:
    if isinstance(value, str) and check_is_cred(key, value):
        expandedValue = expand_cred_macro_and_return_value(key, value, env_creds)
        store_value_to_yaml(credentials_yaml, key, expandedValue, comment)
        return True
    return False

def check_is_creds_list_and_expand_creds(key: str, value_list: list, result_yaml: dict, credentials_yaml: dict, env_creds: dict, comment: str) -> bool:
    result_list = []
    creds_list = []
    is_cred_found = False
    
    for idx, value in enumerate(value_list):
        if isinstance(value, dict):
            res_yaml = empty_yaml()
            cred_yaml = empty_yaml()
            if apply_parameters_from_dict_recursive(value, res_yaml, cred_yaml, env_creds, comment):
                is_cred_found = True
                # For dictionaries that contain credentials, we need to:
                # 1. Store the credentials in credentials_yaml
                # 2. Store the non-credential parts in result_yaml
                if res_yaml:  # If there are non-credential parts
                    result_list.append(res_yaml)
                creds_list.append(cred_yaml)
            else:
                # No credentials found, just add to result_yaml
                result_list.append(value)
        elif isinstance(value, list):
            nested_result_yaml = empty_yaml()
            nested_creds_yaml = empty_yaml()
            nested_key = "temp_key"  # Temporary key for nested processing
            
            if check_is_creds_list_and_expand_creds(nested_key, value, nested_result_yaml, nested_creds_yaml, env_creds, comment):
                is_cred_found = True
                if nested_key in nested_result_yaml:
                    result_list.append(nested_result_yaml[nested_key])
                if nested_key in nested_creds_yaml:
                    creds_list.append(nested_creds_yaml[nested_key])
            else:
                result_list.append(value)
        elif check_is_cred(idx, value):
            expandedValue = expand_cred_macro_and_return_value(idx, value, env_creds)
            is_cred_found = True
            creds_list.append(expandedValue)
        else:
            # Regular value, add to result_yaml
            result_list.append(value)
    
    # Always store the complete list with all nested fields in result_yaml
    # This ensures fields like secretName and insecureSkipVerify are preserved
    if result_list:
        store_value_to_yaml(result_yaml, key, result_list, comment)
    
    if is_cred_found:
        # For credentials, use the updatedValueList which contains all fields
        store_value_to_yaml(credentials_yaml, key, creds_list, comment)
    else:
        credentials_yaml.pop(key, None)
    return is_cred_found

def apply_parameters_from_dict_recursive(template_dict: dict, result_yaml: dict, credentials_yaml: dict, env_creds: dict, comment: str) -> bool:
    is_cred_found = False
    for key in template_dict:
        value = template_dict[key]
        if isinstance(value, dict):
            result_yaml[key] = empty_yaml()
            credentials_yaml[key] = empty_yaml()
            if apply_parameters_from_dict_recursive(value, result_yaml[key], credentials_yaml[key], env_creds, comment):
                is_cred_found = True
        elif isinstance(value, list):
            if not check_is_creds_list_and_expand_creds(key, value, result_yaml, credentials_yaml, env_creds, comment):
                store_value_to_yaml(result_yaml, key, value, comment)
            else:
                is_cred_found = True
        else:
            # adding key to effective set if it is not cred
            if not check_is_cred_and_update_cred_yaml(key, value, credentials_yaml, env_creds, comment):
                store_value_to_yaml(result_yaml, key, value, comment)
            else:
                is_cred_found = True
    return is_cred_found

def apply_parameters_from_template(resultYaml, templateYaml, parameters_tag, credentials_yaml, env_creds, comment) :
    if parameters_tag in templateYaml:
        templateResult = templateYaml[parameters_tag]
        apply_parameters_from_dict_recursive(templateResult, resultYaml, credentials_yaml, env_creds, comment)

def get_namespace_level_parameters(env_dir, namespace, parameters_tag, credentials_yaml, env_creds):
    logger.info(f"Processing {parameters_tag} for namespace {namespace} in {env_dir}")
    result = empty_yaml()
    tenant_yaml = openYaml(f"{env_dir}/tenant.yml")
    apply_parameters_from_template(result, tenant_yaml, parameters_tag, credentials_yaml, env_creds, "from tenant level")
    cloud_yaml = openYaml(f"{env_dir}/cloud.yml")
    apply_parameters_from_template(result, cloud_yaml, parameters_tag, credentials_yaml, env_creds, "from cloud level")
    namespace_yaml = openYaml(f"{env_dir}/Namespaces/{namespace}/namespace.yml")
    apply_parameters_from_template(result, namespace_yaml, parameters_tag, credentials_yaml, env_creds, "from namespace level")
    return result

def getNamespaceName(env_dir, namespacePostfix):
    namespace_yaml = openYaml(f"{env_dir}/Namespaces/{namespacePostfix}/namespace.yml")
    if "name" in namespace_yaml:
        return namespace_yaml["name"]
    else:
        return None

def generate_effective_set(env_name, env_dir, output_dir, apps_dict, env_creds):
    logger.info(f"Generating effective set for {env_name}. Environment directory is {env_dir}, output dir is {output_dir}")
    envDefinitionYaml = getEnvDefinition(env_dir)
    logger.info(getEnvDefinitionPath(env_dir))
    templateArtifactName = getTemplateArtifactName(envDefinitionYaml)
    generated_header_text = GENERATED_HEADER % templateArtifactName
    mapping_file = f"{output_dir}/mapping.yml"
    mapping_dict = {}
    for namespacePostfix in apps_dict:
        logger.info(f"Processing namespace postfix {namespacePostfix}")
        namespaceCredentialsYaml = empty_yaml()
        namespaceDeployParameters = get_namespace_level_parameters(env_dir, namespacePostfix, "deployParameters", namespaceCredentialsYaml, env_creds)
        namespaceTechnicalConfigurationParameters = get_namespace_level_parameters(env_dir, namespacePostfix, "technicalConfigurationParameters", namespaceCredentialsYaml, env_creds)
        mapping_dict = {**mapping_dict, getNamespaceName(env_dir, namespacePostfix): f"{env_dir[env_dir.find('/environments'):len(env_dir)]}/{namespacePostfix}"}
        for app_name in apps_dict[namespacePostfix]:
            logger.info(f"Processing application {app_name}")
            application_yaml_path = f"{env_dir}/Namespaces/{namespacePostfix}/Applications/{app_name}.yml"
            applicationCredentialsYaml = copy.deepcopy(namespaceCredentialsYaml)
            outputDeployParamsYaml = copy.deepcopy(namespaceDeployParameters)
            outputTechnicalConfigurationParamsYaml = copy.deepcopy(namespaceTechnicalConfigurationParameters)
            if check_file_exists(application_yaml_path):
                appYaml = openYaml(application_yaml_path)
                apply_parameters_from_template(outputDeployParamsYaml, appYaml, "deployParameters", applicationCredentialsYaml, env_creds, "from application level")
                apply_parameters_from_template(outputTechnicalConfigurationParamsYaml, appYaml, "technicalConfigurationParameters", applicationCredentialsYaml, env_creds, "from application level")
                logger.info(f"Application level parameters for {app_name} are merged from {application_yaml_path}.")
            else:
                logger.info(f"File with parameters for application {app_name} is not found in {application_yaml_path}. Skipping application level parameters...")
            # writing deploy parameters
            deploy_params_file = f"{output_dir}/{namespacePostfix}/{app_name}/deployment-parameters.yaml"
            writeYamlToFile(deploy_params_file, copy_yaml_and_remove_empty_dicts(outputDeployParamsYaml))
            beautifyYaml(deploy_params_file, schema_path=EFFECTIVE_SET_SCHEMA_PATH, header_text=generated_header_text)
            logger.info(f"Deployment parameters effective set stored in: {deploy_params_file}")
            # writing technical configuration parameters
            technical_params_file = f"{output_dir}/{namespacePostfix}/{app_name}/technical-configuration-parameters.yaml"
            writeYamlToFile(technical_params_file, copy_yaml_and_remove_empty_dicts(outputTechnicalConfigurationParamsYaml))
            beautifyYaml(technical_params_file, schema_path=EFFECTIVE_SET_SCHEMA_PATH, header_text=generated_header_text)
            logger.info(f"Technical configuration parameters effective set stored in: {technical_params_file}")
            # writing credentials
            creds_params_file = f"{output_dir}/{namespacePostfix}/{app_name}/credentials.yaml"
            writeYamlToFile(creds_params_file, copy_yaml_and_remove_empty_dicts(applicationCredentialsYaml))
            beautifyYaml(creds_params_file, schema_path=EFFECTIVE_SET_SCHEMA_PATH, header_text=generated_header_text)
            logger.info(f"Credentials effective set stored in: {creds_params_file}")
    if mapping_dict:
        mappingYaml = convert_dict_to_yaml(mapping_dict)
        writeYamlToFile(mapping_file, mappingYaml)
        beautifyYaml(mapping_file, schema_path=EFFECTIVE_SET_MAPPING_SCHEMA_PATH, header_text="<namespace-name>: <path to namespace folder>")
        logger.info(f"Mapping file is generated: {mapping_dict}, path: {mapping_file}")
    else:
        logger.error("Failed to generate mapping file")
