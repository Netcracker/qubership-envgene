import hashlib
import os
import shutil
import tempfile
from os import getenv
from pathlib import Path
from typing import Optional

from git import GitCommandError, Repo

from envgenehelper import decrypt_file, encrypt_file
from envgenehelper.crypt import get_crypt, is_cred_file
from envgenehelper.logger import logger

DEFAULT_CACHE_DIR_PREFIX = '/tmp/minimize_cred_diff_cache'


def _default_cache_dir() -> Path:
    ci_job_id = getenv('CI_JOB_ID')
    if ci_job_id:
        return Path(f'{DEFAULT_CACHE_DIR_PREFIX}_{ci_job_id}')
    github_run_id = getenv('GITHUB_RUN_ID')
    if github_run_id:
        attempt = getenv('GITHUB_RUN_ATTEMPT', '1')
        return Path(f'{DEFAULT_CACHE_DIR_PREFIX}_{github_run_id}_{attempt}')
    return Path(f'{DEFAULT_CACHE_DIR_PREFIX}_{os.getpid()}')


def _cache_dir() -> Optional[Path]:
    raw = getenv('MINIMIZE_CRED_DIFF_CACHE_DIR')
    if raw is None or raw == '':
        return _default_cache_dir()
    if raw.lower() in {'0', 'false', 'no', 'off'}:
        return None
    return Path(raw)


def _cache_key(rel_path: str, head_blob_sha: str, source_sha: str) -> str:
    return hashlib.sha256(f'{rel_path}\0{head_blob_sha}\0{source_sha}'.encode()).hexdigest()


def _cache_path(cache_dir: Path, cache_key: str) -> Path:
    return cache_dir / f'{cache_key}.enc'


def _minimize_single_cred_file(
    repo: Repo,
    base_dir: Path,
    rel_path: str,
    cache_dir: Optional[Path],
) -> None:
    full_path = base_dir / rel_path
    try:
        head_blob = repo.head.commit.tree[rel_path]
        head_blob_sha = head_blob.hexsha
        head_content = head_blob.data_stream.read()
    except KeyError:
        logger.debug(f'Skipping minimize for new cred file: {rel_path}')
        return
    except (GitCommandError, OSError) as exc:
        logger.warning(f'Cannot read credential file at HEAD, skipping minimize for {rel_path}: {exc}')
        return

    source_sha = hashlib.sha256(full_path.read_bytes()).hexdigest()
    if cache_dir is not None:
        cached_path = _cache_path(cache_dir, _cache_key(rel_path, head_blob_sha, source_sha))
        if cached_path.is_file():
            shutil.copy2(cached_path, full_path)
            logger.debug(f'Restored minimized cred from cache: {rel_path}')
            return

    old_tmp = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(rel_path).suffix) as old_tmp_obj:
            old_tmp_obj.write(head_content)
            old_tmp = Path(old_tmp_obj.name)

        decrypt_file(str(full_path), in_place=True)
        encrypt_file(str(full_path), in_place=True, minimize_diff=True, old_file_path=str(old_tmp))
        logger.debug(f'Minimized cred diff vs HEAD: {rel_path}')

        if cache_dir is not None:
            cached_path = _cache_path(cache_dir, _cache_key(rel_path, head_blob_sha, source_sha))
            shutil.copy2(full_path, cached_path)
    finally:
        if old_tmp is not None:
            old_tmp.unlink(missing_ok=True)


def main() -> None:
    if not get_crypt():
        logger.info("'crypt' is disabled, skipping credential diff minimization")
        return

    base_dir = Path(getenv('CI_PROJECT_DIR', os.getcwd()))
    repo = Repo(base_dir)
    cache_dir = _cache_dir()
    if cache_dir is not None:
        cache_dir.mkdir(parents=True, exist_ok=True)

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
        _minimize_single_cred_file(repo, base_dir, rel_path, cache_dir)


if __name__ == '__main__':
    main()
