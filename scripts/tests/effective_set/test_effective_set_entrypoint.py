from pathlib import Path

import pytest
from envgenehelper.deploy_plan_adapter import DeployPlanEntity, GenerationType
from envgenehelper.effective_set_helper import ESGenerationContext, ES_DIR_NAME, ES_MAPPING_FILE, GenerationMode, \
    PartialMergeMode
from envgenehelper.yaml_helper import openYaml, writeYamlToFile

from effective_set import effective_set_entrypoint
from effective_set.effective_set_entrypoint import _run_deploy_plan_full, _run_deploy_plan_partial, \
    _run_reverse_merge, _resolve_generation_id, _save_es_app_dirs, _restore_saved_dirs, \
    _clear_uniq_for_version_dirs, effective_set_entrypoint as run_entrypoint


PARAMETERS_CONTENT = '{"param": "value"}'
FULL_ENV_NAME = "cluster-01/env-01"
DP_1 = "deploy_postfix-1"
DP_2 = "deploy_postfix-2"
APP_1 = "app-1"
APP_2 = "app-2"
APP_VERSION = "1.0"
RUN_ID = "12345678-1234-5678-1234-567812345678"
OLD_RUN_ID = "11111111-1111-1111-1111-111111111111"


def entry(app: str, version: str, deploy_postfix: str, *, generation_type=GenerationType.UNIQ_FOR_APP,
          generation_id: str = "") -> DeployPlanEntity:
    return DeployPlanEntity(version=f"{app}:{version}", deployPostfix=deploy_postfix, namespace=deploy_postfix,
                             generationType=generation_type, generationId=generation_id)


def create_es_app_dirs(effective_set_dir: Path, deploy_postfix: str, app_name: str, generation_id: str = None):
    runtime_dir = effective_set_dir / ESGenerationContext.RUNTIME.value / deploy_postfix / app_name
    if generation_id:
        runtime_dir = runtime_dir / generation_id
    runtime_dir.mkdir(parents=True, exist_ok=True)
    (runtime_dir / "parameters.yaml").write_text(PARAMETERS_CONTENT)

    deployment_dir = effective_set_dir / ESGenerationContext.DEPLOYMENT.value / deploy_postfix / app_name
    if generation_id:
        deployment_dir = deployment_dir / generation_id
    deployment_values = deployment_dir / "values"
    deployment_values.mkdir(parents=True, exist_ok=True)
    (deployment_values / "parameters.yaml").write_text(PARAMETERS_CONTENT)


def create_es_cleanup_dir(effective_set_dir: Path, deploy_postfix: str) -> None:
    cleanup_dir = effective_set_dir / ESGenerationContext.CLEANUP.value / deploy_postfix
    cleanup_dir.mkdir(parents=True, exist_ok=True)
    (cleanup_dir / "parameters.yaml").write_text(PARAMETERS_CONTENT)


def mock_cli(monkeypatch, on_run=None):
    monkeypatch.setattr(effective_set_entrypoint, "_build_cli_cmd", lambda *a, **k: "fake_cmd")
    monkeypatch.setattr(
        effective_set_entrypoint.EnvgeneDeployPlan,
        "delta_path",
        staticmethod(lambda: Path("/tmp/delta-deploy-plan.yml")),
    )

    def fake_run(cmd, check=False, shell=False):
        if on_run:
            on_run()

    monkeypatch.setattr(effective_set_entrypoint.subprocess, "run", fake_run)


class TestRunDeployPlanPartial:
    @pytest.mark.unit
    def test_invokes_cli_with_delta_deploy_plan(self, tmp_path, monkeypatch):
        es = tmp_path / ES_DIR_NAME
        delta_dp = tmp_path / "Inventory" / "delta-deploy-plan.yml"
        delta_dp.parent.mkdir(parents=True)
        delta_dp.write_text("- version: app-1:1.0\n")
        captured = {}

        def capture_build_cli(es_dir, env_name, deploy_plan_path=None):
            captured["deploy_plan_path"] = deploy_plan_path
            return "fake_cmd"

        monkeypatch.setattr(effective_set_entrypoint, "_build_cli_cmd", capture_build_cli)
        monkeypatch.setattr(effective_set_entrypoint.subprocess, "run", lambda *a, **k: None)
        monkeypatch.setattr(
            effective_set_entrypoint.EnvgeneDeployPlan,
            "delta_path",
            staticmethod(lambda: delta_dp),
        )

        _run_deploy_plan_partial(es, FULL_ENV_NAME, [entry(APP_1, APP_VERSION, DP_1)])

        assert captured["deploy_plan_path"] == delta_dp

    @pytest.mark.unit
    def test_topology_pipeline_deleted_before_cli(self, tmp_path, monkeypatch):
        es = tmp_path / ES_DIR_NAME
        (es / ESGenerationContext.TOPOLOGY.value).mkdir(parents=True)
        (es / ESGenerationContext.PIPELINE.value).mkdir(parents=True)
        create_es_app_dirs(es, DP_1, APP_1)
        mock_cli(monkeypatch)

        _run_deploy_plan_partial(es, FULL_ENV_NAME, [entry(APP_1, APP_VERSION, DP_1)])

        assert not (es / ESGenerationContext.TOPOLOGY.value).exists()
        assert not (es / ESGenerationContext.PIPELINE.value).exists()

    @pytest.mark.unit
    def test_app_dir_deleted_before_cli(self, tmp_path, monkeypatch):
        es = tmp_path / ES_DIR_NAME
        create_es_app_dirs(es, DP_1, APP_1)
        mock_cli(monkeypatch)

        _run_deploy_plan_partial(es, FULL_ENV_NAME, [entry(APP_1, APP_VERSION, DP_1)])

        assert not (es / ESGenerationContext.RUNTIME.value / DP_1 / APP_1).exists()
        assert not (es / ESGenerationContext.DEPLOYMENT.value / DP_1 / APP_1).exists()

    @pytest.mark.unit
    def test_cleanup_ns_deleted_per_deploy_postfix(self, tmp_path, monkeypatch):
        es = tmp_path / ES_DIR_NAME
        create_es_cleanup_dir(es, DP_1)
        create_es_cleanup_dir(es, DP_2)
        create_es_cleanup_dir(es, "dp-3")
        mock_cli(monkeypatch)

        _run_deploy_plan_partial(es, FULL_ENV_NAME, [
            entry(APP_1, APP_VERSION, DP_1),
            entry(APP_2, APP_VERSION, DP_2),
        ])

        assert not (es / ESGenerationContext.CLEANUP.value / DP_1).exists()
        assert not (es / ESGenerationContext.CLEANUP.value / DP_2).exists()
        assert (es / ESGenerationContext.CLEANUP.value / "dp-3").exists()


class TestRunDeployPlanFull:
    @pytest.mark.unit
    def test_wipes_effective_set_dir(self, tmp_path, monkeypatch):
        es = tmp_path / ES_DIR_NAME
        create_es_app_dirs(es, DP_1, APP_1)
        mock_cli(monkeypatch)

        _run_deploy_plan_full(es, FULL_ENV_NAME, [entry(APP_1, APP_VERSION, DP_1)])

        assert not (es / ESGenerationContext.RUNTIME.value / DP_1 / APP_1).exists()

    @pytest.mark.unit
    def test_uniq_for_run_survives_full_wipe(self, tmp_path, monkeypatch):
        es = tmp_path / ES_DIR_NAME
        create_es_app_dirs(es, DP_1, APP_1, generation_id=OLD_RUN_ID)
        mock_cli(monkeypatch, on_run=lambda: create_es_app_dirs(es, DP_1, APP_1, generation_id=RUN_ID))

        _run_deploy_plan_full(es, FULL_ENV_NAME, [
            entry(APP_1, APP_VERSION, DP_1, generation_type=GenerationType.UNIQ_FOR_RUN, generation_id=RUN_ID),
        ])

        assert (es / ESGenerationContext.RUNTIME.value / DP_1 / APP_1 / OLD_RUN_ID / "parameters.yaml").exists()
        assert (es / ESGenerationContext.DEPLOYMENT.value / DP_1 / APP_1 / OLD_RUN_ID / "values").exists()
        assert (es / ESGenerationContext.RUNTIME.value / DP_1 / APP_1 / RUN_ID / "parameters.yaml").exists()
        assert (es / ESGenerationContext.DEPLOYMENT.value / DP_1 / APP_1 / RUN_ID / "values").exists()

    @pytest.mark.unit
    def test_uniq_for_version_sibling_survives_full_wipe(self, tmp_path, monkeypatch):
        es = tmp_path / ES_DIR_NAME
        create_es_app_dirs(es, DP_1, APP_1, generation_id="1.0")
        mock_cli(monkeypatch, on_run=lambda: create_es_app_dirs(es, DP_1, APP_1, generation_id="2.0"))

        _run_deploy_plan_full(es, FULL_ENV_NAME, [
            entry(APP_1, "2.0", DP_1, generation_type=GenerationType.UNIQ_FOR_VERSION),
        ])

        assert (es / ESGenerationContext.RUNTIME.value / DP_1 / APP_1 / "1.0" / "parameters.yaml").exists()
        assert (es / ESGenerationContext.DEPLOYMENT.value / DP_1 / APP_1 / "1.0" / "values").exists()
        assert (es / ESGenerationContext.RUNTIME.value / DP_1 / APP_1 / "2.0" / "parameters.yaml").exists()

    @pytest.mark.unit
    def test_uniq_for_version_same_version_replaces_stale_content(self, tmp_path, monkeypatch):
        es = tmp_path / ES_DIR_NAME
        create_es_app_dirs(es, DP_1, APP_1, generation_id="1.0")
        stale_file = es / ESGenerationContext.RUNTIME.value / DP_1 / APP_1 / "1.0" / "stale.yaml"
        stale_file.write_text(PARAMETERS_CONTENT)
        mock_cli(monkeypatch, on_run=lambda: create_es_app_dirs(es, DP_1, APP_1, generation_id="1.0"))

        _run_deploy_plan_full(es, FULL_ENV_NAME, [
            entry(APP_1, "1.0", DP_1, generation_type=GenerationType.UNIQ_FOR_VERSION),
        ])

        assert not stale_file.exists()
        assert (es / ESGenerationContext.RUNTIME.value / DP_1 / APP_1 / "1.0" / "parameters.yaml").exists()


class TestResolveGenerationId:
    @pytest.mark.unit
    def test_uniq_for_app_has_no_generation_id(self):
        assert _resolve_generation_id(entry(APP_1, APP_VERSION, DP_1)) is None

    @pytest.mark.unit
    def test_uniq_for_version_uses_version(self):
        e = entry(APP_1, "2.5", DP_1, generation_type=GenerationType.UNIQ_FOR_VERSION)
        assert _resolve_generation_id(e) == "2.5"

    @pytest.mark.unit
    def test_uniq_for_run_uses_generation_id(self):
        e = entry(APP_1, APP_VERSION, DP_1, generation_type=GenerationType.UNIQ_FOR_RUN, generation_id=RUN_ID)
        assert _resolve_generation_id(e) == RUN_ID


class TestClearUniqForVersionDirs:
    @pytest.mark.unit
    def test_clears_matching_version_only(self, tmp_path):
        es = tmp_path / ES_DIR_NAME
        create_es_app_dirs(es, DP_1, APP_1, generation_id="1.0")
        create_es_app_dirs(es, DP_1, APP_1, generation_id="2.0")

        _clear_uniq_for_version_dirs(es, [
            entry(APP_1, "1.0", DP_1, generation_type=GenerationType.UNIQ_FOR_VERSION),
        ])

        assert not (es / ESGenerationContext.RUNTIME.value / DP_1 / APP_1 / "1.0").exists()
        assert (es / ESGenerationContext.RUNTIME.value / DP_1 / APP_1 / "2.0").exists()

    @pytest.mark.unit
    def test_uniq_for_run_not_cleared(self, tmp_path):
        es = tmp_path / ES_DIR_NAME
        create_es_app_dirs(es, DP_1, APP_1, generation_id=RUN_ID)

        _clear_uniq_for_version_dirs(es, [
            entry(APP_1, APP_VERSION, DP_1, generation_type=GenerationType.UNIQ_FOR_RUN, generation_id=RUN_ID),
        ])

        assert (es / ESGenerationContext.RUNTIME.value / DP_1 / APP_1 / RUN_ID).exists()

    @pytest.mark.unit
    def test_uniq_for_app_not_cleared(self, tmp_path):
        es = tmp_path / ES_DIR_NAME
        create_es_app_dirs(es, DP_1, APP_1)

        _clear_uniq_for_version_dirs(es, [entry(APP_1, APP_VERSION, DP_1)])

        assert (es / ESGenerationContext.RUNTIME.value / DP_1 / APP_1).exists()


class TestSaveNestedGenerationDirs:
    @pytest.mark.unit
    def test_uniq_for_run_saved_and_restored(self, tmp_path):
        es = tmp_path / ES_DIR_NAME
        create_es_app_dirs(es, DP_1, APP_1)

        tmp_root, saved = _save_es_app_dirs(es, [
            entry(APP_1, APP_VERSION, DP_1, generation_type=GenerationType.UNIQ_FOR_RUN, generation_id=RUN_ID),
        ])
        assert not (es / ESGenerationContext.RUNTIME.value / DP_1 / APP_1).exists()

        _restore_saved_dirs(tmp_root, saved)
        assert (es / ESGenerationContext.RUNTIME.value / DP_1 / APP_1 / "parameters.yaml").exists()

    @pytest.mark.unit
    def test_uniq_for_version_also_saved(self, tmp_path):
        es = tmp_path / ES_DIR_NAME
        create_es_app_dirs(es, DP_1, APP_1)

        tmp_root, saved = _save_es_app_dirs(es, [
            entry(APP_1, "1.0", DP_1, generation_type=GenerationType.UNIQ_FOR_VERSION),
        ])

        assert not (es / ESGenerationContext.RUNTIME.value / DP_1 / APP_1).exists()
        assert tmp_root is not None

    @pytest.mark.unit
    def test_uniq_for_app_not_saved(self, tmp_path):
        es = tmp_path / ES_DIR_NAME
        create_es_app_dirs(es, DP_1, APP_1)

        tmp_root, saved = _save_es_app_dirs(es, [entry(APP_1, APP_VERSION, DP_1)])

        assert tmp_root is None
        assert saved == []


class TestRunReverseMerge:
    @pytest.mark.unit
    def test_removed_app_deleted_namespace_survives(self, tmp_path):
        es = tmp_path / ES_DIR_NAME
        create_es_app_dirs(es, DP_1, APP_1)
        create_es_app_dirs(es, DP_1, APP_2)

        _run_reverse_merge(es, [entry(APP_2, APP_VERSION, DP_1)], [entry(APP_1, APP_VERSION, DP_1)])

        assert not (es / ESGenerationContext.RUNTIME.value / DP_1 / APP_1).exists()
        assert not (es / ESGenerationContext.DEPLOYMENT.value / DP_1 / APP_1).exists()
        assert (es / ESGenerationContext.RUNTIME.value / DP_1 / APP_2).exists()
        assert (es / ESGenerationContext.RUNTIME.value / DP_1).exists()

    @pytest.mark.unit
    def test_namespace_emptied_deletes_whole_namespace(self, tmp_path):
        es = tmp_path / ES_DIR_NAME
        create_es_app_dirs(es, DP_1, APP_1)
        create_es_cleanup_dir(es, DP_1)

        _run_reverse_merge(es, [], [entry(APP_1, APP_VERSION, DP_1)])

        assert not (es / ESGenerationContext.RUNTIME.value / DP_1).exists()
        assert not (es / ESGenerationContext.DEPLOYMENT.value / DP_1).exists()
        assert not (es / ESGenerationContext.CLEANUP.value / DP_1).exists()

    @pytest.mark.unit
    def test_removes_emptied_namespace_from_mapping_files(self, tmp_path):
        es = tmp_path / ES_DIR_NAME
        create_es_app_dirs(es, DP_1, APP_1)
        runtime_mapping_path = es / ESGenerationContext.RUNTIME.value / ES_MAPPING_FILE
        runtime_mapping_path.parent.mkdir(parents=True, exist_ok=True)
        writeYamlToFile(runtime_mapping_path, {f"{DP_1}/{APP_1}": {"some": "mapping"}, "dp-3/app-3": {}})

        _run_reverse_merge(es, [], [entry(APP_1, APP_VERSION, DP_1)])

        mapping = openYaml(runtime_mapping_path, allow_default=True)
        assert f"{DP_1}/{APP_1}" not in mapping
        assert "dp-3/app-3" in mapping


class TestEffectiveSetEntrypointDispatch:
    @pytest.mark.unit
    def test_reverse_mode_calls_cleanup_not_generation(self, tmp_path, monkeypatch):
        es = tmp_path / ES_DIR_NAME
        create_es_app_dirs(es, DP_1, APP_1)
        monkeypatch.setenv("FULL_ENV_NAME", FULL_ENV_NAME)
        monkeypatch.setattr(effective_set_entrypoint, "get_current_env_dir_from_env_vars", lambda: tmp_path)
        monkeypatch.setattr(effective_set_entrypoint, "get_sd_dir", lambda: tmp_path)

        called = {}
        monkeypatch.setattr(effective_set_entrypoint, "_run_reverse_merge",
                             lambda *a: called.setdefault("cleanup", True))
        monkeypatch.setattr(effective_set_entrypoint, "_run_deploy_plan_partial",
                             lambda *a: called.setdefault("partial", True))
        monkeypatch.setattr(effective_set_entrypoint, "_run_deploy_plan_full",
                             lambda *a: called.setdefault("full", True))
        monkeypatch.setattr(effective_set_entrypoint.EnvgeneDeployPlan, "delta_path", staticmethod(lambda: tmp_path / "delta-deploy-plan.yml"))

        class Ctx:
            deploy_plan = type("DP", (), {"entities": [entry(APP_1, APP_VERSION, DP_1)]})()
            deploy_plan_delta = type("DP", (), {"entities": []})()
            es_generation_mode = GenerationMode.PARTIAL
            partial_merge_mode = PartialMergeMode.REVERSE

            def is_gitlab_deploy(self):
                return False

        run_entrypoint(Ctx())

        assert called == {"cleanup": True}
