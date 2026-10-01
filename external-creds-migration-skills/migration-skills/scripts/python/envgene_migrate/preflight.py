"""Pre-flight checks (exit 3) — shell-shared (dirty Git)."""

from __future__ import annotations

import subprocess
from pathlib import Path

from .exit_codes import EXIT_PREFLIGHT


class PreflightError(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


def check_dirty_git(repo_root: Path) -> None:
    try:
        proc = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError as exc:
        raise PreflightError("git not found on PATH") from exc
    if proc.returncode != 0:
        raise PreflightError(f"git status failed: {proc.stderr.strip()}")
    dirty = []
    for line in (proc.stdout or "").splitlines():
        if not line.strip():
            continue
        # porcelain: XY PATH — untracked "?? " ignored
        if line.startswith("??"):
            continue
        dirty.append(line.strip())
    if dirty:
        listing = "\n".join(f"  {d}" for d in dirty)
        raise PreflightError(
            "dirty Git working tree (tracked changes). "
            f"Commit or stash before apply:\n{listing}"
        )


def exit_preflight(err: PreflightError) -> int:
    print(f"[PREFLIGHT] FAILED: {err.message}", flush=True)
    return EXIT_PREFLIGHT
