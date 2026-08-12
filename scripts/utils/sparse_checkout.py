import os

from envgene_shared.utils.collections_utils import split_multi_value_param
from envgenehelper.git_helper import GitRepoManager
from envgenehelper.repo_paths import get_sparse_checkout_paths


def main() -> None:
    env_names = split_multi_value_param(os.environ["ENV_NAMES"])
    repo = GitRepoManager()
    repo.configure()
    paths = get_sparse_checkout_paths(env_names[0]) if len(env_names) == 1 else []
    repo.sparse_checkout(paths)


if __name__ == "__main__":
    main()
