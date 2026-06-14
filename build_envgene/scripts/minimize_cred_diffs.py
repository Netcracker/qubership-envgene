import os
import tempfile
from os import getenv
from pathlib import Path

from git import GitCommandError, Repo

from envgenehelper import decrypt_file, encrypt_file
from envgenehelper.crypt import get_crypt, is_cred_file
from envgenehelper.logger import logger


def _minimize_single_cred_file(repo: Repo, base_dir: Path, rel_path: str) -> None:
    full_path = base_dir / rel_path
    try:
        head_content = repo.head.commit.tree[rel_path].data_stream.read()
    except KeyError:
        logger.debug(f'Skipping minimize for new cred file: {rel_path}')
        return
    except (GitCommandError, OSError) as exc:
        logger.warning(f'Cannot read credential file at HEAD, skipping minimize for {rel_path}: {exc}')
        return

    old_tmp = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(rel_path).suffix) as old_tmp_obj:
            old_tmp_obj.write(head_content)
            old_tmp = Path(old_tmp_obj.name)

        decrypt_file(str(full_path), in_place=True)
        encrypt_file(str(full_path), in_place=True, minimize_diff=True, old_file_path=str(old_tmp))
        logger.debug(f'Minimized cred diff vs HEAD: {rel_path}')
    finally:
        if old_tmp is not None:
            old_tmp.unlink(missing_ok=True)


def main() -> None:
    if not get_crypt():
        logger.info("'crypt' is disabled, skipping credential diff minimization")
        return

    base_dir = Path(getenv('CI_PROJECT_DIR', os.getcwd()))
    repo = Repo(base_dir)

    try:
        changed_paths = repo.git.diff('--name-only', 'HEAD').splitlines()
    except GitCommandError as exc:
        message = f'git diff against HEAD failed in {base_dir}: {exc}'
        logger.error(message)
        raise RuntimeError(message) from exc

    for rel_path in changed_paths:
        rel_path = rel_path.strip()
        if not rel_path:
            continue
        if not is_cred_file(str(base_dir / rel_path)):
            continue
        _minimize_single_cred_file(repo, base_dir, rel_path)


if __name__ == '__main__':
    main()
