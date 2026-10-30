import logging
from pathlib import Path

import pytest
import yaml
from git import Repo

from dpg.v1.cleanup import clean_namespaces, cleanup_repository, finalize_deployment


def snapshot(directory):
    return {str(path.relative_to(directory)): path.read_bytes()
            for path in directory.rglob("*") if path.is_file()}


@pytest.fixture
def effective_set(tmp_path):
    es = tmp_path / "effective-set"
    for context in ("deployment", "runtime"):
        mapping = {}
        for namespace in ("core", "bss"):
            mapping[f"env-{namespace}"] = f"/environments/cluster/env/effective-set/{context}/{namespace}"
            app = es / context / namespace / "app"
            app.mkdir(parents=True)
            (app / "parameters.yaml").write_text("parameter: value\n")
            nested = app / "old-generation" / "values"
            nested.mkdir(parents=True)
            (nested / "credentials.yaml").write_text("credential: value\n")
        (es / context / "mapping.yaml").write_text(yaml.safe_dump(mapping))
    stale_context = es / "cleanup" / "core"
    stale_context.mkdir(parents=True)
    (stale_context / "parameters.yaml").write_text("old: context\n")
    return es


@pytest.mark.parametrize("selection, cleaned", [("env-core", {"core"}), ("", {"core", "bss"})])
def test_cleanup_preserves_mappings_and_unselected_content(effective_set, selection, cleaned):
    before = snapshot(effective_set)

    clean_namespaces(effective_set, selection)

    for context in ("deployment", "runtime"):
        assert (effective_set / context / "mapping.yaml").read_bytes() == before[f"{context}/mapping.yaml"]
        for namespace in ("core", "bss"):
            directory = effective_set / context / namespace
            if namespace in cleaned:
                assert (directory / ".cleaned").is_file()
                assert snapshot(directory / "app") == {".gitkeep": b""}
            else:
                assert not (directory / ".cleaned").exists()
                assert snapshot(directory) == {
                    path.removeprefix(f"{context}/{namespace}/"): content
                    for path, content in before.items() if path.startswith(f"{context}/{namespace}/")}
    assert not (effective_set / "cleanup").exists()


def test_repeated_cleanup_warns_and_is_idempotent(effective_set, caplog):
    clean_namespaces(effective_set, "env-core")
    before = snapshot(effective_set)

    with caplog.at_level(logging.WARNING):
        clean_namespaces(effective_set, "env-core;missing")

    assert snapshot(effective_set) == before
    assert "env-core' is already cleaned" in caplog.text
    assert "missing' is absent from the effective set" in caplog.text


def test_cleanup_rejects_mapping_pointing_outside_context(effective_set):
    mapping = effective_set / "deployment" / "mapping.yaml"
    mapping.write_text(yaml.safe_dump({"env-core": ".."}))

    with pytest.raises(ValueError, match="env-core"):
        clean_namespaces(effective_set, "env-core")


def test_cleanup_and_redeploy_update_the_remote_effective_set(effective_set, tmp_path, monkeypatch):
    import shutil

    remote = tmp_path / "remote.git"
    with Repo.init(remote, bare=True) as bare, Repo.init(tmp_path / "seed", initial_branch="main") as seed:
        remote_es = Path(seed.working_tree_dir) / "environments" / "cluster" / "env" / "effective-set"
        shutil.copytree(effective_set, remote_es)
        seed.git.add(".")
        with seed.git.custom_environment(GIT_AUTHOR_NAME="Test", GIT_AUTHOR_EMAIL="test@example.com",
                                        GIT_COMMITTER_NAME="Test", GIT_COMMITTER_EMAIL="test@example.com"):
            seed.git.commit("-m", "Seed effective set")
        seed.create_remote("origin", str(remote)).push("HEAD:refs/heads/main").raise_if_error()

        local_root = tmp_path / "workspace"
        local_es = local_root / "environments" / "cluster" / "env" / "effective-set"
        pipeline = local_es / "pipeline"
        pipeline.mkdir(parents=True)
        (local_es / "cleanup").mkdir()
        (local_es / "cleanup" / "mapping.yaml").write_text("old: mapping\n")
        (pipeline / "parameters.yaml").write_text(yaml.safe_dump({
            "DCL_GIT_URL": str(remote), "DCL_GIT_BRANCH": "main"}))
        monkeypatch.setenv("GITLAB_USER_NAME", "Test")
        monkeypatch.setenv("GITLAB_USER_EMAIL", "test@example.com")

        cleanup_repository(local_root, "cluster/env", "env-core", "Clean namespace")

        with Repo.clone_from(str(remote), tmp_path / "check", branch="main") as check:
            committed_es = Path(check.working_tree_dir) / remote_es.relative_to(seed.working_tree_dir)
            assert snapshot(committed_es) == {
                path: content for path, content in snapshot(local_es).items() if not path.startswith("pipeline/")}
            assert (committed_es / "deployment/core/app").is_dir()
            assert (committed_es / "deployment/core/.cleaned").is_file()
            assert not (committed_es / "deployment/bss/.cleaned").exists()
            assert not (committed_es / "cleanup").exists()
        assert not (local_es / "cleanup").exists()
        commit = bare.commit("refs/heads/main").hexsha

        cleanup_repository(local_root, "cluster/env", "env-core", "Clean again")

        assert bare.commit("refs/heads/main").hexsha == commit
        assert (pipeline / "parameters.yaml").is_file()

        for context in ("deployment", "runtime"):
            (local_es / context / "core" / ".cleaned").unlink()
            (local_es / context / "core" / "app" / "parameters.yaml").write_text("new: deployment\n")
        untouched = {
            f"{context}/bss/{path}": content
            for context in ("deployment", "runtime")
            for path, content in snapshot(local_es / context / "bss").items()
        }

        with pytest.raises(ValueError, match="No published application content.*env-core"):
            finalize_deployment(local_root, "cluster/env", {"env-core"})
        assert bare.commit("refs/heads/main").hexsha == commit

        with Repo.clone_from(str(remote), tmp_path / "publisher", branch="main") as publisher:
            for context in ("deployment", "runtime"):
                application = Path(publisher.working_tree_dir) / "environments/cluster/env/effective-set" / context / "core/app"
                (application / "parameters.yaml").write_text("new: deployment\n")
                (application / "publisher-output.yaml").write_text("publisher: output\n")
            publisher.git.add(".")
            with publisher.git.custom_environment(GIT_AUTHOR_NAME="Test", GIT_AUTHOR_EMAIL="test@example.com",
                                                  GIT_COMMITTER_NAME="Test", GIT_COMMITTER_EMAIL="test@example.com"):
                publisher.git.commit("-m", "Publish rebuilt namespace")
            publisher.remote().push("HEAD:refs/heads/main").raise_if_error()

        finalize_deployment(local_root, "cluster/env", {"env-core"})

        tree = bare.commit("refs/heads/main").tree / "environments/cluster/env/effective-set"
        for context in ("deployment", "runtime"):
            namespace_tree = tree / context / "core"
            assert ".cleaned" not in [entry.name for entry in namespace_tree]
            assert (namespace_tree / "app/parameters.yaml").data_stream.read() == b"new: deployment\n"
            assert (namespace_tree / "app/publisher-output.yaml").data_stream.read() == b"publisher: output\n"
        for path, content in untouched.items():
            assert (tree / path).data_stream.read() == content
