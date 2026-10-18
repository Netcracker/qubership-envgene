"""YAML and JSON loading with key positions. No EnvGene types."""

from __future__ import annotations

import json
import re
from bisect import bisect_right
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ruamel.yaml import YAML
from ruamel.yaml.error import YAMLError

_JSON_TOKEN = re.compile(r'"(?:[^"\\]|\\.)*"|[{}\[\],:]|[^\s{}\[\],:]+', re.DOTALL)


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
    positions: dict[tuple, tuple[int, int]] | None = None

    def position(self, key_path: tuple) -> tuple[int, int]:
        if self.positions is not None:
            for length in range(len(key_path), -1, -1):
                if key_path[:length] in self.positions:
                    return self.positions[key_path[:length]]
            return 1, 1
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


@dataclass
class _JsonNode:
    position: tuple[int, int]
    children: dict[str | int, _JsonNode] = field(default_factory=dict)


@dataclass
class _JsonFrame:
    node: _JsonNode
    array: bool
    key: tuple[str, tuple[int, int]] | None = None


def _json_positions(text: str) -> dict[tuple, tuple[int, int]]:
    """Locate already validated JSON without YAML's string or newline normalization."""
    newlines = [-1, *(match.start() for match in re.finditer('\n', text))]
    frames: list[_JsonFrame] = []
    root = None
    for match in _JSON_TOKEN.finditer(text):
        token = match.group()
        if token in (',', ':'):
            continue
        if token in ('}', ']'):
            frames.pop()
            continue
        line = bisect_right(newlines, match.start())
        position = (line, match.start() - newlines[line - 1])
        if frames and not frames[-1].array and frames[-1].key is None:
            frames[-1].key = (json.loads(token), position)
            continue
        node = _JsonNode(position)
        if not frames:
            root = node
        else:
            frame = frames[-1]
            if frame.array:
                key = len(frame.node.children)
            else:
                key, node.position = frame.key
                frame.key = None
            # Replacing the whole node discards locations under an earlier duplicate key.
            frame.node.children[key] = node
        if token in ('{', '['):
            frames.append(_JsonFrame(node, token == '['))
    positions = {}
    pending = [((), root)] if root is not None else []
    while pending:
        prefix, node = pending.pop()
        positions[prefix] = node.position
        pending.extend(((*prefix, key), value) for key, value in node.children.items())
    return positions


def load(path: Path) -> LoadedYaml:
    try:
        text = path.read_text(encoding="utf-8")
        if path.suffix == '.json':
            return LoadedYaml(path, json.loads(text), _json_positions(text))
        doc = _processor().load(text)
    except (OSError, UnicodeDecodeError, YAMLError, json.JSONDecodeError) as exc:
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
