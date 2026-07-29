import shlex
import sys
from pathlib import Path

from pipeline.pipeline_parameters import resolve_env_names

RESOLVED_ENV_FILE = "envgene-resolved.env"


def main() -> int:
    try:
        env_names = resolve_env_names()
    except ValueError as exc:
        print(exc, file=sys.stderr)
        return 1

    env_names_value = ",".join(env_names)
    Path(RESOLVED_ENV_FILE).write_text(
        f"ENV_NAMES={shlex.quote(env_names_value)}\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
