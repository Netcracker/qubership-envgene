"""Parse `external-cred-provision` log output into per-cred outcomes.

Format contract (from provisioner.py in `python/external-cred-provision/`):
- `[<cred-id>] created`      - success (secret was absent, now created)
- `[<cred-id>] overwritten`  - success (secret existed, migration overwrote it)
- `[<cred-id>] skipped`      - success (create_if_absent hit and secret already present)
- `[<cred-id>] verified`     - success (fail_if_absent hit and secret present)
- `[<cred-id>] FAILED: <exc-class>: <reason>`  - failure
- `[<cred-id>] dry_run_ok`   - success in dry-run mode
- `[<cred-id>] dry_run_fail: <exc-class>: <reason>`  - failure in dry-run mode
"""

import re
from dataclasses import dataclass


_MARKER_RE = re.compile(
    r"""
    ^\s*\[(?P<cred_id>[^\]]+)\]\s+
    (?P<marker>created|overwritten|skipped|verified|FAILED|dry_run_ok|dry_run_fail)
    (?:\s*:\s*(?P<detail>.+))?
    \s*$
    """,
    re.VERBOSE,
)

_SUCCESS_MARKERS = {"created", "overwritten", "skipped", "verified", "dry_run_ok"}


@dataclass(frozen=True)
class CredOutcome:
    success: bool
    marker: str
    detail: str | None


def parse_cli_log(log_text):
    """Parse a multi-line log and return {cred_id: CredOutcome}.

    If the same cred-id appears multiple times, the last occurrence wins (matches CLI
    behaviour where later markers override earlier ones during a single run).
    """
    outcomes = {}
    for line in log_text.splitlines():
        m = _MARKER_RE.match(line)
        if not m:
            continue
        cred_id = m.group("cred_id")
        marker = m.group("marker")
        detail = m.group("detail")
        if marker in _SUCCESS_MARKERS:
            outcomes[cred_id] = CredOutcome(success=True, marker=marker, detail=detail)
        else:
            normalized = "failed" if marker == "FAILED" else marker
            outcomes[cred_id] = CredOutcome(success=False, marker=normalized, detail=detail)
    return outcomes
