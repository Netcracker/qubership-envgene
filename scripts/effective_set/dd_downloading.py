import asyncio
import json
import time
from pathlib import Path

import envgenehelper as helper
from artifact_searcher import artifact
from artifact_searcher.utils.models import ArtifactDownload, ArtifactSource, FileExtension
from envgenehelper.business_helper import get_app_artifacts_dir, get_version
from envgenehelper.models import ArtifactCoordinateSource
from envgenehelper.file_helper import unpack_archive
from envgenehelper.logger import logger
from envgenehelper.plugin_engine import PluginEngine
from sbom_generator.generate_bom import CHART_DIR_NAME

from sd.process_sd import get_appdef_for_app

APP_DEF_GETTER_PLUGINS_DIR = '/module/scripts/plugins/handle_sd_plugins'
CHART_ARCHIVE_NAME = 'chart.tgz'


async def resolve_dd_info(appver: str, app_artifacts_dir: str, env_creds: dict,
                          plugins: PluginEngine, ctx=None) -> ArtifactDownload:
    app_name, version = get_version(appver)
    app_def = get_appdef_for_app(appver, plugins, ctx=ctx)
    auth_headers = app_def.registry.resolve_auth(env_creds)

    dd_source = await artifact.check_artifact_async(app_def, FileExtension.JSON, version, auth_headers=auth_headers)
    if not dd_source:
        raise ValueError(f"Deployment descriptor was not found for {app_name}:{version}")
    return ArtifactDownload(source=dd_source, local_target_path=f'{app_artifacts_dir}/{app_name}/{version}/dd.json')


def resolve_dd_artifacts(app_versions: list[str], ctx=None) -> list[ArtifactDownload]:
    env_creds = helper.get_cred_config()
    app_artifacts_dir = get_app_artifacts_dir()
    app_def_getter_plugins = PluginEngine(plugins_dir=APP_DEF_GETTER_PLUGINS_DIR)

    async def _gather() -> list[ArtifactDownload]:
        return await asyncio.gather(*(
            resolve_dd_info(appver, app_artifacts_dir, env_creds, app_def_getter_plugins, ctx=ctx)
            for appver in app_versions
        ))

    logger.info(f"Start resolving DD URLs for {len(app_versions)} applications")
    start_time = time.perf_counter()
    dd_artifacts = asyncio.run(_gather())
    logger.info(f"Resolved DD URLs for {len(app_versions)} applications: {time.perf_counter() - start_time:.6f} sec")
    return dd_artifacts


def resolve_chart_url(dd: dict, registry, helm_map_repositories: dict,
                      artifact_coordinate_source: ArtifactCoordinateSource, appver: str) -> str:
    charts = dd.get('charts') or []
    if not charts:
        raise ValueError(f"Deployment descriptor of {appver} has no charts entry, the app chart is required")
    chart = charts[0]
    if artifact_coordinate_source == ArtifactCoordinateSource.AUTO and chart.get('helm_registry'):
        return _chart_field(chart, 'full_chart_name', appver)

    group_repo = registry.helm_app_config.helm_group_repo_name if registry.helm_app_config else ""
    if not group_repo:
        raise ValueError(f"Registry {registry.name} of {appver} defines no helmAppConfig.helmGroupRepoName, "
                         f"the app chart URL cannot be built")
    base = ((helm_map_repositories.get(group_repo) or {}).get('url')
            or f"{registry.maven_config.repository_domain_name.rstrip('/')}/{group_repo}")
    chart_name = _chart_field(chart, 'helm_chart_name', appver)
    chart_version = _chart_field(chart, 'helm_chart_version', appver)
    return f"{base.rstrip('/')}/{chart_name}-{chart_version}.tgz"


def _chart_field(chart: dict, field: str, appver: str) -> str:
    value = chart.get(field)
    if not value:
        raise ValueError(f"Deployment descriptor of {appver} has no charts[0].{field}")
    return value


def resolve_chart_artifact(dd_artifact: ArtifactDownload, appver: str, helm_map_repositories: dict,
                           artifact_coordinate_source: ArtifactCoordinateSource) -> ArtifactDownload:
    dd_path = Path(dd_artifact.local_target_path)
    with dd_path.open('r', encoding='utf-8') as f:
        dd = json.load(f)
    dd_source = dd_artifact.source
    chart_url = resolve_chart_url(dd, dd_source.application.registry, helm_map_repositories,
                                  artifact_coordinate_source, appver)
    chart_source = ArtifactSource(source_url=chart_url, repository=dd_source.repository,
                                  application=dd_source.application, auth_headers=dd_source.auth_headers)
    return ArtifactDownload(source=chart_source, local_target_path=str(dd_path.parent / CHART_ARCHIVE_NAME))


async def _download_chart(chart_artifact: ArtifactDownload) -> None:
    try:
        await artifact.download_all_async([chart_artifact])
    except ValueError:
        raise ValueError(f"App chart was not downloaded from {chart_artifact.source.source_url}") from None


async def _download_charts(chart_artifacts: list[ArtifactDownload]) -> None:
    await asyncio.gather(*(_download_chart(chart_artifact) for chart_artifact in chart_artifacts))


def extract_charts(chart_artifacts: list[ArtifactDownload]) -> None:
    for chart_artifact in chart_artifacts:
        chart_path = Path(chart_artifact.local_target_path)
        unpack_archive(str(chart_path), str(chart_path.parent / CHART_DIR_NAME))


def download_dd_and_chart_artifacts(
        app_versions: list[str], helm_map_repositories: dict, artifact_coordinate_source: ArtifactCoordinateSource,
        ctx=None, unresolved_app_versions: list[str] | None = None
) -> list[ArtifactDownload]:
    dd_artifacts = resolve_dd_artifacts(app_versions, ctx=ctx)
    start_time = time.perf_counter()
    asyncio.run(artifact.download_all_async(dd_artifacts))
    logger.info(f"Downloaded {len(dd_artifacts)} DD artifacts: {time.perf_counter() - start_time:.6f} sec")

    chart_app_versions = set(app_versions if unresolved_app_versions is None else unresolved_app_versions)
    chart_artifacts = [
        resolve_chart_artifact(dd_artifact, app_version, helm_map_repositories, artifact_coordinate_source)
        for app_version, dd_artifact in zip(app_versions, dd_artifacts)
        if app_version in chart_app_versions
    ]
    start_time = time.perf_counter()
    asyncio.run(_download_charts(chart_artifacts))
    extract_charts(chart_artifacts)
    logger.info(f"Downloaded and unpacked {len(chart_artifacts)} app charts: "
                f"{time.perf_counter() - start_time:.6f} sec")
    return dd_artifacts
