from unittest.mock import MagicMock, patch

import pytest
from envgenehelper.deploy_plan_adapter import DeployPlanEntity, EnvgeneDeployPlan

from effective_set import generate_sboms as module
from effective_set.generate_sboms import generate_sboms

RESOLVED = "resolved:1.0"
MISSING = "missing:1.0"


def make_ctx(app_versions: list[str], gitlab_deploy: bool = True) -> MagicMock:
    ctx = MagicMock()
    ctx.is_gitlab_deploy.return_value = gitlab_deploy
    ctx.resolve_source_dp.return_value = EnvgeneDeployPlan(entities=[
        DeployPlanEntity(version=app_version, deployPostfix=app_version.split(":")[0])
        for app_version in app_versions
    ])
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
    return sboms_dir


def test_downloads_dds_when_all_apps_have_sboms(sboms_dir):
    write_sbom(sboms_dir, RESOLVED)
    ctx = make_ctx([RESOLVED])

    with patch.object(module, "download_dd_and_zip_artifacts", return_value=([], [])) as download, \
            patch.object(module.Generator, "generate_bom_by_content") as generate:
        generate_sboms(ctx)

    download.assert_called_once_with([RESOLVED], ctx=ctx, unresolved_app_versions=[])
    generate.assert_not_called()


def test_downloads_dds_for_all_apps_and_generates_only_missing_sboms(sboms_dir):
    write_sbom(sboms_dir, RESOLVED)
    ctx = make_ctx([RESOLVED, MISSING])
    dd_artifacts = [MagicMock(), MagicMock()]

    with patch.object(module, "download_dd_and_zip_artifacts", return_value=(dd_artifacts, [])) as download, \
            patch.object(module.Generator, "generate_bom_by_content",
                         return_value=MagicMock(sboms={}, registries={})) as generate:
        generate_sboms(ctx)

    download.assert_called_once_with([RESOLVED, MISSING], ctx=ctx, unresolved_app_versions=[MISSING])
    sd_content = generate.call_args.kwargs["sd_content"]
    assert [app.version for app in sd_content.entities] == [MISSING]
    assert generate.call_args.kwargs["dd_artifacts"] == dd_artifacts


def test_non_gitlab_deploy_skips_download_when_all_apps_have_sboms(sboms_dir):
    write_sbom(sboms_dir, RESOLVED)
    ctx = make_ctx([RESOLVED], gitlab_deploy=False)

    with patch.object(module, "download_dd_and_zip_artifacts") as download, \
            patch.object(module.Generator, "generate_bom_by_content") as generate:
        generate_sboms(ctx)

    download.assert_not_called()
    generate.assert_not_called()


def test_non_gitlab_deploy_downloads_only_missing_apps(sboms_dir):
    write_sbom(sboms_dir, RESOLVED)
    ctx = make_ctx([RESOLVED, MISSING], gitlab_deploy=False)
    dd_artifacts = [MagicMock()]

    with patch.object(module, "download_dd_and_zip_artifacts", return_value=(dd_artifacts, [])) as download, \
            patch.object(module.Generator, "generate_bom_by_content",
                         return_value=MagicMock(sboms={}, registries={})) as generate:
        generate_sboms(ctx)

    download.assert_called_once_with([MISSING], ctx=ctx)
    assert generate.call_args.kwargs["dd_artifacts"] == dd_artifacts
