"""Compare decoded YAML values without conflating their scalar types."""

from __future__ import annotations

from datetime import date, datetime
from math import isnan
from typing import Any

from ruamel.yaml.scalarbool import ScalarBoolean


def _kind(value: Any) -> type | None:
    if getattr(getattr(value, "tag", None), "value", None) is not None:
        return None
    if value is None:
        return type(None)
    for kind in (dict, list, str):
        if isinstance(value, kind):
            return kind
    if isinstance(value, (bool, ScalarBoolean)):
        return bool
    for kind in (int, float, bytes, datetime, date):
        if isinstance(value, kind):
            return kind
    return None


def _mapping(value: dict) -> dict | None:
    result = {}
    for key, child in value.items():
        kind = _kind(key)
        if kind in (None, dict, list) or (kind is float and isnan(key)):
            return None
        result[(kind, key)] = child
    return result


def equal(left: Any, right: Any) -> bool | None:
    """Return typed equality, or None for unsupported or bounded analysis."""
    pending, seen, uncertain = [(left, right)], set(), False
    for _ in range(20000):
        if not pending:
            return None if uncertain else True
        first, second = pending.pop()
        kind, other = _kind(first), _kind(second)
        if kind is None or other is None:
            uncertain = True
            continue
        if kind is not other:
            return False
        if kind in (dict, list):
            pair = (id(first), id(second))
            if pair in seen:
                uncertain = True
                continue
            seen.add(pair)
            if len(first) != len(second):
                return False
            if kind is list:
                pending.extend(zip(first, second))
            else:
                first_map, second_map = _mapping(first), _mapping(second)
                if first_map is None or second_map is None:
                    uncertain = True
                    continue
                if first_map.keys() != second_map.keys():
                    return False
                pending.extend((value, second_map[key]) for key, value in first_map.items())
        elif kind is float and (isnan(first) or isnan(second)):
            uncertain = True
        elif first != second:
            return False
    return None
