import asyncio
import os
import re
import shutil
import tempfile
from pathlib import Path
from typing import Any, Optional
from functools import partial
from urllib.parse import urljoin
from zipfile import ZipFile

import aiohttp
import requests
from loguru import logger
from requests.auth import HTTPBasicAuth
from artifact_searcher.utils.models import Registry, Application, FileExtension, Credentials, ArtifactInfo

DEFAULT_REQUEST_TIMEOUT = 30
WORKSPACE = limit = os.getenv("WORKSPACE", Path(tempfile.gettempdir()) / "zips")


def create_full_url(app: Application, version: str, repo: str, artifact_extension: FileExtension, folder: str) -> str:
    artifact_id = app.artifact_id
    registry_url = app.registry.maven_config.repository_domain_name
    group_id = app.group_id.replace(".", "/")
    path = f"{folder}/{artifact_id}-{version}.{artifact_extension.value}"
    return urljoin(registry_url, "/".join([repo, group_id, artifact_id, path]))


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
    response = requests.get(url, timeout=os.getenv("REQUEST_TIMEOUT", DEFAULT_REQUEST_TIMEOUT))
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
    # Skip download if already downloaded (V2 cloud artifacts)
    if artifact_info.local_path:
        logger.info(f"Artifact already downloaded (V2): {artifact_info.local_path}")
        return artifact_info
    
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
                                           folder: str,
                                           stop_event, session) -> tuple[str, tuple[str, str]] | None:
    if stop_event.is_set():
        return None
    repo_value, repo_pointer = repo
    if repo_value:
        full_url = create_full_url(app, version, repo_value, artifact_extension, folder)
        try:
            async with session.head(full_url,
                                    timeout=os.getenv("REQUEST_TIMEOUT", DEFAULT_REQUEST_TIMEOUT)) as response:
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


async def check_artifact_async(app: Application, artifact_extension: FileExtension, version: str,
                               env_creds: Optional[dict] = None) -> Optional[tuple[str, tuple[str, str]]]:
    """
    Checks if artifact exists in registry and returns its URL.
    Routes to V2 (cloud-aware) or V1 (URL-based) search based on Registry version.
    """
    registry_version = getattr(app.registry, 'version', "1.0")
    
    if registry_version == "2.0":
        logger.info(f"Detected RegDef V2 for {app.name}, attempting cloud-aware search")
        try:
            return await _check_artifact_v2_async(app, artifact_extension, version, env_creds)
        except Exception as e:
            logger.warning(
                f"V2 artifact search failed for {app.name}: {e}. "
                f"Falling back to V1 URL-based search."
            )
            return await _check_artifact_v1_async(app, artifact_extension, version)
    else:
        logger.debug(f"Using V1 artifact search for {app.name} (version={registry_version})")
        return await _check_artifact_v1_async(app, artifact_extension, version)


async def _check_artifact_v2_async(app: Application, artifact_extension: FileExtension, version: str,
                                   env_creds: Optional[dict]) -> Optional[tuple[str, tuple[str, str]]]:
    """
    V2 artifact search using Maven Client with cloud authentication.
    Falls back to V1 if credentials or authConfig are missing.
    """
    if not env_creds:
        logger.warning(f"V2 registry but no env_creds provided for {app.name}, falling back to V1")
        return await _check_artifact_v1_async(app, artifact_extension, version)
    
    auth_config_ref = getattr(app.registry.maven_config, 'auth_config', None)
    if not auth_config_ref:
        logger.warning(f"V2 registry but no maven authConfig reference for {app.name}, falling back to V1")
        return await _check_artifact_v1_async(app, artifact_extension, version)
    
    try:
        from artifact_searcher.cloud_auth_helper import CloudAuthHelper
        from qubership_pipelines_common_library.v1.maven_client import Artifact as MavenArtifact
        
        auth_config = CloudAuthHelper.resolve_auth_config(app.registry, "maven")
        
        if not auth_config or not auth_config.provider:
            logger.warning(f"V2 registry but no cloud provider for {app.name}, falling back to V1")
            return await _check_artifact_v1_async(app, artifact_extension, version)
        
        if auth_config.provider not in ["aws", "gcp"]:
            logger.warning(f"V2 registry with unsupported provider '{auth_config.provider}' for {app.name}, falling back to V1")
            return await _check_artifact_v1_async(app, artifact_extension, version)
        
        logger.info(f"Creating Maven Client searcher for {app.name} with provider={auth_config.provider}")
        loop = asyncio.get_event_loop()
        
        searcher = await loop.run_in_executor(None, CloudAuthHelper.create_maven_searcher, app.registry, env_creds)
        
        maven_artifact = MavenArtifact(artifact_id=app.artifact_id, version=version, extension=artifact_extension.value)
        logger.info(f"Searching for artifact {app.artifact_id}:{version} using Maven Client")
        urls = await loop.run_in_executor(None, partial(searcher.find_artifact_urls, artifact=maven_artifact))
        
        if not urls:
            logger.warning(f"No artifacts found for {app.artifact_id}:{version} via Maven Client")
            return None
        
        # Maven Client returns relative path, construct full URL from registry base URL
        maven_relative_path = urls[0]
        logger.info(f"Found artifact via Maven Client at: {maven_relative_path}")
        
        # Download artifact directly using Maven Client (handles auth internally)
        logger.info(f"Downloading artifact {app.artifact_id}:{version} using Maven Client")
        app_local_path = create_app_artifacts_local_path(app.name, version)
        artifact_filename = os.path.basename(maven_relative_path)
        local_path = os.path.join(app_local_path, artifact_filename)
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        
        # Use Maven Client to download (it handles authentication)
        # Note: download_artifact expects (resolved_url_string, destination_path_string)
        def download_with_searcher():
            searcher.download_artifact(maven_relative_path, str(local_path))
            return local_path
        
        downloaded_path = await loop.run_in_executor(None, download_with_searcher)
        logger.info(f"Downloaded artifact to: {downloaded_path}")
        
        # Determine base URL from registry config for compatibility
        folder = version_to_folder_name(version)
        if folder == "releases":
            base_url = app.registry.maven.target_release
        elif folder == "staging":
            base_url = app.registry.maven.target_staging
        else:
            base_url = app.registry.maven.target_snapshot
        
        # Return full URL for logging/tracking (artifact already downloaded)
        full_url = f"{base_url.rstrip('/')}/{maven_relative_path}"
        return full_url, ("v2_downloaded", local_path)
        
    except Exception as e:
        logger.error(f"Error in V2 search: {e}", exc_info=True)
        raise


async def _check_artifact_v1_async(app: Application, artifact_extension: FileExtension,
                                   version: str) -> Optional[tuple[str, tuple[str, str]]]:
    """
    V1 artifact search using URL-based approach.
    """
    folder = version_to_folder_name(version)
    stop_event = asyncio.Event()

    repos_dict = get_repo_value_pointer_dict(app.registry)

    async with aiohttp.ClientSession() as session:
        async with asyncio.TaskGroup() as tg:
            tasks = [tg.create_task(
                check_artifact_by_full_url_async(app, version, repo, artifact_extension, folder,
                                                 stop_event, session)) for repo in repos_dict.items()]
        for task in tasks:
            result = task.result()
            if result is not None:
                return result


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
