import asyncio
import os
import tempfile
from pathlib import Path

from artifact_searcher import artifact
from artifact_searcher.utils.models import FileExtension, Credentials, Registry, Application
from env_template.template_testing import run_env_test_setup
from envgenehelper import getEnvDefinition, fetch_cred_value, getAppDefinitionPath
from envgenehelper import openYaml, getenv_with_error, logger, get_or_create_nested_yaml_attribute
from envgenehelper import unpack_archive, get_cred_config, check_dir_exist_and_create
from envgenehelper.yaml_helper import get_nested_yaml_attribute_or_fail
from render_config_env import render_obj_by_context, Context


def parse_artifact_appver(env_definition: dict, attribute_str: str) -> list[str]:
    try:
        get_nested_yaml_attribute_or_fail(env_definition, attribute_str)
        exists = True
    except ValueError:
        exists = False
    appver = str(get_or_create_nested_yaml_attribute(env_definition, attribute_str, ""))

    if exists and not appver:
        raise ValueError(f"{attribute_str} is empty or missing from env_definition: {env_definition}")
    logger.info(f"Artifact version in {attribute_str}: {appver}", attribute_str, appver)
    return appver.split(":")



def get_registry_creds(registry: Registry, cred_config: dict) -> Credentials:
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
    artifact_str = dd_config['configurations'][0]['artifacts'][0].get('id')
    return artifact_str.split(':')


def extract_snapshot_version(url: str, snapshot_version: str) -> str:
    base = snapshot_version.replace("-SNAPSHOT", "")
    filename = url.split("/")[-1]
    name = filename.rsplit(".", 1)[0]
    pos = name.find(base)
    return name[pos:]


def validate_url(url, group_id, artifact_id, version):
    if not url:
        raise ValueError(
            f"artifact not found group_id={group_id}, "
            f"artifact_id={artifact_id}, version={version}"
        )


# logic resolving template by artifact definition
async def resolve_artifact_new_logic(app_def: Application, app_version: str, template_dest: str, cred: Credentials) -> str:
    template_url = None

    resolved_version = app_version
    dd_artifact_info = await artifact.check_artifact_async(app_def, FileExtension.JSON, app_version, cred)
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
        logger.info("Loading environment template artifact from zip directly...")
        group_id, artifact_id, version = app_def.group_id, app_def.artifact_id, app_version
        artifact_info = await artifact.check_artifact_async(app_def, FileExtension.ZIP, app_version, cred)
        if artifact_info:
            template_url, _ = artifact_info
        validate_url(template_url, group_id, artifact_id, version)
        if "-SNAPSHOT" in app_version:
            resolved_version = extract_snapshot_version(template_url, app_version)
    logger.info(f"Environment template url has been resolved: {template_url}")
    artifact_dest = tempfile.mkstemp(suffix='.zip')[1]
    artifact.download(template_url, artifact_dest, cred)
    unpack_archive(artifact_dest, template_dest)
    return resolved_version


def render_creds() -> dict:
    cred_config = get_cred_config()
    context = Context()
    context.env_vars.update(dict(os.environ))
    rendered = render_obj_by_context(cred_config, context)
    logger.info("Credentials rendered successfully")
    return rendered


# logic resolving template by exact coordinates and repo, deprecated
async def resolve_artifact_old_logic(env_definition: dict, template_dest: str, cred_config: dict, registry_dict: dict) -> str:
    template_artifact = env_definition['envTemplate']['templateArtifact']
    artifact_info = template_artifact['artifact']

    group_id = artifact_info['group_id']
    artifact_id = artifact_info['artifact_id']
    dd_version = artifact_info['version']
    dd_repo_type = template_artifact.get('repository')
    repo_type = template_artifact['templateRepository']
    registry_name = template_artifact['registry']

    registry = registry_dict[registry_name]
    repo_url = registry.get(repo_type)
    dd_repo_url = registry.get(dd_repo_type)

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
    artifact_dest = tempfile.mkstemp(suffix='.zip')[1]
    artifact.download(template_url, artifact_dest, cred)
    unpack_archive(artifact_dest, template_dest)
    return resolved_version


def is_valid_appver(appver: list[str]) -> bool:
    return len(appver) >= 2 and bool(appver[0]) and bool(appver[1])


def process_env_template() -> dict:
    env_template_test = os.getenv("ENV_TEMPLATE_TEST", "").lower() == "true"
    if env_template_test:
        run_env_test_setup()

    env_definition = getEnvDefinition()

    appvers = {
        'common': parse_artifact_appver(env_definition, 'envTemplate.artifact'),
        'origin': parse_artifact_appver(env_definition, 'envTemplate.bgNsArtifacts.origin'),
        'peer': parse_artifact_appver(env_definition, 'envTemplate.bgNsArtifacts.peer'),
    }

    tasks = {}
    project_dir = getenv_with_error('CI_PROJECT_DIR')
    cred_config = render_creds()

    for key, appver in appvers.items():
        if key == 'common':
            template_dest = f'{project_dir}/tmp'
        else:
            template_dest = f'{project_dir}/tmp/{key}'

        if not is_valid_appver(appver):
            if not key == "common":
                continue
            registry_dict = openYaml(Path(f"{project_dir}/configuration/registry.yml"))

            logger.info('Using template resolving old logic')
            tasks[key] = resolve_artifact_old_logic(env_definition, template_dest, cred_config, registry_dict)
            continue

        app_name, app_version = appver[0], appver[1]
        artifact_path = getAppDefinitionPath(project_dir, app_name)
        if not artifact_path:
            raise FileNotFoundError(f"No artifact definition file found for {app_name}")
        app_def = Application.model_validate(openYaml(artifact_path))
        cred = get_registry_creds(app_def.registry, cred_config)

        logger.info(f'Use template resolving new logic for {appver}')
        tasks[key] = resolve_artifact_new_logic(app_def, app_version, template_dest, cred)

    async def resolve_all():
        results = await asyncio.gather(*tasks.values())
        return dict(zip(tasks.keys(), results))

    return asyncio.run(resolve_all())
