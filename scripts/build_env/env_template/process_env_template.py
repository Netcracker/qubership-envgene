import asyncio
import os
import shutil
import tempfile
from pathlib import Path
from typing import Optional

from artifact_searcher import artifact
from artifact_searcher.utils.models import FileExtension, Credentials, Registry, Application
from env_template.template_testing import run_env_test_setup
from envgenehelper import getEnvDefinition, fetch_cred_value, getAppDefinitionPath
from envgenehelper import openYaml, getenv_with_error, logger
from envgenehelper import unpack_archive, get_cred_config, check_dir_exist_and_create
from render_config_env import render_obj_by_context, Context

ARTIFACT_DEST = f"{tempfile.gettempdir()}/artifact.zip"


def parse_artifact_appver(env_definition: dict) -> tuple[str, str]:
    """Extract artifact name and version from env_definition.yml."""
    artifact_appver = env_definition.get('envTemplate', {}).get('artifact')
    if not artifact_appver:
        raise ValueError(f"Environment template artifact is empty or missing from env_definition: {env_definition}")
    logger.info(f"Environment template artifact version: {artifact_appver}")
    return artifact_appver.split(':')


def get_registry_creds(registry: Registry) -> Optional[Credentials]:
    """Resolve V1 registry credentials. Returns None for registries without credentials."""
    cred_config = render_creds()
    cred_id = registry.credentials_id
    if cred_id:
        username = cred_config[cred_id]['data'].get('username')
        password = cred_config[cred_id]['data'].get('password')
        if username is None or password is None:
            raise ValueError(
                f"Registry {registry.name} credentials incomplete: username={username}, password={password}")
        return Credentials(username=username, password=password)
    return None


def parse_maven_coord_from_dd(dd_config: dict) -> tuple[str, str, str]:
    """Extract Maven coordinates (groupId:artifactId:version) from deployment descriptor."""
    artifact_str = dd_config['configurations'][0]['artifacts'][0].get('id')
    return artifact_str.split(':')


def extract_snapshot_version(url: str, snapshot_version: str) -> str:
    """Extract timestamped SNAPSHOT version from artifact URL.
    Converts 'feature-branch-SNAPSHOT' to 'feature-branch-20250113.102430-45'.
    """
    base = snapshot_version.replace("-SNAPSHOT", "")
    filename = url.split("/")[-1]
    name = filename.rsplit(".", 1)[0]
    pos = name.find(base)
    return name[pos:]


def validate_url(url, group_id, artifact_id, version):
    """Validate artifact URL is not None/empty. Raises ValueError if invalid."""
    if not url:
        raise ValueError(
            f"artifact not found group_id={group_id}, "
            f"artifact_id={artifact_id}, version={version}"
        )


# logic resolving template by artifact definition
def resolve_artifact_new_logic(env_definition: dict, template_dest: str) -> str:
    """Download environment template using artifact definition (V2-aware).
    
    Supports both V1 and V2 registries. For V2 cloud registries (AWS/GCP/Artifactory/Nexus),
    uses CloudAuthHelper and MavenArtifactSearcher with automatic fallback to V1.
    
    Returns:
        Resolved version string (with SNAPSHOT timestamp if applicable)
    """
    app_name, app_version = parse_artifact_appver(env_definition)

    # Load artifact definition and credentials
    base_dir = getenv_with_error('CI_PROJECT_DIR')
    artifact_path = getAppDefinitionPath(base_dir, app_name)
    if not artifact_path:
        raise FileNotFoundError(f"No artifact definition file found for {app_name} with .yaml or .yml extension")
    app_def = Application.model_validate(openYaml(artifact_path))
    cred = get_registry_creds(app_def.registry)  # V1 credentials
    env_creds = get_cred_config()  # V2 credentials (Jenkins credential store)
    template_url = None

    resolved_version = app_version
    # Try deployment descriptor first (multi-artifact solutions)
    dd_artifact_info = asyncio.run(artifact.check_artifact_async(app_def, FileExtension.JSON, app_version, cred=cred, env_creds=env_creds))
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
        template_url = artifact.check_artifact(repo_url, group_id, artifact_id, version, FileExtension.ZIP, cred)
        validate_url(template_url, group_id, artifact_id, version)
    else:
        # No deployment descriptor, download ZIP directly
        logger.info("Loading environment template artifact from zip directly...")
        group_id, artifact_id, version = app_def.group_id, app_def.artifact_id, app_version
        artifact_info = asyncio.run(artifact.check_artifact_async(app_def, FileExtension.ZIP, app_version, cred=cred, env_creds=env_creds))
        if artifact_info:
            template_url, repo_info = artifact_info
            # V2 optimization: artifact already downloaded by MavenArtifactSearcher
            if isinstance(repo_info, tuple) and len(repo_info) == 2 and repo_info[0] == "v2_downloaded":
                local_path = repo_info[1]
                logger.info(f"V2 artifact already downloaded at: {local_path}")
                shutil.copy(local_path, ARTIFACT_DEST)  # Copy to standard location
                logger.info(f"Copied V2 artifact to: {ARTIFACT_DEST}")
                if "-SNAPSHOT" in app_version:
                    resolved_version = extract_snapshot_version(template_url, app_version)
                unpack_archive(ARTIFACT_DEST, template_dest)
                return resolved_version  # Early return - artifact already available locally
        
        # Standard path: validate URL and continue to HTTP download
        validate_url(template_url, group_id, artifact_id, version)
        if "-SNAPSHOT" in app_version:
            resolved_version = extract_snapshot_version(template_url, app_version)
    
    # V1 path or V2 fallback: download via HTTP
    logger.info(f"Environment template url has been resolved: {template_url}")
    artifact.download(template_url, ARTIFACT_DEST, cred)
    unpack_archive(ARTIFACT_DEST, template_dest)
    return resolved_version


def render_creds() -> dict:
    """Render credential templates with environment variables."""
    cred_config = get_cred_config()
    context = Context()
    context.env_vars.update(dict(os.environ))
    rendered = render_obj_by_context(cred_config, context)
    logger.info("Credentials rendered successfully")
    return rendered


# logic resolving template by exact coordinates and repo, deprecated
def resolve_artifact_old_logic(env_definition: dict, template_dest: str) -> str:
    template_artifact = env_definition['envTemplate']['templateArtifact']
    artifact_info = template_artifact['artifact']

    group_id = artifact_info['group_id']
    artifact_id = artifact_info['artifact_id']
    dd_version = artifact_info['version']
    dd_repo_type = template_artifact.get('repository')
    repo_type = template_artifact['templateRepository']
    registry_name = template_artifact['registry']

    registry_dict = openYaml(
        Path(f"{getenv_with_error('CI_PROJECT_DIR')}/configuration/registry.yml"))  # another registry model
    registry = registry_dict[registry_name]
    repo_url = registry.get(repo_type)
    dd_repo_url = registry.get(dd_repo_type)

    cred_config = render_creds()
    repository_username = fetch_cred_value(registry.get("username"), cred_config)
    repository_password = fetch_cred_value(registry.get("password"), cred_config)
    cred = Credentials(username=repository_username, password=repository_password)

    template_url = None
    resolved_version = dd_version
    dd_url = artifact.check_artifact(dd_repo_url, group_id, artifact_id, dd_version, FileExtension.JSON, cred)
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

        template_url = artifact.check_artifact(repo_url, group_id, artifact_id, version, FileExtension.ZIP, cred)
        validate_url(template_url, group_id, artifact_id, version)
    else:
        logger.info("Loading environment template artifact from zip directly...")
        template_url = artifact.check_artifact(repo_url, group_id, artifact_id, dd_version, FileExtension.ZIP, cred)
        validate_url(template_url, group_id, artifact_id, dd_version)
        if "-SNAPSHOT" in dd_version:
            resolved_version = extract_snapshot_version(template_url, dd_version)
    logger.info(f"Environment template url has been resolved: {template_url}")
    artifact.download(template_url, ARTIFACT_DEST, cred)
    unpack_archive(ARTIFACT_DEST, template_dest)
    return resolved_version


def process_env_template() -> str:
    """Main entry point for template download. Routes to new or old logic based on env_definition format."""
    env_template_test = os.getenv("ENV_TEMPLATE_TEST", "").lower() == "true"
    if env_template_test:
        run_env_test_setup()
    project_dir = getenv_with_error('CI_PROJECT_DIR')
    template_dest = f"{project_dir}/tmp"
    cluster = getenv_with_error("CLUSTER_NAME")
    environment = getenv_with_error("ENVIRONMENT_NAME")
    env_dir = Path(f"{project_dir}/environments/{cluster}/{environment}")
    env_definition = getEnvDefinition(env_dir)

    check_dir_exist_and_create(template_dest)

    # New format: uses artifact definitions (V2-aware)
    if 'artifact' in env_definition.get('envTemplate', {}):
        logger.info("Use template resolving new logic")
        return resolve_artifact_new_logic(env_definition, template_dest)
    else:
        logger.info("Use template resolving old logic")
        return resolve_artifact_old_logic(env_definition, template_dest)
