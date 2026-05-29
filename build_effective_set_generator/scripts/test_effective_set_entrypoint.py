from pathlib import Path

import pytest
from envgenehelper.effective_set_helper import ESGenerationContext, ES_MAPPING_FILE, ES_DIR_NAME
from envgenehelper.sd_helper import SD_FILE_NAME, DELTA_SD_FILE_NAME
from envgenehelper.yaml_helper import openYaml, writeYamlToFile

import effective_set_entrypoint
from effective_set_entrypoint import _run_reverse_merge, _run_forward_merge


def create_es_app_dirs(effective_set_dir: Path, deploy_postfix: str, app_name: str):
    for ctx in [ESGenerationContext.RUNTIME, ESGenerationContext.DEPLOYMENT]:
        app_dir = effective_set_dir / ctx.value / deploy_postfix / app_name
        app_dir.mkdir(parents=True, exist_ok=True)
        (app_dir / "parameters.yaml").write_text(PARAMETERS_CONTENT)


def create_es_cleanup_dir(effective_set_dir: Path, deploy_postfix: str) -> None:
    cleanup_dir = effective_set_dir / ESGenerationContext.CLEANUP.value / deploy_postfix
    cleanup_dir.mkdir(parents=True, exist_ok=True)
    (cleanup_dir / "parameters.yaml").write_text(PARAMETERS_CONTENT)


def create_es_mapping(effective_set_dir: Path, ctx: ESGenerationContext, entries: dict) -> None:
    mapping_path = effective_set_dir / ctx.value / ES_MAPPING_FILE
    mapping_path.parent.mkdir(parents=True, exist_ok=True)
    writeYamlToFile(mapping_path, entries)


def make_sd_app(name: str, version: str, deploy_postfix: str) -> dict:
    return {
        "version": f"{name}:{version}",
        "deployPostfix": deploy_postfix,
    }


def write_sd_yaml(path: Path, apps: list[dict]) -> None:
    writeYamlToFile(path, {
        "version": APP_VERSION,
        "applications": apps,
    })


PARAMETERS_CONTENT = '{"param": "value"}'
ENV_NAME = "ENV_NAME"
CLUSTER_NAME = "cluster-01"
DP_1 = "deploy_postfix-1"
DP_2 = "deploy_postfix-2"
APP_1 = "app-1"
APP_2 = "app-2"
APP_VERSION = "1.0"


class TestRunReverseMerge:

    @pytest.mark.unit
    def test_removes_app_dirs_namespace_still_in_full_sd(self, tmp_path):
        """Remove one app, namespace stays because another app is still in Full SD"""
        es = tmp_path / ES_DIR_NAME
        sd = tmp_path / SD_FILE_NAME
        delta = tmp_path / DELTA_SD_FILE_NAME

        create_es_app_dirs(es, DP_1, APP_1)
        create_es_app_dirs(es, DP_1, APP_2)
        write_sd_yaml(sd, [make_sd_app(APP_2, APP_VERSION, DP_1)])
        write_sd_yaml(delta, [make_sd_app(APP_1, APP_VERSION, DP_1)])

        _run_reverse_merge(es, delta, sd)

        assert not (es / ESGenerationContext.RUNTIME.value / DP_1 / APP_1).exists()
        assert not (es / ESGenerationContext.DEPLOYMENT.value / DP_1 / APP_1).exists()

        assert (es / ESGenerationContext.RUNTIME.value / DP_1 / APP_2).exists()
        assert (es / ESGenerationContext.DEPLOYMENT.value / DP_1 / APP_2).exists()

    @pytest.mark.unit
    def test_multiple_apps_same_namespace_removed_once(self, tmp_path):
        """Two apps in same namespace both removed - namespace dirs and mapping entries deleted"""
        es = tmp_path / ES_DIR_NAME
        sd = tmp_path / SD_FILE_NAME
        delta = tmp_path / DELTA_SD_FILE_NAME

        create_es_app_dirs(es, DP_1, APP_1)
        create_es_app_dirs(es, DP_1, APP_2)
        create_es_cleanup_dir(es, DP_1)
        for ctx in [ESGenerationContext.CLEANUP, ESGenerationContext.RUNTIME, ESGenerationContext.DEPLOYMENT]:
            create_es_mapping(es, ctx, {f"{ENV_NAME}-{DP_1}": f"/{ctx.value}/{DP_1}"})

        write_sd_yaml(sd, [])
        write_sd_yaml(delta, [
            make_sd_app(APP_1, APP_VERSION, DP_1),
            make_sd_app(APP_2, APP_VERSION, DP_1),
        ])

        _run_reverse_merge(es, delta, sd)

        assert not (es / ESGenerationContext.RUNTIME.value / DP_1).exists()
        assert not (es / ESGenerationContext.DEPLOYMENT.value / DP_1).exists()
        assert not (es / ESGenerationContext.CLEANUP.value / DP_1).exists()
        for ctx in [ESGenerationContext.CLEANUP, ESGenerationContext.RUNTIME, ESGenerationContext.DEPLOYMENT]:
            mapping = openYaml(es / ctx.value / ES_MAPPING_FILE)
            assert not any(DP_1 in key for key in mapping)
            assert not any(DP_2 in key for key in mapping)

    @pytest.mark.unit
    def test_two_namespaces_one_removed_one_kept(self, tmp_path):
        """Two namespaces: ns-1 removed (empty in Full SD), ns-2 kept (still in Full SD)."""
        es = tmp_path / ES_DIR_NAME
        sd = tmp_path / SD_FILE_NAME
        delta = tmp_path / DELTA_SD_FILE_NAME

        create_es_app_dirs(es, DP_1, APP_1)
        create_es_app_dirs(es, DP_2, APP_2)
        create_es_cleanup_dir(es, DP_1)
        create_es_cleanup_dir(es, DP_2)
        for ctx in [ESGenerationContext.CLEANUP, ESGenerationContext.RUNTIME, ESGenerationContext.DEPLOYMENT]:
            create_es_mapping(es, ctx, {
                f"{ENV_NAME}-{DP_1}": f"/{ctx.value}/{DP_1}",
                f"{ENV_NAME}-{DP_2}": f"/{ctx.value}/{DP_2}",
            })

        write_sd_yaml(sd, [make_sd_app(APP_2, APP_VERSION, DP_2)])
        write_sd_yaml(delta, [make_sd_app(APP_1, APP_VERSION, DP_1)])

        _run_reverse_merge(es, delta, sd)

        assert not (es / ESGenerationContext.RUNTIME.value / DP_1).exists()
        assert (es / ESGenerationContext.RUNTIME.value / DP_2 / APP_2).exists()
        for ctx in [ESGenerationContext.CLEANUP, ESGenerationContext.RUNTIME, ESGenerationContext.DEPLOYMENT]:
            mapping = openYaml(es / ctx.value / ES_MAPPING_FILE)
            assert not any(DP_1 in key for key in mapping)
            assert any(DP_2 in key for key in mapping)

    @pytest.mark.unit
    def test_app_dir_missing_no_error(self, tmp_path):
        """App directory doesn't exist (failed previous job) and mapping file missing - no exception"""
        es = tmp_path / ES_DIR_NAME
        sd = tmp_path / SD_FILE_NAME
        delta = tmp_path / DELTA_SD_FILE_NAME

        write_sd_yaml(sd, [])
        write_sd_yaml(delta, [make_sd_app(APP_1, APP_VERSION, DP_1)])

        _run_reverse_merge(es, delta, sd)


class TestRunForwardMerge:
    full_env_name = f"{CLUSTER_NAME}/{ENV_NAME}"

    def mock_effective_set_cli(self, monkeypatch):
        monkeypatch.setattr(effective_set_entrypoint, "_build_cli_cmd", lambda *a: "fake_cmd")
        monkeypatch.setattr(effective_set_entrypoint.subprocess, "run", lambda cmd, check: None)

    @pytest.mark.unit
    def test_topology_pipeline_deleted_before_cli(self, tmp_path, monkeypatch):
        """topology and pipeline are deleted before CLI runs"""
        es = tmp_path / ES_DIR_NAME
        delta = tmp_path / DELTA_SD_FILE_NAME

        (es / ESGenerationContext.TOPOLOGY.value).mkdir(parents=True)
        (es / ESGenerationContext.PIPELINE.value).mkdir(parents=True)
        create_es_app_dirs(es, DP_1, APP_1)
        write_sd_yaml(delta, [make_sd_app(APP_1, APP_VERSION, DP_1)])

        self.mock_effective_set_cli(monkeypatch)

        _run_forward_merge(es, self.full_env_name, delta)

        assert not (es / ESGenerationContext.TOPOLOGY.value).exists()
        assert not (es / ESGenerationContext.PIPELINE.value).exists()

    @pytest.mark.unit
    def test_cleanup_ns_deleted_per_deploy_postfix(self, tmp_path, monkeypatch):
        """cleanup/<deploy-postfix> deleted only for dp in delta SD, others untouched"""
        es = tmp_path / ES_DIR_NAME
        delta = tmp_path / DELTA_SD_FILE_NAME

        create_es_cleanup_dir(es, DP_1)
        create_es_cleanup_dir(es, DP_2)
        create_es_cleanup_dir(es, "dp-3")
        write_sd_yaml(delta, [
            make_sd_app(APP_1, APP_VERSION, DP_1),
            make_sd_app(APP_2, APP_VERSION, DP_2),
        ])
        self.mock_effective_set_cli(monkeypatch)

        _run_forward_merge(es, self.full_env_name, delta)

        assert not (es / ESGenerationContext.CLEANUP.value / DP_1).exists()
        assert not (es / ESGenerationContext.CLEANUP.value / DP_2).exists()
        assert (es / ESGenerationContext.CLEANUP.value / "dp-3").exists()
