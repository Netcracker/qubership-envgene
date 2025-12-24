import os
import re
import shutil
from pathlib import Path

from envgenehelper import logger, findAllFilesInDir, writeYamlToFile, readYaml
from envgenehelper import openYaml, unpack_archive, cleanup_dir, addHeaderToYaml, crypt, fetch_cred_value
from envgenehelper.crypt import get_configured_encryption_type
from envgenehelper.errors import ValidationError

from cmdb import update_creds_to_cmdb_format
from git_client import GitRepoManager, GitLabClient
from envgenehelper import get_cred_config

SECRET_KEY = "SECRET_KEY"

header_text = (
    "The contents of this file is generated from Cloud Passport discovery procedure.\n"
    "Contents will be overwritten by next discovery.\n"
    "Please do not modify this file."
)

SECRET_PATTERN = re.compile(
    r"\{\{\s*secrets\(['\"](.*?)['\"]\)\s*}}"
)


def get_integration_config(integration_config_path) -> dict:
    integration_config = {}
    if integration_config_path.exists():
        integration_config = openYaml(integration_config_path)
        logger.info(f"integration_config: {integration_config}")
    else:
        logger.warning(f"Integration config missing: {integration_config_path}")
    return integration_config


def find_downstream_pipeline(pipeline_jobs, env_name) -> dict | None:
    expected = f"trigger-discovery-passport.{env_name.replace('_', '-')}-trigger"
    logger.info(f"Searching for downstream pipeline with names: "
                f"'trigger_discovery_passport' or '{expected}'")
    for item in pipeline_jobs:
        name = item.get("name", "")
        logger.debug(f"Checking job '{name}'")

        if name == "trigger_discovery_passport" or name == expected:
            downstream = item.get("downstream_pipeline", {})
            result = {
                "project_id": downstream.get("project_id"),
                "pipeline_id": downstream.get("id"),
                "ref": downstream.get("ref")
            }
            logger.info(f"Downstream pipeline found: {result}")
            return result
    logger.warning("Downstream pipeline not found")


def process_credentials(discovery_files, cloud_passport_dir, cloud_name, discovery_secret_key):
    creds_path = cloud_passport_dir / f"{cloud_name}-creds.yml"

    for f in discovery_files:
        if "sensitive" in f.name:
            update_creds_to_cmdb_format(f)
            shutil.copyfile(f, creds_path)
    crypt.decrypt_file(creds_path, secret_key=discovery_secret_key, in_place=True, is_crypt=True)
    logger.info(f"Decrypted credential-cp file by discovery secret key: {creds_path}")
    crypt.encrypt_file(creds_path, in_place=True)
    _, is_crypt = get_configured_encryption_type()
    if is_crypt:
        logger.info(f"Re-encrypted credential-cp file by instance secret key: {creds_path}")


# {{ secrets('name.username') }} -> ${creds.get("name").password}
def convert_secret(val: str) -> str:
    if "." in val:
        credential_id = val.rsplit(".", 1)[0] \
            .replace("collector.", "") \
            .replace(".", "-")
        suffix = val.split(".")[-1]
        return f'${{creds.get("{credential_id}").{suffix}}}'
    else:
        credential_id = val.replace(".", "-")
        return f'${{creds.get("{credential_id}")}}'


def process_passport_files(discovery_files, cloud_passport_dir, cloud_name):
    cloud_passport_path = cloud_passport_dir / f"{cloud_name}.yml"

    for f in discovery_files:
        if "passport" in f.name:
            content = f.read_text()
            # replace all secrets(...)
            replaced = SECRET_PATTERN.sub(
                lambda m: convert_secret(m.group(1)),
                content,
            )
            writeYamlToFile(cloud_passport_path, readYaml(replaced))
            addHeaderToYaml(cloud_passport_path, header_text)
            break

    logger.info(f"Discovered cloud_passport: {cloud_passport_path}")


def process_discovery_files(env_name: str,
                            envs_dir_path: str,
                            discovery_files: list[Path],
                            discovery_secret_key: str):
    envs_dir_path = Path(envs_dir_path)

    cloud_name = env_name.split("/")[0]
    cloud_dir = envs_dir_path / cloud_name
    cloud_passport_dir = cloud_dir / "cloud-passport"
    cleanup_dir(cloud_passport_dir)

    process_passport_files(discovery_files, cloud_passport_dir, cloud_name)
    process_credentials(discovery_files, cloud_passport_dir, cloud_name, discovery_secret_key)
    for cp_file in findAllFilesInDir(cloud_passport_dir, ""):
        addHeaderToYaml(cp_file, header_text)


def main():
    env_name = os.getenv("ENV_NAME")
    logger.info(f"Starting discovery of cloud passport for environment {env_name}")
    base_dir = os.getenv("CI_PROJECT_DIR")

    integration_config = get_integration_config(Path(f"{base_dir}/configuration/integration.yml"))
    cred_config = get_cred_config()

    self_git_token = fetch_cred_value(integration_config.get("self_token"), cred_config)
    repo = GitRepoManager(repo_path=base_dir, git_token=self_git_token)
    repo.prepare_repo()

    downstream_gl_client = GitLabClient(token=self_git_token)

    project_id = os.getenv("CI_PROJECT_ID")
    pipeline_id = os.getenv("CI_PIPELINE_ID")

    pipeline_jobs = downstream_gl_client.get_pipeline_bridges(project_id, pipeline_id)
    logger.info(f"Pipeline jobs fetched: {pipeline_jobs}")

    downstream = find_downstream_pipeline(pipeline_jobs, env_name)
    if not downstream:
        raise ValidationError("Downstream pipeline not found")

    downstream_project_id = downstream.get("project_id")
    downstream_jobs = downstream_gl_client.get_pipeline_jobs(downstream_project_id,
                                                             downstream.get("pipeline_id"))
    logger.info(f"Downstream pipeline jobs fetched: {downstream_jobs}")
    passport_archive_path = "/tmp/archive.zip"
    downstream_gl_client.download_job_artifacts(
        downstream_project_id,
        downstream_jobs[0].get("id"),
        passport_archive_path
    )

    passport_unpack_path = Path("/tmp/passport")
    unpack_archive(passport_archive_path, os.path.dirname(passport_unpack_path))
    passport_discovery_files = list(Path(passport_unpack_path).rglob("*"))

    downstream_git_token = fetch_cred_value(integration_config.get("cp_discovery").get("gitlab").get("token"),
                                            cred_config)
    downstream_gl_client = GitLabClient(token=downstream_git_token)
    downstream_vars = downstream_gl_client.get_project_variables(downstream_project_id)
    discovery_secret_key = None
    for var_info in downstream_vars:
        if var_info["key"] == SECRET_KEY:
            discovery_secret_key = var_info["value"]
            break
    logger.info("Discovery secret key fetched")

    process_discovery_files(
        env_name,
        f"{base_dir}/environments",
        passport_discovery_files,
        discovery_secret_key
    )
    logger.info(f"Discovery of cloud passport for environment {env_name} completed successfully")


if __name__ == "__main__":
    main()
