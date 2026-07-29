import os
import shlex
from pathlib import Path

import pytest

from pipeline.resolve_env_names import RESOLVED_ENV_FILE, main


@pytest.fixture(autouse=True)
def clear_resolved_env(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("CLUSTER_NAME", raising=False)
    monkeypatch.delenv("ENVIRONMENT_NAME", raising=False)
    monkeypatch.delenv("ENV_NAMES", raising=False)
    monkeypatch.delenv("PIPELINE_TYPE", raising=False)


class TestResolveEnvNamesScript:
    @pytest.mark.unit
    def test_writes_resolved_env_file(self, monkeypatch):
        monkeypatch.setenv("ENV_NAMES", "cluster-01/env-01,cluster-02/env-02")

        assert main() == 0

        content = Path(RESOLVED_ENV_FILE).read_text(encoding="utf-8")
        assert content == "ENV_NAMES=cluster-01/env-01,cluster-02/env-02\n"

    @pytest.mark.unit
    def test_quotes_values_with_shell_metacharacters(self, monkeypatch):
        monkeypatch.setenv("ENV_NAMES", "cluster-01/env-01")

        assert main() == 0

        content = Path(RESOLVED_ENV_FILE).read_text(encoding="utf-8")
        key, value = content.strip().split("=", 1)
        assert key == "ENV_NAMES"
        assert shlex.split(value) == ["cluster-01/env-01"]

    @pytest.mark.unit
    def test_synthesises_env_names_from_legacy_vars(self, monkeypatch):
        monkeypatch.setenv("CLUSTER_NAME", "cluster-01")
        monkeypatch.setenv("ENVIRONMENT_NAME", "env-01")

        assert main() == 0

        content = Path(RESOLVED_ENV_FILE).read_text(encoding="utf-8")
        assert content == "ENV_NAMES=cluster-01/env-01\n"
        assert os.environ["ENV_NAMES"] == "cluster-01/env-01"

    @pytest.mark.unit
    def test_returns_nonzero_on_validation_error(self, monkeypatch):
        monkeypatch.setenv("ENV_NAMES", "invalid-format")

        assert main() == 1
        assert not Path(RESOLVED_ENV_FILE).exists()
