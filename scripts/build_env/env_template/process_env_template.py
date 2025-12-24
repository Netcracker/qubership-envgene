import asyncio
import os
from pathlib import Path

from artifact_searcher import artifact
from artifact_searcher.artifact import download_all_async
from artifact_searcher.utils.models import FileExtension, ArtifactInfo, Application, Credentials, Registry
from envgenehelper import get_env_definition
from envgenehelper import openYaml, find_all_yaml_files_by_stem, getenv_with_error, logger
from envgenehelper.config_helper import base_dir
from envgenehelper import unpack_archive, get_cred_config


def parse_artifact_appver(env_definition: dict) -> [str, str]:
    artifact_appver = env_definition['envTemplate'].get('artifact', '')
    logger.info(f"Environment template artifact version: {artifact_appver}")
    return artifact_appver.split(':')


def load_artifact_definition(name: str) -> Application:
    path_pattern = os.path.join(base_dir, 'configuration', 'artifact_definitions', name)
    path = next(iter(find_all_yaml_files_by_stem(path_pattern)), None)
    if not path:
        raise FileNotFoundError(f"No configuration file found for {name} with .yaml or .yml extension")
    return Application.model_validate(openYaml(path))


def get_registry_creds(registry: Registry) -> Credentials:
    cred_config = get_cred_config()
    cred_id = registry['credentialsId']
    username = cred_config[cred_id]['data'].get('username')
    password = cred_config[cred_id]['data'].get('password')
    if not username or not password:
        raise ValueError(f"Username or password for registry '{registry['name']}' is null")
    return Credentials(username=username, password=password)


def fetch_dd(app: Application, version: str, cred: Credentials):
    url, _ = asyncio.run(artifact.check_artifact_async(app, FileExtension.JSON, version))
    if not url:
        raise ValueError(
            f"[Application {app.name}:{version}]: URL to deployment descriptor could not be resolved"
        )
    logger.info(f"Resolved deployment descriptor URL: {url}")
    return artifact.download_json_content(url, cred)


def parse_maven_coord_from_dd(dd_config: dict) -> tuple[str, str, str]:
    artifact_str = dd_config['configurations'][0]['artifacts'][0].get('id')
    return artifact_str.split(':')


def get_artifact_info_from_dd(dd_config: dict, app: Application, cred: Credentials) -> ArtifactInfo:
    group_id, artifact_id, version = parse_maven_coord_from_dd(dd_config)
    logger.info(f"Parsed maven coordinates: group_id={group_id}, artifact_id={artifact_id}, version={version}")
    if not all([group_id, artifact_id, version]):
        raise ValueError(f"[Application {app.name}]: invalid maven coordinates from deployment descriptor")
    url = asyncio.run(artifact.check_artifact_async(app, FileExtension.ZIP, version, cred))
    if not url:
        raise ValueError(f"[Application {app.name}]: artifact not found ({group_id}:{artifact_id}:{version})")
    return ArtifactInfo(app_name=app.name, app_version=version, url=url)


def is_zip_template(env_definition: dict) -> bool:
    return env_definition.get('envTemplate', {}).get('artifactIsZip', False)


def build_zip_artifact_info(app: Application, version: str, cred: Credentials) -> ArtifactInfo:
    url = asyncio.run(artifact.check_artifact_async(app, FileExtension.ZIP, version, cred))
    return ArtifactInfo(app_name=app.name, app_version=version, url=url)


def download_artifact_new_logic(env_definition: dict) -> str:
    artifact_name, version = parse_artifact_appver(env_definition)
    app_def = load_artifact_definition(artifact_name)
    cred = get_registry_creds(app_def.registry)

    if is_zip_template(env_definition):
        artifact_info = build_zip_artifact_info(app_def, version, cred)
    else:
        dd_config = fetch_dd(app_def, version, cred)
        artifact_info = get_artifact_info_from_dd(dd_config, app_def, cred)

    #TODO downloading to another  folder how fix better?
    asyncio.run(download_all_async([artifact_info], cred))
    return artifact_info.app_version


def download_artifact_old_logic(env_definition: dict, project_dir: str) -> str:
    artifact_info = env_definition['envTemplate']['templateArtifact']['artifact']

    group_id = artifact_info['group_id']
    artifact_id = artifact_info['artifact_id']
    version = artifact_info['version']
    repo_type = artifact_info['repository']
    template_repo_type = artifact_info['templateRepository']
    registry_name = artifact_info['registry']
    artifact_version = None

    registry_def = openYaml(Path(f"{project_dir}/configuration/registry.yml"))
    cred = get_registry_creds(registry_def)

    if not is_zip_template(env_definition):
        repo_url = registry_def[registry_name][repo_type]
        dd_url = artifact.create_artifact_url_by_parts(repo_url, group_id, artifact_id, version, FileExtension.JSON)
        dd_config = artifact.download_json_content(dd_url, cred)
        group_id, artifact_id, version = parse_maven_coord_from_dd(dd_config)
        template_url = artifact.create_artifact_url_by_parts(repo_url, group_id, artifact_id, version,
                                                             FileExtension.ZIP)
    else:
        template_url = artifact.create_artifact_url_by_parts(
            registry_def[registry_name][template_repo_type], group_id, artifact_id, version, FileExtension.ZIP
        )
        artifact_version = version

    artifact_dest = Path("/tmp/artifact.zip")
    build_env_path = "/build_env"
    artifact.download(template_url, artifact_dest, cred)
    unpack_archive(artifact_dest, build_env_path)
    return artifact_version


def process_env_template() -> str:
    project_dir = getenv_with_error("CI_PROJECT_DIR")
    cluster = getenv_with_error("CLUSTER_NAME")
    environment = getenv_with_error("ENVIRONMENT_NAME")
    env_dir = Path(f"{project_dir}/environments/{cluster}/{environment}")
    env_definition = get_env_definition(env_dir)

    if 'artifact' in env_definition.get('envTemplate', {}):
        logger.info("Use template downloading new logic")
        return download_artifact_new_logic(env_definition)
    else:
        logger.info("Use template downloading old logic")
        return download_artifact_old_logic(env_definition, project_dir)
