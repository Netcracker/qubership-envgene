import json
import os
import sys
from pathlib import Path

import pytest

from scripts.build_env.tests.base_test import BaseTest

os.environ.setdefault("ENVIRONMENT_NAME", "env-01")
os.environ.setdefault("CLUSTER_NAME", "cluster-01")

_ESE_SCRIPTS = Path(__file__).resolve().parents[4] / "build_effective_set_generator" / "scripts"
if str(_ESE_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_ESE_SCRIPTS))

from build_effective_set_generator.scripts.handle_effective_set_config import handle_effective_set_config
from effective_set_entrypoint import _build_cli_cmd

_FIXTURES = (
    Path(__file__).resolve().parents[4]
    / "build_effective_set_generator"
    / "effective-set-generator"
    / "src" / "test" / "resources"
    / "environments" / "cluster-01" / "pl-01" / "effective-set"
)

FEATURE_TEST_DIR = "test_traceability"


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


def _fixture_text(rel: str) -> str:
    return (_FIXTURES / rel).read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# UC-ES-TR-1 / UC-ES-TR-2: --enable-traceability flag wiring
# ---------------------------------------------------------------------------

class TestTraceabilityFlagHandleConfig(BaseTest):
    """
    UC-ES-TR-1 — handle_effective_set_config emits --enable-traceability=true
    when EFFECTIVE_SET_CONFIG sets enable_traceability: true.

    UC-ES-TR-2 — flag is --enable-traceability=false when key is absent (default)
    or explicitly false.

    Content of output files (inline source comments, multiline placement, deploy-
    descriptor header, mapping.yaml omission) is produced by the Java Calculator
    and is not reachable from Python. End-to-end verification lives in
    CmdbCliTest.java (build_effective_set_generator/effective-set-generator/
    src/test/java/.../CmdbCliTest.java).
    """

    def test_enable_traceability_true_emits_true_flag(self):
        # UC-ES-TR-1: explicit true → --enable-traceability=true in extra_args.
        result = handle_effective_set_config('{"enable_traceability": true}')
        assert "--enable-traceability=true" in result["extra_args"]
        assert "--enable-traceability=false" not in result["extra_args"]

    def test_enable_traceability_false_emits_false_flag(self):
        # UC-ES-TR-2: explicit false → --enable-traceability=false.
        result = handle_effective_set_config('{"enable_traceability": false}')
        assert "--enable-traceability=false" in result["extra_args"]
        assert "--enable-traceability=true" not in result["extra_args"]

    def test_traceability_defaults_to_false_when_key_absent(self):
        # UC-ES-TR-2: key absent → default false; no traceability comments generated.
        result = handle_effective_set_config("{}")
        assert "--enable-traceability=false" in result["extra_args"]
        assert "--enable-traceability=true" not in result["extra_args"]

    def test_traceability_coexists_with_app_chart_validation_flag(self):
        # UC-ES-TR-1: both flags emitted in the same config without interference.
        result = handle_effective_set_config(
            '{"enable_traceability": true, "app_chart_validation": false}'
        )
        assert "--enable-traceability=true" in result["extra_args"]
        assert "--app_chart_validation=false" in result["extra_args"]

    def test_traceability_coexists_with_version_flag(self):
        # UC-ES-TR-1: traceability flag present alongside --effective-set-version.
        result = handle_effective_set_config(
            '{"enable_traceability": true, "version": "v2.0"}'
        )
        assert "--enable-traceability=true" in result["extra_args"]
        assert any("effective-set-version=v2.0" in f for f in result["extra_args"])

    def test_traceability_flag_always_present_in_extra_args(self):
        # UC-ES-TR-1 / TR-2: the flag is always emitted (never omitted silently),
        # so the Java Calculator always receives an explicit mode instruction.
        for cfg in ('{}', '{"enable_traceability": true}', '{"enable_traceability": false}'):
            result = handle_effective_set_config(cfg)
            traceability_flags = [f for f in result["extra_args"] if "--enable-traceability=" in f]
            assert len(traceability_flags) == 1, (
                f"exactly one --enable-traceability flag expected; got {traceability_flags} for cfg={cfg}"
            )


class TestTraceabilityFlagBuildCliCmd(BaseTest):
    """
    UC-ES-TR-1 / UC-ES-TR-2 — _build_cli_cmd propagates --enable-traceability
    to the final shell command via EFFECTIVE_SET_CONFIG → handle_effective_set_config.
    """

    def setup_method(self):
        self.feature_dir = self.output_dir / FEATURE_TEST_DIR / "cli_cmd"
        if self.feature_dir.exists():
            import shutil
            shutil.rmtree(self.feature_dir)
        self.feature_dir.mkdir(parents=True)
        for var in ("EFFECTIVE_SET_CONFIG", "DEPLOYMENT_SESSION_ID", "CUSTOM_PARAMS"):
            os.environ.pop(var, None)

    def teardown_method(self):
        for var in ("EFFECTIVE_SET_CONFIG", "DEPLOYMENT_SESSION_ID", "CUSTOM_PARAMS"):
            os.environ.pop(var, None)

    def test_enable_traceability_true_reaches_cli_command(self):
        # UC-ES-TR-1: EFFECTIVE_SET_CONFIG with enable_traceability=true →
        # --enable-traceability=true appears in the CLI command string.
        os.environ["EFFECTIVE_SET_CONFIG"] = '{"enable_traceability": true}'
        sd_path = self.feature_dir / "sd.yaml"
        _write(sd_path, "applications: []\n")

        cmd = _build_cli_cmd(self.feature_dir / "es", "cluster-01/env-01", sd_path)

        assert "--enable-traceability=true" in cmd, (
            f"--enable-traceability=true must be in CLI cmd;\ncmd: {cmd}"
        )

    def test_enable_traceability_false_reaches_cli_command(self):
        # UC-ES-TR-2: EFFECTIVE_SET_CONFIG with enable_traceability=false →
        # --enable-traceability=false in CLI command; no annotation comments produced.
        os.environ["EFFECTIVE_SET_CONFIG"] = '{"enable_traceability": false}'
        sd_path = self.feature_dir / "sd.yaml"
        _write(sd_path, "applications: []\n")

        cmd = _build_cli_cmd(self.feature_dir / "es", "cluster-01/env-01", sd_path)

        assert "--enable-traceability=false" in cmd
        assert "--enable-traceability=true" not in cmd

    def test_traceability_absent_from_cmd_when_no_effective_set_config(self):
        # UC-ES-TR-2: no EFFECTIVE_SET_CONFIG → entire extra_args block skipped;
        # --enable-traceability must not appear in the command at all.
        sd_path = self.feature_dir / "sd.yaml"
        _write(sd_path, "applications: []\n")

        cmd = _build_cli_cmd(self.feature_dir / "es", "cluster-01/env-01", sd_path)

        assert "--enable-traceability" not in cmd


# ---------------------------------------------------------------------------
# UC-ES-TR-5: mapping.yaml and credentials files contain no comments
# ---------------------------------------------------------------------------

class TestMappingYamlNoComments(BaseTest):
    """
    UC-ES-TR-5 — mapping.yaml files must never contain #source comments,
    even when --enable-traceability=true is active.  The fixture files capture
    the expected output of the Java Calculator for this invariant.
    """

    @pytest.mark.parametrize("rel_path", [
        "deployment/mapping.yaml",
        "runtime/mapping.yaml",
        "cleanup/mapping.yaml",
    ])
    def test_mapping_yaml_has_no_comment_lines(self, rel_path):
        # UC-ES-TR-5: no line in any mapping.yaml begins with '#'.
        for line in _fixture_text(rel_path).splitlines():
            stripped = line.strip()
            if stripped:
                assert not stripped.startswith("#"), (
                    f"{rel_path} must not contain comment lines; found: {line!r}"
                )

    @pytest.mark.parametrize("rel_path", [
        "deployment/mapping.yaml",
        "runtime/mapping.yaml",
        "cleanup/mapping.yaml",
    ])
    def test_mapping_yaml_has_no_inline_comments(self, rel_path):
        # UC-ES-TR-5: no value line contains an inline '#' comment.
        for line in _fixture_text(rel_path).splitlines():
            if ":" in line:
                value_part = line.split(":", 1)[1]
                assert " #" not in value_part, (
                    f"{rel_path} must not contain inline comments; found: {line!r}"
                )
