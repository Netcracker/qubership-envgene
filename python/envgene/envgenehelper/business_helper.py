from dataclasses import dataclass, field
import re
from os import getenv
from pathlib import Path
from typing import overload

from ruyaml import CommentedMap

from .collections_helper import merge_lists
from .yaml_helper import findYamls, openYaml, yaml, writeYamlToFile, store_value_to_yaml, \
    validate_yaml_by_scheme_or_fail
from .json_helper import findJsons
from .file_helper import getAbsPath, extractNameFromFile, check_file_exists, check_dir_exists, getParentDirName, \
    extractNameFromDir
from .collections_helper import dump_as_yaml_format
from .logger import logger
from ruyaml.scalarstring import DoubleQuotedScalarString
from pathlib import Path

# const
INVENTORY_DIR_NAME = "Inventory"
ENV_DEFINITION_FILE_NAME = "env_definition.yml"
CREDENTIALS_DIR_NAME = "Credentials"
CREDENTIALS_FILE_NAME = "credentials.yml"
BUILD_ENV_TAG = "BUILD_ENV"
CMDB_IMPORT_TAG = "CMDB_IMPORT"
DEFAULT_PASSPORT_NAME = "passport"
DEFAULT_PASSPORT_DIR_NAME = "cloud-passport"
INV_GEN_CREDS_PATH = "Inventory/credentials/inventory_generation_creds.yml"


def find_env_instances_dir(env_name, instances_dir):
    logger.debug(f"Searching for directory {env_name} in {instances_dir}")
    dirPointer = Path(instances_dir)
    dirList = list(dirPointer.rglob(f"{env_name}/Inventory"))
    logger.debug(f"Search results: {dump_as_yaml_format(dirList)}")
    if len(dirList) > 1:
        logger.error(f"Duplicate directories for {env_name} found in {instances_dir}: \n\t" + ",\n\t".join(
            str(x) for x in dirList))
        raise ReferenceError(
            f"Duplicate directories for {env_name} found. Please specify env name with environment folder e.g. sdp-dev/{env_name}.")
    for dir in dirList:
        if dir.is_dir():
            return str(dir.parent)
    logger.error(f"Directory for {env_name} is not found in {instances_dir}")
    raise ReferenceError(f"Can't find directory for {env_name}")

@overload
def getenv_and_log(name: str) -> None | str: ...
@overload
def getenv_and_log(name: str, default: str) -> str: ...

def getenv_and_log(name, *args, **kwargs):
    var = getenv(name, *args, **kwargs)
    logger.info(f"{name}: {var}")
    return var

def getenv_with_error(var_name):
    var = getenv(var_name)
    if not var:
        raise ValueError(f'Required value was not given and is not set in environment as {var_name}')
    logger.debug(f"{var_name}: {var}")
    return var

def get_env_instances_dir(environment_name, cluster_name, instances_dir):
    return f"{instances_dir}/{cluster_name}/{environment_name}"

def get_current_env_dir_from_env_vars() -> Path:
    instances_dir = getenv_with_error('CI_PROJECT_DIR')
    env_name = getenv_with_error('FULL_ENV_NAME')
    env_dir_path = Path(f"{instances_dir}/environments/{env_name}")
    logger.debug(env_dir_path)
    return env_dir_path

def check_environment_is_valid_or_fail(environment_name, cluster_name, instances_dir, skip_env_definition_check=False,
                                       validate_env_definition_by_schema=False, schemas_dir=""):
    env_dir = get_env_instances_dir(environment_name, cluster_name, instances_dir)
    # check that environment directory exists
    if not check_dir_exists(env_dir):
        logger.error(
            f"Directory for environment '{cluster_name}/{environment_name}' does not exist in: {instances_dir}. We tried to find it in the following path: {env_dir}")
        raise ReferenceError(f"Validation of environment folder '{env_dir}' failed. See logs above.")
    # check that env_definition yaml exists
    env_definition_path = f"{env_dir}/Inventory/env_definition.yml"
    if skip_env_definition_check:
        logger.info("Validation of env_definition is skipped")
        logger.info(f"Environment {cluster_name}/{environment_name} validation is succesful")
        return
    if not check_file_exists(env_definition_path):
        logger.error(
            f"Env_definition.yml is not found in path '{env_definition_path}' for environment {cluster_name}/{environment_name}. Please specify correct env_definition.yml in '{cluster_name}/{environment_name}/Inventory' folder")
        raise ReferenceError(f"Validation of environment folder '{env_dir}' failed. See logs above.")
    if validate_env_definition_by_schema:
        check_env_definition_is_valid_or_fail(env_definition_path, schemas_dir)
    logger.info(f"Environment {cluster_name}/{environment_name} validation is succesful")


def check_env_definition_is_valid_or_fail(env_definition_path, schemas_dir):
    schemaPath = f"{schemas_dir}/env-definition.schema.json" if schemas_dir else "schemas/env-definition.schema.json"
    try:
        validate_yaml_by_scheme_or_fail(env_definition_path, schemaPath)
    except ValueError:
        raise ValueError(f"Validation of env_definition in '{env_definition_path} failed. See logs above'") from None


def findResourcesBottomTop(sourceDir, stopParentDir, pattern, notPattern="", additionalRegexpPattern="",
                           additionalRegexpNotPattern="", searchJsons=False):
    result = []
    foundMap = {}
    # checking that stopParentDir is real parent of sourceDir or we will have infinite loop
    stopParentDirAbs = getAbsPath(stopParentDir)
    sourceDirAbs = getAbsPath(sourceDir)
    parentPath = Path(stopParentDirAbs)
    sourcePath = Path(sourceDirAbs)
    if parentPath not in sourcePath.parents:
        logger.error(f"Error while finding resources. {stopParentDirAbs} is not in parents of {sourceDirAbs}.")
        raise ReferenceError(
            f"Error while finding resources. {stopParentDirAbs} is not in parents of {sourceDirAbs}. See logs above.")
    return __findResourcesBottomTop__(sourceDir, stopParentDir, pattern, notPattern, additionalRegexpPattern,
                                      additionalRegexpNotPattern, searchJsons, result, foundMap)


def __findResourcesBottomTop__(sourceDir, stopParentDir, pattern, notPattern, additionalRegexpPattern,
                               additionalRegexpNotPattern, searchJsons, result, foundMap):
    logger.debug(
        f"Searching files in {sourceDir}. Pattern:{pattern}\nNotPattern:{notPattern}\nResult:\n{dump_as_yaml_format(result)}. foundMap:\n{foundMap}")
    findResults = findYamls(sourceDir, pattern, notPattern, additionalRegexpPattern, additionalRegexpNotPattern)
    if searchJsons:
        findResults = merge_lists(findResults, findJsons(sourceDir, pattern, notPattern, additionalRegexpPattern,
                                                         additionalRegexpNotPattern))
    for foundFile in findResults:
        fileName = extractNameFromFile(foundFile)
        if fileName not in foundMap:
            foundMap[fileName] = foundFile
            if len(findResults) == 1:
                yamlPath = findResults[0]
                result.append(yamlPath)
                logger.debug(f"Resource added from: {yamlPath}")
            elif len(findResults) > 1:
                logger.error(
                    f"Duplicate resource file with pattern {pattern} found in {sourceDir}: \n\t" + ",\n\t".join(
                        str(x) for x in findResults))
                raise ReferenceError(f"Duplicate resource file with pattern {pattern} found. See logs above.")
    if getAbsPath(sourceDir) == getAbsPath(stopParentDir):
        logger.debug(f"Reached parent dir {stopParentDir}. Stopping.")
        return result
    else:
        parentEnvDirPath = str(Path(sourceDir).parent)
        return __findResourcesBottomTop__(parentEnvDirPath, stopParentDir, pattern, notPattern, additionalRegexpPattern,
                                          additionalRegexpNotPattern, searchJsons, result, foundMap)


def getTemplateArtifactName(env_definition_yaml):
    if "artifact" in env_definition_yaml["envTemplate"]:
        artifact = env_definition_yaml["envTemplate"]["artifact"]
        return artifact.split(":")[0]
    else:
        gav = env_definition_yaml["envTemplate"]["templateArtifact"]["artifact"]
        return gav["artifact_id"]


def getEnvDefinition(env_dir):
    env_definition_path = getEnvDefinitionPath(env_dir)
    if not check_file_exists(env_definition_path):
        raise ReferenceError(f"Environment definition for env {env_dir} is not found in {env_definition_path}")
    return openYaml(env_definition_path)


def getEnvDefinitionPath(env_dir) -> str:
    return str(Path(env_dir) / INVENTORY_DIR_NAME / ENV_DEFINITION_FILE_NAME)


def getEnvCredentials(env_dir):
    envCredentialsPath = getEnvCredentialsPath(env_dir)
    if not check_file_exists(envCredentialsPath):
        logger.error(f"Credentials for env {env_dir} are not found in {envCredentialsPath}")
        raise ReferenceError(f"Credentials for env {env_dir} are not found. See logs above.")
    credYaml = openYaml(envCredentialsPath)
    return credYaml


def getEnvCredentialsPath(env_dir):
    return f"{env_dir}/{CREDENTIALS_DIR_NAME}/{CREDENTIALS_FILE_NAME}"


def getAppDefinitionPath(base_path, template_name):
    path_without_extension = f"{base_path}/configuration/artifact_definitions/{template_name}"
    yaml_path = f"{path_without_extension}.yaml"
    yml_path = f"{path_without_extension}.yml"
    if check_file_exists(yml_path):
        return yml_path
    else:
        return yaml_path


def getTemplateVersionFromEnvDefinition(env_definition_yaml):
    return env_definition_yaml["generatedVersions"]["generateEnvironmentLatestVersion"]


def getTemplateLatestSnapshotVersion(env_definition_yaml):
    return env_definition_yaml["env_template_latest_snapshot_version"]


def update_generated_versions(env_dir, stage_tag, template_version=""):
    comment = "This value is automatically generated during job run."
    env_definition_yaml = getEnvDefinition(env_dir)
    if "generatedVersions" not in env_definition_yaml:
        versionsYaml = yaml.load("{}")
        env_definition_yaml["generatedVersions"] = versionsYaml
    else:
        versionsYaml = env_definition_yaml["generatedVersions"]
    if "envTemplate" in env_definition_yaml and "artifact" in env_definition_yaml["envTemplate"]:
        artifact = env_definition_yaml["envTemplate"]["artifact"]
        artifact_id = artifact.split(":")[0]
    else:
        artifact_id = None
    if stage_tag == BUILD_ENV_TAG:
        version = DoubleQuotedScalarString(template_version)
        if isinstance(version, str) and not isinstance(version, DoubleQuotedScalarString):
            version = DoubleQuotedScalarString(version)
        if artifact_id and artifact_id.strip():
            version = DoubleQuotedScalarString(f"{artifact_id}:{version}")
        store_value_to_yaml(versionsYaml, "generateEnvironmentLatestVersion", version, comment)
    elif stage_tag == CMDB_IMPORT_TAG and "generateEnvironmentLatestVersion" in versionsYaml:
        version = versionsYaml["generateEnvironmentLatestVersion"]
        store_value_to_yaml(versionsYaml, "cmdbImportLatestVersion", version, comment)
    else:
        version = "UNDEFINED"
    env_definition_path = getEnvDefinitionPath(env_dir)
    writeYamlToFile(env_definition_path, env_definition_yaml)
    logger.info(f"Generated version {version} updated for stage tag {stage_tag} in environment {env_definition_path}")


def extract_namespace_from_application_path(app_yaml_path):
    file_path_posix = Path(app_yaml_path).as_posix()
    pattern = r'^.+/Namespaces/(.+)/Applications/.+$'
    return re.sub(pattern, r'\1', file_path_posix)


def extract_namespace_from_namespace_path(namespace_yaml_path):
    file_path_posix = Path(namespace_yaml_path).as_posix()
    pattern = r'^.+/Namespaces/(.+)/.+$'
    return re.sub(pattern, r'\1', file_path_posix)


def contains_cyrillic(text):
    return bool(re.search(r'[а-яА-Я]', text))


def check_for_cyrillic(data, filename, path=''):
    error_found = False
    if isinstance(data, dict):
        for key, value in data.items():
            if contains_cyrillic(key):
                logger.error(f"Cyrillic character found in key '{key}' in file '{filename}'")
                error_found = True
            if isinstance(value, (dict, list)):
                if check_for_cyrillic(value, filename, path=f"{path}/{key}"):
                    error_found = True
            elif isinstance(value, str) and contains_cyrillic(value):
                logger.error(f"Cyrillic character found in value '{value}' in file '{filename}' at path '{path}/{key}'")
                error_found = True
    elif isinstance(data, list):
        for index, item in enumerate(data):
            if isinstance(item, (dict, list)):
                if check_for_cyrillic(item, filename, path=f"{path}[{index}]"):
                    error_found = True
            elif isinstance(item, str) and contains_cyrillic(item):
                logger.error(
                    f"Cyrillic character found in list item '{item}' in file '{filename}' at path '{path}[{index}]'")
                error_found = True
    return error_found


def get_cluster_name_from_full_name(env):
    return env.split('/')[0].strip()


def get_environment_name_from_full_name(env):
    return env.split('/')[1].strip()


def find_cloud_passport_definition(env_instances_dir, instances_dir):
    # trying to get explicit passport name from env_definition
    inventoryYaml = getEnvDefinition(env_instances_dir)
    cloud_passport_file_name = ""
    if ("cloudPassport" in inventoryYaml["inventory"]):
        cloud_passport_file_name = inventoryYaml["inventory"]["cloudPassport"]
    if (cloud_passport_file_name):
        return findPassportByEnvDefinition(env_instances_dir, instances_dir, cloud_passport_file_name)
    else:
        cloudDir = getParentDirName(env_instances_dir + "/")
        logger.info(
            f"Explicit name of cloud passport is not defined. Trying to find by directory in cloud dir {cloudDir}.")
        # trying to search passport by cloud name (cloud dir name)
        cloudDirName = extractNameFromDir(cloudDir)
        passportFilePath = findPassportInDefaultDirByName(cloudDir, cloudDirName)
        if passportFilePath:
            return passportFilePath
        # trying to find passport by default passport name
        return findPassportInDefaultDirByName(cloudDir, DEFAULT_PASSPORT_NAME)


def findPassportByEnvDefinition(env_instances_dir, instances_dir, cloud_passport_file_name):
    logger.debug(
        f"Searching for cloud passport file {cloud_passport_file_name} from {env_instances_dir} to {instances_dir}")
    passportFiles = findResourcesBottomTop(env_instances_dir, instances_dir, f"/{cloud_passport_file_name}.y",
                                           "redentials/")
    if len(passportFiles) == 1:
        yamlPath = passportFiles[0]
        logger.info(f"Cloud passport file for {cloud_passport_file_name} found in: {yamlPath}")
        return yamlPath
    elif len(passportFiles) > 1:
        logger.error(
            f"Duplicate cloud passport files with key {cloud_passport_file_name} found in {instances_dir}: \n\t" + ",\n\t".join(
                str(x) for x in passportFiles))
        raise ReferenceError(
            f"Duplicate cloud passport files with key {cloud_passport_file_name} found. See logs above.")
    else:
        raise ReferenceError(f"Cloud passport with key {cloud_passport_file_name} not found in {instances_dir}")


def findPassportInDefaultDirByName(env_instances_dir, passport_name):
    logger.debug(
        f"Searching for yaml with pattern '{DEFAULT_PASSPORT_DIR_NAME}/{passport_name}.y' in {env_instances_dir}")
    passportFiles = findYamls(env_instances_dir, f"{DEFAULT_PASSPORT_DIR_NAME}/{passport_name}.y",
                              notPattern="redentials/")
    if len(passportFiles) == 1:
        yamlPath = passportFiles[0]
        logger.info(f"Cloud passport file for {env_instances_dir} with name {passport_name} found in: {yamlPath}")
        return yamlPath
    elif len(passportFiles) > 1:
        logger.error(
            f"More than one passport files found for env {env_instances_dir} with name {passport_name}:\n{dump_as_yaml_format(passportFiles)}")
        raise ReferenceError(
            f"More than one passport files found for env {env_instances_dir} with name {passport_name}. See logs above.")
    else:
        logger.info(f"Cloud passport for env {env_instances_dir} with name {passport_name} is not found. ")
        return ""


def find_cloud_name_from_passport(source_env_dir, all_instances_dir):
    # checking if inventory is related to cloud passport
    inventoryYaml = getEnvDefinition(source_env_dir)
    cloudPassportFileName = ""
    # if passport name is defined in env_definition than using it
    if ("cloudPassport" in inventoryYaml["inventory"]):
        cloudPassportFileName = inventoryYaml["inventory"]["cloudPassport"]
        logger.info(f"Got cloud name from env_definition passport {cloudPassportFileName}")
    cloudPassportFile = find_cloud_passport_definition(source_env_dir, all_instances_dir)
    if cloudPassportFile:
        if f"{DEFAULT_PASSPORT_DIR_NAME}/{DEFAULT_PASSPORT_NAME}.y" in cloudPassportFile:
            cloudName = extractNameFromDir(getParentDirName(cloudPassportFile))
            logger.info(f"Got cloud name {cloudName} from environment directory {source_env_dir}")
            return cloudName
        else:
            cloudPassportFileName = extractNameFromFile(cloudPassportFile)
            logger.info(f"Cloud name '{cloudPassportFileName}' got from cloud passport file: {cloudPassportFile}")
            return cloudPassportFileName
    else:
        return ""

@dataclass
class NamespaceFile:
    path: Path
    name: str = field(init=False)
    definition_path: Path = field(init=False)

    def __post_init__(self):
        self.definition_path = self.path.joinpath('namespace.yml')
        self.name = openYaml(self.definition_path)['name']

def get_namespaces_path(env_dir: Path | None = None) -> Path:
    env_dir = env_dir or get_current_env_dir_from_env_vars()
    namespaces_path = env_dir.joinpath('Namespaces')
    logger.debug(namespaces_path)
    return namespaces_path

def get_namespaces(env_dir: Path | None = None) -> list[NamespaceFile]:
    namespaces_path = get_namespaces_path(env_dir)
    if not check_dir_exists(str(namespaces_path)):
        return []
    namespace_paths = [p for p in namespaces_path.iterdir() if p.is_dir()]
    namespaces = [NamespaceFile(path=p) for p in namespace_paths]
    logger.debug(namespaces)
    return namespaces

def get_bgd_path(env_dir: Path | None = None) -> Path:
    env_dir = env_dir or get_current_env_dir_from_env_vars()
    bgd_path = env_dir.joinpath('bg_domain.yml')
    logger.debug(bgd_path)
    return bgd_path

def get_bgd_object(env_dir: Path | None = None) -> CommentedMap:
    bgd_path = get_bgd_path(env_dir)
    bgd_object = openYaml(bgd_path, allow_default=True)
    logger.debug(bgd_object)
    return bgd_object

