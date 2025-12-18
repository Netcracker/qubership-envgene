import asyncio
import os
import re
import shutil
import tempfile
import xml.etree.ElementTree as ET
from functools import partial
from pathlib import Path
from typing import Any, Optional
from urllib.parse import urljoin, urlparse, urlunparse
from zipfile import ZipFile

import aiohttp
import requests
from envgenehelper import logger
from requests.auth import HTTPBasicAuth

from artifact_searcher.utils.constants import DEFAULT_REQUEST_TIMEOUT
from artifact_searcher.utils.models import Application, ArtifactInfo, Credentials, FileExtension, Registry

WORKSPACE = os.getenv("WORKSPACE", Path(tempfile.gettempdir()) / "zips")

# V2 timeouts for cloud registries
V2_SEARCH_TIMEOUT = 60  # Timeout for find_artifact_urls
V2_DOWNLOAD_TIMEOUT = 120  # Timeout for download_artifact
V2_HTTP_TIMEOUT = (30, 60)  # (connect, read) for HTTP requests


def convert_nexus_repo_url_to_index_view(url: str) -> str:
    parsed = urlparse(url)

    parts = parsed.path.rstrip("/").split("/")

    if not parts or parts[-1] != "repository":
        return url

    new_parts = parts[:-1] + ["service", "rest", "repository", "browse"]
    new_path = "/".join(new_parts) + "/"

    return urlunparse(parsed._replace(path=new_path))


def create_full_url(app: Application, version: str, repo: str, artifact_extension: FileExtension, folder: str) -> str:
    artifact_id = app.artifact_id
    registry_url = app.registry.maven_config.repository_domain_name
    group_id = app.group_id.replace(".", "/")
    path = f"{folder}/{artifact_id}-{version}.{artifact_extension.value}"
    return urljoin(registry_url, "/".join([repo, group_id, artifact_id, path]))


async def resolve_snapshot_version_async(
    session,
    app: Application,
    version: str,
    repo_value: str,
    stop_event: asyncio.Event,
    classifier: str = "",
    extension: FileExtension = FileExtension.JSON,
) -> str | None:
    if stop_event.is_set():
        return None
    if not version.endswith("-SNAPSHOT"):
        return version

    group_id = app.group_id.replace(".", "/")
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

                if node_classifier == classifier and node_extension == extension.value:
                    stop_event.set()
                    logger.info(f"Resolved snapshot version {version} to {value}")
                    return value

            logger.warning(f"No matching snapshotVersion found for {app.artifact_id} in {metadata_url}")
            return None

    except Exception as e:
        logger.warning(f"Error resolving snapshot version from {metadata_url}: {e}")
        return None


def version_to_folder_name(version: str) -> str:
    """Normalize timestamped snapshot version to -SNAPSHOT folder name."""
    snapshot_pattern = re.compile(r"-\d{8}\.\d{6}-\d+$")
    return snapshot_pattern.sub("-SNAPSHOT", version) if snapshot_pattern.search(version) else version


def download_json_content(url: str) -> dict[str, Any]:
    response = requests.get(url, timeout=DEFAULT_REQUEST_TIMEOUT)
    response.raise_for_status()
    json_data = response.json()
    logger.debug(f"Got the json data by url {url}")
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
    return f"{WORKSPACE}/{app_name}/{app_version}"


async def download(session, artifact_info: ArtifactInfo) -> ArtifactInfo:
    if artifact_info.local_path:
        logger.info(f"Artifact already downloaded: {artifact_info.local_path}")
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


async def check_artifact_by_full_url_async(
    app: Application, version: str, repo, artifact_extension: FileExtension, folder: str, stop_event, session
) -> tuple[str, tuple[str, str]] | None:
    if stop_event.is_set():
        return None
    repo_value, repo_pointer = repo
    if repo_value:
        full_url = create_full_url(app, version, repo_value, artifact_extension, folder)
        try:
            async with session.head(full_url, timeout=DEFAULT_REQUEST_TIMEOUT) as response:
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
    maven = registry.maven_config
    repos = {
        maven.target_snapshot: "targetSnapshot",
        maven.target_staging: "targetStaging",
        maven.target_release: "targetRelease",
        maven.snapshot_group: "snapshotGroup",
    }
    return repos


def get_repo_pointer(repo_value: str, registry: Registry):
    repos_dict = get_repo_value_pointer_dict(registry)
    return repos_dict.get(repo_value)


async def _attempt_check(
    app: Application, version: str, artifact_extension: FileExtension, registry_url: str | None = None
) -> Optional[tuple[str, tuple[str, str]]]:
    folder = version_to_folder_name(version)
    check_artifact_stop_event = asyncio.Event()
    resolve_snapshot_stop_event = asyncio.Event()

    repos_dict = get_repo_value_pointer_dict(app.registry)
    if registry_url:
        app.registry.maven_config.repository_domain_name = registry_url

    async with aiohttp.ClientSession() as session:
        resolved_version = version
        if version.endswith("-SNAPSHOT"):
            resolve_snapshot_coros = [
                (resolve_snapshot_version_async(session, app, version, repo[0], resolve_snapshot_stop_event, extension=artifact_extension))
                for repo in repos_dict.items()
            ]
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
                    check_artifact_by_full_url_async(
                        app, resolved_version, repo, artifact_extension, folder, check_artifact_stop_event, session
                    )
                )
                for repo in repos_dict.items()
            ]

        for task in check_artifact_tasks:
            result = task.result()
            if result is not None:
                return result


async def check_artifact_async(
    app: Application, artifact_extension: FileExtension, version: str,
    env_creds: Optional[dict] = None
) -> Optional[tuple[str, tuple[str, str]]]:
    registry_version = getattr(app.registry, 'version', "1.0")

    if registry_version == "2.0":
        logger.info(f"Detected RegDef V2 for {app.name}, attempting cloud-aware search")
        try:
            return await _check_artifact_v2_async(app, artifact_extension, version, env_creds)
        except Exception as e:
            logger.warning(f"V2 artifact search failed for {app.name}: {e}. Falling back to V1.")
            return await _check_artifact_v1_async(app, artifact_extension, version)
    else:
        logger.debug(f"Using V1 artifact search for {app.name} (version={registry_version})")
        return await _check_artifact_v1_async(app, artifact_extension, version)


async def _check_artifact_v2_async(app: Application, artifact_extension: FileExtension, version: str,
                                   env_creds: Optional[dict]) -> Optional[tuple[str, tuple[str, str]]]:
    if not getattr(app.registry.maven_config, 'auth_config', None):
        return await _check_artifact_v1_async(app, artifact_extension, version)

    try:
        from artifact_searcher.cloud_auth_helper import CloudAuthHelper
        from qubership_pipelines_common_library.v1.maven_client import Artifact as MavenArtifact
    except ImportError:
        return await _check_artifact_v1_async(app, artifact_extension, version)

    auth_config = CloudAuthHelper.resolve_auth_config(app.registry, "maven")
    if not auth_config or auth_config.provider not in ["aws", "gcp", "artifactory", "nexus"]:
        return await _check_artifact_v1_async(app, artifact_extension, version)

    # AWS and GCP require credentials; Artifactory/Nexus can work with anonymous access
    if auth_config.provider in ["aws", "gcp"] and not env_creds:
        logger.warning(f"V2 {auth_config.provider} requires credentials but env_creds is empty")
        return await _check_artifact_v1_async(app, artifact_extension, version)
    if auth_config.provider in ["aws", "gcp"] and auth_config.credentials_id and auth_config.credentials_id not in (env_creds or {}):
        logger.warning(f"V2 {auth_config.provider} credentials '{auth_config.credentials_id}' not found in env_creds")
        return await _check_artifact_v1_async(app, artifact_extension, version)

    logger.info(f"V2 search for {app.name} with provider={auth_config.provider}")
    loop = asyncio.get_running_loop()

    try:
        searcher = await loop.run_in_executor(None, CloudAuthHelper.create_maven_searcher, app.registry, env_creds)
    except Exception as e:
        logger.warning(f"Failed to create V2 searcher for {app.name}: {e}")
        return await _check_artifact_v1_async(app, artifact_extension, version)

    artifact_string = f"{app.group_id}:{app.artifact_id}:{version}"
    maven_artifact = MavenArtifact.from_string(artifact_string)
    maven_artifact.extension = artifact_extension.value

    max_retries = 2
    last_error = None
    local_path = None
    maven_url = None

    for attempt in range(max_retries):
        try:
            if attempt > 0:
                logger.info(f"Retry {attempt} for {app.name} after 5s delay...")
                await asyncio.sleep(5)
                searcher = await loop.run_in_executor(None, CloudAuthHelper.create_maven_searcher, app.registry, env_creds)

            # Wrap find_artifact_urls with timeout to prevent indefinite hangs
            urls = await asyncio.wait_for(
                loop.run_in_executor(None, partial(searcher.find_artifact_urls, artifact=maven_artifact)),
                timeout=V2_SEARCH_TIMEOUT
            )
            if not urls:
                logger.warning(f"No artifacts found for {app.artifact_id}:{version}")
                return None

            maven_url = urls[0]
            logger.info(f"Found V2 artifact: {maven_url}")

            local_path = os.path.join(create_app_artifacts_local_path(app.name, version), os.path.basename(maven_url))
            os.makedirs(os.path.dirname(local_path), exist_ok=True)

            download_success = await _v2_download_with_fallback(
                searcher, maven_url, local_path, auth_config, app.registry, env_creds
            )

            if download_success:
                logger.info(f"V2 artifact downloaded: {local_path}")
                break
            raise TimeoutError(f"V2 download failed for {maven_url}")

        except asyncio.TimeoutError:
            last_error = TimeoutError(f"V2 search timed out after {V2_SEARCH_TIMEOUT}s")
            logger.warning(f"V2 search timed out for {app.name} (attempt {attempt + 1}/{max_retries})")
            if attempt < max_retries - 1:
                continue
            return await _check_artifact_v1_async(app, artifact_extension, version)

        except Exception as e:
            last_error = e
            error_str = str(e).lower()
            if attempt < max_retries - 1 and any(x in error_str for x in ["401", "unauthorized", "forbidden", "expired", "timeout"]):
                logger.warning(f"V2 error for {app.name}: {e}, retrying...")
                continue
            logger.warning(f"V2 failed after {max_retries} attempts for {app.name}: {e}")
            return await _check_artifact_v1_async(app, artifact_extension, version)
    else:
        logger.warning(f"V2 failed after {max_retries} attempts: {last_error}")
        return await _check_artifact_v1_async(app, artifact_extension, version)

    if auth_config.provider == "aws":
        registry_domain = app.registry.maven_config.repository_domain_name
        folder_name = version_to_folder_name(version)
        repo_path = app.registry.maven_config.target_snapshot if folder_name.endswith("-SNAPSHOT") else app.registry.maven_config.target_release
        full_url = f"{registry_domain.rstrip('/')}/{repo_path.rstrip('/')}/{maven_url}"
    else:
        full_url = maven_url

    return full_url, ("v2_downloaded", local_path)


async def _v2_download_with_fallback(searcher, url: str, local_path: str, auth_config,
                                     registry: Registry, env_creds: Optional[dict]) -> bool:
    loop = asyncio.get_running_loop()

    try:
        await asyncio.wait_for(
            loop.run_in_executor(None, lambda: searcher.download_artifact(url, str(local_path))),
            timeout=V2_DOWNLOAD_TIMEOUT
        )
        return True
    except asyncio.TimeoutError:
        logger.warning(f"Searcher download timed out after {V2_DOWNLOAD_TIMEOUT}s")
    except Exception as e:
        logger.warning(f"Searcher download failed: {e}")

    if auth_config.provider not in ["gcp", "artifactory", "nexus"]:
        return False

    try:
        from artifact_searcher.cloud_auth_helper import CloudAuthHelper
        headers = {}
        if auth_config.provider == "gcp":
            sa_json = CloudAuthHelper.get_gcp_credentials_from_registry(registry, env_creds)
            if sa_json:
                token = CloudAuthHelper.get_gcp_access_token(sa_json)
                if token:
                    headers["Authorization"] = f"Bearer {token}"

        response = requests.get(url, headers=headers, timeout=V2_HTTP_TIMEOUT, stream=True)
        response.raise_for_status()
        with open(local_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        logger.info(f"Direct HTTP download successful: {local_path}")
        return True
    except Exception as e:
        logger.warning(f"Direct HTTP download failed: {e}")
        return False


async def _check_artifact_v1_async(app: Application, artifact_extension: FileExtension,
                                   version: str) -> Optional[tuple[str, tuple[str, str]]]:
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
    return None


def unzip_file(artifact_id: str, app_name: str, app_version: str, zip_url: str):
    extracted = False
    app_artifacts_dir = f"{artifact_id}/"
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
