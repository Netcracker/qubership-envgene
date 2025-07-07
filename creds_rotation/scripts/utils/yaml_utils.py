import os
import yaml
import re
from typing import Any
import envgenehelper.logger as logger

def write_yaml_to_file(file_path: str, contents: Any) -> None:
    logger.debug(f"Writing YAML to file: {file_path}")
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "w") as f:
        yaml.safe_dump(contents, f, sort_keys=False)

def convert_json_to_yaml(file_path: str, json_data: Any):
    # Convert and write to a YAML file
    with open(file_path, "w") as yaml_file:
        yaml.dump(json_data, yaml_file, sort_keys=False)


def get_content_form_file(file: str) -> Any:
        try:
            with open(file, "r", encoding="utf-8") as f:
                return yaml.safe_load(f)
        except Exception as e:
            raise Exception(f"Failed to load str(file): {e}")

def get_nested_target_key(yaml_data: dict, path: str) -> str:
    current = yaml_data

    for part in path.split('.'):
        key, index = part, None

        if '[' in part:
            match = re.fullmatch(r'(.*?)\[(\d+)\]', part)
            if not match:
                raise ValueError(f"Invalid path segment: {part}")
            key, index = match.group(1), int(match.group(2))

        if not isinstance(current, dict) or key not in current:
            raise KeyError(f"Missing key: {key} in {current}")
        current = current[key]

        if index is not None:
            if not isinstance(current, list):
                raise TypeError(f"Expected list at {key}[{index}], got {type(current)}")
            if index >= len(current):
                raise IndexError(f"Index {index} out of bounds for key: {key}")
            current = current[index]

    return current

