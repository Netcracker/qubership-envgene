#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request

PYPI_JSON_URL_TEMPLATE = "https://pypi.org/pypi/{package_name}/json"
TOKEN_ENV_VAR = "POETRY_PYPI_TOKEN_PYPI"
TOKEN_PREFIX = "pypi-"

EXIT_VALIDATION_ERROR = 1
EXIT_PYPI_QUERY_ERROR = 2


class PyPIQueryError(RuntimeError):
    """Raised when PyPI cannot be reached or returns an unexpected response."""


def require_non_empty(name: str, value: str | None) -> str:
    if value is None or not value.strip():
        raise ValueError(f"{name} is not set or empty.")
    return value.strip()


def validate_token_shape(token: str) -> None:
    if not token.startswith(TOKEN_PREFIX):
        raise ValueError(
            f"PyPI API token must start with '{TOKEN_PREFIX}'. "
            f"Configure repository secret PYPI_API_TOKEN with a token from pypi.org."
        )


def probe_pypi_json_api(package_name: str) -> None:
    url = PYPI_JSON_URL_TEMPLATE.format(package_name=package_name)

    print(f"Checking PyPI JSON API reachability: {url}")

    try:
        with urllib.request.urlopen(url, timeout=20) as response:
            json.load(response)
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            print(
                f"OK: PyPI JSON API is reachable (package '{package_name}' is not published yet)."
            )
            return
        raise PyPIQueryError(f"Failed to query PyPI JSON API: HTTP {exc.code}") from exc
    except urllib.error.URLError as exc:
        raise PyPIQueryError(f"Failed to query PyPI JSON API: {exc.reason}") from exc
    except json.JSONDecodeError as exc:
        raise PyPIQueryError("Failed to query PyPI JSON API: invalid JSON response") from exc

    print(f"OK: PyPI JSON API is reachable for package '{package_name}'.")


def check_pypi_credentials(package_name: str, token: str) -> None:
    validate_token_shape(token)
    probe_pypi_json_api(package_name=package_name)
    print(
        "NOTE: Upload authorization is confirmed during poetry publish. "
        "PyPI reachability and token shape checks passed."
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify PyPI reachability and Poetry publish token configuration."
    )
    parser.add_argument("--package-name", required=True)
    parser.add_argument(
        "--token",
        default=os.environ.get(TOKEN_ENV_VAR),
        help=(
            "PyPI API token (default: POETRY_PYPI_TOKEN_PYPI environment variable). "
            "Poetry reads the same variable during publish."
        ),
    )

    args = parser.parse_args()

    try:
        token = require_non_empty(TOKEN_ENV_VAR, args.token)
        check_pypi_credentials(package_name=args.package_name, token=token)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return EXIT_VALIDATION_ERROR
    except PyPIQueryError as exc:
        print(f"PYPI QUERY ERROR: {exc}", file=sys.stderr)
        return EXIT_PYPI_QUERY_ERROR

    print("OK: PyPI connectivity and token configuration verified.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
