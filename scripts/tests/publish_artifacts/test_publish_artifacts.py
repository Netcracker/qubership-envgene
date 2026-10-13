from types import SimpleNamespace

from publish_artifacts.publish_artifacts import copy_env_artifact, finalize_artifacts


def _ctx(work_dir):
    return SimpleNamespace(work_dir=work_dir, cluster_name="c1", env_name="env1")


def _write(path, content=b"x"):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)


class TestStageEnvArtifact:
    def test_strategy_never_stages_nothing(self, tmp_path, monkeypatch):
        work_dir = tmp_path / "work"
        _write(work_dir / "environments" / "env1" / "env_definition.yml")
        monkeypatch.setenv("SAVE_ARTIFACTS_STRATEGY", "NEVER")
        monkeypatch.setenv("ARTIFACTS_OUTPUT_DIR", str(tmp_path / "artifacts"))

        copy_env_artifact(_ctx(work_dir))

        assert not (tmp_path / "artifacts" / "c1" / "env1").exists()

    def test_always_copies_scope_into_shared_root(self, tmp_path, monkeypatch):
        work_dir = tmp_path / "work"
        _write(work_dir / "environments" / "env1" / "env_definition.yml", b"x" * 2048)
        monkeypatch.setenv("SAVE_ARTIFACTS_STRATEGY", "ALWAYS")
        monkeypatch.setenv("ARTIFACTS_OUTPUT_DIR", str(tmp_path / "artifacts"))

        copy_env_artifact(_ctx(work_dir))

        published = tmp_path / "artifacts" / "c1" / "env1" / "environments" / "env1" / "env_definition.yml"
        assert published.exists()


class TestFinalizeArtifacts:
    def test_strategy_never_writes_marker_only(self, tmp_path, monkeypatch):
        output_root = tmp_path / "artifacts"
        monkeypatch.setenv("SAVE_ARTIFACTS_STRATEGY", "NEVER")

        finalize_artifacts(output_root, limit_mb=300)

        assert (output_root / "NOT-PUBLISHED.txt").exists()

    def test_under_limit_keeps_everything(self, tmp_path, monkeypatch):
        monkeypatch.setenv("SAVE_ARTIFACTS_STRATEGY", "ALWAYS")
        output_root = tmp_path / "artifacts"
        _write(output_root / "c1" / "env1" / "environments" / "env_definition.yml", b"x" * 100)
        _write(output_root / "logs" / "c1_env1.log", b"x" * 100)

        finalize_artifacts(output_root, limit_mb=300)

        assert (output_root / "c1" / "env1" / "environments" / "env_definition.yml").exists()
        assert (output_root / "logs" / "c1_env1.log").exists()
        assert not (output_root / "NOT-PUBLISHED.txt").exists()

    def test_over_limit_drops_scope_but_keeps_logs(self, tmp_path, monkeypatch):
        monkeypatch.setenv("SAVE_ARTIFACTS_STRATEGY", "ALWAYS")
        output_root = tmp_path / "artifacts"
        mb = 1024 * 1024
        _write(output_root / "c1" / "env1" / "environments" / "env_definition.yml", b"x" * (2 * mb))
        _write(output_root / "c2" / "env2" / "environments" / "env_definition.yml", b"x" * (2 * mb))
        _write(output_root / "logs" / "c1_env1.log", b"x" * 100)

        finalize_artifacts(output_root, limit_mb=1)

        assert not (output_root / "c1").exists()
        assert not (output_root / "c2").exists()
        assert (output_root / "logs" / "c1_env1.log").exists()
        assert (output_root / "NOT-PUBLISHED.txt").exists()

    def test_missing_output_root_still_creates_it(self, tmp_path, monkeypatch):
        monkeypatch.setenv("SAVE_ARTIFACTS_STRATEGY", "ALWAYS")
        output_root = tmp_path / "does-not-exist"

        finalize_artifacts(output_root, limit_mb=300)

        assert output_root.exists()
