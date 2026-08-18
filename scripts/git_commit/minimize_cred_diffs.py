import os
import tempfile
from os import getenv
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

from git import GitCommandError, Repo

from envgenehelper import decrypt_file, encrypt_file
from envgenehelper.crypt import get_crypt, is_cred_file
from envgenehelper.logger import logger


def _read_head_content(repo: Repo, rel_path: str):
    try:
        head_blob = repo.head.commit.tree[rel_path]
        return head_blob.data_stream.read()
    except KeyError:
        logger.debug(f'Skipping minimize for new cred file: {rel_path}')
        return
    except (GitCommandError, OSError) as exc:
        logger.warning(f'Cannot read credential file at HEAD, skipping minimize for {rel_path}: {exc}')
        return


def _minimize_single_cred_file(
    base_dir: Path,
    rel_path: str,
    head_content,
) -> None:
    full_path = base_dir / rel_path
    if not full_path.is_file():
        logger.debug(f'Skipping minimize for missing working-tree cred file: {rel_path}')
        return

    cred_path = Path(rel_path)
    old_tmp = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=cred_path.suffix) as old_tmp_obj:
            old_tmp_obj.write(head_content)
            old_tmp = Path(old_tmp_obj.name)

        decrypt_file(str(full_path), in_place=True)
        encrypt_file(str(full_path), in_place=True, minimize_diff=True, old_file_path=str(old_tmp))
        logger.debug(f'Minimized cred diff vs HEAD: {rel_path}')
    finally:
        if old_tmp is not None:
            old_tmp.unlink(missing_ok=True)


def minimize_cred_diffs() -> None:
    if not get_crypt():
        logger.info("'crypt' is disabled, skipping credential diff minimization")
        return

    base_dir = Path(getenv('CI_PROJECT_DIR', os.getcwd()))
    repo = Repo(base_dir)

    try:
        changed_paths = repo.git.diff('--name-only', 'HEAD').splitlines()
    except GitCommandError as exc:
        if "ambiguous argument 'HEAD'" in str(exc):
            logger.info("No HEAD exists in the repository, skipping credential diff minimization")
            return
        message = f'git diff against HEAD failed in {base_dir}: {exc}'
        logger.error(message)
        raise RuntimeError(message) from exc

    to_process = []
    for rel_path in changed_paths:
        if not is_cred_file(str(base_dir / rel_path)):
            continue
        head_content = _read_head_content(repo, rel_path)
        if head_content is None:
            continue
        to_process.append((rel_path, head_content))
        
    if not to_process:
        return

    max_workers = min(len(to_process), os.cpu_count() or 4)
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futures = {
            ex.submit(_minimize_single_cred_file, base_dir, rel_path, content): rel_path
            for rel_path, content in to_process
        }
        for f in as_completed(futures):
            f.result()
