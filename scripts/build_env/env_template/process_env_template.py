import asyncio
import os
import tempfile
from pathlib import Path

from artifact_searcher import artifact
from artifact_searcher.utils.models import FileExtension, Application, Credentials, Registry
from envgenehelper import getEnvDefinition, fetch_cred_value
from envgenehelper import openYaml, find_all_yaml_files_by_stem, getenv_with_error, logger
from envgenehelper import unpack_archive, get_cred_config, check_dir_exist_and_create

PROJECT_DIR = getenv_with_error('CI_PROJECT_DIR')
ARTIFACT_DEST = f"{tempfile.gettempdir()}/artifact.zip"
TEMPLATE_DEST = f"{PROJECT_DIR}/tmp"


def parse_artifact_appver(env_definition: dict) -> [str, str]:
    artifact_appver = env_definition['envTemplate'].get('artifact', '')
    logger.info(f"Environment template artifact version: {artifact_appver}")
    return artifact_appver.split(':')


def load_artifact_definition(name: str) -> Application:
    path_pattern = os.path.join(PROJECT_DIR, 'configuration', 'artifact_definitions', name)
    path = next(iter(find_all_yaml_files_by_stem(path_pattern)), None)
    if not path:
        raise FileNotFoundError(f"No artifact definition file found for {name} with .yaml or .yml extension")
    return Application.model_validate(openYaml(path))


def get_registry_creds(registry: Registry) -> Credentials:
    cred_config = get_cred_config()
    cred_id = registry.credentials_id
    if cred_id:
        username = cred_config[cred_id]['data'].get('username')
        password = cred_config[cred_id]['data'].get('password')
        if username is None or password is None:
            raise ValueError(
                f"Registry {registry.name} credentials incomplete: username={username}, password={password}")
        return Credentials(username=username, password=password)


def parse_maven_coord_from_dd(dd_config: dict) -> tuple[str, str, str]:
    artifact_str = dd_config['configurations'][0]['artifacts'][0].get('id')
    return artifact_str.split(':')


def extract_snapshot_version(url: str, snapshot_version: str) -> str:
    base = snapshot_version.replace("-SNAPSHOT", "")
    filename = url.split("/")[-1]
    name = filename.rsplit(".", 1)[0]
    pos = name.find(base)
    return name[pos:]


# logic resolving artifact version by artifact definition
def resolve_artifact_new_logic(env_definition: dict, download_template: bool = True) -> str:
    app_name, app_version = parse_artifact_appver(env_definition)
    app_def = load_artifact_definition(app_name)
    cred = get_registry_creds(app_def.registry)
    template_url = None

    resolved_version = app_version
    dd_artifact_info = asyncio.run(artifact.check_artifact_async(app_def, FileExtension.JSON, app_version))
    if dd_artifact_info:
        logger.info("Loading environment template artifact info from deployment descriptor...")
        dd_url, dd_repo = dd_artifact_info
        logger.info(f"Resolved deployment descriptor URL: {dd_url}")
        if "-SNAPSHOT" in app_version:
            resolved_version = extract_snapshot_version(dd_url, app_version)
        if download_template:
            dd_config = artifact.download_json_content(dd_url, cred)
            group_id, artifact_id, version = parse_maven_coord_from_dd(dd_config)
            logger.info(
                f"Parsed maven coordinates: group_id={group_id}, artifact_id={artifact_id}, version={version} from dd")
            if not all([group_id, artifact_id, version]):
                raise ValueError(f"Invalid maven coordinates from deployment descriptor {dd_url}")

            repo_url = dd_config.get("configurations", [{}])[0].get("maven_repository") or dd_repo
            template_url = artifact.check_artifact(repo_url, group_id, artifact_id, version, FileExtension.ZIP)
    else:
        logger.info("Loading environment template artifact from zip directly...")
        group_id, artifact_id, version = app_def.group_id, app_def.artifact_id, app_version
        artifact_info = asyncio.run(artifact.check_artifact_async(app_def, FileExtension.ZIP, app_version))

        if artifact_info:
            template_url, _ = artifact_info
        if "-SNAPSHOT" in app_version:
            resolved_version = extract_snapshot_version(template_url, app_version)

    if download_template:
        if not template_url:
            raise ValueError(f"artifact not found group_id={group_id}, artifact_id={artifact_id}, version={version}")

        logger.info(f"Environment template url has been resolved: {template_url}")
        artifact.download(template_url, ARTIFACT_DEST, cred)
        unpack_archive(ARTIFACT_DEST, TEMPLATE_DEST)

    return resolved_version


# logic resolving artifact version by exact coordinates and repo, deprecated
def resolve_artifact_old_logic(env_definition: dict, download_template: bool = True) -> str:
    template_artifact = env_definition['envTemplate']['templateArtifact']
    artifact_info = template_artifact['artifact']

    group_id = artifact_info['group_id']
    artifact_id = artifact_info['artifact_id']
    dd_version = artifact_info['version']
    dd_repo_type = template_artifact.get('repository')
    repo_type = template_artifact['templateRepository']
    registry_name = template_artifact['registry']

    registry_dict = openYaml(Path(f"{PROJECT_DIR}/configuration/registry.yml"))  # another registry model
    registry = registry_dict[registry_name]
    repo_url = registry.get(repo_type)
    dd_repo_url = registry.get(dd_repo_type)

    cred = None
    if download_template:
        cred_config = get_cred_config()
        repository_username = fetch_cred_value(registry.get("username"), cred_config)
        repository_password = fetch_cred_value(registry.get("password"), cred_config)
        cred = Credentials(username=repository_username, password=repository_password)
    
    template_url = None
    resolved_version = dd_version
    dd_url = artifact.check_artifact(dd_repo_url, group_id, artifact_id, dd_version, FileExtension.JSON)
    if dd_url:
        logger.info(f"Deployment descriptor url for environment template has been resolved: {dd_url}")
        if "-SNAPSHOT" in dd_version:
            resolved_version = extract_snapshot_version(dd_url, dd_version)
        if download_template:
            dd_config = artifact.download_json_content(dd_url, cred)
            group_id, artifact_id, version = parse_maven_coord_from_dd(dd_config)
            logger.info(
                f"Parsed maven coordinates from dd: group_id={group_id}, artifact_id={artifact_id}, version={version}")
            if not all([group_id, artifact_id, version]):
                raise ValueError(f"Invalid maven coordinates from deployment descriptor {dd_url}")

            template_url = artifact.check_artifact(repo_url, group_id, artifact_id, version, FileExtension.ZIP)
    else:
        logger.info("Loading environment template artifact from zip directly...")
        template_url = artifact.check_artifact(repo_url, group_id, artifact_id, dd_version, FileExtension.ZIP)
        if "-SNAPSHOT" in dd_version:
            resolved_version = extract_snapshot_version(template_url, dd_version)

    if download_template:
        if not template_url:
            raise ValueError(f"artifact not found group_id={group_id}, artifact_id={artifact_id}, version={version}")
        logger.info(f"Environment template url has been resolved: {template_url}")
        artifact.download(template_url, ARTIFACT_DEST, cred)
        unpack_archive(ARTIFACT_DEST, TEMPLATE_DEST)

    return resolved_version


def process_env_template(download_template: bool = True) -> str:
    cluster = getenv_with_error("CLUSTER_NAME")
    environment = getenv_with_error("ENVIRONMENT_NAME")
    env_dir = Path(f"{PROJECT_DIR}/environments/{cluster}/{environment}")
    env_definition = getEnvDefinition(env_dir)
    
    check_dir_exist_and_create(TEMPLATE_DEST)

    if 'artifact' in env_definition.get('envTemplate', {}):
        logger.info("Use template resolving new logic")
        return resolve_artifact_new_logic(env_definition, download_template)
    else:
        logger.info("Use template resolving old logic")
        return resolve_artifact_old_logic(env_definition, download_template)
