from pathlib import Path

import pytest
from envgenehelper.effective_set_helper import ESGenerationContext, ES_MAPPING_FILE, GenerationMode, PartialMergeMode, \
    ES_DIR_NAME
from envgenehelper.sd_helper import SD_FILE_NAME, DELTA_SD_FILE_NAME
from envgenehelper.yaml_helper import openYaml, writeYamlToFile

import effective_set_entrypoint
from effective_set_entrypoint import _run_reverse_merge, _run_forward_merge, effective_set_entrypoint as run_entrypoint


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
        "version": "1.0",
        "applications": apps,
    })


PARAMETERS_CONTENT = '{"param": "value"}'
ENV_NAME = "env_name"


class TestRunReverseMerge:

    @pytest.mark.unit
    def test_removes_app_dirs_namespace_still_in_full_sd(self, tmp_path):
        """Remove one app, namespace stays because another app is still in Full SD."""
        es = tmp_path / ES_DIR_NAME
        sd = tmp_path / SD_FILE_NAME
        delta = tmp_path / DELTA_SD_FILE_NAME

        create_es_app_dirs(es, "ns-1", "app-a")
        create_es_app_dirs(es, "ns-1", "app-b")
        write_sd_yaml(sd, [make_sd_app("app-b", "1.0", "ns-1")])
        write_sd_yaml(delta, [make_sd_app("app-a", "1.0", "ns-1")])

        _run_reverse_merge(es, delta, sd)

        assert not (es / ESGenerationContext.RUNTIME.value / "ns-1" / "app-a").exists()
        assert not (es / ESGenerationContext.DEPLOYMENT.value / "ns-1" / "app-a").exists()

        assert (es / ESGenerationContext.RUNTIME.value / "ns-1" / "app-b").exists()
        assert (es / ESGenerationContext.DEPLOYMENT.value / "ns-1" / "app-b").exists()

    @pytest.mark.unit
    def test_removes_namespace_when_empty_in_full_sd(self, tmp_path):
        """Remove last app - namespace absent from Full SD, dirs and mapping entries deleted."""
        es = tmp_path / ES_DIR_NAME
        sd = tmp_path / SD_FILE_NAME
        delta = tmp_path / DELTA_SD_FILE_NAME

        create_es_app_dirs(es, "ns-1", "app-a")
        create_es_cleanup_dir(es, "ns-1")
        for ctx in [ESGenerationContext.CLEANUP, ESGenerationContext.RUNTIME, ESGenerationContext.DEPLOYMENT]:
            create_es_mapping(es, ctx, {f"{ENV_NAME}-ns-1": f"/{ctx.value}/ns-1"})

        write_sd_yaml(sd, [])
        write_sd_yaml(delta, [make_sd_app("app-a", "1.0", "ns-1")])

        _run_reverse_merge(es, delta, sd)

        assert not (es / ESGenerationContext.RUNTIME.value / "ns-1").exists()
        assert not (es / ESGenerationContext.DEPLOYMENT.value / "ns-1").exists()
        assert not (es / ESGenerationContext.CLEANUP.value / "ns-1").exists()
        for ctx in [ESGenerationContext.CLEANUP, ESGenerationContext.RUNTIME, ESGenerationContext.DEPLOYMENT]:
            mapping = openYaml(es / ctx.value / ES_MAPPING_FILE)
            assert not any("ns-1" in key for key in mapping)

    @pytest.mark.unit
    def test_multiple_apps_same_namespace_removed_once(self, tmp_path):
        """Two apps in same namespace both removed — namespace deleted once, no errors."""
        es = tmp_path / ES_DIR_NAME
        sd = tmp_path / SD_FILE_NAME
        delta = tmp_path / DELTA_SD_FILE_NAME

        create_es_app_dirs(es, "ns-1", "app-a")
        create_es_app_dirs(es, "ns-1", "app-b")
        create_es_cleanup_dir(es, "ns-1")
        for ctx in [ESGenerationContext.CLEANUP, ESGenerationContext.RUNTIME, ESGenerationContext.DEPLOYMENT]:
            create_es_mapping(es, ctx, {f"{ENV_NAME}-ns-1": f"/es/{ctx.value}/ns-1"})

        write_sd_yaml(sd, [])
        write_sd_yaml(delta, [
            make_sd_app("app-a", "1.0", "ns-1"),
            make_sd_app("app-b", "1.0", "ns-1"),
        ])

        _run_reverse_merge(es, delta, sd)

        assert not (es / ESGenerationContext.RUNTIME.value / "ns-1").exists()
        assert not (es / ESGenerationContext.DEPLOYMENT.value / "ns-1").exists()
        for ctx in [ESGenerationContext.CLEANUP, ESGenerationContext.RUNTIME, ESGenerationContext.DEPLOYMENT]:
            mapping = openYaml(es / ctx.value / ES_MAPPING_FILE, allow_default=True) or {}
            assert "ns-1" not in mapping

    @pytest.mark.unit
    def test_two_namespaces_one_removed_one_kept(self, tmp_path):
        """Two namespaces: ns-1 removed (empty in Full SD), ns-2 kept (still in Full SD)."""
        es = tmp_path / ES_DIR_NAME
        sd = tmp_path / SD_FILE_NAME
        delta = tmp_path / DELTA_SD_FILE_NAME

        create_es_app_dirs(es, "ns-1", "app-a")
        create_es_app_dirs(es, "ns-2", "app-b")
        create_es_cleanup_dir(es, "ns-1")
        create_es_cleanup_dir(es, "ns-2")
        for ctx in [ESGenerationContext.CLEANUP, ESGenerationContext.RUNTIME, ESGenerationContext.DEPLOYMENT]:
            create_es_mapping(es, ctx, {
                f"{ENV_NAME}-ns-1": f"/es/{ctx.value}/ns-1",
                "ns-2": f"/es/{ctx.value}/ns-2",
            })

        write_sd_yaml(sd, [make_sd_app("app-b", "1.0", "ns-2")])
        write_sd_yaml(delta, [make_sd_app("app-a", "1.0", "ns-1")])

        _run_reverse_merge(es, delta, sd)

        assert not (es / ESGenerationContext.RUNTIME.value / "ns-1").exists()
        assert (es / ESGenerationContext.RUNTIME.value / "ns-2" / "app-b").exists()
        for ctx in [ESGenerationContext.CLEANUP, ESGenerationContext.RUNTIME, ESGenerationContext.DEPLOYMENT]:
            mapping = openYaml(es / ctx.value / ES_MAPPING_FILE, allow_default=True) or {}
            assert "ns-1" not in mapping
            assert "ns-2" in mapping

    @pytest.mark.unit
    def test_app_dir_missing_no_error(self, tmp_path):
        """App directory doesn't exist (failed previous job) — no FileNotFoundError."""
        es = tmp_path / ES_DIR_NAME
        sd = tmp_path / SD_FILE_NAME
        delta = tmp_path / DELTA_SD_FILE_NAME

        write_sd_yaml(sd, [])
        write_sd_yaml(delta, [make_sd_app("app-a", "1.0", "ns-1")])

        _run_reverse_merge(es, delta, sd)

    @pytest.mark.unit
    def test_mapping_missing_logs_warning_no_error(self, tmp_path):
        """Mapping file missing — warning logged, no exception."""
        es = tmp_path / ES_DIR_NAME
        sd = tmp_path / SD_FILE_NAME
        delta = tmp_path / DELTA_SD_FILE_NAME

        create_es_app_dirs(es, "ns-1", "app-a")
        write_sd_yaml(sd, [])
        write_sd_yaml(delta, [make_sd_app("app-a", "1.0", "ns-1")])

        _run_reverse_merge(es, delta, sd)

    @pytest.mark.unit
    def test_empty_delta_sd_no_changes(self, tmp_path):
        """Empty delta SD — nothing deleted."""
        es = tmp_path / ES_DIR_NAME
        sd = tmp_path / SD_FILE_NAME
        delta = tmp_path / DELTA_SD_FILE_NAME

        create_es_app_dirs(es, "ns-1", "app-a")
        write_sd_yaml(sd, [make_sd_app("app-a", "1.0", "ns-1")])
        write_sd_yaml(delta, [])

        _run_reverse_merge(es, delta, sd)

        assert (es / ESGenerationContext.RUNTIME.value / "ns-1" / "app-a").exists()


class TestRunForwardMerge:

    @pytest.mark.unit
    def test_topology_pipeline_deleted_before_cli(self, tmp_path, monkeypatch):
        """topology/ and pipeline/ are deleted before CLI runs."""
        es = tmp_path / ES_DIR_NAME
        delta = tmp_path / DELTA_SD_FILE_NAME

        (es / ESGenerationContext.TOPOLOGY.value).mkdir(parents=True)
        (es / ESGenerationContext.PIPELINE.value).mkdir(parents=True)
        create_es_app_dirs(es, "ns-1", "app-a")
        write_sd_yaml(delta, [make_sd_app("app-a", "1.0", "ns-1")])

        import effective_set_entrypoint
        monkeypatch.setattr(effective_set_entrypoint, "_build_cli_cmd", lambda *a: "fake_cmd")
        monkeypatch.setattr(effective_set_entrypoint.subprocess, "run", lambda cmd, check: None)

        _run_forward_merge(es, "cluster-01/env-01", delta)

        assert not (es / ESGenerationContext.TOPOLOGY.value).exists()
        assert not (es / ESGenerationContext.PIPELINE.value).exists()

    @pytest.mark.unit
    def test_cleanup_ns_deleted_per_deploy_postfix(self, tmp_path, monkeypatch):
        """cleanup/<ns> deleted only for namespaces in delta SD, others untouched."""
        es = tmp_path / ES_DIR_NAME
        delta = tmp_path / DELTA_SD_FILE_NAME

        create_es_cleanup_dir(es, "ns-1")
        create_es_cleanup_dir(es, "ns-2")
        create_es_cleanup_dir(es, "ns-3")
        write_sd_yaml(delta, [
            make_sd_app("app-a", "1.0", "ns-1"),
            make_sd_app("app-b", "1.0", "ns-2"),
        ])

        import effective_set_entrypoint
        monkeypatch.setattr(effective_set_entrypoint, "_build_cli_cmd", lambda *a: "fake_cmd")
        monkeypatch.setattr(effective_set_entrypoint.subprocess, "run", lambda cmd, check: None)

        _run_forward_merge(es, "cluster-01/env-01", delta)

        assert not (es / ESGenerationContext.CLEANUP.value / "ns-1").exists()
        assert not (es / ESGenerationContext.CLEANUP.value / "ns-2").exists()
        assert (es / ESGenerationContext.CLEANUP.value / "ns-3").exists()

    @pytest.mark.unit
    def test_mapping_upserted_not_replaced(self, tmp_path, monkeypatch):
        """Existing mapping entries outside delta SD are preserved after CLI merge."""
        es = tmp_path / ES_DIR_NAME
        delta = tmp_path / DELTA_SD_FILE_NAME

        for ctx in [ESGenerationContext.CLEANUP, ESGenerationContext.RUNTIME, ESGenerationContext.DEPLOYMENT]:
            create_es_mapping(es, ctx, {
                f"{ENV_NAME}-ns-1": f"/es/{ctx.value}/ns-1",
                "ns-2": f"/es/{ctx.value}/ns-2",
            })

        write_sd_yaml(delta, [make_sd_app("app-a", "1.0", "ns-1")])

        def fake_cli_run(cmd, check):
            for ctx in [ESGenerationContext.CLEANUP, ESGenerationContext.RUNTIME, ESGenerationContext.DEPLOYMENT]:
                create_es_mapping(es, ctx, {f"{ENV_NAME}-ns-1": f"/es/{ctx.value}/ns-1-new"})

        import effective_set_entrypoint
        monkeypatch.setattr(effective_set_entrypoint, "_build_cli_cmd", lambda *a: "fake_cmd")
        monkeypatch.setattr(effective_set_entrypoint.subprocess, "run", fake_cli_run)

        _run_forward_merge(es, "cluster-01/env-01", delta)

        for ctx in [ESGenerationContext.CLEANUP, ESGenerationContext.RUNTIME, ESGenerationContext.DEPLOYMENT]:
            mapping = openYaml(es / ctx.value / ES_MAPPING_FILE)
            assert "ns-1" in mapping
            assert "ns-2" in mapping
            assert mapping["ns-1"] == f"/es/{ctx.value}/ns-1-new"


class TestEffectiveSetEntrypoint:

    def _patch_paths(self, monkeypatch, tmp_path):
        env_dir = tmp_path / "environments" / "cluster-01" / "env-01"
        sd_dir = env_dir / "Inventory" / "solution-descriptor"
        monkeypatch.setattr(effective_set_entrypoint, "get_current_env_dir_from_env_vars", lambda: env_dir)
        monkeypatch.setattr(effective_set_entrypoint, "get_sd_dir", lambda: sd_dir)
        monkeypatch.setattr(effective_set_entrypoint, "getenv",
                            lambda key, *a: "cluster-01/env-01" if key == "FULL_ENV_NAME" else None)
        return env_dir, sd_dir

    @pytest.mark.unit
    def test_full_mode_calls_full_generation(self, tmp_path, monkeypatch):
        """FULL generation mode — _run_full_generation called, effective-set dir deleted and re-created."""
        env_dir, sd_dir = self._patch_paths(monkeypatch, tmp_path)
        sd_dir.mkdir(parents=True, exist_ok=True)
        writeYamlToFile(sd_dir / SD_FILE_NAME, {"applications": []})

        monkeypatch.setattr(effective_set_entrypoint, "resolve_es_generation_mode", lambda: GenerationMode.FULL)

        called = {}
        monkeypatch.setattr(effective_set_entrypoint, "_run_full_generation",
                            lambda es, name, sd: called.update({"es": es, "name": name, "sd": sd}))

        run_entrypoint()

        assert "es" in called
        assert called["es"] == env_dir / ES_DIR_NAME
        assert called["name"] == "cluster-01/env-01"

    @pytest.mark.unit
    def test_partial_first_run_calls_full_generation(self, tmp_path, monkeypatch):
        """PARTIAL mode, effective-set dir doesn't exist yet — first run, calls _run_full_generation."""
        env_dir, sd_dir = self._patch_paths(monkeypatch, tmp_path)
        sd_dir.mkdir(parents=True, exist_ok=True)
        writeYamlToFile(sd_dir / SD_FILE_NAME, {"applications": []})
        writeYamlToFile(sd_dir / DELTA_SD_FILE_NAME, {"applications": []})

        monkeypatch.setattr(effective_set_entrypoint, "resolve_es_generation_mode", lambda: GenerationMode.PARTIAL)

        called = {}
        monkeypatch.setattr(effective_set_entrypoint, "_run_full_generation",
                            lambda es, name, sd: called.update({"called": True}))

        run_entrypoint()

        assert called.get("called")

    @pytest.mark.unit
    def test_partial_reverse_mode(self, tmp_path, monkeypatch):
        """PARTIAL mode + REVERSE — _run_reverse_merge called."""
        env_dir, sd_dir = self._patch_paths(monkeypatch, tmp_path)
        sd_dir.mkdir(parents=True, exist_ok=True)
        writeYamlToFile(sd_dir / SD_FILE_NAME, {"applications": []})
        writeYamlToFile(sd_dir / DELTA_SD_FILE_NAME, {"applications": []})
        (env_dir / ES_DIR_NAME).mkdir(parents=True, exist_ok=True)

        monkeypatch.setattr(effective_set_entrypoint, "resolve_es_generation_mode", lambda: GenerationMode.PARTIAL)
        monkeypatch.setattr(effective_set_entrypoint, "resolve_partial_merge_mode", lambda: PartialMergeMode.REVERSE)

        called = {}
        monkeypatch.setattr(effective_set_entrypoint, "_run_reverse_merge",
                            lambda es, delta, sd: called.update({"called": True}))

        run_entrypoint()

        assert called.get("called")

    @pytest.mark.unit
    def test_partial_forward_mode(self, tmp_path, monkeypatch):
        """PARTIAL mode + FORWARD — _run_forward_merge called."""
        env_dir, sd_dir = self._patch_paths(monkeypatch, tmp_path)
        sd_dir.mkdir(parents=True, exist_ok=True)
        writeYamlToFile(sd_dir / SD_FILE_NAME, {"applications": []})
        writeYamlToFile(sd_dir / DELTA_SD_FILE_NAME, {"applications": []})
        (env_dir / ES_DIR_NAME).mkdir(parents=True, exist_ok=True)

        monkeypatch.setattr(effective_set_entrypoint, "resolve_es_generation_mode", lambda: GenerationMode.PARTIAL)
        monkeypatch.setattr(effective_set_entrypoint, "resolve_partial_merge_mode", lambda: PartialMergeMode.FORWARD)

        called = {}
        monkeypatch.setattr(effective_set_entrypoint, "_run_forward_merge",
                            lambda es, name, delta: called.update({"called": True}))

        run_entrypoint()

        assert called.get("called")

    @pytest.mark.unit
    def test_partial_missing_delta_raises(self, tmp_path, monkeypatch):
        """PARTIAL mode, delta_sd.yaml missing — ValueError raised."""
        env_dir, sd_dir = self._patch_paths(monkeypatch, tmp_path)
        sd_dir.mkdir(parents=True, exist_ok=True)
        writeYamlToFile(sd_dir / SD_FILE_NAME, {"applications": []})
        # delta_sd.yaml intentionally not created

        monkeypatch.setattr(effective_set_entrypoint, "resolve_es_generation_mode", lambda: GenerationMode.PARTIAL)

        with pytest.raises(ValueError):
            run_entrypoint()

    @pytest.mark.unit
    def test_delta_sd_deleted_after_run(self, tmp_path, monkeypatch):
        """delta_sd.yaml is deleted at the end regardless of generation mode."""
        env_dir, sd_dir = self._patch_paths(monkeypatch, tmp_path)
        sd_dir.mkdir(parents=True, exist_ok=True)
        writeYamlToFile(sd_dir / SD_FILE_NAME, {"applications": []})
        delta_path = sd_dir / DELTA_SD_FILE_NAME
        writeYamlToFile(delta_path, {"applications": []})
        (env_dir / ES_DIR_NAME).mkdir(parents=True, exist_ok=True)

        monkeypatch.setattr(effective_set_entrypoint, "resolve_es_generation_mode", lambda: GenerationMode.PARTIAL)
        monkeypatch.setattr(effective_set_entrypoint, "resolve_partial_merge_mode", lambda: PartialMergeMode.FORWARD)
        monkeypatch.setattr(effective_set_entrypoint, "_run_forward_merge", lambda *a: None)

        run_entrypoint()

        assert not delta_path.exists()
