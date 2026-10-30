import shutil
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml
from git import Actor, Repo

from dpg.v1.cleanup import cleanup_repository
from effective_set import effective_set_entrypoint as entrypoint
from effective_set import publish_effective_set as publication
from envgenehelper.deploy_plan_adapter import DeployPlanEntity, EnvgeneDeployPlan


@pytest.fixture
def cleaned_repository(tmp_path, monkeypatch):
    environment_id = "cluster/env"
    relative_es = Path("environments") / environment_id / "effective-set"
    rootdir = tmp_path / "work"
    local_es = rootdir / relative_es
    remote_path = tmp_path / "es.git"
    actor = Actor("Test", "test@example.com")
    monkeypatch.setenv("CI_PROJECT_DIR", str(rootdir))
    monkeypatch.setenv("FULL_ENV_NAME", environment_id)
    monkeypatch.setenv("GITLAB_USER_NAME", actor.name)
    monkeypatch.setenv("GITLAB_USER_EMAIL", actor.email)
    with Repo.init(remote_path, bare=True) as remote, Repo.init(tmp_path / "seed", initial_branch="main") as seed:
        seed_es = Path(seed.working_tree_dir) / relative_es
        for context in ("deployment", "runtime"):
            mapping = {}
            for folder in ("core", "bss"):
                application = seed_es / context / folder / "app"
                application.mkdir(parents=True)
                (application / "parameters.yaml").write_text("old: value\n")
                mapping[f"env-{folder}"] = f"/environments/{environment_id}/effective-set/{context}/{folder}"
            (seed_es / context / "mapping.yaml").write_text(yaml.safe_dump(mapping))
        seed.git.add(".")
        seed.index.commit("Seed effective set", author=actor, committer=actor)
        seed.create_remote("origin", str(remote_path)).push("HEAD:refs/heads/main").raise_if_error()
        pipeline = local_es / "pipeline"
        pipeline.mkdir(parents=True)
        (pipeline / "parameters.yaml").write_text(yaml.safe_dump({
            "DCL_GIT_URL": str(remote_path), "DCL_GIT_BRANCH": "main"}))
        cleanup_repository(rootdir, environment_id, "env-core", "Clean namespace")
        for context in ("deployment", "runtime"):
            (local_es / context / "core/.cleaned").unlink()
            (local_es / context / "core/app/parameters.yaml").write_text("new: value\n")
        inventory = local_es.parent / "Inventory"
        inventory.mkdir()
        plan = EnvgeneDeployPlan(entities=[DeployPlanEntity(version="app:2.0", namespace="env-core")])
        plan.write(inventory / "delta-deploy-plan.yml")
        yield SimpleNamespace(
            rootdir=rootdir, environment_id=environment_id, relative_es=relative_es, local_es=local_es,
            remote=remote, remote_path=remote_path, actor=actor, plan=plan, tmp_path=tmp_path,
            initial_commit=remote.commit("refs/heads/main").hexsha,
        )


def assert_still_cleaned(repository):
    assert repository.remote.commit("refs/heads/main").hexsha == repository.initial_commit
    tree = repository.remote.commit("refs/heads/main").tree / repository.relative_es.as_posix()
    for context in ("deployment", "runtime"):
        assert (tree / context / "core/.cleaned").data_stream.read() == b""


@pytest.mark.parametrize("failure", [None, "calculator", "provisioning"])
def test_effective_set_generation_never_publishes(cleaned_repository, monkeypatch, failure):
    repository = cleaned_repository
    monkeypatch.setattr(entrypoint, "get_current_env_dir_from_env_vars", lambda: repository.local_es.parent)
    monkeypatch.setattr(entrypoint, "get_sd_dir", lambda: repository.rootdir)

    def calculate(*args):
        if failure == "calculator":
            raise RuntimeError("Calculator failed")

    def provision(*args):
        if failure == "provisioning":
            raise RuntimeError("External provisioning failed")

    monkeypatch.setattr(entrypoint, "_run_deploy_plan_full", calculate)
    monkeypatch.setattr(entrypoint, "_run_external_credential_provision_cli", provision)
    ctx = SimpleNamespace(deploy_plan_delta=repository.plan)
    if failure:
        with pytest.raises(RuntimeError):
            entrypoint.run_gitlab_deploy_effective_set(ctx)
    else:
        entrypoint.run_gitlab_deploy_effective_set(ctx)

    assert_still_cleaned(repository)


def test_failed_publisher_keeps_remote_cleaned_markers(cleaned_repository, monkeypatch):
    repository = cleaned_repository

    def fail(cmd, **kwargs):
        raise subprocess.CalledProcessError(1, cmd)

    monkeypatch.setattr(publication.subprocess, "run", fail)

    with pytest.raises(subprocess.CalledProcessError):
        publication.publish_effective_set(
            repository.rootdir, repository.environment_id, repository.plan.dp_path, "INFO")

    assert_still_cleaned(repository)


def test_publication_without_deployment_does_not_use_a_stale_plan(cleaned_repository, monkeypatch):
    repository = cleaned_repository
    calls = []
    monkeypatch.setattr(publication.subprocess, "run", lambda *args, **kwargs: calls.append(args))

    publication.publish_effective_set(repository.rootdir, repository.environment_id, None, "INFO")

    assert len(calls) == 1
    assert_still_cleaned(repository)


def test_successful_publisher_removes_markers_without_replacing_published_content(cleaned_repository, monkeypatch):
    repository = cleaned_repository
    calls = []

    def publish(cmd, **kwargs):
        calls.append((cmd, kwargs))
        with Repo.clone_from(str(repository.remote_path), repository.tmp_path / "publisher", branch="main") as publisher:
            effective_set = Path(publisher.working_tree_dir) / repository.relative_es
            for context in ("deployment", "runtime"):
                source = repository.local_es / context / "core/app"
                application = effective_set / context / "core/app"
                shutil.copytree(source, application, dirs_exist_ok=True)
                (application / "publisher-output.yaml").write_text("publisher: output\n")
            publisher.git.add(".")
            publisher.index.commit("Publish generated namespace", author=repository.actor, committer=repository.actor)
            publisher.remote().push("HEAD:refs/heads/main").raise_if_error()

    monkeypatch.setattr(publication.subprocess, "run", publish)
    before = repository.remote.commit("refs/heads/main").tree / repository.relative_es.as_posix()

    publication.publish_effective_set(
        repository.rootdir, repository.environment_id, repository.plan.dp_path, "INFO")

    after = repository.remote.commit("refs/heads/main").tree / repository.relative_es.as_posix()
    for context in ("deployment", "runtime"):
        namespace = after / context / "core"
        assert ".cleaned" not in [entry.name for entry in namespace]
        assert (namespace / "app/parameters.yaml").data_stream.read() == b"new: value\n"
        assert (namespace / "app/publisher-output.yaml").data_stream.read() == b"publisher: output\n"
        assert (after / context / "bss").hexsha == (before / context / "bss").hexsha
        assert (after / context / "mapping.yaml").data_stream.read() == (before / context / "mapping.yaml").data_stream.read()
    assert len(calls) == 1
    assert calls[0][1] == {"cwd": repository.rootdir, "check": True}
