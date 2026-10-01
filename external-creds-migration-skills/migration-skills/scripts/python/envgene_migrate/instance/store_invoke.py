"""Invoke product `external-cred-provision` on a context YAML file."""

from __future__ import annotations

import re
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from .reports import progress
from .yaml_io import write_yaml

OUTCOME_RE = re.compile(
    r"\[(?P<cid>[^\]]+)\]\s+(?P<status>created|overwritten|skipped|verified|"
    r"FAILED|dry_run_ok|dry_run_fail)(?P<rest>:.*)?"
)


def parse_provision_output(text: str) -> dict[str, str]:
    """cred_id → status (created|overwritten|skipped|verified|FAILED|dry_run_*)."""
    out: dict[str, str] = {}
    for line in text.splitlines():
        m = OUTCOME_RE.search(line.strip())
        if not m:
            continue
        status = m.group("status")
        if status == "dry_run_fail":
            status = "FAILED"
        out[m.group("cid")] = status
    return out


def success_status(status: str) -> bool:
    return status in {
        "created",
        "overwritten",
        "skipped",
        "verified",
        "dry_run_ok",
    }


def run_provision(
    *,
    context: dict[str, Any],
    dry_run: bool = False,
) -> dict[str, str]:
    """Write temp context YAML and invoke product CLI.

    Expected context shape (product)::

        credentials:
          <cred-id>:
            vals: "ref+vault://..."
            strategy: overwrite | create_if_absent | fail_if_absent
            data: {...}

    Invokes: ``external-cred-provision [--dry-run] <context-path>``
    """
    creds = context.get("credentials") or {}
    if not creds:
        return {}

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".yml", delete=False, encoding="utf-8"
    ) as fh:
        tmp = Path(fh.name)
    try:
        write_yaml(tmp, context)
        cmd = ["external-cred-provision"]
        if dry_run:
            cmd.append("--dry-run")
        cmd.append(str(tmp))
        progress(
            f"store: writing {len(creds)} creds via external-cred-provision",
            force=True,
        )
        progress(f"store: {' '.join(cmd)}")
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
        )
        combined = (proc.stderr or "") + "\n" + (proc.stdout or "")
        for line in combined.splitlines():
            if not line.strip():
                continue
            progress(line, force="FAILED" in line)
        statuses = parse_provision_output(combined)
        if proc.returncode not in (0, 1) and not statuses:
            raise RuntimeError(
                f"external-cred-provision exited {proc.returncode}: "
                f"{(proc.stderr or proc.stdout or '')[:500]}"
            )
        return statuses
    finally:
        tmp.unlink(missing_ok=True)
