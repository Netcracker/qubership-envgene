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
from aiohttp import BasicAuth
from requests.auth import HTTPBasicAuth

from artifact_searcher.utils.constants import DEFAULT_REQUEST_TIMEOUT, TCP_CONNECTION_LIMIT, METADATA_XML
from artifact_searcher.utils.models import Registry, Application, FileExtension, Credentials, ArtifactInfo
from envgenehelper import logger

try:
    from qubership_pipelines_common_library.v1.maven_client import Artifact as MavenArtifact
except ImportError:
    MavenArtifact = None

try:
    from artifact_searcher.cloud_auth_helper import CloudAuthHelper
except ImportError:
    CloudAuthHelper = None

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
    # Build new path
    new_parts = parts[:-1] + ["service", "rest", "repository", "browse"]
    new_path = "/".join(new_parts) + "/"

    return urlunparse(parsed._replace(path=new_path))


def create_artifact_path(app: Application, version: str, repo: str) -> str:
    registry_url = app.registry.maven_config.repository_domain_name.rstrip("/") + "/"
    group_id = app.group_id.replace(".", "/")
    folder = version_to_folder_name(version)
    return urljoin(registry_url, f"{repo}/{group_id}/{app.artifact_id}/{folder}/")


def create_full_url(app: Application, version: str, repo: str, artifact_extension: FileExtension,
                    classifier: str = "") -> str:
    base_path = create_artifact_path(app, version, repo)
    filename = create_artifact_name(app.artifact_id, artifact_extension, version, classifier)
    return urljoin(base_path, filename)


def _create_metadata_url(app: Application, version: str, repo_value: str) -> str:
    base_path = create_artifact_path(app, version, repo_value)
    return urljoin(base_path, METADATA_XML)


async def resolve_snapshot_version_async(
        session,
        app: Application,
        version: str,
        repo_value: str,
        task_id: int,
        stop_artifact_event: asyncio.Event,
        stop_snapshot_event_for_others: asyncio.Event,
        extension: FileExtension = FileExtension.JSON,
        classifier: str = ""
) -> tuple[str, int] | None:
    metadata_url = _create_metadata_url(app, version, repo_value)
    if stop_artifact_event.is_set() or stop_snapshot_event_for_others.is_set():
        return None
    try:
        async with session.get(metadata_url) as response:
            if response.status != 200:
                logger.warning(
                    f"[Task {task_id}] [Application: {app.name}: {version}] - Failed to fetch maven-metadata.xml: {metadata_url}, status: {response.status}")
                return None

            content = await response.text()
            resolved_version = _parse_snapshot_version(content, app, task_id, extension, version, classifier)
            if resolved_version:
                stop_snapshot_event_for_others.set()
                logger.info(
                    f"[Task {task_id}] [Application: {app.name}: {version}] - Successfully fetched maven-metadata.xml: {metadata_url}")
                return resolved_version, task_id
            return None
    except Exception as e:
        logger.warning(
            f"[Task {task_id}] [Application: {app.name}: {version}] - Error resolving snapshot version from {metadata_url}: {e}")


def _parse_snapshot_version(
        content: str,
        app: Application,
        task_id: int,
        extension: FileExtension,
        version: str,
        classifier: str = ""
) -> str | None:
    root = ET.fromstring(content)
    
    # Trying new-style <snapshotVersions> first (Maven 3+) if its not found then its switched to Old Style
    snapshot_versions = root.findall(".//snapshotVersions/snapshotVersion")
    if snapshot_versions:
        for node in snapshot_versions:
            node_classifier = node.findtext("classifier", default="")
            node_extension = node.findtext("extension", default="")
            value = node.findtext("value")
            if node_classifier == classifier and node_extension == extension.value:
                logger.info(
                    f"[Task {task_id}] [Application: {app.name}: {version}] - Resolved snapshot version '{value}'")
                return value
        logger.warning(f"[Task {task_id}] [Application: {app.name}: {version}] - No matching snapshotVersion found")
        return None
    
    # Fallback to old-style <snapshot> metadata (Maven 2 / some Nexus repos)
    snapshot_node = root.find(".//snapshot")
    if snapshot_node is not None:
        timestamp = snapshot_node.findtext("timestamp")
        build_number = snapshot_node.findtext("buildNumber")
        
        if timestamp and build_number:
            # Convert timestamp from "yyyyMMdd.HHmmss" format and build timestamped version
            base_version = version.replace("-SNAPSHOT", "")
            resolved = f"{base_version}-{timestamp}-{build_number}"
            logger.info(
                f"[Task {task_id}] [Application: {app.name}: {version}] - Resolved snapshot version '{resolved}' from old-style metadata")
            return resolved
        
        logger.warning(f"[Task {task_id}] [Application: {app.name}: {version}] - <snapshot> found but missing timestamp or buildNumber")
        return None
    
    logger.warning(f"[Application: {app.name}: {version}] - No <snapshotVersions> or <snapshot> found in metadata")
    return None


def version_to_folder_name(version: str) -> str:
    """
    Normalizes version string for folder naming.

    If version is timestamped snapshot (e.g. '1.0.0-20240702.123456-1'), it replaces the timestamp suffix with
    '-SNAPSHOT'. Otherwise, returns the version unchanged
    """
    snapshot_pattern = re.compile(r"-\d{8}\.\d{6}-\d+$")
    if snapshot_pattern.search(version):
        folder = snapshot_pattern.sub("-SNAPSHOT", version)
    else:
        folder = version
    return folder

def clean_temp_dir():
    if WORKSPACE.exists():
        shutil.rmtree(WORKSPACE)
    os.makedirs(WORKSPACE, exist_ok=True)


async def download_all_async(artifacts_info: list[ArtifactInfo], cred: Credentials | None = None):
    auth = BasicAuth(login=cred.username, password=cred.password) if cred else None
    connector = aiohttp.TCPConnector(limit=TCP_CONNECTION_LIMIT)
    timeout = aiohttp.ClientTimeout(total=DEFAULT_REQUEST_TIMEOUT)
    async with aiohttp.ClientSession(connector=connector, timeout=timeout, auth=auth) as session:
        async with asyncio.TaskGroup() as tg:
            tasks = [tg.create_task(download_async(session, artifact_info)) for artifact_info in artifacts_info]
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


async def download_async(session, artifact_info: ArtifactInfo) -> ArtifactInfo:
    """
    Downloads an artifact to a local directory: <workspace_dir>/<app_name>/<app_version>/filename.extension
    Sets full local path of artifact to artifact info
    Returns:
        ArtifactInfo: Object containing related information about the artifact
    """
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
                error_text = await response.text()
                logger.error(f"Download process with error (status {response.status}): {url} - {error_text}")
    except Exception as e:
        logger.error(f"Download process with exception {url}: {e}")


async def check_artifact_by_full_url_async(
        app: Application,
        version: str,
        repo,
        artifact_extension: FileExtension,
        stop_snapshot_event_for_others: asyncio.Event,
        stop_artifact_event: asyncio.Event,
        session,
        task_id: int,
        classifier: str = ""
) -> tuple[str, tuple[str, str]] | None:
    repo_value, repo_pointer = repo
    if not repo_value:
        logger.warning(f"[Task {task_id}] [Registry: {app.registry.name}] - {repo_pointer} is not configured")
        return None

    resolved_version = version
    id_main_task = None
    if version.endswith("-SNAPSHOT"):
        snapshot_info = await resolve_snapshot_version_async(session, app, version, repo_value, task_id,
                                                             stop_artifact_event, stop_snapshot_event_for_others,
                                                             artifact_extension, classifier)
        if not snapshot_info:
            return None
        snapshot_version, id_main_task = snapshot_info
        resolved_version = snapshot_version

    if stop_artifact_event.is_set() or (stop_snapshot_event_for_others.is_set() and task_id != id_main_task):
        return None

    full_url = create_full_url(app, resolved_version, repo_value, artifact_extension, classifier)
    try:
        async with session.head(full_url) as response:
            if response.status == 200:
                stop_artifact_event.set()
                logger.info(f"[Task {task_id}] [Application: {app.name}: {version}] - Artifact found: {full_url}")
                return full_url, repo
            logger.warning(
                f"[Task {task_id}] [Application: {app.name}: {version}] - Artifact not found at URL {full_url}, status: {response.status}")
            
            # Fallback: Try direct -SNAPSHOT filename if resolved version failed (Nexus compatibility)
            if version.endswith("-SNAPSHOT") and resolved_version != version:
                fallback_url = create_full_url(app, version, repo_value, artifact_extension, classifier)
                async with session.head(fallback_url) as fallback_response:
                    if fallback_response.status == 200:
                        stop_artifact_event.set()
                        logger.info(f"[Task {task_id}] [Application: {app.name}: {version}] - Artifact found with direct SNAPSHOT fallback: {fallback_url}")
                        return fallback_url, repo
    except Exception as e:
        logger.warning(
            f"[Task {task_id}] [Application: {app.name}: {version}] - Error checking artifact URL {full_url}: {e}")


def get_repo_value_pointer_dict(registry: Registry):
    """Permanent set of repositories for searching of artifacts"""
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
        app: Application,
        version: str,
        artifact_extension: FileExtension,
        registry_url: str | None = None,
        cred: Credentials | None = None,
        classifier: str = ""
) -> Optional[tuple[str, tuple[str, str]]]:
    repos_dict = get_repo_value_pointer_dict(app.registry)
    original_domain = app.registry.maven_config.repository_domain_name
    if registry_url:
        app.registry.maven_config.repository_domain_name = registry_url

    auth = BasicAuth(login=cred.username, password=cred.password) if cred else None
    timeout = aiohttp.ClientTimeout(total=DEFAULT_REQUEST_TIMEOUT)
    stop_snapshot_event_for_others = asyncio.Event()
    stop_artifact_event = asyncio.Event()
    try:
        async with aiohttp.ClientSession(timeout=timeout, auth=auth) as session:
            async with asyncio.TaskGroup() as tg:
                tasks = [
                    tg.create_task(
                        check_artifact_by_full_url_async(
                            app,
                            version,
                            repo,
                            artifact_extension,
                            stop_snapshot_event_for_others,
                            stop_artifact_event,
                            session,
                            i,
                            classifier
                        )
                    )
                    for i, repo in enumerate(repos_dict.items())
                ]

            for task in tasks:
                result = task.result()
                if result is not None:
                    return result
    finally:
        # Always restore original repository domain to avoid persisting browse-index URL
        if registry_url:
            app.registry.maven_config.repository_domain_name = original_domain


async def check_artifact_async(
        app: Application, artifact_extension: FileExtension, version: str, cred: Credentials | None = None,
        classifier: str = "", env_creds: Optional[dict] = None) -> Optional[tuple[str, tuple[str, str]]] | None:
    """
    Resolves the full artifact URL and the first repository where it was found.
    Supports both release and snapshot versions.
    Returns:
        Optional[tuple[str, tuple[str, str]]]: A tuple containing:
            - str: Full URL to the artifact.
            - tuple[str, str]: A pair of (repository name, repository pointer/alias in CMDB).
            Returns None if the artifact could not be resolved
    """
    registry_version = getattr(app.registry, 'version', "1.0")
    if registry_version == "2.0":
        logger.info(f"Detected RegDef V2 for {app.name}, attempting cloud-aware search")
        try:
            return await _check_artifact_v2_async(app, artifact_extension, version, env_creds)
        except Exception as e:
            logger.warning(f"V2 artifact search failed for {app.name}: {e}. Falling back to V1.")
            return await _check_artifact_v1_async(app, artifact_extension, version, cred, classifier)
    else:
        logger.debug(f"Using V1 artifact search for {app.name} (version={registry_version})")
        return await _check_artifact_v1_async(app, artifact_extension, version, cred, classifier)


async def _check_artifact_v2_async(app: Application, artifact_extension: FileExtension, version: str,
                                   env_creds: Optional[dict]) -> Optional[tuple[str, tuple[str, str]]]:
    """Search for artifacts using V2 cloud registry approach.
    
    Supports AWS CodeArtifact, GCP Artifact Registry, Artifactory, and Nexus via
    MavenArtifactSearcher library. Falls back to V1 on failure.
    
    Returns:
        (artifact_url, download_info) tuple or None
    """
    # V2 requires authConfig to know how to authenticate with the registry
    if not getattr(app.registry.maven_config, 'auth_config', None):
        logger.error(f"V2 fallback for '{app.name}': Registry '{app.registry.name}' version 2.0 missing maven_config.authConfig")
        return await _check_artifact_v1_async(app, artifact_extension, version, cred=None, classifier="")

    # Check optional V2 dependencies
    if CloudAuthHelper is None or MavenArtifact is None:
        missing = []
        if CloudAuthHelper is None:
            missing.append("artifact_searcher.cloud_auth_helper")
        if MavenArtifact is None:
            missing.append("qubership_pipelines_common_library.v1.maven_client.Artifact")
        logger.error(f"V2 fallback for '{app.name}': Missing required libraries - {', '.join(missing)}")
        return await _check_artifact_v1_async(app, artifact_extension, version, cred=None, classifier="")

    auth_config = CloudAuthHelper.resolve_auth_config(app.registry, "maven")
    if not auth_config:
        logger.error(f"V2 fallback for '{app.name}': Could not resolve authConfig for registry '{app.registry.name}'")
        return await _check_artifact_v1_async(app, artifact_extension, version, cred=None, classifier="")
    
    # AWS/GCP require credentials; Artifactory/Nexus support anonymous if provider is set
    if auth_config.provider in ["aws", "gcp"]:
        if not env_creds:
            logger.error(f"V2 fallback for '{app.name}': {auth_config.provider} requires credentials but env_creds is empty")
            return await _check_artifact_v1_async(app, artifact_extension, version, cred=None, classifier="")
        if auth_config.credentials_id and auth_config.credentials_id not in env_creds:
            logger.error(f"V2 fallback for '{app.name}': {auth_config.provider} credential '{auth_config.credentials_id}' not found in env_creds")
            logger.error(f"Available credentials: {list(env_creds.keys())}")
            return await _check_artifact_v1_async(app, artifact_extension, version, cred=None, classifier="")

    logger.info(f"V2 search for {app.name} with provider={auth_config.provider}")
    loop = asyncio.get_running_loop()

    try:
        searcher = await loop.run_in_executor(None, CloudAuthHelper.create_maven_searcher, app.registry, env_creds)
    except KeyError as e:
        logger.error(f"V2 fallback for '{app.name}': Credential not found - {e}")
        return await _check_artifact_v1_async(app, artifact_extension, version, cred=None, classifier="")
    except ValueError as e:
        logger.error(f"V2 fallback for '{app.name}': Invalid configuration - {e}")
        return await _check_artifact_v1_async(app, artifact_extension, version, cred=None, classifier="")
    except Exception as e:
        logger.error(f"V2 fallback for '{app.name}': Failed to create searcher - {e}", exc_info=True)
        return await _check_artifact_v1_async(app, artifact_extension, version, cred=None, classifier="")

    # Build artifact identifier — pass version as-is; the library resolves SNAPSHOTs internally
    artifact_string = f"{app.group_id}:{app.artifact_id}:{version}"
    maven_artifact = MavenArtifact.from_string(artifact_string)
    maven_artifact.extension = artifact_extension.value

    logger.info(f"V2 searching: {artifact_string}.{artifact_extension.value}")

    max_retries = 2
    last_error = None
    local_path = None
    maven_url = None

    # Retry on transient errors (401, timeout, expired)
    for attempt in range(max_retries):
        try:
            if attempt > 0:
                # On retry, recreate the searcher in case credentials expired
                logger.info(f"V2 retry {attempt} for {app.name} after 5s delay...")
                await asyncio.sleep(5)
                searcher = await loop.run_in_executor(None, CloudAuthHelper.create_maven_searcher, app.registry, env_creds)

            urls = await asyncio.wait_for(
                loop.run_in_executor(None, partial(searcher.find_artifact_urls, artifact=maven_artifact)),
                timeout=V2_SEARCH_TIMEOUT
            )
            if not urls:
                logger.warning(f"V2 search returned no artifacts for {app.artifact_id}:{version}")
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
            return await _check_artifact_v1_async(app, artifact_extension, version, cred=None, classifier="")

        except Exception as e:
            last_error = e
            error_str = str(e).lower()
            
            # Nexus: 404 means artifact not yet indexed in search
            if "404" in error_str and "search request" in error_str:
                logger.info(f"V2 search index miss for {app.name} - artifact may not be indexed in Nexus search DB")
                logger.info(f"Falling back to V1 direct HTTP lookup")
                return await _check_artifact_v1_async(app, artifact_extension, version, cred=None, classifier="")
            
            # Try to extract useful HTTP error details for debugging
            if hasattr(e, 'response'):
                try:
                    status = getattr(e.response, 'status_code', 'N/A')
                    url = getattr(e.response, 'url', 'N/A')
                    logger.error(f"V2 HTTP {status} from {url}")
                except Exception:
                    pass
            
            # Retry on transient errors (401, timeout, expired)
            if attempt < max_retries - 1 and any(x in error_str for x in ["401", "unauthorized", "forbidden", "expired", "timeout"]):
                logger.warning(f"V2 transient error for {app.name}, retrying: {e}")
                continue
            
            logger.error(f"V2 error for '{app.name}': {e}")
            return await _check_artifact_v1_async(app, artifact_extension, version, cred=None, classifier="")
    else:
        logger.error(f"V2 fallback for '{app.name}': All {max_retries} attempts exhausted - {last_error}")
        return await _check_artifact_v1_async(app, artifact_extension, version, cred=None, classifier="")

    # AWS: construct full URL from resource ID
    if auth_config.provider == "aws":
        registry_domain = app.registry.maven_config.repository_domain_name
        folder_name = version_to_folder_name(version)
        repo_path = app.registry.maven_config.target_snapshot if folder_name.endswith("-SNAPSHOT") else app.registry.maven_config.target_release
        full_url = f"{registry_domain.rstrip('/')}/{repo_path.rstrip('/')}/{maven_url}"
    else:
        # GCP/Artifactory/Nexus: URL ready-to-use
        full_url = maven_url

    return full_url, ("v2_downloaded", local_path)


async def _v2_download_with_fallback(searcher, url: str, local_path: str, auth_config,
                                     registry: Registry, env_creds: Optional[dict]) -> bool:
    """Download artifact via searcher with HTTP fallback.
    
    Tries searcher download first, falls back to HTTP GET for GCP/Artifactory/Nexus.
    Adds GCP access tokens if needed.
    """
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
        logger.warning(f"Direct HTTP download failed for {url}: {e}", exc_info=True)
        return False


async def _check_artifact_v1_async(
    app: Application, 
    artifact_extension: FileExtension,
    version: str,
    cred: Credentials | None = None,  # ADD from incoming
    classifier: str = ""
) -> Optional[tuple[str, tuple[str, str]]]:
    result = await _attempt_check(app, version, artifact_extension, cred=cred, classifier=classifier)
    if result is not None:
        return result

    # Browse URL retry removed - browse endpoints don't support downloads
    # V1 fallback will rely on V2 search or direct repository URLs only
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
        logger.error(f"Error unpacking artifact {artifact_id} for {app_name}:{app_version} from {zip_url}: {e}", exc_info=True)
    if not extracted:
        logger.warning(f"No files were extracted for application {app_name}:{app_version}")


def create_aql_artifacts(aqls: list[str]):
    return f'items.find({{"$or":  [{', '.join(aqls)}]}})'


def create_artifact_name(artifact_id: str, artifact_extension: FileExtension, version: str,
                         classifier: str = "") -> str:
    return f"{artifact_id}-{version}{'-' + classifier if classifier else ''}.{artifact_extension.value}"


def create_aql_artifact(app: Application, artifact_extension: FileExtension, version: str,
                        classifier: str = "") -> str:
    group_id = app.group_id.replace(".", "/")
    folder = version_to_folder_name(version)
    path = f"{group_id}/{app.artifact_id}/{folder}"
    name = create_artifact_name(app.artifact_id, artifact_extension, version, classifier)
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


# not async, download artifact directly
# TODO delete after deletion feature getting artifact by not artifact def
# --------------------------------------------------------------------------------------

def download_json_content(url: str, cred: Credentials | None = None) -> dict[str, Any]:
    auth = HTTPBasicAuth(cred.username, cred.password) if cred else None
    response = requests.get(
        url,
        auth=auth,
        timeout=DEFAULT_REQUEST_TIMEOUT
    )
    response.raise_for_status()
    json_data = response.json()
    logger.info(f"Got json data by url {url}")
    return json_data


def download(url: str, target_path: str, cred: Credentials | None = None) -> str:
    auth = HTTPBasicAuth(cred.username, cred.password) if cred else None
    os.makedirs(os.path.dirname(target_path), exist_ok=True)
    response = requests.get(url, auth=auth, timeout=DEFAULT_REQUEST_TIMEOUT)
    response.raise_for_status()
    with open(target_path, "wb") as f:
        f.write(response.content)
    logger.info(f"Downloaded: {target_path}")
    return target_path


def check_artifact(repo_url: str, group_id: str, artifact_id: str, version: str,
                   artifact_extension: FileExtension,
                   cred: Credentials | None = None,
                   classifier: str = "") -> str | None:
    base = repo_url.rstrip("/") + "/"
    group_id = group_id.replace(".", "/")

    if "SNAPSHOT" in version:
        base_path = urljoin(base, f"{group_id}/{artifact_id}/{version}/")
        resolved_version = resolve_snapshot_version(base_path, artifact_extension, cred, classifier)
        if not resolved_version:
            return None
        version = resolved_version

    folder = version_to_folder_name(version)
    filename = create_artifact_name(artifact_id, artifact_extension, version, classifier)
    full_url = urljoin(base, f"{group_id}/{artifact_id}/{folder}/{filename}")

    try:
        response = requests.head(full_url, timeout=DEFAULT_REQUEST_TIMEOUT)
        if response.status_code == 200:
            logger.info(
                f"[Repository: {repo_url}] [Artifact: {group_id}:{artifact_id}:{version}] - Artifact found: {full_url}"
            )
            return full_url
        logger.warning(
            f"[Repository: {repo_url}] [Artifact: {group_id}:{artifact_id}:{version}] - Artifact not found at URL {full_url}, status: {response.status_code}"
        )
    except Exception as e:
        logger.warning(
            f"[Repository: {repo_url}] [Artifact: {group_id}:{artifact_id}:{version}] - Error checking artifact URL {full_url}: {e}"
        )

    return None


def resolve_snapshot_version(base_path, extension: FileExtension, cred: Credentials | None = None,
                             classifier: str = "") -> Optional[str]:
    metadata_url = urljoin(base_path, METADATA_XML)
    auth = HTTPBasicAuth(cred.username, cred.password) if cred else None

    try:
        response = requests.get(
            metadata_url,
            auth=auth,
            timeout=DEFAULT_REQUEST_TIMEOUT,
        )
        if response.status_code != 200:
            logger.warning(f"Failed to fetch {metadata_url}, status={response.status_code}")
            return None
        content = response.text
        root = ET.fromstring(content)
        snapshot_versions = root.findall(".//snapshotVersions/snapshotVersion")
        if not snapshot_versions:
            logger.warning(f"No <snapshotVersions> found")
            return

        for node in snapshot_versions:
            node_classifier = node.findtext("classifier", default="")
            node_extension = node.findtext("extension", default="")
            value = node.findtext("value")
            if node_classifier == classifier and node_extension == extension.value:
                logger.info(f"Resolved snapshot version '{value}'")
                return value

        logger.warning(f"No matching snapshotVersion found")

    except Exception as e:
        logger.warning(f"Snapshot resolve error: {e}")

# --------------------------------------------------------------------------------------
