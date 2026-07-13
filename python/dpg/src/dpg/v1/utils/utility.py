import yaml
from pathlib import Path

def is_file_path(value: str) -> bool:
    return bool(value and Path(value).exists())

def load_json_or_yaml(content: str):
    data = yaml.safe_load(content)
    if isinstance(data, (dict, list)):
        return data
    return None
