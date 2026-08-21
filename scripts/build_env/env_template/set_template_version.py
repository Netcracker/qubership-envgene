from pathlib import Path

from envgenehelper import beautifyYaml, writeYamlToFile, logger, getEnvDefinitionPath
from envgenehelper import getEnvDefinition
from envgenehelper.business_helper import NamespaceRole
from envgenehelper.models import TemplateVersionUpdateMode


def _update_common_artifact_version(data: dict, version_to_add: str, env_definition_path: Path) -> None:
    if ":" in version_to_add:
        if 'envTemplate' in data:
            if 'templateArtifact' in data['envTemplate']:
                del data['envTemplate']['templateArtifact']
            data['envTemplate']['artifact'] = version_to_add
        else:
            logger.error(f"Bad env_definition structure in file {env_definition_path}.")
            raise ReferenceError(f"Can't update version in {env_definition_path}. See logs above.")
    else:
        if 'envTemplate' in data and 'templateArtifact' in data['envTemplate'] and 'artifact' in data['envTemplate'][
            'templateArtifact']:
            old_version = "undefined"
            if 'version' in data['envTemplate']['templateArtifact']['artifact']:
                old_version = data['envTemplate']['templateArtifact']['artifact']['version']
            data['envTemplate']['templateArtifact']['artifact']['version'] = version_to_add
            logger.info(
                f"Succesfully updated version from {old_version} to {version_to_add} in {env_definition_path}")
        else:
            logger.error(f"Bad env_definition structure in file {env_definition_path}.")
            raise ReferenceError(f"Can't update version in {env_definition_path}. See logs above.")


def _update_bg_ns_artifact_version(
    data: dict, role: NamespaceRole, version_to_add: str, env_definition_path: Path,
) -> None:
    if 'envTemplate' not in data:
        logger.error(f"Bad env_definition structure in file {env_definition_path}.")
        raise ReferenceError(f"Can't update version in {env_definition_path}. See logs above.")

    field_name = "origin" if role == NamespaceRole.ORIGIN else "peer"
    data['envTemplate'].setdefault('bgNsArtifacts', {})[field_name] = version_to_add
    logger.info(
        f"Updated envTemplate.bgNsArtifacts.{field_name} to {version_to_add} in {env_definition_path}")


def update_version(
    env_definition_dir,
    version_to_add,
    update_mode: TemplateVersionUpdateMode,
    bg_ns_target: NamespaceRole | None = None,
):
    if not version_to_add:
        logger.info('No ENV_TEMPLATE_VERSION provided, skipping template version update')
        return

    env_definition_path = getEnvDefinitionPath(env_definition_dir)
    logger.info(f"Started version update to {version_to_add} in {env_definition_path}.")
    data = getEnvDefinition(env_definition_dir)

    if update_mode == TemplateVersionUpdateMode.TEMPORARY:
        logger.info(
            "Template update mode: TEMPORARY, Skip updating template artifact version in env_definition.yml")
        data.setdefault("generatedVersions", {})["generateEnvironmentLatestVersion"] = version_to_add
        writeYamlToFile(env_definition_path, data)
        beautifyYaml(env_definition_path)
        return

    if bg_ns_target is None:
        _update_common_artifact_version(data, version_to_add, env_definition_path)
    else:
        _update_bg_ns_artifact_version(data, bg_ns_target, version_to_add, env_definition_path)

    writeYamlToFile(env_definition_path, data)
    beautifyYaml(env_definition_path)
