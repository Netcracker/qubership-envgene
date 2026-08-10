import hashlib
import os
import shutil
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
        return head_blob.hexsha, head_blob.data_stream.read()
    except KeyError:
        logger.debug(f'Skipping minimize for new cred file: {rel_path}')
        return None
    except (GitCommandError, OSError) as exc:
        logger.warning(f'Cannot read credential file at HEAD, skipping minimize for {rel_path}: {exc}')
        return None


def _minimize_single_cred_file(
    base_dir: Path,
    rel_path: str,
    cache_dir: Path,
    head_blob_sha,
    head_content,
) -> None:
    full_path = base_dir / rel_path
    if not full_path.is_file():
        logger.debug(f'Skipping minimize for missing working-tree cred file: {rel_path}')
        return

    source_sha = hashlib.sha256(full_path.read_bytes()).hexdigest()
    cred_path = Path(rel_path)
    cached_path = cache_dir / cred_path.parent / f'{cred_path.name}.{head_blob_sha}.{source_sha}'
    if cached_path.is_file():
        shutil.copy2(cached_path, full_path)
        logger.debug(f'Restored minimized cred from cache: {rel_path}')
        return

    old_tmp = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=cred_path.suffix) as old_tmp_obj:
            old_tmp_obj.write(head_content)
            old_tmp = Path(old_tmp_obj.name)

        decrypt_file(str(full_path), in_place=True)
        encrypt_file(str(full_path), in_place=True, minimize_diff=True, old_file_path=str(old_tmp))
        logger.debug(f'Minimized cred diff vs HEAD: {rel_path}')

        cached_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(full_path, cached_path)
    finally:
        if old_tmp is not None:
            old_tmp.unlink(missing_ok=True)


def minimize_cred_diffs() -> None:
    if not get_crypt():
        logger.info("'crypt' is disabled, skipping credential diff minimization")
        return

    base_dir = Path(getenv('CI_PROJECT_DIR', os.getcwd()))
    repo = Repo(base_dir)

    cache_dir = Path(
        getenv('MINIMIZE_CRED_DIFF_CACHE_DIR') or base_dir / 'tmp' / 'minimize_cred_diff_cache'
    )
    cache_dir.mkdir(parents=True, exist_ok=True)

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
        result = _read_head_content(repo, rel_path)
        if result is None:
            continue
        head_blob_sha, head_content = result
        to_process.append((rel_path, head_blob_sha, head_content))
        
    if not to_process:
        return

    max_workers = min(len(to_process), os.cpu_count() or 4)
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futures = {
            ex.submit(_minimize_single_cred_file, base_dir, rel_path, cache_dir, sha, content): rel_path
            for rel_path, sha, content in to_process
        }
        for f in as_completed(futures):
            f.result()
