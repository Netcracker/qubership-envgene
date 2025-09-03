from io import StringIO
from pprint import pformat
from .yaml_helper import yaml
import copy

def merge_lists(list1, list2) :
    if len(list2) > 0 :
        return list1 + list2
    return list1

primitives = (bool, str, int, float, type(None))

def is_primitive(obj):
    return isinstance(obj, primitives)

def dump_as_yaml_format(collection) :
    if collection and isinstance(collection, dict):
        tmp = copy.deepcopy(collection)
        stream = StringIO()
        yaml.dump(tmp, stream)
        return stream.getvalue()
    else:
        return pformat(collection)

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

DictPath = list[str | int]
def compare_dicts(source: dict, target: dict) -> tuple[list[DictPath], list[DictPath]]:
    diff_paths = []
    removed_paths = []
    path = []
    _compare_dicts_recurse(source, target, path, diff_paths, removed_paths)
    return diff_paths, removed_paths

def _compare_dicts_recurse(source: object, target: object, path: DictPath, diff_paths: list[DictPath], removed_paths: list[DictPath]) -> None:
    if isinstance(target, list) and isinstance(source, list):
        sl = len(source)
        tl = len(target)
        for i in range(max(sl,tl)):
            new_path = path + [i]
            if i >= sl:
                diff_paths.append(new_path.copy())
                continue
            if i >= tl:
                removed_paths.append(new_path.copy())
                continue
            _compare_dicts_recurse(source[i], target[i], new_path, diff_paths, removed_paths)
    elif isinstance(target, dict) and isinstance(source, dict):
        s_keys = source.keys()
        t_keys = target.keys()
        keys = set(s_keys).union(t_keys)
        for k in keys:
            new_path = path + [k]
            if k not in s_keys:
                diff_paths.append(new_path.copy())
                continue
            if k not in t_keys:
                removed_paths.append(new_path.copy())
                continue
            _compare_dicts_recurse(source[k], target[k], new_path, diff_paths, removed_paths)
    elif source != target:
        diff_paths.append(path.copy())

