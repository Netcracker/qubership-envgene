import json
import os
import shutil
import sys
from pathlib import Path
from subprocess import CalledProcessError

import pytest

from scripts.build_env.tests.base_test import BaseTest

os.environ.setdefault("ENVIRONMENT_NAME", "env-01")
os.environ.setdefault("CLUSTER_NAME", "cluster-01")

from build_effective_set_generator.scripts.handle_effective_set_config import handle_effective_set_config

# effective_set_entrypoint uses a bare import ("from handle_effective_set_config import ...")
# that only resolves when build_effective_set_generator/scripts/ is on sys.path.
_ESE_SCRIPTS = Path(__file__).resolve().parents[4] / "build_effective_set_generator" / "scripts"
if str(_ESE_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_ESE_SCRIPTS))

import effective_set_entrypoint as _ese
from effective_set_entrypoint import _build_cli_cmd, _run_full_generation

FEATURE_TEST_DIR = "test_sbom_processing"


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


# ---------------------------------------------------------------------------
# SBOM fixture builder helpers
# ---------------------------------------------------------------------------

def _prop(name: str, value: str) -> dict:
    return {"name": name, "value": value}


def _service_component(name: str) -> dict:
    """application/vnd.qubership.service component — contributes to serviceNames."""
    return {
        "type": "application",
        "mime-type": "application/vnd.qubership.service",
        "bom-ref": f"ref-{name}",
        "name": name,
        "version": "1.0.0",
        "properties": [
            _prop("deploy_param", ""),
            _prop("full_image_name", f"registry.example.local/ns/{name}:1.0.0"),
        ],
    }


def _image_component(name: str, deploy_param: str, full_image_name: str) -> dict:
    """application/octet-stream component — candidate for root deploy_param key."""
    return {
        "type": "application",
        "mime-type": "application/octet-stream",
        "bom-ref": f"ref-{name}",
        "name": name,
        "version": "",
        "properties": [
            _prop("deploy_param", deploy_param),
            _prop("full_image_name", full_image_name),
            _prop("docker_registry", "registry.example.local"),
            _prop("image_type", "image"),
        ],
    }


def _app_chart_component(name: str = "app-chart") -> dict:
    """application/vnd.qubership.app.chart component — required by app chart validation."""
    return {
        "type": "application",
        "mime-type": "application/vnd.qubership.app.chart",
        "bom-ref": f"ref-chart-{name}",
        "name": name,
        "version": "1.0.0",
    }


def _sbom(app_name: str, components: list) -> dict:
    return {
        "bomFormat": "CycloneDX",
        "specVersion": "1.6",
        "metadata": {
            "component": {
                "type": "application",
                "mime-type": "application/vnd.qubership.application",
                "name": app_name,
                "version": "1.0.0",
                "components": [
                    {
                        "type": "data",
                        "mime-type": "application/vnd.qubership.deployment-descriptor",
                        "name": f"descriptor.{app_name}",
                        "version": "1.0.0",
                    }
                ],
            }
        },
        "components": components,
    }


# ---------------------------------------------------------------------------
# UC-ES-DEP-14 / A16 / A18: CLI command wiring
# ---------------------------------------------------------------------------

class TestBuildCliCmdSbomWiring(BaseTest):
    """
    Verifies that _build_cli_cmd correctly wires --sboms-path (UC-ES-DEP-14)
    and --app_chart_validation (UC-ES-DEP-A16 / A18) into the CLI command
    passed to the Java effective-set-generator.

    Note — UC-ES-DEP-20 (collision routing), UC-ES-DEP-A9 (deploy-descriptor.yaml),
    UC-ES-DEP-A11 (per-service-parameters layout and resource profiles): all of this
    logic runs entirely inside the Java Calculator (BomReaderUtilsImplV2,
    ParametersCalculationServiceV2, CliParameterParser, HelmNameNormalizer) and is
    not reachable from Python. The Python-level contract for all three UCs is that
    --sboms-path and --sd-path are both forwarded to the CLI (covered by
    test_sboms_path_included_when_sd_file_exists and
    test_sd_path_and_registries_present_with_sboms_path below).
    End-to-end verification lives in CmdbCliTest.java (build_effective_set_generator/
    effective-set-generator/src/test/java/.../CmdbCliTest.java).
    """

    def setup_method(self):
        self.feature_dir = self.output_dir / FEATURE_TEST_DIR / "cli_cmd"
        if self.feature_dir.exists():
            shutil.rmtree(self.feature_dir)
        self.feature_dir.mkdir(parents=True)
        for var in ("EFFECTIVE_SET_CONFIG", "DEPLOYMENT_SESSION_ID", "CUSTOM_PARAMS"):
            os.environ.pop(var, None)

    def teardown_method(self):
        for var in ("EFFECTIVE_SET_CONFIG", "DEPLOYMENT_SESSION_ID", "CUSTOM_PARAMS"):
            os.environ.pop(var, None)

    # ------------------------------------------------------------------
    # UC-ES-DEP-14: --sboms-path wiring
    # ------------------------------------------------------------------

    def test_sboms_path_included_when_sd_file_exists(self):
        # UC-ES-DEP-14: sd file present → --sboms-path forwarded to CLI so the
        # Java Calculator can read SBOM components (deploy_param, full_image_name).
        sd_path = self.feature_dir / "sd.yaml"
        _write(sd_path, "applications: []\n")
        es_dir = self.feature_dir / "effective-set"

        cmd = _build_cli_cmd(es_dir, "cluster-01/env-01", sd_path)

        assert "--sboms-path=$CI_PROJECT_DIR/sboms" in cmd, (
            f"--sboms-path must be in CLI cmd when sd file exists;\ncmd: {cmd}"
        )

    def test_sboms_path_absent_when_sd_file_missing(self):
        # UC-ES-DEP-14: no sd file → --sboms-path omitted (no SBOMs to process).
        sd_path = self.feature_dir / "nonexistent_sd.yaml"
        es_dir = self.feature_dir / "effective-set"

        cmd = _build_cli_cmd(es_dir, "cluster-01/env-01", sd_path)

        assert "--sboms-path" not in cmd

    def test_sd_path_and_registries_present_with_sboms_path(self):
        # UC-ES-DEP-14: --sd-path and --registries are included alongside --sboms-path.
        sd_path = self.feature_dir / "sd.yaml"
        _write(sd_path, "applications: []\n")
        es_dir = self.feature_dir / "effective-set"

        cmd = _build_cli_cmd(es_dir, "cluster-01/env-01", sd_path)

        assert f"--sd-path={sd_path}" in cmd
        assert "--registries=" in cmd

    # ------------------------------------------------------------------
    # UC-ES-DEP-A16: --app_chart_validation=true reaches the CLI
    # ------------------------------------------------------------------

    def test_app_chart_validation_true_in_cli_command(self):
        # UC-ES-DEP-A16: EFFECTIVE_SET_CONFIG with validation enabled →
        # --app_chart_validation=true is appended to the CLI command.
        os.environ["EFFECTIVE_SET_CONFIG"] = '{"app_chart_validation": true}'
        sd_path = self.feature_dir / "sd.yaml"
        _write(sd_path, "applications: []\n")

        cmd = _build_cli_cmd(self.feature_dir / "es", "cluster-01/env-01", sd_path)

        assert "--app_chart_validation=true" in cmd, (
            f"--app_chart_validation=true expected in CLI cmd;\ncmd: {cmd}"
        )

    def test_no_effective_set_config_omits_app_chart_flag(self):
        # UC-ES-DEP-A16: without EFFECTIVE_SET_CONFIG the extra_args block is skipped.
        sd_path = self.feature_dir / "sd.yaml"
        _write(sd_path, "applications: []\n")

        cmd = _build_cli_cmd(self.feature_dir / "es", "cluster-01/env-01", sd_path)

        assert "--app_chart_validation" not in cmd

    # ------------------------------------------------------------------
    # UC-ES-DEP-A18: --app_chart_validation=false reaches the CLI
    # ------------------------------------------------------------------

    def test_app_chart_validation_false_in_cli_command(self):
        # UC-ES-DEP-A18: EFFECTIVE_SET_CONFIG with validation disabled →
        # --app_chart_validation=false is appended so the Java Calculator skips
        # app chart component presence checks.
        os.environ["EFFECTIVE_SET_CONFIG"] = '{"app_chart_validation": false}'
        sd_path = self.feature_dir / "sd.yaml"
        _write(sd_path, "applications: []\n")

        cmd = _build_cli_cmd(self.feature_dir / "es", "cluster-01/env-01", sd_path)

        assert "--app_chart_validation=false" in cmd, (
            f"--app_chart_validation=false expected in CLI cmd;\ncmd: {cmd}"
        )
        assert "--app_chart_validation=true" not in cmd


# ---------------------------------------------------------------------------
# UC-ES-DEP-A16 / A18: full generation lifecycle
# ---------------------------------------------------------------------------

class TestFullGenerationLifecycle(BaseTest):
    """
    UC-ES-DEP-A16 — generation fails (CalledProcessError propagated) when the
    Java CLI exits non-zero (e.g., app chart validation error).

    UC-ES-DEP-A18 — generation completes successfully when the Java CLI exits
    zero (app chart validation disabled via --app_chart_validation=false).
    """

    def setup_method(self):
        self.feature_dir = self.output_dir / FEATURE_TEST_DIR / "lifecycle"
        if self.feature_dir.exists():
            shutil.rmtree(self.feature_dir)
        self.feature_dir.mkdir(parents=True)

    def test_uc_dep_a16_cli_failure_propagates_as_called_process_error(self, monkeypatch):
        # UC-ES-DEP-A16: Java CLI exits non-zero (app chart validation error) →
        # _run_full_generation must propagate CalledProcessError.
        def _fail(cmd, shell=True, check=True):
            raise CalledProcessError(1, cmd)

        monkeypatch.setattr(_ese, "_build_cli_cmd", lambda *a, **kw: "fake_cmd")
        monkeypatch.setattr(_ese.subprocess, "run", _fail)

        es_dir = self.feature_dir / "effective-set"
        es_dir.mkdir(parents=True)
        sd_path = self.feature_dir / "sd.yaml"
        _write(sd_path, "applications: []\n")

        with pytest.raises(CalledProcessError):
            _run_full_generation(es_dir, "cluster-01/env-01", sd_path)

    def test_uc_dep_a16_es_dir_wiped_before_cli_is_called(self, monkeypatch):
        # UC-ES-DEP-A16: _run_full_generation deletes es_dir before invoking the CLI.
        # After a CLI failure the dir remains absent (CLI never recreated it).
        def _fail(cmd, shell=True, check=True):
            raise CalledProcessError(1, cmd)

        monkeypatch.setattr(_ese, "_build_cli_cmd", lambda *a, **kw: "fake_cmd")
        monkeypatch.setattr(_ese.subprocess, "run", _fail)

        es_dir = self.feature_dir / "effective-set-a16"
        es_dir.mkdir(parents=True)
        (es_dir / "old-output.txt").write_text("stale")
        sd_path = self.feature_dir / "sd-a16.yaml"
        _write(sd_path, "applications: []\n")

        with pytest.raises(CalledProcessError):
            _run_full_generation(es_dir, "cluster-01/env-01", sd_path)

        assert not es_dir.exists(), "effective-set dir must have been wiped before CLI call"

    def test_uc_dep_a18_cli_success_completes_without_exception(self, monkeypatch):
        # UC-ES-DEP-A18: Java CLI exits 0 (validation skipped) → _run_full_generation
        # returns normally without raising.
        monkeypatch.setattr(_ese, "_build_cli_cmd", lambda *a, **kw: "fake_cmd")
        monkeypatch.setattr(_ese.subprocess, "run", lambda cmd, shell=True, check=True: None)

        es_dir = self.feature_dir / "effective-set-a18"
        es_dir.mkdir(parents=True)
        sd_path = self.feature_dir / "sd-a18.yaml"
        _write(sd_path, "applications: []\n")

        # Must not raise.
        _run_full_generation(es_dir, "cluster-01/env-01", sd_path)

    def test_uc_dep_a18_stale_es_dir_cleared_on_success(self, monkeypatch):
        # UC-ES-DEP-A18: _run_full_generation deletes the existing effective-set dir
        # before invoking the CLI, so stale artifacts from a previous run are removed.
        monkeypatch.setattr(_ese, "_build_cli_cmd", lambda *a, **kw: "fake_cmd")
        monkeypatch.setattr(_ese.subprocess, "run", lambda cmd, shell=True, check=True: None)

        es_dir = self.feature_dir / "effective-set-a18-stale"
        es_dir.mkdir(parents=True)
        stale_file = es_dir / "stale-deployment.yaml"
        stale_file.write_text("old content")
        sd_path = self.feature_dir / "sd-a18-stale.yaml"
        _write(sd_path, "applications: []\n")

        _run_full_generation(es_dir, "cluster-01/env-01", sd_path)

        assert not stale_file.exists(), "stale file must have been removed before CLI invocation"


# ---------------------------------------------------------------------------
# UC-ES-DEP-A16 / UC-ES-DEP-A18: handle_effective_set_config app_chart flag
# ---------------------------------------------------------------------------

class TestHandleEffectiveSetConfigAppChart(BaseTest):
    """
    UC-ES-DEP-A16 — app chart validation enabled (default).
    UC-ES-DEP-A18 — app chart validation disabled via EFFECTIVE_SET_CONFIG.

    handle_effective_set_config() parses EFFECTIVE_SET_CONFIG JSON and emits
    CLI arguments consumed by the Java effective-set-generator.
    """

    # ------------------------------------------------------------------
    # UC-ES-DEP-A16: validation enabled — default and explicit true
    # ------------------------------------------------------------------

    def test_app_chart_validation_explicit_true_emits_true_flag(self):
        # UC-ES-DEP-A16: explicit true → --app_chart_validation=true; false must not appear.
        result = handle_effective_set_config('{"app_chart_validation": true}')
        assert "--app_chart_validation=true" in result["extra_args"]
        assert "--app_chart_validation=false" not in result["extra_args"]

    def test_app_chart_validation_true_version_flag_also_present(self):
        # UC-ES-DEP-A16: app chart flag and version flag both emitted.
        result = handle_effective_set_config(
            '{"version": "v2.0", "app_chart_validation": true}'
        )
        flags = result["extra_args"]
        assert any("app_chart_validation=true" in f for f in flags)
        assert any("effective-set-version=v2.0" in f for f in flags)

    def test_empty_config_defaults_app_chart_validation_to_true(self):
        # UC-ES-DEP-A16: empty JSON object → default True.
        result = handle_effective_set_config("{}")
        assert "--app_chart_validation=true" in result["extra_args"]

    # ------------------------------------------------------------------
    # UC-ES-DEP-A18: validation disabled via false flag
    # ------------------------------------------------------------------

    def test_app_chart_validation_false_emits_false_flag(self):
        # UC-ES-DEP-A18: "app_chart_validation": false → --app_chart_validation=false; true must not appear.
        result = handle_effective_set_config('{"app_chart_validation": false}')
        assert "--app_chart_validation=false" in result["extra_args"], (
            f"expected --app_chart_validation=false; got: {result['extra_args']}"
        )
        assert "--app_chart_validation=true" not in result["extra_args"]

    def test_app_chart_validation_false_with_version(self):
        # UC-ES-DEP-A18: version and app_chart_validation=false together.
        result = handle_effective_set_config(
            '{"version": "v2.0", "app_chart_validation": false}'
        )
        flags = result["extra_args"]
        assert "--app_chart_validation=false" in flags
        assert any("effective-set-version=v2.0" in f for f in flags)

    # ------------------------------------------------------------------
    # UC-ES-DEP-14: version flag
    # ------------------------------------------------------------------

    def test_version_default_applied_when_absent(self):
        # UC-ES-DEP-14: no version key → default v2.0.
        result = handle_effective_set_config('{"app_chart_validation": true}')
        assert any("effective-set-version=v2.0" in f for f in result["extra_args"])

    def test_custom_version_forwarded_to_cli(self):
        # UC-ES-DEP-14: custom version string is preserved verbatim.
        result = handle_effective_set_config('{"version": "v3.1"}')
        assert any("effective-set-version=v3.1" in f for f in result["extra_args"])

    # ------------------------------------------------------------------
    # Negative
    # ------------------------------------------------------------------

    def test_invalid_json_raises_json_decode_error(self):
        with pytest.raises(json.JSONDecodeError):
            handle_effective_set_config("not-json-{")


# ---------------------------------------------------------------------------
# UC-ES-PIPE-4/5/6/7: handle_effective_set_config consumer schema wiring
# ---------------------------------------------------------------------------

class TestHandleEffectiveSetConfigConsumers(BaseTest):
    """
    UC-ES-PIPE-4/5/6/7 — handle_effective_set_config writes each consumer
    schema to a temp file and appends one --pipeline-consumer-specific-schema-path
    flag per consumer to extra_args.  The flag is the Python-level contract that
    makes UC-ES-PIPE-4..7 possible; the actual pipeline/consumer-*.yaml files
    are written by the Java Calculator.

    Note — UC-ES-PIPE-1 (pipeline/parameters.yaml and pipeline/credentials.yaml
    from Cloud e2eParameters), UC-ES-PIPE-4..7 output file content (consumer
    parameters/credentials split, schema defaults, mandatory-key failure): all
    run entirely inside the Java Calculator (CliParameterParser.createPipelineFiles).
    End-to-end verification lives in CmdbCliTest.java (build_effective_set_generator/
    effective-set-generator/src/test/java/.../CmdbCliTest.java).
    """

    _SCHEMA = {
        "$schema": "http://json-schema.org/draft-07/schema",
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "version": {"type": "integer"},
        },
        "required": ["name", "version"],
    }

    def _config(self, consumers):
        return json.dumps({"contexts": {"pipeline": {"consumers": consumers}}})

    def test_consumer_with_inline_schema_adds_pcssp_flag(self):
        # UC-ES-PIPE-4: consumer with inline schema → one --pipeline-consumer-specific-schema-path
        # flag appended to extra_args so the Java CLI knows where to find the schema.
        config = self._config([{"name": "consumer-v1.0", "version": "v1.0", "schema": self._SCHEMA}])
        result = handle_effective_set_config(config)
        pcssp_flags = [f for f in result["extra_args"] if "--pipeline-consumer-specific-schema-path=" in f]
        assert len(pcssp_flags) == 1

    def test_consumer_schema_written_to_disk(self):
        # UC-ES-PIPE-4: inline schema is persisted so the Java CLI can read it by path.
        config = self._config([{"name": "myapp", "version": "v2.0", "schema": self._SCHEMA}])
        result = handle_effective_set_config(config)
        pcssp = next(f for f in result["extra_args"] if "--pipeline-consumer-specific-schema-path=" in f)
        schema_path = pcssp.split("=", 1)[1]
        assert Path(schema_path).is_file(), f"schema file must exist on disk: {schema_path}"

    def test_schema_filename_uses_name_and_version(self):
        # UC-ES-PIPE-4: filename = "{name}-{version}.schema.json" (consumed by Java CLI
        # to derive the consumer output file prefix).
        config = self._config([{"name": "consumer-v1.0", "version": "v1.0", "schema": self._SCHEMA}])
        result = handle_effective_set_config(config)
        pcssp = next(f for f in result["extra_args"] if "--pipeline-consumer-specific-schema-path=" in f)
        assert pcssp.endswith("consumer-v1.0-v1.0.schema.json")

    def test_multiple_consumers_produce_multiple_pcssp_flags(self):
        # UC-ES-PIPE-4: two consumers → two separate --pipeline-consumer-specific-schema-path flags.
        config = self._config([
            {"name": "app-a", "version": "v1", "schema": self._SCHEMA},
            {"name": "app-b", "version": "v2", "schema": self._SCHEMA},
        ])
        result = handle_effective_set_config(config)
        pcssp_flags = [f for f in result["extra_args"] if "--pipeline-consumer-specific-schema-path=" in f]
        assert len(pcssp_flags) == 2

    def test_no_consumers_produces_no_pcssp_flag(self):
        # UC-ES-PIPE-4: empty consumers list → no --pipeline-consumer-specific-schema-path in CLI.
        result = handle_effective_set_config('{"contexts": {"pipeline": {"consumers": []}}}')
        assert not any("pipeline-consumer-specific-schema-path" in f for f in result["extra_args"])

    def test_consumer_missing_name_or_version_is_skipped(self):
        # UC-ES-PIPE-7 precondition: consumer entry without name/version is skipped —
        # no pcssp flag emitted, no exception raised.
        config = self._config([{"schema": self._SCHEMA}])
        result = handle_effective_set_config(config)
        assert not any("pipeline-consumer-specific-schema-path" in f for f in result["extra_args"])


# ---------------------------------------------------------------------------
# UC-ES-NOSBOM-1: No SBOMs Mode — CLI command omits SD/SBOM flags
# ---------------------------------------------------------------------------

class TestNoSbomMode(BaseTest):
    """
    UC-ES-NOSBOM-1 — when no Solution Descriptor is present, the Calculator
    is invoked without --sd-path, --sboms-path, and --registries, which causes
    the Java side to generate only Pipeline and Topology contexts.

    Python-level contract: _build_cli_cmd receives a non-existent sd_path and
    must omit all three SD-related flags from the command.  The fact that only
    pipeline/ and topology/ directories are produced is Java-side behaviour
    verified in CmdbCliTest.java.
    """

    def setup_method(self):
        self.feature_dir = self.output_dir / FEATURE_TEST_DIR / "no_sbom"
        if self.feature_dir.exists():
            shutil.rmtree(self.feature_dir)
        self.feature_dir.mkdir(parents=True)
        for var in ("EFFECTIVE_SET_CONFIG", "DEPLOYMENT_SESSION_ID", "CUSTOM_PARAMS"):
            os.environ.pop(var, None)

    def teardown_method(self):
        for var in ("EFFECTIVE_SET_CONFIG", "DEPLOYMENT_SESSION_ID", "CUSTOM_PARAMS"):
            os.environ.pop(var, None)

    def test_no_sd_path_flag_when_sd_file_absent(self):
        # UC-ES-NOSBOM-1: absent sd file → --sd-path omitted from CLI command.
        sd_path = self.feature_dir / "nonexistent_sd.yaml"
        cmd = _build_cli_cmd(self.feature_dir / "es", "cluster-01/env-01", sd_path)
        assert "--sd-path" not in cmd

    def test_no_sboms_path_flag_when_sd_file_absent(self):
        # UC-ES-NOSBOM-1: absent sd file → --sboms-path omitted.
        sd_path = self.feature_dir / "nonexistent_sd.yaml"
        cmd = _build_cli_cmd(self.feature_dir / "es", "cluster-01/env-01", sd_path)
        assert "--sboms-path" not in cmd

    def test_no_registries_flag_when_sd_file_absent(self):
        # UC-ES-NOSBOM-1: absent sd file → --registries omitted.
        sd_path = self.feature_dir / "nonexistent_sd.yaml"
        cmd = _build_cli_cmd(self.feature_dir / "es", "cluster-01/env-01", sd_path)
        assert "--registries" not in cmd

    def test_env_id_and_output_still_present_in_no_sbom_mode(self):
        # UC-ES-NOSBOM-1: --env-id and --output must be present regardless of SD mode —
        # they are required for both full and No SBOMs generation.
        sd_path = self.feature_dir / "nonexistent_sd.yaml"
        es_dir = self.feature_dir / "es"
        cmd = _build_cli_cmd(es_dir, "cluster-01/env-01", sd_path)
        assert "--env-id=cluster-01/env-01" in cmd
        assert f"--output={es_dir}" in cmd

    def test_all_three_sd_flags_present_when_sd_file_exists(self):
        # UC-ES-NOSBOM-1 contrast: all three flags appear only when sd file exists.
        sd_path = self.feature_dir / "sd.yaml"
        sd_path.write_text("applications: []\n")
        cmd = _build_cli_cmd(self.feature_dir / "es", "cluster-01/env-01", sd_path)
        assert "--sd-path" in cmd
        assert "--sboms-path" in cmd
        assert "--registries" in cmd
