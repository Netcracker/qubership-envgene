import os
import shlex
import sys
from pathlib import Path

from scripts.build_env.tests.base_test import BaseTest

os.environ.setdefault("ENVIRONMENT_NAME", "env-01")
os.environ.setdefault("CLUSTER_NAME", "cluster-01")

# effective_set_entrypoint has a bare import that only resolves when
# build_effective_set_generator/scripts/ is on sys.path.
_ESE_SCRIPTS = Path(__file__).resolve().parents[4] / "build_effective_set_generator" / "scripts"
if str(_ESE_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_ESE_SCRIPTS))

from effective_set_entrypoint import _build_cli_cmd

FEATURE_TEST_DIR = "test_deployment_context"


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


# ---------------------------------------------------------------------------
# UC-ES-DEP-15: DEPLOYMENT_SESSION_ID from pipeline
# ---------------------------------------------------------------------------

class TestDeploymentSessionId(BaseTest):
    """
    UC-ES-DEP-15 — DEPLOYMENT_SESSION_ID from the instance pipeline is forwarded
    to the Java Calculator as an extra_param and appears in deployment-parameters.yaml.

    Python-level contract: _build_cli_cmd appends
    --extra_params=DEPLOYMENT_SESSION_ID=<value> when DEPLOYMENT_SESSION_ID env var is set.
    """

    def setup_method(self):
        self.feature_dir = self.output_dir / FEATURE_TEST_DIR / "dep_session_id"
        if self.feature_dir.exists():
            import shutil
            shutil.rmtree(self.feature_dir)
        self.feature_dir.mkdir(parents=True)
        for var in ("DEPLOYMENT_SESSION_ID", "EFFECTIVE_SET_CONFIG", "CUSTOM_PARAMS"):
            os.environ.pop(var, None)

    def teardown_method(self):
        for var in ("DEPLOYMENT_SESSION_ID", "EFFECTIVE_SET_CONFIG", "CUSTOM_PARAMS"):
            os.environ.pop(var, None)

    def test_session_id_forwarded_to_cli_as_extra_param(self):
        # UC-ES-DEP-15: DEPLOYMENT_SESSION_ID env var → --extra_params=DEPLOYMENT_SESSION_ID=<uuid>
        # in the CLI command so the Java Calculator writes it into deployment-parameters.yaml.
        uuid = "550e8400-e29b-41d4-a716-446655440000"
        os.environ["DEPLOYMENT_SESSION_ID"] = uuid
        sd_path = self.feature_dir / "sd.yaml"
        _write(sd_path, "applications: []\n")

        cmd = _build_cli_cmd(self.feature_dir / "es", "cluster-01/env-01", sd_path)

        assert f"--extra_params=DEPLOYMENT_SESSION_ID={uuid}" in cmd, (
            f"DEPLOYMENT_SESSION_ID extra_param not found in CLI cmd;\ncmd: {cmd}"
        )

    def test_session_id_absent_when_env_var_not_set(self):
        # UC-ES-DEP-15: when DEPLOYMENT_SESSION_ID is not set in the pipeline,
        # the --extra_params flag must not appear in the CLI command.
        sd_path = self.feature_dir / "sd.yaml"
        _write(sd_path, "applications: []\n")

        cmd = _build_cli_cmd(self.feature_dir / "es", "cluster-01/env-01", sd_path)

        assert "--extra_params=DEPLOYMENT_SESSION_ID=" not in cmd


# ---------------------------------------------------------------------------
# UC-ES-DEP-A8: custom-params.yaml from CUSTOM_PARAMS
# ---------------------------------------------------------------------------

class TestCustomParamsWiring(BaseTest):
    """
    UC-ES-DEP-A8 — The CUSTOM_PARAMS pipeline variable is forwarded to the Calculator
    as --custom-params=<value> (shell-quoted). The Calculator writes the "deployment"
    object into custom-params.yaml under deployment/<ns>/<app>/values/.

    Python-level contract: _build_cli_cmd appends --custom-params=<shlex-quoted value>
    when CUSTOM_PARAMS env var is set.

    Note — UC-ES-RUN-1 (runtime/parameters.yaml from technicalConfigurationParameters)
    and UC-ES-RUN-2 (runtime/credentials.yaml with custom-params runtime section):
    both run entirely inside the Java Calculator — Python only forwards --custom-params
    to the CLI (covered by test_custom_params_value_is_shell_quoted below).
    End-to-end verification lives in CmdbCliTest.java (build_effective_set_generator/
    effective-set-generator/src/test/java/.../CmdbCliTest.java).
    """

    CUSTOM_PARAMS_JSON = '{"deployment":{"CUSTOM_ROUTING_ENABLED":"true","CUSTOM_RESOURCE_LIMIT":"512Mi"}}'

    def setup_method(self):
        self.feature_dir = self.output_dir / FEATURE_TEST_DIR / "custom_params"
        if self.feature_dir.exists():
            import shutil
            shutil.rmtree(self.feature_dir)
        self.feature_dir.mkdir(parents=True)
        for var in ("CUSTOM_PARAMS", "DEPLOYMENT_SESSION_ID", "EFFECTIVE_SET_CONFIG"):
            os.environ.pop(var, None)

    def teardown_method(self):
        for var in ("CUSTOM_PARAMS", "DEPLOYMENT_SESSION_ID", "EFFECTIVE_SET_CONFIG"):
            os.environ.pop(var, None)

    def test_custom_params_value_is_shell_quoted(self):
        # UC-ES-DEP-A8: value is passed through shlex.quote so special chars are safe.
        # effective_set_entrypoint: cmd.append(f"--custom-params={shlex.quote(custom_params)}")
        os.environ["CUSTOM_PARAMS"] = self.CUSTOM_PARAMS_JSON
        sd_path = self.feature_dir / "sd.yaml"
        _write(sd_path, "applications: []\n")

        cmd = _build_cli_cmd(self.feature_dir / "es", "cluster-01/env-01", sd_path)

        quoted = shlex.quote(self.CUSTOM_PARAMS_JSON)
        assert f"--custom-params={quoted}" in cmd, (
            f"Expected shell-quoted --custom-params in cmd;\ncmd: {cmd}"
        )

    def test_custom_params_absent_when_env_var_not_set(self):
        # UC-ES-DEP-A8: CUSTOM_PARAMS not set → --custom-params flag absent.
        sd_path = self.feature_dir / "sd.yaml"
        _write(sd_path, "applications: []\n")

        cmd = _build_cli_cmd(self.feature_dir / "es", "cluster-01/env-01", sd_path)

        assert "--custom-params" not in cmd

    def test_custom_params_coexists_with_session_id(self):
        # UC-ES-DEP-A8: when both CUSTOM_PARAMS and DEPLOYMENT_SESSION_ID are set,
        # both flags appear in the CLI command independently.
        uuid = "550e8400-e29b-41d4-a716-446655440000"
        os.environ["CUSTOM_PARAMS"] = self.CUSTOM_PARAMS_JSON
        os.environ["DEPLOYMENT_SESSION_ID"] = uuid
        sd_path = self.feature_dir / "sd.yaml"
        _write(sd_path, "applications: []\n")

        cmd = _build_cli_cmd(self.feature_dir / "es", "cluster-01/env-01", sd_path)

        assert "--custom-params=" in cmd
        assert f"--extra_params=DEPLOYMENT_SESSION_ID={uuid}" in cmd
