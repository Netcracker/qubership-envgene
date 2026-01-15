import asyncio
import os
import tempfile
from pathlib import Path

from artifact_searcher import artifact
from artifact_searcher.utils.models import FileExtension, Application, Credentials, Registry
from envgenehelper import getEnvDefinition, fetch_cred_value
from envgenehelper import openYaml, find_all_yaml_files_by_stem, getenv_with_error, logger
from envgenehelper import unpack_archive, get_cred_config

build_env_path = "/build_env"
ORIGIN_NS_TEMPLATE_PATH = "/build_env_origin_ns"
PEER_NS_TEMPLATE_PATH = "/build_env_peer_ns"


def parse_artifact_appver(artifact_appver: str) -> list[str]:
    logger.info(f"Environment template artifact version: {artifact_appver}")
    return artifact_appver.split(':')


def load_artifact_definition(name: str, base_dir: str) -> Application:
    path_pattern = os.path.join(base_dir, 'configuration', 'artifact_definitions', name)
    path = next(iter(find_all_yaml_files_by_stem(path_pattern)), None)
    if not path:
        raise FileNotFoundError(f"No artifact definition file found for {name} with .yaml or .yml extension")
    return Application.model_validate(openYaml(path))


def get_registry_creds(registry: Registry, cred_config: dict) -> Credentials:
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


# logic downloading template by artifact definition
def download_artifact_new_logic(artifact_appver: str, target_path: str, base_dir: str, cred_config: dict) -> str:
    app_name, app_version = parse_artifact_appver(artifact_appver)
    app_def = load_artifact_definition(app_name, base_dir)
    cred = get_registry_creds(app_def.registry, cred_config)
    template_url = None

    resolved_version = app_version
    dd_artifact_info = asyncio.run(artifact.check_artifact_async(app_def, FileExtension.JSON, app_version))
    if dd_artifact_info:
        logger.info("Loading environment template artifact info from deployment descriptor...")
        dd_url, dd_repo = dd_artifact_info
        logger.info(f"Resolved deployment descriptor URL: {dd_url}")
        if "-SNAPSHOT" in app_version:
            resolved_version = extract_snapshot_version(dd_url, app_version)

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
    if not template_url:
        raise ValueError(f"artifact not found group_id={group_id}, artifact_id={artifact_id}, version={version}")
    logger.info(f"Environment template url has been resolved: {template_url}")

    # Use a unique temporary file for each download to avoid conflicts
    with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as tmp_file:
        artifact_dest = tmp_file.name

    try:
        artifact.download(template_url, artifact_dest, cred)
        unpack_archive(artifact_dest, target_path)
    finally:
        # Clean up the temporary file
        if os.path.exists(artifact_dest):
            os.unlink(artifact_dest)

    return resolved_version


# logic downloading template by exact coordinates and repo, deprecated
def download_artifact_old_logic(env_definition: dict, project_dir: str, cred_config: dict) -> str:
    template_artifact = env_definition['envTemplate']['templateArtifact']
    artifact_info = template_artifact['artifact']

    group_id = artifact_info['group_id']
    artifact_id = artifact_info['artifact_id']
    dd_version = artifact_info['version']
    dd_repo_type = template_artifact.get('repository')
    repo_type = template_artifact['templateRepository']
    registry_name = template_artifact['registry']

    registry_dict = openYaml(Path(f"{project_dir}/configuration/registry.yml"))  # another registry model
    registry = registry_dict[registry_name]
    repo_url = registry.get(repo_type)
    dd_repo_url = registry.get(dd_repo_type)

    repository_username = fetch_cred_value(registry.get("username"), cred_config)
    repository_password = fetch_cred_value(registry.get("password"), cred_config)
    cred = Credentials(username=repository_username, password=repository_password)

    resolved_version = dd_version
    dd_url = artifact.check_artifact(dd_repo_url, group_id, artifact_id, dd_version, FileExtension.JSON)
    if dd_url:
        logger.info(f"Deployment descriptor url for environment template has been resolved: {dd_url}")
        if "-SNAPSHOT" in dd_version:
            resolved_version = extract_snapshot_version(dd_url, dd_version)
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

    logger.info(f"Environment template url has been resolved: {template_url}")

    # Use a unique temporary file for each download to avoid conflicts
    with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as tmp_file:
        artifact_dest = tmp_file.name

    try:
        artifact.download(template_url, artifact_dest, cred)
        unpack_archive(artifact_dest, build_env_path)
    finally:
        # Clean up the temporary file
        if os.path.exists(artifact_dest):
            os.unlink(artifact_dest)

    return resolved_version


async def download_artifact_new_logic_async(artifact_appver: str, target_path: str, base_dir: str, cred_config: dict) -> str:
    """Async wrapper for download_artifact_new_logic to enable concurrent downloads"""
    return await asyncio.to_thread(download_artifact_new_logic, artifact_appver, target_path, base_dir, cred_config)


async def download_artifact_old_logic_async(env_definition: dict, project_dir: str, cred_config: dict) -> str:
    """Async wrapper for download_artifact_old_logic to enable concurrent downloads"""
    return await asyncio.to_thread(download_artifact_old_logic, env_definition, project_dir, cred_config)


def process_env_template() -> tuple[str, str | None, str | None]:
    project_dir = getenv_with_error("CI_PROJECT_DIR")
    cluster = getenv_with_error("CLUSTER_NAME")
    environment = getenv_with_error("ENVIRONMENT_NAME")
    env_dir = Path(f"{project_dir}/environments/{cluster}/{environment}")
    env_definition = getEnvDefinition(env_dir)
    env_template = env_definition.get('envTemplate', {})

    cred_config = get_cred_config()

    bg_artifacts_key = 'bgNsArtifacts'
    bg_artifacts = env_template.get(bg_artifacts_key, {})

    async def download_all_templates():
        if 'artifact' in env_template:
            logger.info("Use template downloading new logic")
            main_task = download_artifact_new_logic_async(
                env_template.get('artifact', ''),
                build_env_path,
                project_dir,
                cred_config
            )
        else:
            logger.info("Use template downloading old logic")
            main_task = download_artifact_old_logic_async(env_definition, project_dir, cred_config)

        tasks = [main_task]
        task_labels = ['main']

        bg_artifact_configs = [
            ('origin', ORIGIN_NS_TEMPLATE_PATH),
            ('peer', PEER_NS_TEMPLATE_PATH),
        ]

        for artifact_key, target_path in bg_artifact_configs:
            artifact_appver = bg_artifacts.get(artifact_key)
            if artifact_appver:
                logger.info(f'Try to download template for appver: {artifact_appver}, from {bg_artifacts_key}.{artifact_key}')
                tasks.append(download_artifact_new_logic_async(artifact_appver, target_path, project_dir, cred_config))
                task_labels.append(artifact_key)

        results = await asyncio.gather(*tasks)

        result_map = dict(zip(task_labels, results))
        return (
            result_map['main'],
            result_map.get('origin', None),
            result_map.get('peer', None)
        )

    return asyncio.run(download_all_templates())
