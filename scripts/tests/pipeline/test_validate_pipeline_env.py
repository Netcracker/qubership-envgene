import os

import pytest

from pipeline.multi_env_runner import resolve_env_selection


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    monkeypatch.delenv("ENV_NAMES", raising=False)
    monkeypatch.delenv("CLUSTER_NAME", raising=False)
    monkeypatch.delenv("ENVIRONMENT_NAME", raising=False)
    monkeypatch.delenv("FULL_ENV_NAME", raising=False)


class TestResolveEnvSelection:
    @pytest.mark.unit
    def test_fails_when_no_env_selection(self):
        with pytest.raises(ValueError, match="Set ENV_NAMES or both CLUSTER_NAME and ENVIRONMENT_NAME"):
            resolve_env_selection()

    @pytest.mark.unit
    def test_fails_when_env_names_combined_with_cluster_name(self, monkeypatch):
        monkeypatch.setenv("ENV_NAMES", "cluster-01/env-01")
        monkeypatch.setenv("CLUSTER_NAME", "cluster-01")

        with pytest.raises(ValueError, match="Set ENV_NAMES only, or both CLUSTER_NAME and ENVIRONMENT_NAME, but not both at the same time"):
            resolve_env_selection()

    @pytest.mark.unit
    def test_fails_when_env_names_combined_with_environment_name(self, monkeypatch):
        monkeypatch.setenv("ENV_NAMES", "cluster-01/env-01")
        monkeypatch.setenv("ENVIRONMENT_NAME", "env-01")

        with pytest.raises(ValueError, match="Set ENV_NAMES only, or both CLUSTER_NAME and ENVIRONMENT_NAME, but not both at the same time"):
            resolve_env_selection()

    @pytest.mark.unit
    def test_fails_when_env_names_combined_with_both_per_env_vars(self, monkeypatch):
        monkeypatch.setenv("ENV_NAMES", "cluster-01/env-01")
        monkeypatch.setenv("CLUSTER_NAME", "cluster-01")
        monkeypatch.setenv("ENVIRONMENT_NAME", "env-01")

        with pytest.raises(ValueError, match="Set ENV_NAMES only, or both CLUSTER_NAME and ENVIRONMENT_NAME, but not both at the same time"):
            resolve_env_selection()

    @pytest.mark.unit
    def test_passes_with_env_names_only(self, monkeypatch):
        monkeypatch.setenv("ENV_NAMES", "cluster-01/env-01")

        result = resolve_env_selection()

        assert result == ["cluster-01/env-01"]
        assert os.environ["ENV_NAMES"] == "cluster-01/env-01"

    @pytest.mark.unit
    def test_fails_when_env_names_has_invalid_format(self, monkeypatch):
        monkeypatch.setenv("ENV_NAMES", "cluster-01-env-01")

        with pytest.raises(ValueError, match="Invalid environment name"):
            resolve_env_selection()

    @pytest.mark.unit
    def test_synthesises_env_names_from_cluster_and_environment_name(self, monkeypatch):
        monkeypatch.setenv("CLUSTER_NAME", "cluster-01")
        monkeypatch.setenv("ENVIRONMENT_NAME", "env-01")

        result = resolve_env_selection()

        assert result == ["cluster-01/env-01"]
        assert os.environ["ENV_NAMES"] == "cluster-01/env-01"

    @pytest.mark.unit
    def test_fails_when_only_cluster_name_provided(self, monkeypatch):
        monkeypatch.setenv("CLUSTER_NAME", "cluster-01")

        with pytest.raises(ValueError, match="Set ENV_NAMES or both CLUSTER_NAME and ENVIRONMENT_NAME"):
            resolve_env_selection()
