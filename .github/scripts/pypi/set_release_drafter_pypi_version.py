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
    pattern = re.compile(
        rf"(https://pypi\.org/project/{re.escape(package_name)}/)"
        r"[0-9]+\.[0-9]+\.[0-9]+"
        r"(/)"
    )

    new_text, replacements = pattern.subn(
        rf"\g<1>{release_version}\2",
        text,
        count=1,
    )

    if replacements != 1:
        raise ValueError(
            f"Could not update PyPI release URL for '{package_name}' in {config_path}. "
            "Expected exactly one matching link."
        )

    config_path.write_text(new_text, encoding="utf-8")

    print(f"Config: {config_path}")
    print(f"Package: {package_name}")
    print(f"Release version: {release_version}")
    print("OK: release drafter PyPI link updated.")


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
