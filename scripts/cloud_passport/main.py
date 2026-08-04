import os
import re
import shutil
import time
from pathlib import Path
from urllib.parse import quote

from envgenehelper import logger, findAllFilesInDir, writeYamlToFile, readYaml
from envgenehelper import openYaml, unpack_archive, cleanup_dir, addHeaderToYaml, crypt, fetch_cred_value
from envgenehelper.crypt import get_configured_encryption_type
from envgenehelper.git_helper import GitLabClient
from envgenehelper.errors import ValidationError

from cloud_passport.cmdb import update_creds_to_cmdb_format
from envgenehelper import get_cred_config

SECRET_KEY = "SECRET_KEY"
PASSPORT_JOB_NAME = "get_cloud_passport"
POLL_INTERVAL_SECONDS = 10
POLL_MAX_TRIES = int(os.getenv("CP_DISCOVERY_POLL_MAX_TRIES", "30"))
PIPELINE_TERMINAL_STATUSES = frozenset({"success", "failed", "canceled", "skipped"})

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


def run_cloud_passport():
    env_name = os.getenv("FULL_ENV_NAME")
    logger.info(f"Starting discovery of cloud passport for environment {env_name}")
    base_dir = os.getenv("CI_PROJECT_DIR")

    integration_config = get_integration_config(Path(f"{base_dir}/configuration/integration.yml"))
    cred_config = get_cred_config()
    cp_discovery = integration_config.get("cp_discovery", {}).get("gitlab", {})
    project_path = cp_discovery.get("project")
    branch = cp_discovery.get("branch")
    discovery_token = fetch_cred_value(cp_discovery.get("token"), cred_config)

    gl_client = GitLabClient(token=discovery_token)

    pipeline = gl_client.trigger_pipeline(
        project_path=project_path,
        ref=branch,
        variables={"ENV_NAME": env_name},
    )
    pipeline_id = pipeline["id"]
    logger.info(f"Triggered Discovery pipeline {pipeline_id} on {project_path}@{branch}")

    encoded_path = quote(project_path, safe="")
    pipeline_url = f"{gl_client.api_url}/projects/{encoded_path}/pipelines/{pipeline_id}"

    status = ""
    for attempt in range(1, POLL_MAX_TRIES + 1):
        status = gl_client.http.get_json(pipeline_url, headers=gl_client.headers).get("status") or ""
        logger.info(
            f"Discovery pipeline {pipeline_id} status: {status} "
            f"(attempt {attempt}/{POLL_MAX_TRIES})"
        )
        if not status:
            raise ValidationError(
                f"Discovery pipeline {pipeline_id} status unavailable "
                f"(pipeline missing or API error)"
            )
        if status in PIPELINE_TERMINAL_STATUSES:
            break
        if attempt == POLL_MAX_TRIES:
            raise ValidationError(
                f"Discovery pipeline {pipeline_id} did not finish after "
                f"{POLL_MAX_TRIES} status checks (last status: {status})"
            )
        time.sleep(POLL_INTERVAL_SECONDS)

    if status != "success":
        raise ValidationError(f"Discovery pipeline {pipeline_id} finished with status: {status}")

    jobs = gl_client.get_pipeline_jobs(project_path, pipeline_id)
    logger.info(f"Discovery pipeline jobs fetched: {jobs}")
    passport_job = next((job for job in jobs if job.get("name") == PASSPORT_JOB_NAME), None)
    if not passport_job:
        raise ValidationError(f"Job '{PASSPORT_JOB_NAME}' not found in Discovery pipeline {pipeline_id}")

    passport_archive_path = "/tmp/archive.zip"
    gl_client.download_job_artifacts(
        project_path,
        passport_job["id"],
        passport_archive_path,
    )

    passport_unpack_path = Path("/tmp/passport")
    unpack_archive(passport_archive_path, os.path.dirname(passport_unpack_path))
    passport_discovery_files = list(Path(passport_unpack_path).rglob("*"))

    discovery_vars = gl_client.get_project_variables(project_path)
    discovery_secret_key = None
    for var_info in discovery_vars:
        if var_info["key"] == SECRET_KEY:
            discovery_secret_key = var_info["value"]
            break
    logger.info("Discovery secret key fetched")

    process_discovery_files(
        env_name,
        f"{base_dir}/environments",
        passport_discovery_files,
        discovery_secret_key,
    )
    logger.info(f"Discovery of cloud passport for environment {env_name} completed successfully")
