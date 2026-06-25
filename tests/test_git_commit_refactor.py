import importlib.util
from pathlib import Path

REPO_ROOT = Path("github_workflows/instance-repo-pipeline/extend_logic/scripts")
GIT_COMMIT_PY = REPO_ROOT / "git_commit.py"
PIPELINE_HELPER = Path("build_pipegene/scripts/pipeline_helper.py")


def load_module_from_path(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_git_commit_refactor_calls_git_manager_and_minimize(monkeypatch):
    """
    Проверяет, что git_commit.git_commit():
      - вызывает функцию минимизации diff'ов,
      - использует GitRepoManager и вызывает configure(), stage_changes(),
        create_detached_commit() и sync_and_push(sha).
    Все внешние операции замоканы.
    """
    git_commit_mod = load_module_from_path(GIT_COMMIT_PY, "gc_mod")

    calls = {"minimized": False, "configure_called": False, "staged": False, "created": None, "pushed": None}

    def fake_minimize():
        calls["minimized"] = True

    class FakeGitRepoManager:
        def __init__(self, *a, **kw):
            pass

        def configure(self):
            calls["configure_called"] = True

        def stage_changes(self):
            calls["staged"] = True
            return True  # симулируем, что есть изменения

        def create_detached_commit(self, message):
            calls["created"] = message
            return "deadbeefsha"

        def sync_and_push(self, sha):
            calls["pushed"] = sha

    monkeypatch.setattr(git_commit_mod, "minimize_cred_diffs", fake_minimize)
    monkeypatch.setattr(git_commit_mod, "GitRepoManager", FakeGitRepoManager)

    git_commit_mod.git_commit()

    assert calls["minimized"], "minimize_cred_diffs не был вызван"
    assert calls["configure_called"], "GitRepoManager.configure не был вызван"
    assert calls["staged"], "stage_changes() не был вызван/вернул False"
    assert calls["created"] is not None, "create_detached_commit не был вызван"
    assert calls["pushed"] == "deadbeefsha", "sync_and_push не был вызван с SHA"


def test_set_sparse_checkout_prepend_script():
    """
    Проверяет, что JobExtended.set_sparse_checkout добавляет в начало job.script вызов
    sparse-checkout (новый python-скрипт или, как запас, old .sh).
    """
    ph = load_module_from_path(PIPELINE_HELPER, "ph_mod")

    # создаём минимальный JobExtended (используем конструктор напрямую)
    job = ph.JobExtended(
        name="t",
        stage="s",
        image=None,
        script=["echo hello"],
        variables=None,
        timeout="10m",
    )

    job.set_sparse_checkout(["environments/cluster/env"])
    rendered = job.render()
    scripts = rendered.get("script", []) if isinstance(rendered, dict) else []

    assert any("sparse_checkout.py" in s or "sparse_checkout.sh" in s for s in scripts), (
        "Не найден prepend-скрипт sparse checkout в списке script"
    )
