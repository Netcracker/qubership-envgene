from envgene_shared.utils.logger import logger


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

def split_multi_value_param(param: str)-> list[str]:

    if not param:
        return []

    param = param.strip()
    if not param:
        return []

    has_comma = ',' in param
    has_semicolon = ';' in param
    has_space = ' ' in param
    has_newline = '\n' in param

    delimiter_count = sum([has_comma, has_semicolon, has_space, has_newline])

    if delimiter_count > 1:
        raise ValueError(
            "Invalid input: use only ONE delimiter type (comma, semicolon, space, or newline)"
        )

    if has_comma:
        logger.info(f"env names {param} has comma as delimiter. splitting it")
        parts = param.split(',')
    elif has_semicolon:
        logger.info(f"env names {param} has semicolon as delimiter. splitting it")
        parts = param.split(';')
    elif has_space:
        logger.info(f"env names {param} has space as delimiter. splitting it")
        parts = param.split()
    elif has_newline:
        logger.info(f"env names {param} has newline as delimiter. splitting it")
        parts = param.splitlines()
    else:
        return [param]

    return [p.strip() for p in parts if p.strip()]

