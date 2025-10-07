from pathlib import Path
import subprocess

from envgenehelper.business_helper import get_current_env_dir_with_env_vars, getenv_with_error
from envgenehelper.yaml_helper import openYaml
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
        alias = sel[1:]
        if alias not in bgd_object:
            raise ValueError(f"Unknown alias in NS_BUILD_FILTER: {sel}")
        name = bgd_object[alias]["name"]

        resolved_filter.append(name)
    if is_exclusion:
        filtered_namespaces = [ns for ns in namespaces if ns not in resolved_filter]
    else:
        filtered_namespaces = [ns for ns in namespaces if ns in resolved_filter]
    return filtered_namespaces

def main():
    env_dir = Path(get_current_env_dir_with_env_vars())

    filter = getenv_with_error('NS_BUILD_FILTER')
    logger.info(f"Filtering namespaces with NS_BUILD_FILTER: {filter}")

    namespaces_path = env_dir.joinpath('Namespaces')
    logger.info(f'Namespaces path: {namespaces_path}')

    namespaces = [p.name for p in namespaces_path.iterdir() if p.is_dir()]
    logger.info(f'Namespaces found: {namespaces}')

    bgd = openYaml(env_dir.joinpath('bg_domain.yml'))
    logger.info(f'BGD object: {bgd}')

    filtered_namespaces = filter_namespaces(namespaces, filter, bgd)
    namespaces_to_restore = [ns for ns in namespaces if ns not in filtered_namespaces]
    logger.info(f"Namespaces that didn't pass filter will be restored: {namespaces_to_restore}")

    namespace_paths_to_restore = [namespaces_path.joinpath(ns) for ns in namespaces_to_restore]
    if namespace_paths_to_restore:
        subprocess.run(['git','restore','--'] + namespace_paths_to_restore, check=True)
        logger.info(f"Restoration was successful")
    else:
        logger.info(f"No namespaces to restore")

if __name__ == "__main__":
    main()

