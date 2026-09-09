"""Load values files for fill (single file or directory)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from migration_cli.errors import MigrationCliError, ValidationError
from migration_cli.yaml_io import load_yaml


def _yaml_files_in_dir(directory: Path) -> list[Path]:
    if not directory.is_dir():
        raise ValidationError(f"Values directory not found: {directory}")
    paths = sorted(directory.glob("*.yml")) + sorted(directory.glob("*.yaml"))
    if not paths:
        raise ValidationError(f"No YAML files found in values directory: {directory}")
    return paths


def load_instance_values(path: Path) -> dict[str, Any]:
    try:
        doc = load_yaml(path)
    except (OSError, yaml.YAMLError) as exc:
        raise MigrationCliError(f"Failed to load values file {path}: {exc}") from exc
    if not isinstance(doc, dict):
        raise MigrationCliError(f"Values file must be a YAML mapping: {path}")
    return doc


def load_instance_values_source(*, values: Path | None, values_dir: Path | None) -> dict[str, Any]:
    if values is not None:
        return load_instance_values(values)
    assert values_dir is not None
    paths = _yaml_files_in_dir(values_dir)
    if len(paths) != 1:
        raise ValidationError(
            f"instance_scoped values-dir must contain exactly one YAML file, found {len(paths)} in {values_dir}"
        )
    return load_instance_values(paths[0])


def load_jenkins_index(*, values: Path | None, values_dir: Path | None) -> dict[str, Any]:
    paths: list[Path]
    if values is not None:
        paths = [values]
    else:
        assert values_dir is not None
        paths = _yaml_files_in_dir(values_dir)

    merged: dict[str, Any] = {}
    for path in paths:
        try:
            doc = load_yaml(path)
        except (OSError, yaml.YAMLError) as exc:
            raise MigrationCliError(f"Failed to load Jenkins export {path}: {exc}") from exc
        raw = doc.get("credentials") if isinstance(doc.get("credentials"), dict) else doc
        if not isinstance(raw, dict):
            raise MigrationCliError(f"Jenkins export must be a mapping: {path}")
        for key, payload in raw.items():
            if not isinstance(payload, dict):
                continue
            existing = merged.get(str(key))
            if existing is not None and existing != payload:
                raise MigrationCliError(
                    f"Duplicate Jenkins id {key!r} with different payload (files: {path})"
                )
            merged[str(key)] = payload
    if not merged:
        raise MigrationCliError("Jenkins export contains no credential entries")
    return merged
