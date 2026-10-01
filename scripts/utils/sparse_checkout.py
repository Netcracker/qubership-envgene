from envgenehelper.git_helper import GitRepoManager
from envgenehelper.repo_paths import get_sparse_checkout_paths, REPO_ROOT_PATHS


def run_sparse_checkout(env_names: list[str]) -> None:
    repo = GitRepoManager()
    repo.configure()
    paths = get_sparse_checkout_paths(env_names[0]) if len(env_names) == 1 else list(REPO_ROOT_PATHS)
    repo.sparse_checkout(paths)
