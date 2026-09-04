import os
from pathlib import Path

import pytest

from pipeline.resolve_env_names import RESOLVED_ENV_FILE, main, resolve_env_names


@pytest.fixture(autouse=True)
def clear_env_selection(monkeypatch):
    monkeypatch.delenv("CLUSTER_NAME", raising=False)
    monkeypatch.delenv("ENVIRONMENT_NAME", raising=False)
    monkeypatch.delenv("FULL_ENV_NAME", raising=False)
    monkeypatch.delenv("PIPELINE_TYPE", raising=False)
    monkeypatch.delenv("ENV_NAMES", raising=False)


class TestResolveEnvNames:
    @pytest.mark.unit
    def test_fails_when_no_env_selection(self):
        with pytest.raises(ValueError, match="Set ENV_NAMES or both CLUSTER_NAME and ENVIRONMENT_NAME"):
            resolve_env_names()

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "extra_env",
        [
            {"CLUSTER_NAME": "cluster-01"},
            {"ENVIRONMENT_NAME": "env-01"},
            {"ENV_NAMES": "cluster-02/env-02", "ENVIRONMENT_NAME": "env-01"},
            {"ENV_NAMES": "cluster-02/env-02", "CLUSTER_NAME": "cluster-01"},
        ],
    )
    def test_fails_when_cluster_name_or_environment_name_is_not_provided(self, monkeypatch, extra_env):
        monkeypatch.setenv("ENV_NAMES", "cluster-02/env-02")
        for key, value in extra_env.items():
            monkeypatch.setenv(key, value)

        with pytest.raises(
            ValueError,
            match="Set both CLUSTER_NAME and ENVIRONMENT_NAME",
        ):
            resolve_env_names()

    @pytest.mark.unit
    def test_fails_when_env_names_has_invalid_format(self, monkeypatch):

        with pytest.raises(ValueError, match="Set ENV_NAMES or both CLUSTER_NAME and ENVIRONMENT_NAME"):
            resolve_env_names()

    @pytest.mark.unit
    def test_passes_with_cluster_name_environment_name_even_if_env_names_provided(self, monkeypatch):
        monkeypatch.setenv("ENV_NAMES", "cluster-01/env-01")
        monkeypatch.setenv("CLUSTER_NAME", "cluster-02")
        monkeypatch.setenv("ENVIRONMENT_NAME", "env-02")

        assert resolve_env_names() == ["cluster-02/env-02"]
        assert os.environ["ENV_NAMES"] == "cluster-02/env-02"

    @pytest.mark.unit
    def test_passes_with_env_names_only(self, monkeypatch):
        monkeypatch.setenv("ENV_NAMES", "cluster-01/env-01")

        assert resolve_env_names() == ["cluster-01/env-01"]
        assert os.environ["ENV_NAMES"] == "cluster-01/env-01"

    @pytest.mark.unit
    def test_fails_when_env_names_has_invalid_format(self, monkeypatch):
        monkeypatch.setenv("ENV_NAMES", "cluster-01-env-01")

        with pytest.raises(ValueError, match="Invalid environment name"):
            resolve_env_names()

    @pytest.mark.unit
    def test_synthesises_env_names_from_cluster_and_environment_name(self, monkeypatch):
        monkeypatch.setenv("CLUSTER_NAME", "cluster-01")
        monkeypatch.setenv("ENVIRONMENT_NAME", "env-01")

        assert resolve_env_names() == ["cluster-01/env-01"]
        assert os.environ["ENV_NAMES"] == "cluster-01/env-01"

    @pytest.mark.unit
    def test_allows_multi_env_when_pipeline_type_unset(self, monkeypatch):
        monkeypatch.setenv("ENV_NAMES", "cluster-01/env-01,cluster-02/env-02")

        assert resolve_env_names() == ["cluster-01/env-01", "cluster-02/env-02"]

    @pytest.mark.unit
    def test_rejects_multi_env_for_gitlab_deploy(self, monkeypatch):
        monkeypatch.setenv("PIPELINE_TYPE", "GITLAB_DEPLOY")
        monkeypatch.setenv("ENV_NAMES", "cluster-01/env-01,cluster-02/env-02")

        with pytest.raises(ValueError, match="Multiple values in ENV_NAMES are not supported"):
            resolve_env_names()

    @pytest.mark.unit
    def test_allows_single_env_for_gitlab_deploy(self, monkeypatch):
        monkeypatch.setenv("PIPELINE_TYPE", "GITLAB_DEPLOY")
        monkeypatch.setenv("ENV_NAMES", "cluster-01/env-01")

        assert resolve_env_names() == ["cluster-01/env-01"]


class TestResolvedEnvFile:
    @staticmethod
    def _read_resolved_env() -> dict[str, str]:
        variables: dict[str, str] = {}
        for line in Path(RESOLVED_ENV_FILE).read_text(encoding="utf-8").splitlines():
            key, _, value = line.partition("=")
            variables[key] = value
        return variables

    @pytest.mark.unit
    def test_writes_per_env_paths_for_single_env(self, monkeypatch, tmp_path):
        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("ENV_NAMES", "cluster-01/env-01")
        monkeypatch.setenv("CI_PROJECT_DIR", "/instance-repo")

        main()

        assert self._read_resolved_env() == {
            "ENV_NAMES": "cluster-01/env-01",
            "LOCAL_APPDEFS_PATH": "/instance-repo/environments/cluster-01/env-01/AppDefs",
            "LOCAL_REGDEFS_PATH": "/instance-repo/environments/cluster-01/env-01/RegDefs",
        }

    @pytest.mark.unit
    def test_writes_only_env_names_for_multi_env(self, monkeypatch, tmp_path):
        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("ENV_NAMES", "cluster-01/env-01,cluster-02/env-02")

        main()

        assert self._read_resolved_env() == {
            "ENV_NAMES": "cluster-01/env-01,cluster-02/env-02",
        }
