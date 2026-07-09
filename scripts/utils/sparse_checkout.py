import argparse

from envgenehelper.git_helper import GitRepoManager

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--sparse-paths",
        nargs="+",
        required=True,
        help="Paths to include in sparse checkout",
    )

    args = parser.parse_args()

    repo = GitRepoManager()
    repo.configure()
    repo.sparse_checkout(args.sparse_paths)
