import asyncio
import os
import re
import shutil
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Optional
from urllib.parse import urljoin, urlparse, urlunparse
from zipfile import ZipFile

import aiohttp
import requests
from aiohttp import BasicAuth
from artifact_searcher.utils.constants import DEFAULT_REQUEST_TIMEOUT, TCP_CONNECTION_LIMIT, METADATA_XML
from artifact_searcher.utils.models import Registry, Application, FileExtension, Credentials, ArtifactInfo
from envgenehelper import logger
from requests.auth import HTTPBasicAuth

WORKSPACE = os.getenv("WORKSPACE", Path(tempfile.gettempdir()) / "zips")


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
    path_template = f"{repo}/{group_id}/{app.artifact_id}/{folder}/"
    full_path = urljoin(registry_url, path_template)
    
    # Debug logging - using INFO level to ensure visibility
    logger.info(f"[create_artifact_path] Input parameters:")
    logger.info(f"  - app.name: {app.name}")
    logger.info(f"  - app.group_id: {app.group_id}")
    logger.info(f"  - app.artifact_id: {app.artifact_id}")
    logger.info(f"  - app.registry.name: {app.registry.name}")
    logger.info(f"  - app.registry.maven_config.repository_domain_name: {app.registry.maven_config.repository_domain_name}")
    logger.info(f"  - version: {version}")
    logger.info(f"  - repo: '{repo}' (length: {len(repo)}, repr: {repr(repo)})")
    logger.info(f"[create_artifact_path] Intermediate values:")
    logger.info(f"  - registry_url: {registry_url}")
    logger.info(f"  - group_id (converted): {group_id}")
    logger.info(f"  - folder: {folder}")
    logger.info(f"  - path_template: {path_template}")
    logger.info(f"[create_artifact_path] Final path: {full_path}")
    
    return full_path


def create_full_url(app: Application, version: str, repo: str, artifact_extension: FileExtension,
                    classifier: str = "") -> str:
    base_path = create_artifact_path(app, version, repo)
    filename = create_artifact_name(app.artifact_id, artifact_extension, version, classifier)
    full_url = urljoin(base_path, filename)
    
    # Debug logging - using INFO level to ensure visibility
    logger.info(f"[create_full_url] Final URL components:")
    logger.info(f"  - base_path: {base_path}")
    logger.info(f"  - filename: {filename}")
    logger.info(f"  - full_url: {full_url}")
    
    return full_url


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
    snapshot_versions = root.findall(".//snapshotVersions/snapshotVersion")
    if not snapshot_versions:
        logger.warning(f"[Application: {app.name}: {version}] - No <snapshotVersions> found")
        return

    for node in snapshot_versions:
        node_classifier = node.findtext("classifier", default="")
        node_extension = node.findtext("extension", default="")
        value = node.findtext("value")
        if node_classifier == classifier and node_extension == extension:
            logger.info(
                f"[Task {task_id}] [Application: {app.name}: {version}] - Resolved snapshot version '{value}'")
            return value

    logger.warning(f"[Task {task_id}] [Application: {app.name}: {version}] - No matching snapshotVersion found")


def version_to_folder_name(version: str):
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
    logger.info(f"[check_artifact_by_full_url_async] Task {task_id}, repo_value='{repo_value}' (len={len(repo_value) if repo_value else 0}), repo_pointer='{repo_pointer}'")
    if not repo_value:
        logger.warning(f"[Task {task_id}] [Registry: {app.registry.name}] - {repo_pointer} is not configured (repo_value is empty or None)")
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
    logger.info(f"[Task {task_id}] [Registry: {app.registry.name}] Checking artifact at URL: {full_url}")
    try:
        async with session.head(full_url) as response:
            logger.info(f"[Task {task_id}] [Registry: {app.registry.name}] HTTP response status: {response.status} for URL: {full_url}")
            if response.status == 200:
                stop_artifact_event.set()
                logger.info(f"[Task {task_id}] [Application: {app.name}: {version}] - Artifact found: {full_url}")
                return full_url, repo
            logger.warning(
                f"[Task {task_id}] [Application: {app.name}: {version}] - Artifact not found at URL {full_url}, status: {response.status}")
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
    logger.info(f"[get_repo_value_pointer_dict] Registry: {registry.name}, repos dict: {repos}")
    logger.info(f"[get_repo_value_pointer_dict] Values: targetSnapshot='{maven.target_snapshot}' (len={len(maven.target_snapshot)}), "
                f"targetStaging='{maven.target_staging}' (len={len(maven.target_staging)}), "
                f"targetRelease='{maven.target_release}' (len={len(maven.target_release)}), "
                f"snapshotGroup='{maven.snapshot_group}' (len={len(maven.snapshot_group)})")
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
    logger.info(f"[_attempt_check] Called with app.name={app.name}, version={version}, extension={artifact_extension.value}")
    repos_dict = get_repo_value_pointer_dict(app.registry)
    logger.info(f"[_attempt_check] Repositories dict: {repos_dict}")
    if registry_url:
        app.registry.maven_config.repository_domain_name = registry_url

    auth = BasicAuth(login=cred.username, password=cred.password) if cred else None
    timeout = aiohttp.ClientTimeout(total=DEFAULT_REQUEST_TIMEOUT)
    stop_snapshot_event_for_others = asyncio.Event()
    stop_artifact_event = asyncio.Event()
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

        logger.info(f"[_attempt_check] Created {len(tasks)} tasks for checking artifacts, processing results...")
        for idx, task in enumerate(tasks):
            result = task.result()
            logger.info(f"[_attempt_check] Task {idx} result: {result}")
            if result is not None:
                logger.info(f"[_attempt_check] Found artifact, returning: {result}")
                return result
        logger.warning(f"[_attempt_check] No artifact found in any of {len(tasks)} repositories")


async def check_artifact_async(
        app: Application, artifact_extension: FileExtension, version: str, cred: Credentials | None = None,
        classifier: str = "") -> Optional[tuple[str, tuple[str, str]]] | None:
    """
    Resolves the full artifact URL and the first repository where it was found.
    Supports both release and snapshot versions.

    Returns:
        Optional[tuple[str, tuple[str, str]]]: A tuple containing:
            - str: Full URL to the artifact.
            - tuple[str, str]: A pair of (repository name, repository pointer/alias in CMDB).
            Returns None if the artifact could not be resolved
    """
    logger.info(f"[check_artifact_async] Called with app.name={app.name}, app.group_id={app.group_id}, "
                f"app.artifact_id={app.artifact_id}, version={version}, extension={artifact_extension.value}")
    logger.info(f"[check_artifact_async] Registry: {app.registry.name}, "
                f"repositoryDomainName: {app.registry.maven_config.repository_domain_name}")
    logger.info(f"[check_artifact_async] targetSnapshot='{app.registry.maven_config.target_snapshot}', "
                f"targetStaging='{app.registry.maven_config.target_staging}', "
                f"targetRelease='{app.registry.maven_config.target_release}'")

    result = await _attempt_check(app, version, artifact_extension)
    if result is not None:
        return result

    if not app.registry.maven_config.is_nexus:
        return result

    # trying to edit url for nexus and repeat
    original_domain = app.registry.maven_config.repository_domain_name
    fixed_domain = convert_nexus_repo_url_to_index_view(original_domain)
    if fixed_domain != original_domain:
        logger.info(f"Retrying artifact check with edited domain: {fixed_domain}")
        result = await _attempt_check(app, version, artifact_extension, fixed_domain, cred, classifier)
        if result is not None:
            return result
    else:
        logger.debug("Domain is same after editing, skipping retry")

    logger.warning("Artifact not found")


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
            if node_classifier == classifier and node_extension == extension:
                logger.info(f"Resolved snapshot version '{value}'")
                return value

        logger.warning(f"No matching snapshotVersion found")

    except Exception as e:
        logger.warning(f"Snapshot resolve error: {e}")

# --------------------------------------------------------------------------------------
