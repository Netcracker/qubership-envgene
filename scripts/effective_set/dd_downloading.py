import asyncio
import time
from pathlib import Path

import envgenehelper as helper
from artifact_searcher import artifact
from artifact_searcher.utils.models import ArtifactDownload, ArtifactSource, FileExtension
from envgenehelper.business_helper import get_app_artifacts_dir, get_version
from envgenehelper.logger import logger
from envgenehelper.plugin_engine import PluginEngine

from sd.process_sd import get_appdef_for_app

APP_DEF_GETTER_PLUGINS_DIR = '/module/scripts/plugins/handle_sd_plugins'


def _replace_extension(url: str, new_extension: str) -> str:
    return f"{url.rsplit('.', 1)[0]}.{new_extension}"


async def resolve_dd_and_zip_info(appver: str, app_artifacts_dir: str, env_creds: dict,
                                   plugins: PluginEngine, ctx=None) -> tuple[ArtifactDownload, ArtifactDownload]:
    app_name, version = get_version(appver)
    app_def = get_appdef_for_app(appver, plugins, ctx=ctx)
    auth_headers = app_def.registry.resolve_auth(env_creds)

    dd_source = await artifact.check_artifact_async(app_def, FileExtension.JSON, version, auth_headers=auth_headers)
    if not dd_source:
        raise ValueError(f"Deployment descriptor was not found for {app_name}:{version}")
    zip_url = _replace_extension(dd_source.source_url, "zip")

    app_version_dir = f'{app_artifacts_dir}/{app_name}/{version}'
    dd_artifact = ArtifactDownload(source=dd_source, local_target_path=f'{app_version_dir}/dd.json')
    zip_source = ArtifactSource(
        source_url=zip_url, repository=dd_source.repository, application=app_def, auth_headers=auth_headers)
    zip_artifact = ArtifactDownload(source=zip_source, local_target_path=f'{app_version_dir}/dd.zip')
    return dd_artifact, zip_artifact


def resolve_artifacts(app_versions: list[str], ctx=None) -> tuple[list[ArtifactDownload], list[ArtifactDownload]]:
    env_creds = helper.get_cred_config()
    app_artifacts_dir = get_app_artifacts_dir()
    app_def_getter_plugins = PluginEngine(plugins_dir=APP_DEF_GETTER_PLUGINS_DIR)

    async def _gather() -> list[tuple[ArtifactDownload, ArtifactDownload]]:
        return await asyncio.gather(*(
            resolve_dd_and_zip_info(appver, app_artifacts_dir, env_creds, app_def_getter_plugins, ctx=ctx)
            for appver in app_versions
        ))

    logger.info(f"Start resolving DD and zip URLs for {len(app_versions)} applications")
    start_time = time.perf_counter()
    results = asyncio.run(_gather())
    dd_artifacts = [dd_artifact for dd_artifact, _ in results]
    zip_artifacts = [zip_artifact for _, zip_artifact in results]
    logger.info(
        f"Resolved DD+zip URLs for {len(app_versions)} applications: {time.perf_counter() - start_time:.6f} sec")

    return dd_artifacts, zip_artifacts


def extract_artifact_contents(zip_artifacts: list[ArtifactDownload]) -> None:
    logger.info(f"Start unpacking {len(zip_artifacts)} zip artifacts")
    start_time = time.perf_counter()
    for zip_artifact in zip_artifacts:
        artifact_id = Path(zip_artifact.source.source_url).parent.parent.name
        source_zip_path = Path(zip_artifact.local_target_path)
        artifact.unzip_file(artifact_id, source_zip_path, source_zip_path.parent / source_zip_path.stem)
    logger.info(f"Unpacked {len(zip_artifacts)} zip artifacts: {time.perf_counter() - start_time:.6f} sec")


async def _download_zips(zip_artifacts: list[ArtifactDownload]) -> list[ArtifactDownload]:
    downloaded: list[ArtifactDownload] = []
    for zip_artifact in zip_artifacts:
        try:
            downloaded.extend(await artifact.download_all_async([zip_artifact]))
        except ValueError:
            logger.warning(
                f"Zip artifact not downloaded, continuing without it: {zip_artifact.source.source_url}"
            )
    return downloaded


async def _download_dd_required_zips_optional(
        dd_artifacts: list[ArtifactDownload],
        zip_artifacts: list[ArtifactDownload],
) -> list[ArtifactDownload]:
    await artifact.download_all_async(dd_artifacts)
    return await _download_zips(zip_artifacts)


def download_dd_and_zip_artifacts(app_versions: list[str], ctx=None) -> tuple[list[ArtifactDownload], list[ArtifactDownload]]:
    dd_artifacts, zip_artifacts = resolve_artifacts(app_versions, ctx=ctx)
    logger.info(
        f"Start downloading {len(dd_artifacts)} DD artifacts "
        f"(and up to {len(zip_artifacts)} optional zip sidecars)")
    start_time = time.perf_counter()
    downloaded_zips = asyncio.run(_download_dd_required_zips_optional(dd_artifacts, zip_artifacts))
    logger.info(
        f"Downloaded {len(dd_artifacts)} DD + {len(downloaded_zips)}/{len(zip_artifacts)} zip artifacts: "
        f"{time.perf_counter() - start_time:.6f} sec")

    extract_artifact_contents(downloaded_zips)

    return dd_artifacts, downloaded_zips
