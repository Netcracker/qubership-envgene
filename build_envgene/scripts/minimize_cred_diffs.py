import os
import subprocess
import tempfile
from os import getenv, path

from envgenehelper import decrypt_file, encrypt_file
from envgenehelper.crypt import get_crypt, is_cred_file, is_encrypted
from envgenehelper.logger import logger

BASE_DIR = getenv('CI_PROJECT_DIR', os.getcwd())


def _minimize_single_cred_file(rel_path: str, repo_root: str) -> None:
    full_path = path.join(repo_root, rel_path)
    result = subprocess.run(
        ['git', 'show', f'HEAD:{rel_path}'],
        cwd=repo_root,
        capture_output=True,
    )
    if result.returncode != 0:
        logger.debug(f'Skipping minimize for new cred file: {rel_path}')
        return

    suffix = path.splitext(rel_path)[1]
    old_tmp = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as old_tmp_obj:
            old_tmp_obj.write(result.stdout)
            old_tmp = old_tmp_obj.name

        if not is_encrypted(old_tmp):
            logger.debug(f'Skipping minimize for unencrypted cred file at HEAD: {rel_path}')
            return

        decrypt_file(full_path, in_place=True)
        encrypt_file(full_path, in_place=True, minimize_diff=True, old_file_path=old_tmp)
        logger.debug(f'Minimized cred diff vs HEAD: {rel_path}')
    finally:
        if old_tmp and os.path.exists(old_tmp):
            os.remove(old_tmp)


def main(repo_root: str | None = None) -> None:
    repo_root = repo_root or BASE_DIR
    if not get_crypt():
        logger.info("'crypt' is disabled, skipping credential diff minimization")
        return

    result = subprocess.run(
        ['git', 'diff', '--name-only', 'HEAD'],
        cwd=repo_root,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"git diff against HEAD failed in {repo_root}: {result.stderr.strip() or result.stdout.strip()}"
        )
    for rel_path in result.stdout.splitlines():
        rel_path = rel_path.strip()
        if not rel_path:
            continue
        if not is_cred_file(path.join(repo_root, rel_path)):
            continue
        _minimize_single_cred_file(rel_path, repo_root)


if __name__ == '__main__':
    main()
