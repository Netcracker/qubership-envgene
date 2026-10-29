import pytest

from pipeline.pipeline_parameters import JOB_ENV_EXPORTS, PipelineParametersHandler


@pytest.fixture(autouse=True)
def single_env(monkeypatch):
    monkeypatch.setenv("ENV_NAMES", "cluster-01/env-01")
    monkeypatch.setenv("PIPELINE_TYPE", "")
    for name in JOB_ENV_EXPORTS:
        monkeypatch.delenv(name, raising=False)


def _read_dotenv(ctx: PipelineParametersHandler) -> dict[str, str]:
    variables: dict[str, str] = {}
    for line in ctx.dotenv_path.read_text(encoding="utf-8").splitlines():
        key, _, value = line.partition("=")
        variables[key] = value
    return variables


class TestJobEnvExports:
    @pytest.mark.unit
    def test_writes_job_env_exports_to_dotenv(self, monkeypatch):
        monkeypatch.setenv("REQUESTS_CA_BUNDLE", "/etc/ssl/certs/ca-certificates.crt")
        monkeypatch.setenv("LOCAL_APPDEFS_PATH", "/repo/environments/cluster-01/env-01/AppDefs")
        monkeypatch.setenv("LOCAL_REGDEFS_PATH", "/repo/environments/cluster-01/env-01/RegDefs")
        monkeypatch.setenv("LOCAL_PUBREG_FILE", "/repo/tmp/envgene-regdefv2-adapter/pubreg_params.yaml")

        ctx = PipelineParametersHandler.from_env()
        ctx.write_dotenv()

        dotenv = _read_dotenv(ctx)
        assert dotenv["REQUESTS_CA_BUNDLE"] == "/etc/ssl/certs/ca-certificates.crt"
        assert dotenv["LOCAL_APPDEFS_PATH"] == "/repo/environments/cluster-01/env-01/AppDefs"
        assert dotenv["LOCAL_REGDEFS_PATH"] == "/repo/environments/cluster-01/env-01/RegDefs"
        assert dotenv["LOCAL_PUBREG_FILE"] == "/repo/tmp/envgene-regdefv2-adapter/pubreg_params.yaml"

    @pytest.mark.unit
    def test_skips_unset_job_env_exports(self):
        ctx = PipelineParametersHandler.from_env()
        ctx.write_dotenv()

        assert not set(JOB_ENV_EXPORTS) & set(_read_dotenv(ctx))
