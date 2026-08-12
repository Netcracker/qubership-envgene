from functools import lru_cache
import os
import ruyaml
import threading
from typing import OrderedDict

import jschon
import jsonschema
from jsonschema import RefResolver
from typing import Callable
from ruyaml import CommentedMap, CommentedSeq
from pathlib import Path

from envgene_shared.utils.file_utils import *
from envgene_shared.utils.logger import logger


def get_empty_yaml():
    return ruyaml.CommentedMap()


def openYaml(filePath, safe_load=False, default_yaml: Callable = get_empty_yaml, allow_default=False):
    if allow_default and not check_file_exists(filePath):
        logger.info(f'{filePath} not found. Returning default value')
        return default_yaml()

    logger.debug(f"Open yaml file: {filePath}")
    with open(filePath, 'r') as f:
        resultYaml = readYaml(f.read(), safe_load, context=f"File: {filePath}")
    return resultYaml


def readYaml(text, safe_load=False, context=None) -> CommentedMap:
    if text is None:
        resultYaml = None
    elif safe_load:
        resultYaml = safe_yaml.load(text)
    else:
        resultYaml = yaml.load(text)

    if not resultYaml:
        logger.warning(f"Failed to read yaml. Returning empty dictionary. Context: {context}")
        return get_empty_yaml()
    return resultYaml


def validate_yaml_by_scheme_or_fail(yaml_file_path: str = None, schema_file_path: str = None,
                                    input_yaml_content: dict = None, input_schema_content: dict = None,
                                    schemas_dir=None):
    yaml_content = openYaml(yaml_file_path) if yaml_file_path else input_yaml_content
    schema_content = openJson(schema_file_path) if schema_file_path else input_schema_content

    if schemas_dir:
        base_uri = Path(schemas_dir).absolute().as_uri() + "/"
        resolver = RefResolver(base_uri=base_uri, referrer=schema_content)
        errors = validate_yaml_data_by_schema(yaml_content, schema_content, resolver=resolver)
    else:
        errors = validate_yaml_data_by_schema(yaml_content, schema_content)
    if len(errors) > 0:
        if yaml_file_path:
            rel_path = getRelPath(yaml_file_path)
            logger.error(f"Validation of {rel_path} file has failed")
        for err in errors:
            log_jsonschema_validation_error(err)
        raise ValueError("Validation failed") from None


def validate_yaml_data_by_schema(data, schema, cls=None, *args, **kwargs):
    if cls is None:
        cls = jsonschema.validators.validator_for(schema)
    cls.check_schema(schema)
    validator = cls(schema, *args, **kwargs)
    errors = sorted(validator.iter_errors(data), key=lambda e: e.path)
    return errors


def log_jsonschema_validation_error(error: jsonschema.ValidationError) -> None:
    key_path = '.'.join(str(index) for index in error.absolute_path)
    if isinstance(error.instance, OrderedDict):
        error.instance = convert_ordereddict_to_dict(error.instance)
    if error.validator == "type":
        logger.error(f"Attribute {key_path} has value {error.instance}")
        logger.error(f"Value of type {error.validator_value} is expected instead")
    elif error.validator == "required":
        message = error.message
        if key_path:
            message = f"{message} at '{key_path}' property"
        logger.error(message)
    else:
        logger.error(error.message)
    logger.error(f"\n")


def convert_ordereddict_to_dict(obj):
    if isinstance(obj, OrderedDict):
        return {k: convert_ordereddict_to_dict(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_ordereddict_to_dict(i) for i in obj]
    else:
        return obj


def writeYamlToFile(filePath, contents):
    filePath = Path(filePath)
    logger.info(f"Writing yaml to file: {filePath}")
    os.makedirs(os.path.dirname(filePath), exist_ok=True)
    if is_cred_file(str(filePath)):
        remove_cred_yaml_comments(contents)
    else:
        remove_empty_list_comments(contents)
    with open(filePath, 'w+') as f:
        yaml.dump(contents, f)
    return


def remove_cred_yaml_comments(data):
    if not isinstance(data, (CommentedMap, CommentedSeq)):
        return
    if data.ca:
        data.ca.comment = None
        if data.ca.items:
            data.ca.items.clear()
    children = data.values() if isinstance(data, CommentedMap) else data
    for child in children:
        remove_cred_yaml_comments(child)


def remove_empty_list_comments(data):
    # There are cases when list has values and those values have comments related
    # to them. When all values are removed from list, comments are left behind
    # and when rendered by ruyaml create an invalid file content that makes
    # future parsing to fail. To avoid this we clean up those comments
    if isinstance(data, CommentedMap):
        for key, value in data.items():
            if isinstance(value, list) and not value:
                if data.ca and data.ca.items and key in data.ca.items:
                    comment_info = data.ca.items[key]
                    if len(comment_info) > 3:
                        comment_info[3] = None
            if isinstance(value, (CommentedMap, CommentedSeq)):
                remove_empty_list_comments(value)
    elif isinstance(data, CommentedSeq):
        for item in data:
            if isinstance(item, (CommentedMap, CommentedSeq)):
                remove_empty_list_comments(item)


def ensure_nested_attr_parents_exist(yaml_content, attribute_str):
    keys = attribute_str.split('.')
    sub_content = yaml_content
    for key in keys[:-1]:
        if key not in sub_content:
            sub_content[key] = get_empty_yaml()
        sub_content = sub_content[key]
    last_key = keys[-1]
    return sub_content, last_key


def ensure_nested_attr_exists(yaml_content, attribute_str, default_value=None):
    sub_content, last_key = ensure_nested_attr_parents_exist(yaml_content, attribute_str)
    if not last_key in sub_content:
        sub_content[last_key] = default_value
    return sub_content, last_key


def get_or_create_nested_yaml_attribute(yaml_content, attribute_str, default_value=None):
    yaml_content, key = ensure_nested_attr_exists(yaml_content, attribute_str, default_value)
    return yaml_content[key]



def create_yaml_processor(is_safe=False) -> ruyaml.main.YAML:
    def _null_representer(self: ruyaml.representer.BaseRepresenter, data: None) -> ruyaml.Any:
        return self.represent_scalar('tag:yaml.org,2002:null', 'null')

    if is_safe:
        yaml = ruyaml.main.YAML(typ='safe')
    else:
        yaml = ruyaml.main.YAML()
    yaml.preserve_quotes = True
    yaml.width = 200
    yaml.indent(mapping=2, sequence=4, offset=2)
    yaml.Representer.add_representer(type(None), _null_representer)
    return yaml


class _ThreadLocalYaml:
    def __init__(self, is_safe: bool = False):
        self.is_safe = is_safe
        self._local = threading.local()

    def _get_instance(self):
        attr = "safe_yaml" if self.is_safe else "yaml"
        if not hasattr(self._local, attr):
            setattr(self._local, attr, create_yaml_processor(self.is_safe))
        return getattr(self._local, attr)

    def __getattr__(self, name):
        return getattr(self._get_instance(), name)


jschon.create_catalog('2020-12')
yaml = _ThreadLocalYaml(is_safe=False)
safe_yaml = _ThreadLocalYaml(is_safe=True)