#!/usr/bin/env python3

from __future__ import annotations

import argparse
import pathlib
import re
import sys
import tomllib


STRICT_SEMVER_RE = re.compile(
    r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$"
)
PROJECT_SECTION_RE = re.compile(r"^\[project\]\s*(?:#.*)?$")
SECTION_HEADER_RE = re.compile(r"^\[.*\]\s*(?:#.*)?$")
VERSION_LINE_RE = re.compile(
    r'^(version\s*=\s*)(?:"[^"]*"|\'[^\']*\')(\s*(?:#.*)?)$'
)


def validate_semver(version: str) -> None:
    if not STRICT_SEMVER_RE.fullmatch(version):
        raise ValueError(
            f"Invalid version '{version}'. Expected strict semver format: X.Y.Z"
        )


def replace_project_version(
    pyproject_path: pathlib.Path,
    expected_package_name: str,
    release_version: str,
) -> None:
    if not pyproject_path.exists():
        raise FileNotFoundError(f"File not found: {pyproject_path}")

    validate_semver(release_version)

    text = pyproject_path.read_text(encoding="utf-8")
    data = tomllib.loads(text)

    project = data.get("project")
    if not isinstance(project, dict):
        raise ValueError("[project] section was not found in pyproject.toml")

    actual_package_name = project.get("name")
    current_version = project.get("version")

    if actual_package_name != expected_package_name:
        raise ValueError(
            f"Package name mismatch: expected '{expected_package_name}', "
            f"got '{actual_package_name}'"
        )

    if not current_version:
        raise ValueError("[project].version was not found in pyproject.toml")

    result_lines: list[str] = []
    in_project_section = False
    replaced = False

    for line in text.splitlines():
        if PROJECT_SECTION_RE.match(line):
            in_project_section = True
            result_lines.append(line)
            continue

        if in_project_section and SECTION_HEADER_RE.match(line):
            in_project_section = False

        version_match = VERSION_LINE_RE.match(line) if in_project_section else None
        if version_match:
            prefix, suffix = version_match.group(1), version_match.group(2)
            result_lines.append(f'{prefix}"{release_version}"{suffix}')
            replaced = True
        else:
            result_lines.append(line)

    if not replaced:
        raise ValueError("Could not replace [project].version in pyproject.toml")

    pyproject_path.write_text("\n".join(result_lines) + "\n", encoding="utf-8")

    print(f"Package: {actual_package_name}")
    print(f"Previous version: {current_version}")
    print(f"Release version: {release_version}")
    print("OK: pyproject.toml version updated.")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Set [project].version in pyproject.toml."
    )
    parser.add_argument("--pyproject", required=True)
    parser.add_argument("--package-name", required=True)
    parser.add_argument("--version", required=True)

    args = parser.parse_args()

    try:
        replace_project_version(
            pyproject_path=pathlib.Path(args.pyproject),
            expected_package_name=args.package_name,
            release_version=args.version,
        )
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())