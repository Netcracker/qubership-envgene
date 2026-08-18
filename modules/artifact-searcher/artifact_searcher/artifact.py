import asyncio
import base64
import os
import re
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Optional
from urllib.parse import urljoin, urlparse, urlunparse
from collections import defaultdict
from zipfile import ZipFile

import aiohttp
import requests
from artifact_searcher.utils.constants import DEFAULT_REQUEST_TIMEOUT, TCP_CONNECTION_LIMIT, METADATA_XML
from artifact_searcher.utils.models import RegistryV2, Application, FileExtension, Credentials, ArtifactSource, ArtifactDownload, Repo, RepoType, Provider, MavenConfig
from envgenehelper import logger

TIMESTAMPED_VERSION_PATTERN = re.compile(r"-\d{8}\.\d{6}-\d+$")


def convert_nexus_repo_url_to_index_view(url: str) -> str:
    parsed = urlparse(url)

    parts = parsed.path.rstrip("/").split("/")

    if not parts or parts[-1] != "repository":
        return url

    # Build new path
    new_parts = parts[:-1] + ["service", "rest", "repository", "browse"]
    new_path = "/".join(new_parts) + "/"

    return urlunparse(parsed._replace(path=new_path))


def create_artifact_path(app: Application, version: str, repo: str = "",
                         use_exact_version_folder: bool = False) -> str:
    registry_url = app.registry.maven_config.repository_domain_name
    group_id = app.group_id.replace(".", "/")
    folder = version if use_exact_version_folder else version_to_folder_name(version)

    # For cloud providers (AWS/GCP), repo is empty since repositoryDomainName already contains full path
    if repo:
        path = f"{repo}/{group_id}/{app.artifact_id}/{folder}/"
    else:
        path = f"{group_id}/{app.artifact_id}/{folder}/"

    return urljoin(registry_url, path)


def create_full_url(app: Application, version: str, repo: str, artifact_extension: FileExtension,
                    classifier: str = "", use_exact_version_folder: bool = False) -> str:
    base_path = create_artifact_path(app, version, repo, use_exact_version_folder)
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
    if TIMESTAMPED_VERSION_PATTERN.search(version):
        folder = TIMESTAMPED_VERSION_PATTERN.sub("-SNAPSHOT", version)
    else:
        folder = version
    return folder


def _create_candidate_urls(app: Application, version: str, repo: str, artifact_extension: FileExtension,
                           classifier: str = "") -> list[str]:
    urls = [create_full_url(app, version, repo, artifact_extension, classifier)]
    if TIMESTAMPED_VERSION_PATTERN.search(version):
        urls.append(create_full_url(app, version, repo, artifact_extension, classifier, True))
    return urls


def _create_candidate_urls_from_coordinates(repo_url: str, group_id: str, artifact_id: str, version: str,
                                            artifact_extension: FileExtension, classifier: str = "") -> list[str]:
    filename = create_artifact_name(artifact_id, artifact_extension, version, classifier)
    base = repo_url.rstrip("/") + "/"
    snapshot_folder = version_to_folder_name(version)

    urls = [urljoin(base, f"{group_id}/{artifact_id}/{snapshot_folder}/{filename}")]
    if TIMESTAMPED_VERSION_PATTERN.search(version):
        urls.append(urljoin(base, f"{group_id}/{artifact_id}/{version}/{filename}"))
    return urls


async def _check_candidate_url_async(session, full_url: str) -> tuple[str, int | None, Exception | None]:
    try:
        async with session.head(full_url) as response:
            return full_url, response.status, None
    except Exception as e:
        return full_url, None, e


def _check_candidate_url(full_url: str, auth_headers: dict | None = None) -> tuple[str, int | None, Exception | None]:
    try:
        response = requests.head(full_url, headers=auth_headers, timeout=DEFAULT_REQUEST_TIMEOUT)
        return full_url, response.status_code, None
    except Exception as e:
        return full_url, None, e


def credentials_to_headers(cred: Credentials) -> dict:
    # Convert Credentials object to Authorization headers dict.
    token = base64.b64encode(f"{cred.username}:{cred.password}".encode()).decode()
    return {"Authorization": f"Basic {token}"}


async def download_all_async(downloads: list[ArtifactDownload]):
    auth_groups = defaultdict(list)
    for download in downloads:
        # Use sorted tuple of auth items as key, or "none" for None
        auth_headers = download.source.auth_headers
        auth_key = tuple(sorted(auth_headers.items())) if auth_headers else "none"
        auth_groups[auth_key].append(download)

    all_results = []
    for auth_key, downloads_group in auth_groups.items():
        headers = downloads_group[0].source.auth_headers
        connector = aiohttp.TCPConnector(limit=TCP_CONNECTION_LIMIT)
        timeout = aiohttp.ClientTimeout(total=DEFAULT_REQUEST_TIMEOUT)
        async with aiohttp.ClientSession(connector=connector, timeout=timeout, headers=headers) as session:
            async with asyncio.TaskGroup() as tg:
                tasks = [tg.create_task(download_async(session, download)) for download in downloads_group]
            results = []
            errors = []

            for i, task in enumerate(tasks):
                result = task.result()
                if not result:
                    errors.append(f"Task {i}: artifact was not downloaded")
                else:
                    results.append(result)

            if errors:
                raise ValueError("Some tasks failed:\n" + "\n".join(errors))

            all_results.extend(results)

    return all_results


async def download_async(session, download: ArtifactDownload) -> ArtifactDownload:
    """
    Downloads an artifact to download.local_target_path.
    Returns:
        ArtifactDownload: Object containing related information about the artifact
    """
    url = download.source.source_url
    os.makedirs(os.path.dirname(download.local_target_path), exist_ok=True)
    try:
        async with session.get(url) as response:
            if response.status == 200:
                with open(download.local_target_path, "wb") as f:
                    f.write(await response.read())
                logger.info(f"Downloaded: {download.local_target_path}")
                return download
            else:
                logger.error(f"Download process with error {response.text}: {url}")
    except Exception as e:
        logger.error(f"Download process with exception {url}: {e}")


async def check_artifact_by_full_url_async(
        app: Application,
        version: str,
        repo: Repo,
        artifact_extension: FileExtension,
        stop_snapshot_event_for_others: asyncio.Event,
        stop_artifact_event: asyncio.Event,
        session,
        task_id: int,
        auth_headers: dict | None = None,
        classifier: str = ""
) -> ArtifactSource | None:
    # Allow empty repo value for cloud providers (REPOSITORY_NAME), but not for Nexus/Artifactory
    if not repo.value and repo.type != RepoType.REPOSITORY_NAME:
        logger.warning(f"[Task {task_id}] [Registry: {app.registry.name}] - {repo.type.value} is not configured")
        return None

    resolved_version = version
    id_main_task = None
    if version.endswith("-SNAPSHOT"):
        snapshot_info = await resolve_snapshot_version_async(session, app, version, repo.value, task_id,
                                                             stop_artifact_event, stop_snapshot_event_for_others,
                                                             artifact_extension, classifier)
        if not snapshot_info:
            return None
        snapshot_version, id_main_task = snapshot_info
        resolved_version = snapshot_version

    if stop_artifact_event.is_set() or (stop_snapshot_event_for_others.is_set() and task_id != id_main_task):
        return None

    candidate_urls = _create_candidate_urls(app, resolved_version, repo.value, artifact_extension, classifier)
    async with asyncio.TaskGroup() as tg:
        tasks = [tg.create_task(_check_candidate_url_async(session, full_url)) for full_url in candidate_urls]
    candidate_results = [task.result() for task in tasks]

    for full_url, status, _ in candidate_results:
        if status == 200:
            stop_artifact_event.set()
            logger.info(
                f"[Task {task_id}] [Application: {app.name}: {version}] - Artifact found: {full_url}"
            )
            return ArtifactSource(source_url=full_url, repository=repo, application=app, auth_headers=auth_headers)

    for full_url, status, error in candidate_results:
        if error:
            logger.warning(
                f"[Task {task_id}] [Application: {app.name}: {version}] - Error checking artifact URL {full_url}: {error}"
            )
        else:
            logger.warning(
                f"[Task {task_id}] [Application: {app.name}: {version}] - Artifact not found at URL {full_url}, status: {status}"
            )


def _is_cloud_provider(registry) -> bool:
    """Check if registry uses AWS or GCP provider."""
    if not getattr(registry, "auth_config", None):
        return False
    for auth_cfg in registry.auth_config.values():
        if getattr(auth_cfg, "provider", None) in (Provider.AWS, Provider.GCP):
            return True
    return False


# TODO: delete after models are refactored to use polymorphism
def get_repos(registry) -> list[Repo]:
    """V2 cloud providers: use empty repo (domain already contains full path).
    V1/Nexus/Artifactory: use target fields."""
    if _is_cloud_provider(registry):
        return [Repo(value="", type=RepoType.REPOSITORY_NAME)]
    maven = registry.maven_config
    return [
        Repo(value=maven.target_snapshot, type=RepoType.TARGET_SNAPSHOT),
        Repo(value=maven.target_staging, type=RepoType.TARGET_STAGING),
        Repo(value=maven.target_release, type=RepoType.TARGET_RELEASE),
        Repo(value=maven.snapshot_group, type=RepoType.SNAPSHOT_GROUP),
    ]


def get_repo_pointer(repo_value: str, registry) -> Optional[RepoType]:
    return next((repo.type for repo in get_repos(registry) if repo.value == repo_value), None)


async def _attempt_check(
        app: Application,
        version: str,
        artifact_extension: FileExtension,
        registry_url: str | None = None,
        auth_headers: dict | None = None,
        classifier: str = ""
) -> Optional[ArtifactSource]:
    repos = get_repos(app.registry)
    if registry_url:
        app.registry.maven_config.repository_domain_name = registry_url

    session_headers = auth_headers

    timeout = aiohttp.ClientTimeout(total=DEFAULT_REQUEST_TIMEOUT)
    stop_snapshot_event_for_others = asyncio.Event()
    stop_artifact_event = asyncio.Event()
    async with aiohttp.ClientSession(timeout=timeout, headers=session_headers) as session:
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
                        auth_headers,
                        classifier
                    )
                )
                for i, repo in enumerate(repos)
            ]

        for task in tasks:
            result = task.result()
            if result is not None:
                return result


def _should_retry_nexus_url(registry) -> bool:
    """Check whether the registry needs Nexus-style URL retry."""
    if isinstance(registry, RegistryV2):
        return any(cfg.provider == Provider.NEXUS for cfg in registry.auth_config.values())
    return MavenConfig.is_nexus(registry.maven_config.repository_domain_name)


async def _retry_with_nexus_url(
        app: Application,
        version: str,
        artifact_extension: FileExtension,
        auth_headers: dict | None,
        classifier: str = ""
) -> Optional[ArtifactSource]:
    """Retry artifact check with Nexus index-view URL conversion."""
    original_domain = app.registry.maven_config.repository_domain_name
    fixed_domain = convert_nexus_repo_url_to_index_view(original_domain)
    if fixed_domain != original_domain:
        logger.info(f"Retrying artifact check with edited domain: {fixed_domain}")
        result = await _attempt_check(app, version, artifact_extension, fixed_domain, auth_headers, classifier)
        app.registry.maven_config.repository_domain_name = original_domain
        if result is not None:
            return result
    else:
        logger.debug("Domain is same after editing, skipping retry")
    return None


async def check_artifact_async(app: Application, artifact_extension: FileExtension, version: str,
        auth_headers: dict | None = None, classifier: str = "") -> Optional[ArtifactSource]:
    """
    Resolves the full artifact URL and the first repository where it was found.
    Supports both release and snapshot versions.
    """
    repos = get_repos(app.registry)

    # Single repo: no parallelism
    if len(repos) == 1:
        repo = repos[0]
        if not repo.value and repo.type != RepoType.REPOSITORY_NAME:
            logger.warning(f"[Registry: {app.registry.name}] - {repo.type.value} is not configured")
            return None
        domain = app.registry.maven_config.repository_domain_name
        repo_url = domain if not repo.value else domain.rstrip('/') + '/' + repo.value
        url = check_artifact(repo_url, app.group_id, app.artifact_id, version,
                             artifact_extension, auth_headers=auth_headers, classifier=classifier)
        if url:
            return ArtifactSource(source_url=url, repository=repo, application=app, auth_headers=auth_headers)
        if _should_retry_nexus_url(app.registry):
            return await _retry_with_nexus_url(app, version, artifact_extension, auth_headers, classifier)
        return None

    # Multiple repos: use async parallel checking
    result = await _attempt_check(app, version, artifact_extension, auth_headers=auth_headers, classifier=classifier)
    if result is not None:
        return result

    if _should_retry_nexus_url(app.registry):
        return await _retry_with_nexus_url(app, version, artifact_extension, auth_headers, classifier)

    logger.warning("Artifact not found")
    return None


def unzip_file(artifact_id: str, source_zip_path: Path, target_dir: Path):
    extracted = False
    entry_prefix = f"{artifact_id}/"
    try:
        with ZipFile(source_zip_path, "r") as zip_file:
            for file in zip_file.namelist():
                if file.startswith(entry_prefix):
                    zip_file.extract(file, target_dir)
                    extracted = True
    except Exception as e:
        logger.error(f"Error unpacking {e}")
    if not extracted:
        logger.warning(f"No files were extracted for artifact {artifact_id} from {source_zip_path}")


def create_artifact_name(artifact_id: str, artifact_extension: FileExtension, version: str,
                         classifier: str = "") -> str:
    return f"{artifact_id}-{version}{'-' + classifier if classifier else ''}.{artifact_extension.value}"


# not async, download artifact directly
# TODO delete after deletion feature getting artifact by not artifact def
# --------------------------------------------------------------------------------------

def download_json_content(url: str, auth_headers: dict | None = None) -> dict[str, Any]:
    headers = auth_headers
    response = requests.get(url, headers=headers, timeout=DEFAULT_REQUEST_TIMEOUT)
    response.raise_for_status()
    json_data = response.json()
    logger.info(f"Got json data by url {url}")
    return json_data


def download(url: str, target_path: str, auth_headers: dict | None = None) -> str:
    headers = auth_headers
    response = requests.get(url, headers=headers, timeout=DEFAULT_REQUEST_TIMEOUT)
    os.makedirs(os.path.dirname(target_path), exist_ok=True)
    response.raise_for_status()
    with open(target_path, "wb") as f:
        f.write(response.content)
    logger.info(f"Downloaded: {target_path}")
    return target_path


def check_artifact(repo_url: str, group_id: str, artifact_id: str, version: str,
                   artifact_extension: FileExtension,
                   auth_headers: dict | None = None,
                   classifier: str = "") -> str | None:
    if MavenConfig.is_nexus(repo_url):
        repo_url = convert_nexus_repo_url_to_index_view(repo_url)

    base = repo_url.rstrip("/") + "/"
    group_id = group_id.replace(".", "/")

    if "SNAPSHOT" in version:
        base_path = urljoin(base, f"{group_id}/{artifact_id}/{version}/")
        resolved_version = resolve_snapshot_version(base_path, artifact_extension, auth_headers, classifier)
        if not resolved_version:
            return None
        version = resolved_version

    candidate_urls = _create_candidate_urls_from_coordinates(
        repo_url, group_id, artifact_id, version, artifact_extension, classifier
    )
    if len(candidate_urls) == 1:
        candidate_results = [_check_candidate_url(candidate_urls[0], auth_headers)]
    else:
        with ThreadPoolExecutor(max_workers=len(candidate_urls)) as executor:
            futures = [
                executor.submit(_check_candidate_url, full_url, auth_headers)
                for full_url in candidate_urls
            ]
            candidate_results = [future.result() for future in futures]

    for full_url, status, _ in candidate_results:
        if status == 200:
            logger.info(
                f"[Repository: {repo_url}] [Artifact: {group_id}:{artifact_id}:{version}] - Artifact found: {full_url}"
            )
            return full_url

    for full_url, status, error in candidate_results:
        if error:
            logger.warning(
                f"[Repository: {repo_url}] [Artifact: {group_id}:{artifact_id}:{version}] - Error checking artifact URL {full_url}: {error}"
            )
        else:
            logger.warning(
                f"[Repository: {repo_url}] [Artifact: {group_id}:{artifact_id}:{version}] - Artifact not found at URL {full_url}, status: {status}"
            )

    return None


def resolve_snapshot_version(base_path, extension: FileExtension,
                             auth_headers: dict | None = None,
                             classifier: str = "") -> Optional[str]:
    metadata_url = urljoin(base_path, METADATA_XML)

    try:
        response = requests.get(metadata_url, headers=auth_headers, timeout=DEFAULT_REQUEST_TIMEOUT)
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
