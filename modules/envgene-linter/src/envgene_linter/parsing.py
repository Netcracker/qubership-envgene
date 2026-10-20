"""Safe failures at third-party parser boundaries, without source excerpts."""

from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

from jinja2 import Environment, TemplateSyntaxError, nodes
from ruamel.yaml import YAML
from ruamel.yaml.error import YAMLError
from ruamel.yaml.nodes import MappingNode, SequenceNode

MAX_CONTAINER_DEPTH = 256


class ParseFailure(Exception):
    def __init__(self, reason: str, line: int = 1, column: int = 1) -> None:
        super().__init__(reason)
        self.reason = reason
        self.line = max(1, line)
        self.column = max(1, column)


def _yaml_failure(exc: YAMLError) -> ParseFailure:
    mark = getattr(exc, 'problem_mark', None) or getattr(exc, 'context_mark', None)
    return ParseFailure('cannot parse YAML source', mark.line + 1 if mark else 1,
                        mark.column + 1 if mark else 1)


def _validate_containers(value: Any) -> None:
    """Compute graph height iteratively; shared aliases are valid, cycles are not."""
    active: set[int] = set()
    heights: dict[int, int] = {}
    pending = [(value, False)]
    while pending:
        node, exiting = pending.pop()
        if isinstance(node, MappingNode):
            children = [child for pair in node.value for child in pair]
        elif isinstance(node, SequenceNode):
            children = node.value
        elif isinstance(node, Mapping):
            children = [child for pair in node.items() for child in pair]
        elif isinstance(node, (list, tuple, set)):
            children = list(node)
        else:
            continue
        identity = id(node)
        if exiting:
            height = 1 + max((heights.get(id(child), 0) for child in children), default=0)
            if height > MAX_CONTAINER_DEPTH:
                raise ParseFailure('source exceeds the supported container depth')
            heights[identity] = height
            active.remove(identity)
        elif identity in active:
            raise ParseFailure('cyclic source containers cannot be analyzed safely')
        elif identity not in heights:
            active.add(identity)
            pending.append((node, True))
            pending.extend((child, False) for child in children)


def parse_yaml(text: str) -> Any:
    # Round-trip construction can replace a recursive mapping alias with None.
    # Validate the composed graph before that information is lost.
    compose_yaml(text)
    processor = YAML()
    processor.preserve_quotes = True
    try:
        value = processor.load(text)
    except YAMLError as exc:
        raise _yaml_failure(exc) from exc
    except (ValueError, RecursionError) as exc:
        raise ParseFailure('YAML source exceeds parser value or recursion limits') from exc
    except (KeyError, IndexError, OverflowError) as exc:
        # ruamel's malformed !!bool/!!int/!!float and YAML 1.1 conversions
        # expose these Python exceptions instead of a YAMLError.
        raise ParseFailure('cannot construct YAML scalar value') from exc
    _validate_containers(value)
    return value


def compose_yaml(text: str):
    try:
        value = YAML(typ='safe', pure=True).compose(text)
    except YAMLError as exc:
        raise _yaml_failure(exc) from exc
    except (ValueError, RecursionError) as exc:
        raise ParseFailure('YAML source exceeds parser value or recursion limits') from exc
    _validate_containers(value)
    return value


def parse_json(text: str) -> Any:
    try:
        value = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ParseFailure('cannot parse JSON source', exc.lineno, exc.colno) from exc
    except (ValueError, RecursionError) as exc:
        raise ParseFailure('JSON source exceeds parser value or recursion limits') from exc
    _validate_containers(value)
    return value


def parse_jinja(environment: Environment, text: str) -> nodes.Template:
    try:
        return environment.parse(text)
    except TemplateSyntaxError as exc:
        raise ParseFailure('cannot parse Jinja source', exc.lineno or 1) from exc
    except (ValueError, RecursionError) as exc:
        raise ParseFailure('Jinja source exceeds parser value or recursion limits') from exc
