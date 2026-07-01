#!/usr/bin/env python3
import os
import sys
from pathlib import Path

from envgenehelper import openYaml, get_cred_config
from envgenehelper.system_creds_helper import resolve_integration_param

PARAM_ENV_FALLBACKS = {
    "self_token": ["GITHUB_TOKEN", "GITLAB_TOKEN"],
    "docker_registry_auth": ["GCP_SA_KEY"],
}


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: resolve_integration_token.py <param_name>", file=sys.stderr)
        return 1

    param_name = sys.argv[1]
    base_dir = Path(os.environ.get("CI_PROJECT_DIR", "."))
    integration_path = base_dir / "configuration" / "integration.yml"
    integration_config = openYaml(integration_path) if integration_path.exists() else {}
    cred_config = get_cred_config()
    value = resolve_integration_param(
        integration_config,
        param_name,
        PARAM_ENV_FALLBACKS.get(param_name, []),
        cred_config,
        base_dir,
    )
    if value:
        print(value, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
