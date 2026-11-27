from unittest.mock import MagicMock, patch

import pytest
from envgenehelper.deploy_plan_adapter import DeployPlanEntity, EnvgeneDeployPlan
from envgenehelper.models import ArtifactCoordinateSource
from sbom_generator import generate_bom

from effective_set import generate_sboms as module
from effective_set.generate_sboms import generate_sboms

RESOLVED = "resolved:1.0"
MISSING = "missing:1.0"
HELM_MAP = {"nc.helm.charts": {"url": "https://mirror.example.com/helm"}}
SOURCE = ArtifactCoordinateSource.REGDEF


def make_ctx(app_versions: list[str], gitlab_deploy: bool = True) -> MagicMock:
    ctx = MagicMock()
    ctx.is_gitlab_deploy.return_value = gitlab_deploy
    ctx.helm_map_repositories = HELM_MAP
    entities = [
        DeployPlanEntity(version=app_version, deployPostfix=app_version.split(":")[0])
        for app_version in app_versions
    ]
    ctx.deploy_plan = MagicMock(entities=list(entities))
    ctx.deploy_plan_delta = MagicMock(entities=[])
    ctx.resolve_source_dp.return_value = EnvgeneDeployPlan(entities=entities)
    return ctx


def write_sbom(sboms_dir, app_version: str) -> None:
    app_name = app_version.split(":")[0]
    (sboms_dir / app_name).mkdir(parents=True)
    (sboms_dir / app_name / f'{app_version.replace(":", "-")}.sbom.json').write_text("{}")


@pytest.fixture
def sboms_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("CI_PROJECT_DIR", str(tmp_path))
    sboms_dir = tmp_path / "sboms"
    monkeypatch.setattr(module, "get_sboms_dir", lambda _: sboms_dir)
    monkeypatch.setattr(module, "get_artifact_coordinate_source", lambda: SOURCE)
    return sboms_dir


def test_downloads_dds_when_all_apps_have_sboms(sboms_dir):
    write_sbom(sboms_dir, RESOLVED)
    ctx = make_ctx([RESOLVED])

    with patch.object(module, "download_dd_and_chart_artifacts", return_value=[]) as download, \
            patch.object(module.Generator, "generate_bom_by_content") as generate:
        generate_sboms(ctx)

    download.assert_called_once_with([RESOLVED], HELM_MAP, SOURCE, ctx=ctx, unresolved_app_versions=[])
    generate.assert_not_called()


def test_downloads_dds_for_all_apps_and_generates_only_missing_sboms(sboms_dir):
    write_sbom(sboms_dir, RESOLVED)
    ctx = make_ctx([RESOLVED, MISSING])
    dd_artifacts = [MagicMock(), MagicMock()]

    with patch.object(module, "download_dd_and_chart_artifacts", return_value=dd_artifacts) as download, \
            patch.object(module.Generator, "generate_bom_by_content",
                         return_value=MagicMock(sboms={}, registries={})) as generate:
        generate_sboms(ctx)

    download.assert_called_once_with([RESOLVED, MISSING], HELM_MAP, SOURCE, ctx=ctx, unresolved_app_versions=[MISSING])
    sd_content = generate.call_args.kwargs["sd_content"]
    assert [app.version for app in sd_content.entities] == [MISSING]
    assert [app.version for app in ctx.resolve_source_dp.return_value.entities] == [RESOLVED, MISSING]
    assert sd_content is not ctx.resolve_source_dp.return_value
    assert generate.call_args.kwargs["dd_artifacts"] == dd_artifacts
    assert generate.call_args.kwargs["artifact_coordinate_source"] == SOURCE
    ctx.deploy_plan.write.assert_not_called()
    ctx.deploy_plan_delta.write.assert_not_called()


def test_resolves_snapshot_before_excluding_existing_sboms(sboms_dir):
    ctx = make_ctx(["app:1.0-SNAPSHOT"])
    ctx.deploy_plan_delta = MagicMock(entities=[
        DeployPlanEntity(version="app:1.0-SNAPSHOT", deployPostfix="app")
    ])
    resolved_artifact = MagicMock()
    resolved_artifact.source.resolved_version = "1.0-20261027.123456-1"
    dd_artifact = MagicMock()
    delta_path = sboms_dir / "delta-deploy-plan.yml"

    with patch.object(module, "resolve_dd_artifacts", return_value=[resolved_artifact]) as resolve, \
            patch.object(module, "download_dd_and_chart_artifacts", return_value=[dd_artifact]) as download, \
            patch.object(module.EnvgeneDeployPlan, "delta_path", return_value=delta_path), \
            patch.object(module.Generator, "generate_bom_by_content",
                         return_value=MagicMock(sboms={}, registries={})) as generate:
        generate_sboms(ctx)

    resolve.assert_called_once_with(["app:1.0-SNAPSHOT"], ctx=ctx)
    download.assert_called_once_with(
        ["app:1.0-20261027.123456-1"],
        HELM_MAP,
        SOURCE,
        ctx=ctx,
        unresolved_app_versions=["app:1.0-20261027.123456-1"],
    )
    sd_content = generate.call_args.kwargs["sd_content"]
    assert [app.version for app in sd_content.entities] == ["app:1.0-20261027.123456-1"]
    ctx.deploy_plan.write.assert_called_once_with()
    ctx.deploy_plan_delta.write.assert_called_once_with(delta_path)


def test_non_gitlab_deploy_skips_download_when_all_apps_have_sboms(sboms_dir):
    write_sbom(sboms_dir, RESOLVED)
    ctx = make_ctx([RESOLVED], gitlab_deploy=False)

    with patch.object(module, "download_dd_and_chart_artifacts") as download, \
            patch.object(module.Generator, "generate_bom_by_content") as generate:
        generate_sboms(ctx)

    download.assert_not_called()
    generate.assert_not_called()


def test_non_gitlab_deploy_downloads_only_missing_apps(sboms_dir):
    write_sbom(sboms_dir, RESOLVED)
    ctx = make_ctx([RESOLVED, MISSING], gitlab_deploy=False)
    dd_artifacts = [MagicMock()]

    with patch.object(module, "download_dd_and_chart_artifacts", return_value=dd_artifacts) as download, \
            patch.object(module.Generator, "generate_bom_by_content",
                         return_value=MagicMock(sboms={}, registries={})) as generate:
        generate_sboms(ctx)

    download.assert_called_once_with([MISSING], HELM_MAP, SOURCE, ctx=ctx)
    assert generate.call_args.kwargs["dd_artifacts"] == dd_artifacts


@pytest.mark.parametrize("gitlab_deploy", [True, False])
def test_disabled_cache_regenerates_every_run_for_each_zone(sboms_dir, monkeypatch, gitlab_deploy):
    monkeypatch.setattr(module, "get_sbom_cache_enabled", lambda: False)
    write_sbom(sboms_dir, RESOLVED)
    write_sbom(sboms_dir, "obsolete:1.0")
    ctx = make_ctx([RESOLVED, MISSING], gitlab_deploy=gitlab_deploy)
    versions = [RESOLVED, MISSING]

    for zone in ("zone-a", "zone-b"):
        fresh_sboms = {app: {"image": f"registry-{zone}/{app}"} for app in versions}
        with patch.object(module, "download_dd_and_chart_artifacts", return_value=[]) as download, \
                patch.object(generate_bom, "generate_boms",
                             return_value=MagicMock(sboms=fresh_sboms, registries={})) as generate:
            generate_sboms(ctx)

        assert download.call_args.args[0] == versions
        assert [app.version for app in generate.call_args.kwargs["sd_content"].entities] == versions
        assert not (sboms_dir / "obsolete").exists()
        for app, sbom in fresh_sboms.items():
            app_name = app.split(":")[0]
            assert module.openYaml(sboms_dir / app_name / f'{app.replace(":", "-")}.sbom.json') == sbom


@pytest.mark.parametrize("deploy_plan", [None, EnvgeneDeployPlan(entities=[])])
def test_disabled_cache_removes_old_sboms_without_deploy_plan(sboms_dir, monkeypatch, deploy_plan):
    monkeypatch.setattr(module, "get_sbom_cache_enabled", lambda: False)
    write_sbom(sboms_dir, RESOLVED)
    ctx = make_ctx([])
    ctx.resolve_source_dp.return_value = deploy_plan

    with patch.object(module, "download_dd_and_chart_artifacts") as download:
        generate_sboms(ctx)

    assert not sboms_dir.exists()
    download.assert_not_called()
