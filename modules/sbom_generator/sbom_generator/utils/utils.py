import base64
import json
import os
from pathlib import Path

import yaml
from envgenehelper import logger
from sbom_generator.utils.errors import IllegalArgumentException, NotFoundException
from flatten_dict import unflatten
from deepmerge import always_merger
from sbom_generator.utils.models import Extensions

WORK_DIR = Path(os.getcwd())
BASE_DIR = Path(__file__).resolve().parent.parent
SCHEMA_TEMPLATE = str(BASE_DIR / "schemas" / "{name}.sbom.schema.json")


def encode_dict_to_base64(raw: dict, suffix: str) -> str:
    text = ""
    if Extensions.YAML.value in suffix or Extensions.YML.value in suffix:
        text = yaml.safe_dump(raw, sort_keys=False, indent=2)
    elif Extensions.JSON.value in suffix:
        text = json.dumps(raw, sort_keys=False, indent=2)
    raw_bytes = text.encode("utf-8")
    return base64.b64encode(raw_bytes).decode("utf-8")


def encode_file_to_base64(file_path) -> str:
    with open(WORK_DIR.joinpath(file_path), "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def find_file_by_name_in_dir(directory: Path, file_name: str) -> Path | None:
    if not isinstance(directory, Path):
        directory = Path(directory)
    if directory.exists() and directory.is_dir():
        for item in WORK_DIR.joinpath(directory).iterdir():
            if item.is_file() and item.stem == file_name:
                return item.resolve()
    else:
        logger.debug(f"The specified path was not found: {directory}")


def load_file(file_path: Path) -> dict:
    if not isinstance(file_path, Path):
        file_path = Path(file_path)

    with file_path.open('r', encoding='utf-8') as f:
        if Extensions.JSON.value in file_path.suffix:
            return json.load(f)
        elif Extensions.YAML.value in file_path.suffix or Extensions.YML.value in file_path.suffix:
            return yaml.safe_load(f)
        else:
            raise IllegalArgumentException(f"Unsupported file type: {file_path.suffix}")


def open_and_convert(cls, path: Path, filename: str) -> list | dict:
    file_path = find_file_by_name_in_dir(path, filename)
    if file_path:
        data = load_file(file_path)
        if isinstance(data, list):
            items = []
            for i in data:
                items.append(cls.model_validate(i))
            return items
        else:
            return cls.model_validate(data)
    else:
        raise NotFoundException(f"There is no file by name {filename} in dir {path}")


def load_schema(schema_name: str):
    schema_path = Path(SCHEMA_TEMPLATE.format(name=schema_name))
    with open(schema_path, 'r', encoding='utf-8') as file:
        return json.load(file)


def replace_extension(url: str, ext):
    return url.rsplit('.', 1)[0] + '.' + ext


def has_dotted_keys(data: dict) -> bool:
    for key, value in data.items():
        if "." in key:
            return True
        if isinstance(value, dict) and has_dotted_keys(value):
            return True
        if isinstance(value, list):
            for item in value:
                if isinstance(item, dict) and has_dotted_keys(item):
                    return True
    return False


def splitter(k: str) -> list[str]:
    return k.split(".")


def safe_unflatten(data: dict) -> dict:
    result = {}
    for key, value in data.items():
        if isinstance(value, dict):
            value = safe_unflatten(value)
        elif isinstance(value, list):
            value = [safe_unflatten(x) if isinstance(x, dict) else x for x in value]

        if "." in key:
            expanded_dict = unflatten({key: value}, splitter=splitter)
            result = always_merger.merge(result, expanded_dict)
        else:
            result = always_merger.merge(result, {key: value})
    return result


def list_files(path: Path) -> list[Path]:
    if not isinstance(path, Path):
        path = Path(path)
    if not path.exists() or not path.is_dir():
        logger.warning(f"Directory does not exist: {path}")
        return []
    return sorted((f for f in path.iterdir() if f.is_file()), key=lambda f: f.name)


