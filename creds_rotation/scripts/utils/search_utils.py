
from typing import Any, Dict, List, Optional, Tuple
from functools import lru_cache
from models import AffectedParameter
from utils.yaml_utils import get_content_form_file
from pathlib import Path, PurePath
import envgenehelper.logger as logger

CONTEXT_MAP = {
    "deployment": "deployParameters",
    "pipeline": "technicalConfigurationParameters", 
    "runtime": "e2eParameters"
}

REVERSE_CONTEXT_MAP = {
    "deployparameters": "deployment",
    "technicalconfigurationparameters": "pipeline",
    "e2eparameters": "runtime"
}


@lru_cache(maxsize=None)
def resolve_param(context: str) -> str:
    return CONTEXT_MAP.get(context.lower(), "")

@lru_cache(maxsize=None)
def resolve_context(context: str) -> str:
    return REVERSE_CONTEXT_MAP.get(context.lower(), "")


def find_matching_keys(data: dict, search_pattern: str, is_target: bool,
                       context: str, target_key: str, target_context: str) -> list[str]:
    results: List[str] = []

    def recurse(obj, path):
        if isinstance(obj, dict):
            for k, v in obj.items():
                recurse(v, path + [k])
        elif isinstance(obj, list):
            for idx, item in enumerate(obj):
               if path:
                    base_path = path[:-1]
                    last_key_with_index = f"{path[-1]}[{idx}]"
                    recurse(item, base_path + [last_key_with_index])
               else:
                    recurse(item, [f"[{idx}]"])
        elif isinstance(obj, str) and search_pattern in obj:
            final_key = ".".join(path)
            if  is_target and context == target_context and final_key == target_key:
                logger.debug("skipping target param")
            else:
                results.append(final_key)
    recurse(data, [])
    return results


def find_in_yaml(data: dict, search_pattern: str, is_target: bool, target_key: str, target_context: str) -> Dict[str, List[str]]:
    matches = {}
    for context in CONTEXT_MAP.values():
        params = data.get(context, {})
        if params and search_pattern in str(params):
            affected_params = find_matching_keys(params, search_pattern, is_target, context, target_key, target_context)
            if affected_params:
                matches[context] = affected_params
    return matches


def get_ns_content(
    yaml_content_map: Dict[str, Dict[str, Any]],
    namespace: str
) -> Optional[Tuple[str, Dict[str, Any]]]:
    for file_name, content in yaml_content_map.items():
    
        if file_name.endswith(("namespace.yml", "namespace.yaml")) and content:
            if namespace == content.get("name"):
                return file_name, content
    return None


def get_app_content(
    yaml_content_map: Dict[str, Dict[str, Any]],
    namespace: str,
    app: str
) -> Optional[Tuple[str, Dict[str, Any]]]:
    for file_name, content in yaml_content_map.items():
        if file_name.endswith(("namespace.yml", "namespace.yaml")) or content is None:
            continue

        if app != content.get("name"):
            continue

        parent_dir = Path(file_name).parent.parent
        ns_file_yaml = parent_dir / "namespace.yaml"
        ns_file_yml = parent_dir / "namespace.yml"

        try:
            ns_content = get_content_form_file(ns_file_yaml)
        except Exception:
            try:
                ns_content = get_content_form_file(ns_file_yml)
            except Exception as e:
                logger.warning(f"Failed to load namespace file for {file_name}: {e}")
                continue

        if ns_content and ns_content.get("name") == namespace:
            return file_name, content

    return None


def get_app_and_ns(filename: str, content: dict) -> Tuple[str, Optional[str]]:
    if filename.endswith(("namespace.yml", "namespace.yaml")):
        return '', content.get('name', '')
    
    filepath = PurePath(filename)
    parent_dir = filepath.parent.parent
    ns_file_yaml = parent_dir / "namespace.yaml"
    ns_file_yml = parent_dir / "namespace.yml"

    try:
        ns_content = get_content_form_file(ns_file_yml)
    except Exception:
        try:
            ns_content = get_content_form_file(ns_file_yaml)
        except Exception as e:
            raise Exception(f"Failed to load namespace file from {parent_dir}: {e}")
    return content.get('name', ''), ns_content.get('name','')

def trim_path_from_environments(path: str):
    normalized = path.replace("\\", "/")
    marker = "/environments/"
    idx = normalized.find(marker)
    return normalized[idx:] if idx != -1 else normalized

def get_affected_param_map(
    cred_id: str,
    env: str,
    shared_cred_files: list,
    env_cred_files: list,
    filename: str,
    content: dict,
    matches: dict
) -> list[AffectedParameter]:
    result = []
    app, namespace = get_app_and_ns(filename, content)

    for context, param_keys in matches.items():
        for key in param_keys:
            affected = AffectedParameter(
                environment=env,
                namespace=namespace,
                application=app,
                context=resolve_context(context),
                parameter_key=key,
                environment_cred_filepath=trim_path_from_environments(env_cred_files),
                shared_cred_filepath=[trim_path_from_environments(p) for p in shared_cred_files],
                cred_id=cred_id
            )
            result.append(affected)

    return result


def search_yaml_files(search_string: str, ns_files_map: Dict[str, Dict[str, Any]], cred_id: str, env: str, shared_cred_files: List[str], env_cred_file: str, target_key: str,
 target_context: str, target_file: str) -> List[AffectedParameter]:
    affected: List[AffectedParameter] = []

    for filename, content in ns_files_map.items():

        is_target = filename == target_file
        matches = find_in_yaml(content, search_string, is_target, target_key, target_context)
        if matches:
            affected.extend(get_affected_param_map(
            cred_id, env, shared_cred_files, env_cred_file, filename, content, matches
            ))
    return affected