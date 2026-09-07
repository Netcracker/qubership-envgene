"""JSON stdout + process exit helper."""

from __future__ import annotations

import json
import sys
from typing import Any

from extcreds_mig.constants import EXIT_OK


def emit(result: dict[str, Any], exit_code: int = EXIT_OK) -> None:
    """Print structured JSON to stdout and exit."""
    payload = json.dumps(result, indent=2, ensure_ascii=True)
    sys.stdout.buffer.write((payload + "\n").encode("utf-8"))
    sys.stdout.buffer.flush()
    sys.exit(exit_code)
