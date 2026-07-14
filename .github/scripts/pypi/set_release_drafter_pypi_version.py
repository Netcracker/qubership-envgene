#!/usr/bin/env python3

from __future__ import annotations

import argparse
import pathlib
import re
import sys


STRICT_SEMVER_RE = re.compile(
    r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$"
)


def validate_semver(version: str) -> None:
    if not STRICT_SEMVER_RE.fullmatch(version):
        raise ValueError(
            f"Invalid version '{version}'. Expected strict semver format: X.Y.Z"
        )


def replace_pypi_release_url(
    config_path: pathlib.Path,
    package_name: str,
    release_version: str,
) -> None:
    if not config_path.exists():
        raise FileNotFoundError(f"File not found: {config_path}")

    validate_semver(release_version)

    text = config_path.read_text(encoding="utf-8")
    link_pattern = re.compile(
        rf"\*\*\[{re.escape(package_name)}:"
        r"[0-9]+\.[0-9]+\.[0-9]+"
        rf"\]\(https://pypi\.org/project/{re.escape(package_name)}/"
        r"[0-9]+\.[0-9]+\.[0-9]+"
        r"/\)\*\*"
    )

    new_text, replacements = link_pattern.subn(
        rf"**[{package_name}:{release_version}]"
        rf"(https://pypi.org/project/{package_name}/{release_version}/)**",
        text,
        count=1,
    )

    if replacements != 1:
        raise ValueError(
            f"Could not update PyPI package link for '{package_name}' in {config_path}. "
            f"Expected exactly one `**[{package_name}:X.Y.Z](https://pypi.org/project/{package_name}/X.Y.Z/)**` entry."
        )

    config_path.write_text(new_text, encoding="utf-8")

    print(f"Config: {config_path}")
    print(f"Package: {package_name}")
    print(f"Release version: {release_version}")
    print("OK: release drafter PyPI package link updated.")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Update the PyPI package version link in release-drafter-config.yml."
    )
    parser.add_argument("--config", required=True)
    parser.add_argument("--package-name", required=True)
    parser.add_argument("--version", required=True)

    args = parser.parse_args()

    try:
        replace_pypi_release_url(
            config_path=pathlib.Path(args.config),
            package_name=args.package_name,
            release_version=args.version,
        )
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
