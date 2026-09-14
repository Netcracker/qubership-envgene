"""YAML loading with key positions. No EnvGene types."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ruamel.yaml import YAML
from ruamel.yaml.error import YAMLError


class YamlReadError(Exception):
    def __init__(self, path: Path, cause: str) -> None:
        super().__init__(f"{path}: {cause}")
        self.path = path
        self.cause = cause


def _processor() -> YAML:
    yaml = YAML()
    yaml.preserve_quotes = True
    return yaml


@dataclass
class LoadedYaml:
    path: Path
    doc: Any

    def position(self, key_path: tuple) -> tuple[int, int]:
        return _position(self.doc, key_path)


def _position(node: Any, key_path: tuple) -> tuple[int, int]:
    line, col = 1, 1
    current = node
    for step in key_path:
        lc = getattr(current, "lc", None)
        if lc is None:
            break
        try:
            pos = lc.item(step) if isinstance(step, int) else lc.key(step)
        except (KeyError, IndexError, TypeError, AttributeError):
            break
        if not pos:
            break
        line, col = pos[0] + 1, pos[1] + 1
        try:
            current = current[step]
        except (KeyError, IndexError, TypeError):
            break
    return line, col


def load(path: Path) -> LoadedYaml:
    try:
        doc = _processor().load(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, YAMLError) as exc:
        raise YamlReadError(path, str(exc)) from exc
    return LoadedYaml(path=path, doc=doc)


def plain(value: Any) -> Any:
    if isinstance(value, dict):
        return {plain(k): plain(v) for k, v in value.items()}
    if isinstance(value, list):
        return [plain(item) for item in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return value


def leaves(value: Any, prefix: tuple = ()) -> list[tuple[tuple, Any]]:
    value = plain(value)
    if isinstance(value, dict):
        out: list[tuple[tuple, Any]] = []
        for key, child in value.items():
            out.extend(leaves(child, (*prefix, key)))
        return out
    return [(prefix, value)] if prefix else []


def dotted(path: tuple) -> str:
    return ".".join(str(part) for part in path)
