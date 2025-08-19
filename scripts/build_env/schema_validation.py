from envgenehelper import *
import os

def normalize_env_specific_schema_white_list(white_list, namespace_names):
    resulting_white_list = copy.deepcopy(white_list)
    if not "namespaces" in resulting_white_list:
       resulting_white_list["namespaces"] = {}
    for nsName in namespace_names:
        if not nsName in resulting_white_list["namespaces"]:
            resulting_white_list["namespaces"][nsName] = {
                "deployParameters": {},
                "e2eParameters": {},
                "technicalConfigurationParameters": {},
                "applications": {}
            }
        else:
            normalize_item_params(resulting_white_list["namespaces"][nsName])
            if not "applications" in resulting_white_list["namespaces"][nsName]:
                resulting_white_list["namespaces"][nsName]["applications"] = {}
            else:
                for app in resulting_white_list["namespaces"][nsName]["applications"]:
                    normalize_item_params(resulting_white_list["namespaces"][nsName]["applications"][app])
    if not "cloud" in resulting_white_list:
        resulting_white_list["cloud"] = {}
    normalize_item_params(resulting_white_list["cloud"])
    if not "applications" in resulting_white_list["cloud"]:
        resulting_white_list["cloud"]["applications"] = {}
    else:
        for app in resulting_white_list["cloud"]:
            normalize_item_params(resulting_white_list["cloud"][app])
    return resulting_white_list

def normalize_item_params(item):
    if not "deployParameters" in item:
        item["deployParameters"] = {}
    if not "e2eParameters" in item:
        item["e2eParameters"] = {}
    if not "technicalConfigurationParameters" in item:
        item["technicalConfigurationParameters"] = {}

def checkByMandatoryList(params_map, mandatory_list):
    missing_keys = []

    def check_mandatory(item, mandatory, path=""):
        for key, value in mandatory.items():
            current_path = f"{path}.{key}" if path else key
            if key not in item:
                if path.endswith("applications"):
                    missing_keys.append(f"Application '{key}' is missing in '{path}'")
                else:
                    missing_keys.append(f"Mandatory key '{current_path}' is missing")
            elif isinstance(value, dict):
                if not isinstance(item[key], dict):
                    missing_keys.append(f"Key '{current_path}' should be a dictionary")
                else:
                    check_mandatory(item[key], value, current_path)

    for ns_name, ns_mandatory in mandatory_list.get("namespaces", {}).items():
        if ns_name in params_map["namespaces"]:
            check_mandatory(params_map["namespaces"][ns_name], ns_mandatory, f"namespaces.{ns_name}")
        else:
            missing_keys.append(f"Namespace '{ns_name}' is missing")

    if "cloud" in mandatory_list:
        check_mandatory(params_map.get("cloud", {}), mandatory_list["cloud"], "cloud")

    if missing_keys:
        return False, "\n".join(missing_keys)
    return True, ""

def checkSchemaValidationFailed(checkResult):
    if not isinstance(checkResult, dict):
        raise TypeError("Expected checkResult to be a dictionary.")
    return len(checkResult.get("extraKeys", [])) > 0 or len(checkResult.get("absentKeys", [])) > 0 or len(checkResult.get("checkMismatch", [])) > 0

def checkEnvSpecificParametersBySchema(env_dir, env_specific_params_map, namespace_names):
    envSpecificSchemaPath = f"{env_dir}/env-specific-schema.yml"
    if os.getenv("ENV_TEMPLATE_TEST") == 'true':
        logger.info(f"ENV_TEMPLATE_TEST is set to 'true'. Skipping environment specific parameters validation.")
        return
    else:
        if check_file_exists(envSpecificSchemaPath):
            envSpecificSchemaYaml = openYaml(envSpecificSchemaPath)
            if "envSpecific" in envSpecificSchemaYaml:
                logger.info(f"Env specific parameters will be checked by schema {envSpecificSchemaPath} ...")
                envSpecificParamsWhiteList = envSpecificSchemaYaml["envSpecific"]["whiteList"] if "whiteList" in envSpecificSchemaYaml["envSpecific"] else None
                envSpecificParamsBlackList = envSpecificSchemaYaml["envSpecific"]["blackList"] if "blackList" in envSpecificSchemaYaml["envSpecific"] else None
                envSpecificParamsMandatoryList = envSpecificSchemaYaml["envSpecific"].get("mandatoryList")
                logger.debug(f"White list: \n{dump_as_yaml_format(envSpecificParamsWhiteList)}")
                if envSpecificParamsWhiteList:
                    logger.info(f"Checking environment specific parameters by white list in schema {envSpecificSchemaPath} ...")
                    whiteList = normalize_env_specific_schema_white_list(envSpecificParamsWhiteList, namespace_names)
                    logger.debug(f"White list after normalization: \n{dump_as_yaml_format(whiteList)}")
                    checkResult = checkByWhiteList(env_specific_params_map, whiteList, isComplex=True)
                    if checkSchemaValidationFailed(checkResult):
                        logger.error(f"Environment specific parameters validation by white list failed:" + getSchemaValidationErrorMessage("environment specific parameters", checkResult))
                        raise ReferenceError(f"Environment specific parameters validation by white list failed. See logs above.")
                    else:
                        logger.info(f"Environment specific parameters validation by white list successfully passed.")
                if envSpecificParamsMandatoryList:
                    logger.info(f"Checking environment specific parameters by mandatory list in schema {envSpecificSchemaPath} ...")
                    mandatoryList = normalize_env_specific_schema_white_list(envSpecificParamsMandatoryList, namespace_names)
                    logger.debug(f"Mandatory list after normalization: \n{dump_as_yaml_format(mandatoryList)}")
                    checkResult, message = checkByMandatoryList(env_specific_params_map, mandatoryList)
                    if not checkResult:
                        logger.error(f"Environment specific parameters validation by mandatory list failed:\n{message}")
                        raise ReferenceError(f"Environment specific parameters validation by mandatory list failed. See logs above.")
                    else:
                        logger.info(f"Environment specific parameters validation by mandatory list successfully passed.")
                logger.debug(f"Black list: \n{dump_as_yaml_format(envSpecificParamsBlackList)}")
            else:
                logger.info(f"No env specific parameters schema found in {envSpecificSchemaPath}. Environment specific parameters validation by schema skipped...")
        else:
            logger.info("No env specific parameters schema found. Environment specific parameters validation by schema skipped...")

def checkCloudPassportBySchema(env_dir, cloudPassportFilePath):
    # checking passport for schema
    envSpecificSchemaPath = f"{env_dir}/env-specific-schema.yml"
    if os.getenv("ENV_TEMPLATE_TEST") == 'true':
        logger.info(f"ENV_TEMPLATE_TEST is set to 'true'. Skipping cloud passport validation.")
        return
    else:
        passportSchema = None
        passportMandatoryList = None
        if check_file_exists(envSpecificSchemaPath):
            envSpecificSchemaYaml = openYaml(envSpecificSchemaPath)
            if "cloudPassport" in envSpecificSchemaYaml:
                if "whiteList" in envSpecificSchemaYaml["cloudPassport"]:
                    logger.info(f"Cloud passport will be checked by schema {envSpecificSchemaPath} ...")
                    passportSchema = envSpecificSchemaYaml["cloudPassport"]["whiteList"]
                if "mandatoryList" in envSpecificSchemaYaml["cloudPassport"]:
                    logger.info(f"Cloud passport mandatory parameters will be checked by schema {envSpecificSchemaPath} ...")
                    passportMandatoryList = envSpecificSchemaYaml["cloudPassport"]["mandatoryList"]
                else:
                    logger.info(f"No whiteList or mandatoryList found for cloudPassport in {envSpecificSchemaPath}. Cloud passport validation by schema skipped...")
            else:
                logger.info(f"No cloudPassport block found in {envSpecificSchemaPath}. Cloud passport validation by schema skipped...")
        else:
            logger.info("No env specific schema file found. Cloud passport validation by schema skipped...")

        if passportSchema:
            if cloudPassportFilePath:
                cloudPassportYaml = openYaml(cloudPassportFilePath)
                checkResult = checkByWhiteList(cloudPassportYaml, passportSchema)
                if checkSchemaValidationFailed(checkResult):
                    logger.error(f"Cloud passport '{cloudPassportFilePath}' validation failed:" + getSchemaValidationErrorMessage("CloudPassport", checkResult))
                    raise ReferenceError(f"Cloud passport '{cloudPassportFilePath}' validation failed. See logs above.")
                else:
                    logger.info(f"Cloud passport {cloudPassportFilePath} validation by schema {envSpecificSchemaPath} successfully passed.")
            else:
                logger.error(f"No cloud passport definition found, but passport schema validation is defined in {envSpecificSchemaPath}. Please create file with cloud passport.")
                raise ReferenceError(f"No cloud passport definition found, but passport schema validation is defined in {envSpecificSchemaPath}. See logs above.")

        if passportMandatoryList:
            if cloudPassportFilePath:
                cloudPassportYaml = openYaml(cloudPassportFilePath)
                checkResult, message = checkByMandatoryList(cloudPassportYaml, passportMandatoryList)
                if not checkResult:
                    logger.error(f"Cloud passport '{cloudPassportFilePath}' validation by mandatory list failed:\n{message}")
                    raise ReferenceError(f"Cloud passport '{cloudPassportFilePath}' validation by mandatory list failed. See logs above.")
                else:
                    logger.info(f"Cloud passport {cloudPassportFilePath} validation by mandatory list from schema {envSpecificSchemaPath} successfully passed.")
            else:
                logger.error(f"No cloud passport definition found, but mandatory list validation is defined in {envSpecificSchemaPath}. Please create file with cloud passport.")
                raise ReferenceError(f"No cloud passport definition found, but mandatory list validation is defined in {envSpecificSchemaPath}. See logs above.")
        else:
            logger.info("No cloud passport mandatory list found. Cloud passport validation by mandatory list skipped...")
