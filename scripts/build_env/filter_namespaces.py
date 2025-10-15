from pathlib import Path
import shutil

from envgenehelper.business_helper import get_bgd_object, get_namespaces, get_namespaces_path, getenv_and_log, getenv_with_error
from envgenehelper import logger

def filter_namespaces(namespaces: list[str], filter: str, bgd_object: dict) -> list[str]:
    if not filter:
        return namespaces
    is_exclusion = filter.startswith("!")
    if is_exclusion: filter = filter[1:]
    selectors = [s.strip() for s in filter.split(",") if s.strip()]
    resolved_filter = []

    for sel in selectors:
        if not sel.startswith("@"):
            resolved_filter.append(sel)
            continue
        alias = sel[1:] + 'Namespace'
        if alias not in bgd_object:
            raise ValueError(f"Unknown alias in NS_BUILD_FILTER: {sel}, can't find {alias} in BGD object")
        name = bgd_object[alias]["name"]

        resolved_filter.append(name)
    if is_exclusion:
        filtered_namespaces = [ns for ns in namespaces if ns not in resolved_filter]
    else:
        filtered_namespaces = [ns for ns in namespaces if ns in resolved_filter]
    return filtered_namespaces

def apply_ns_build_filter():
    filter = getenv_and_log('NS_BUILD_FILTER', default='')
    logger.info(f"Filtering namespaces with NS_BUILD_FILTER: {filter}")
    base_dir = getenv_with_error("CI_PROJECT_DIR")

    source_namespaces = get_namespaces(Path(f'{base_dir}/build_env/tmp/initial_namespaces_content'))
    namespaces = get_namespaces()
    namespace_names = [ns.name for ns in namespaces]
    logger.info(f'Namespaces found: {namespaces}')

    bgd = get_bgd_object()
    logger.info(f'BGD object: {bgd}')

    filtered_namespaces = filter_namespaces(namespace_names, filter, bgd)
    namespaces_to_restore = [ns for ns in namespaces if ns.name not in filtered_namespaces]
    logger.info(f"Namespaces that didn't pass filter will be restored: {namespaces_to_restore}")

    namespace_paths_to_restore = [ns for ns in namespaces_to_restore]

    if namespace_paths_to_restore:
        for ns in namespace_paths_to_restore:
            shutil.rmtree(ns.path)
            shutil.copytree(next((sns.path for sns in source_namespaces if sns.name == ns.name)), ns.path, dirs_exist_ok=True)
        logger.info(f"Restoration was successful")
    else:
        logger.info(f"No namespaces to restore")

