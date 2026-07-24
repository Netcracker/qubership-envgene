#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.error
import urllib.request

from packaging.version import InvalidVersion, Version


STRICT_SEMVER_RE = re.compile(
    r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$"
)

EXIT_VALIDATION_ERROR = 1
EXIT_PYPI_QUERY_ERROR = 2
EXIT_PYPI_VERSION_PENDING = 3


class PyPIQueryError(RuntimeError):
    """Raised when PyPI cannot be queried due to network or API errors."""


class PyPIVersionNotFoundError(RuntimeError):
    """Raised when PyPI was queried but the expected release is not indexed yet."""


def validate_strict_semver(version: str) -> Version:
    if not STRICT_SEMVER_RE.fullmatch(version):
        raise ValueError(
            "Version must be strict semver: X.Y.Z. "
            "Examples: 0.1.0, 1.0.0, 2.3.4. "
            "Not allowed: v1.0.0, 1.0, 1.0.0-rc1, 1.0.0+build, 01.0.0"
        )

    return Version(version)


def fetch_pypi_releases(package_name: str) -> dict:
    url = f"https://pypi.org/pypi/{package_name}/json"

    print(f"Checking PyPI package: {package_name}")
    print(f"PyPI URL: {url}")

    try:
        with urllib.request.urlopen(url, timeout=20) as response:
            payload = json.load(response)
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            print(f"OK: package '{package_name}' does not exist on PyPI yet. First release is allowed.")
            return {}
        raise PyPIQueryError(f"Failed to query PyPI: HTTP {exc.code}") from exc
    except urllib.error.URLError as exc:
        raise PyPIQueryError(f"Failed to query PyPI: {exc.reason}") from exc
    except json.JSONDecodeError as exc:
        raise PyPIQueryError("Failed to query PyPI: invalid JSON response") from exc

    if not isinstance(payload, dict):
        raise PyPIQueryError("Unexpected PyPI response: JSON root must be an object.")

    releases = payload.get("releases", {})

    if not isinstance(releases, dict):
        raise PyPIQueryError("Unexpected PyPI response: 'releases' field is missing or invalid.")

    return releases


def get_latest_pypi_version(releases: dict) -> Version | None:
    parsed_versions: list[Version] = []

    for raw_version in releases.keys():
        try:
            parsed_versions.append(Version(raw_version))
        except InvalidVersion:
            print(f"WARNING: skipping invalid existing PyPI version: {raw_version}")

    if not parsed_versions:
        return None

    return max(parsed_versions)


def check_candidate_version(package_name: str, candidate_raw: str) -> None:
    candidate = validate_strict_semver(candidate_raw)

    print(f"Candidate version: {candidate}")

    releases = fetch_pypi_releases(package_name)
    latest = get_latest_pypi_version(releases)

    if latest is None:
        print(f"OK: no existing releases found for '{package_name}'. Version '{candidate}' is allowed.")
        return

    print(f"Latest PyPI version: {latest}")

    if candidate <= latest:
        raise ValueError(
            f"Candidate version '{candidate}' must be greater than latest PyPI version '{latest}'."
        )

    print(f"OK: candidate version '{candidate}' is greater than latest PyPI version '{latest}'.")


def verify_published_version(package_name: str, expected_raw: str) -> None:
    expected = validate_strict_semver(expected_raw)

    print(f"Expected published version: {expected}")

    releases = fetch_pypi_releases(package_name)
    release_files = releases.get(str(expected), [])

    if not release_files:
        raise PyPIVersionNotFoundError(
            f"Version '{expected}' was not found on PyPI for package '{package_name}'."
        )

    print(f"OK: version '{expected}' is published on PyPI ({len(release_files)} file(s)).")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate or verify PyPI release versions."
    )
    parser.add_argument("--package-name", required=True)
    parser.add_argument("--version", required=True)
    parser.add_argument(
        "--verify-published",
        action="store_true",
        help="Verify that the given version already exists on PyPI.",
    )
    parser.add_argument(
        "--semver-only",
        action="store_true",
        help="Validate semver format only, without querying PyPI.",
    )

    args = parser.parse_args()

    try:
        if args.semver_only:
            validate_strict_semver(args.version)
            print(f"OK: version '{args.version}' is valid semver.")
        elif args.verify_published:
            verify_published_version(
                package_name=args.package_name,
                expected_raw=args.version,
            )
        else:
            check_candidate_version(
                package_name=args.package_name,
                candidate_raw=args.version,
            )
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return EXIT_VALIDATION_ERROR
    except PyPIQueryError as exc:
        print(f"PYPI QUERY ERROR: {exc}", file=sys.stderr)
        return EXIT_PYPI_QUERY_ERROR
    except PyPIVersionNotFoundError as exc:
        print(f"PYPI VERSION PENDING: {exc}", file=sys.stderr)
        return EXIT_PYPI_VERSION_PENDING

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
