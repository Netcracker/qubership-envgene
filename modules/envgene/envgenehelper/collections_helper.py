from io import StringIO
from pprint import pformat
from .yaml_helper import yaml
import copy
from .logger import logger
from enum import Enum
from envgene_shared.utils.collections_utils import split_multi_value_param, compare_dicts

def merge_lists(list1, list2) :
    if len(list2) > 0 :
        return list1 + list2
    return list1

primitives = (bool, str, int, float, type(None))

def is_primitive(obj):
    return isinstance(obj, primitives)

def _convert_enums(obj):
    if isinstance(obj, Enum):
        return obj.value
    if isinstance(obj, dict):
        return {
            _convert_enums(k): _convert_enums(v)
            for k, v in obj.items()
        }
    if isinstance(obj, list):
        return [_convert_enums(v) for v in obj]
    if isinstance(obj, tuple):
        return tuple(_convert_enums(v) for v in obj)
    if isinstance(obj, set):
        return {_convert_enums(v) for v in obj}
    return obj


def dump_as_yaml_format(collection):
    converted = _convert_enums(collection)
    if converted and isinstance(converted, dict):
        stream = StringIO()
        yaml.dump(converted, stream)
        return stream.getvalue()
    return pformat(converted)

def get_merged_param_value(key, source_dict, override_dict):
    if isinstance(override_dict[key], dict):
        # if source_dict has the same key
        if key in source_dict:
            return dict_merge(source_dict[key], override_dict[key])
    return override_dict[key]


def dict_merge(a, b):
    """
    Merge two values, with `b` taking precedence over `a`.

    Semantics:
    - If either `a` or `b` is not a dictionary, `a` will be returned only if
      `b` is `None`. Otherwise `b` will be returned.
    - If both values are dictionaries, they are merged as follows:
        * Each key that is found only in `a` or only in `b` will be included in
          the output collection with its value intact.
        * For any key in common between `a` and `b`, the corresponding values
          will be merged with the same semantics.
    """
    if not isinstance(a, dict) or not isinstance(b, dict):
        return a if b is None else b
    else:
        # If we're here, both a and b must be dictionaries or subtypes thereof.

        # Compute set of all keys in both dictionaries.
        keys = set(a.keys()) | set(b.keys())

        # Build output dictionary, merging recursively values with common keys,
        # where `None` is used to mean the absence of a value.
        return {
            key: dict_merge(a.get(key), b.get(key))
            for key in keys
        }
