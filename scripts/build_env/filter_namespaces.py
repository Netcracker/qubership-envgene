from pathlib import Path
import shutil

from envgenehelper.business_helper import NamespaceFile, get_bgd_object, get_namespaces, get_namespaces_path, getenv_and_log, getenv_with_error
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
    logger.info(f'Namespaces found:\n {namespace_list_to_str(namespaces)}')
    logger.info(f'Source namespaces found:\n {namespace_list_to_str(source_namespaces)}')

    bgd = get_bgd_object()
    logger.info(f'BGD object: {bgd}')

    filtered_namespaces = filter_namespaces(namespace_names, filter, bgd)
    namespaces_to_restore = [ns for ns in namespaces if ns.name not in filtered_namespaces]
    logger.info(f"Namespaces that didn't pass filter will be restored:\n {namespace_list_to_str(namespaces_to_restore)}")

    namespace_paths_to_restore = [ns for ns in namespaces_to_restore]

    if namespace_paths_to_restore:
        for ns in namespace_paths_to_restore:
            restore_namespace(ns, source_namespaces)
        logger.info(f"Restoration was successful")
    else:
        logger.info(f"No namespaces to restore")

def restore_namespace(namespace: NamespaceFile, source_namespaces: list[NamespaceFile]):
    shutil.rmtree(namespace.path)
    source_namespace = next((sns for sns in source_namespaces if sns.name == namespace.name), None)
    if not source_namespace:
        logger.debug(f'Source namespace for {namespace.name} not found, just removed namespace')
        return
    logger.debug(f'Restored {namespace.name}')
    shutil.copytree(source_namespace.path, namespace.path, dirs_exist_ok=True)

def namespace_list_to_str(namespaces: list[NamespaceFile]):
    return "\n".join(f"  - {ns.name} {ns.path}" for ns in namespaces)



