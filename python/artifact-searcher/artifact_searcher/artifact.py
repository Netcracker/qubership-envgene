import asyncio
import os
import re
import shutil
import tempfile
from pathlib import Path
from typing import Any, Optional
from urllib.parse import urljoin, urlparse, urlunparse
from zipfile import ZipFile
import xml.etree.ElementTree as ET

import aiohttp
import requests
from loguru import logger
from requests.auth import HTTPBasicAuth
from artifact_searcher.utils.models import Registry, Application, FileExtension, Credentials, ArtifactInfo
from artifact_searcher.utils.constants import DEFAULT_REQUEST_TIMEOUT

WORKSPACE = limit = os.getenv("WORKSPACE", Path(tempfile.gettempdir()) / "zips")


def convert_nexus_repo_url_to_index_view(url: str) -> str:
    parsed = urlparse(url)

    parts = parsed.path.rstrip("/").split("/")

    if not parts or parts[-1] != "repository":
        return url

    # Build new path
    new_parts = parts[:-1] + ["service", "rest", "repository", "browse"]
    new_path = "/".join(new_parts) + "/"

    return urlunparse(parsed._replace(path=new_path))

def create_full_url(app: Application, version: str, repo: str, artifact_extension: FileExtension, folder: str) -> str:
    artifact_id = app.artifact_id
    registry_url = app.registry.maven_config.repository_domain_name
    group_id = app.group_id.replace(".", "/")
    path = f"{folder}/{artifact_id}-{version}.{artifact_extension.value}"
    return urljoin(registry_url, "/".join([repo, group_id, artifact_id, path]))


async def resolve_snapshot_version_async(session, app: Application, version: str, repo_value: str, stop_event: asyncio.Event, classifier: str="", extension: FileExtension=FileExtension.JSON) -> str | None:
    if stop_event.is_set():
        return None
    if not version.endswith('-SNAPSHOT'):
        return version

    group_id = app.group_id.replace('.', '/')
    artifact_id = app.artifact_id
    registry_url = app.registry.maven_config.repository_domain_name

    metadata_path = f"{repo_value}/{group_id}/{artifact_id}/{version}/maven-metadata.xml"
    metadata_url = urljoin(registry_url, metadata_path)

    try:
        async with session.get(metadata_url, timeout=DEFAULT_REQUEST_TIMEOUT) as response:
            if response.status != 200:
                logger.warning(f"Failed to fetch maven-metadata.xml: {metadata_url}, status: {response.status}")
                return None

            content = await response.text()
            root = ET.fromstring(content)
            snapshot_versions = root.findall(".//snapshotVersions/snapshotVersion")
            if not snapshot_versions:
                logger.warning(f"No <snapshotVersions> found in {metadata_url}")
                return None

            for node in snapshot_versions:
                node_classifier = node.findtext("classifier", default="")
                node_extension = node.findtext("extension", default="")
                value = node.findtext("value")

                if (
                    node_classifier == classifier and
                    node_extension == extension
                ):
                    stop_event.set()
                    logger.info(f"Resolved snapshot version {version} to {value}")
                    return value

            logger.warning(f"No matching snapshotVersion found for {app.artifact_id} in {metadata_url}")

    except Exception as e:
        logger.warning(f"Error resolving snapshot version from {metadata_url}: {e}")


def version_to_folder_name(version: str):
    """
    Normalizes version string for folder naming.

    If version is timestamped snapshot (e.g. '1.0.0-20240702.123456-1'), it replaces the timestamp suffix with
    '-SNAPSHOT'. Otherwise, returns the version unchanged
    """
    snapshot_pattern = re.compile(r"-\d{8}\.\d{6}-\d+$")
    if snapshot_pattern.search(version):
        folder = snapshot_pattern.sub('-SNAPSHOT', version)
    else:
        folder = version
    return folder


def download_json_content(url: str) -> dict[str, Any]:
    response = requests.get(url, timeout=DEFAULT_REQUEST_TIMEOUT)
    response.raise_for_status()
    json_data = response.json()
    logger.debug(f'Got the json data by url {url}')
    return json_data


def clean_temp_dir():
    if WORKSPACE.exists():
        shutil.rmtree(WORKSPACE)
    os.makedirs(WORKSPACE, exist_ok=True)


async def download_all_async(artifacts_info: list[ArtifactInfo]):
    connector = aiohttp.TCPConnector(limit=os.getenv("TCP_CONNECTION_LIMIT", 100))
    async with aiohttp.ClientSession(connector=connector) as session:
        async with asyncio.TaskGroup() as tg:
            tasks = [tg.create_task(download(session, artifact_info)) for artifact_info in artifacts_info]
        results = []
        errors = []

        for i, task in enumerate(tasks):
            result = task.result()
            if not result or result.local_path is None:
                errors.append(f"Task {i}: artifact was not downloaded")
            else:
                results.append(result)

        if errors:
            raise ValueError("Some tasks failed:\n" + "\n".join(errors))

        return results


def create_app_artifacts_local_path(app_name, app_version):
    return f'{WORKSPACE}/{app_name}/{app_version}'


async def download(session, artifact_info: ArtifactInfo) -> ArtifactInfo:
    """
    Downloads an artifact to a local directory: <workspace_dir>/<app_name>/<app_version>/filename.extension
    Sets full local path of artifact to artifact info
    Returns:
        ArtifactInfo: Object containing related information about the artifact
    """
    url = artifact_info.url
    app_local_path = create_app_artifacts_local_path(artifact_info.app_name, artifact_info.app_version)
    artifact_local_path = os.path.join(app_local_path, os.path.basename(url))
    os.makedirs(os.path.dirname(artifact_local_path), exist_ok=True)
    try:
        async with session.get(url) as response:
            if response.status == 200:
                with open(artifact_local_path, "wb") as f:
                    f.write(await response.read())
                logger.info(f"Downloaded: {artifact_local_path}")
                artifact_info.local_path = artifact_local_path
                return artifact_info
            else:
                logger.error(f"Download process with error {response.text}: {url}")
    except Exception as e:
        logger.error(f"Download process with exception {url}: {e}")


async def check_artifact_by_full_url_async(app: Application, version: str, repo, artifact_extension: FileExtension,
                                           folder: str, stop_event, session) -> tuple[str, tuple[str, str]] | None:
    if stop_event.is_set():
        return None
    repo_value, repo_pointer = repo
    if repo_value:
        full_url = create_full_url(app, version, repo_value, artifact_extension, folder)
        try:
            async with session.head(full_url,
                                    timeout=DEFAULT_REQUEST_TIMEOUT) as response:
                if response.status == 200:
                    stop_event.set()
                    logger.info(f"Successful while checking if artifact is present with URL {full_url}")
                    return full_url, repo
                logger.warning(f"Failed while checking if artifact is present with URL {full_url}, {response.text}")
        except Exception as e:
            logger.warning(f"Failed while checking if artifact is present with URL {full_url}, {e}")
    else:
        logger.warning(f"Repository {repo_pointer} is not configured for registry {app.registry.name}")


def get_repo_value_pointer_dict(registry: Registry):
    """Permanent set of repositories for searching of artifacts"""
    maven = registry.maven_config
    repos = {maven.target_snapshot: "targetSnapshot", maven.target_staging: "targetStaging",
             maven.target_release: "targetRelease", maven.snapshot_group: "snapshotGroup"}
    return repos


def get_repo_pointer(repo_value: str, registry: Registry):
    repos_dict = get_repo_value_pointer_dict(registry)
    return repos_dict.get(repo_value)


async def _attempt_check(app: Application, version: str, artifact_extension: FileExtension, registry_url: str | None=None) -> Optional[tuple[str, tuple[str, str]]]:
    """Helper function to attempt artifact check with a given registry URL"""
    folder = version_to_folder_name(version)
    check_artifact_stop_event = asyncio.Event()
    resolve_snapshot_stop_event = asyncio.Event()

    repos_dict = get_repo_value_pointer_dict(app.registry)
    if registry_url:
        app.registry.maven_config.repository_domain_name = registry_url

    async with aiohttp.ClientSession() as session:
        resolved_version = version
        resolve_snapshot_coros = [(resolve_snapshot_version_async(session, app, version, repo[0], resolve_snapshot_stop_event, extension=artifact_extension)) for repo in repos_dict.items()]
        if version.endswith('-SNAPSHOT'):
            async with asyncio.TaskGroup() as resolve_snapshot_tg:
                resolve_snapshot_tasks = [resolve_snapshot_tg.create_task(coro) for coro in resolve_snapshot_coros]
            for task in resolve_snapshot_tasks:
                result = task.result()
                if result is None:
                    continue
                resolved_version = result
                folder = version_to_folder_name(resolved_version)
                logger.info(f"Using resolved snapshot version: {resolved_version}")
                break
        async with asyncio.TaskGroup() as check_artifact_tg:
            check_artifact_tasks = [
                check_artifact_tg.create_task(
                    check_artifact_by_full_url_async(app, resolved_version, repo, artifact_extension, folder, check_artifact_stop_event, session)
                )
                for repo in repos_dict.items()
            ]

        for task in check_artifact_tasks:
            result = task.result()
            if result is not None:
                return result

async def check_artifact_async(app: Application, artifact_extension: FileExtension, version: str) -> Optional[
                                                                                                         tuple[
                                                                                                             str, tuple[
                                                                                                                 str, str]]] | None:
    """
    Resolves the full artifact URL and the first repository where it was found.
    Supports both release and snapshot versions.

    Returns:
        Optional[tuple[str, tuple[str, str]]]: A tuple containing:
            - str: Full URL to the artifact.
            - tuple[str, str]: A pair of (repository name, repository pointer/alias in CMDB).
            Returns None if the artifact could not be resolved
    """

    result = await _attempt_check(app, version, artifact_extension)
    if result is not None:
        return result

    if not app.registry.maven_config.is_nexus:
        return result

    original_domain = app.registry.maven_config.repository_domain_name
    fixed_domain = convert_nexus_repo_url_to_index_view(original_domain)
    if fixed_domain != original_domain:
        logger.info(f"Retrying artifact check with edited domain: {fixed_domain}")
        result = await _attempt_check(app, version, artifact_extension, fixed_domain)
        if result is not None:
            return result
    else:
        logger.debug("Domain is same after editing, skipping retry")

    logger.warning("Artifact not found")

def unzip_file(artifact_id: str, app_name: str, app_version: str, zip_url: str):
    extracted = False
    app_artifacts_dir = f'{artifact_id}/'
    try:
        with ZipFile(zip_url, "r") as zip_file:
            for file in zip_file.namelist():
                if file.startswith(app_artifacts_dir):
                    zip_file.extract(file, create_app_artifacts_local_path(app_name, app_version))
                    extracted = True
    except Exception as e:
        logger.error(f"Error unpacking {e}")
    if not extracted:
        logger.warning(f"No files were extracted for application {app_name}:{app_version}")


def create_aql_artifacts(aqls: list[str]):
    return f'items.find({{"$or":  [{', '.join(aqls)}]}})'


def create_artifact_path(app: Application, version: str):
    group_id = app.group_id.replace(".", "/")
    folder = version_to_folder_name(version)
    return f"{group_id}/{app.artifact_id}/{folder}"


def create_artifact_name(app: Application, artifact_extension: FileExtension, version: str):
    return f"{app.artifact_id}-{version}.{artifact_extension.value}"


def create_aql_artifact(app: Application, artifact_extension: FileExtension, version: str) -> str:
    path = create_artifact_path(app, version)
    name = create_artifact_name(app, artifact_extension, version)
    aql = f'{{"$and": [{{"name": "{name}"}},{{"path":"{path}"}}]}}'
    return aql


def check_artifacts_by_aql(aql: str, cred: Credentials, url: str) -> list[ArtifactInfo]:
    artifacts = []
    response = requests.post(f"{url}/api/search/aql", data=aql, auth=HTTPBasicAuth(cred.username, cred.password))
    results = response.json()
    for result in results.get("results"):
        repo = result.get("repo")
        path = result.get("path")
        name = result.get("name")
        url = f"{url}/{repo}/{path}/{name}"
        artifact = ArtifactInfo(repo=repo, path=path, name=name, url=url)
        artifacts.append(artifact)
    return artifacts
