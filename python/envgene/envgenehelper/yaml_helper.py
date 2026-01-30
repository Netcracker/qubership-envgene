import copy
import json
import pathlib
from io import StringIO
from typing import OrderedDict

import jschon
import jschon_tools
import jsonschema
import ruyaml
from ruyaml import CommentedMap, CommentedSeq
from ruyaml.scalarstring import DoubleQuotedScalarString, LiteralScalarString

from .file_helper import *
from .json_helper import openJson
from .logger import logger
from jsonschema import RefResolver


def create_yaml_processor(is_safe=False) -> ruyaml.main.YAML:
    def _null_representer(self: ruyaml.representer.BaseRepresenter) -> ruyaml.Any:
        return self.represent_scalar('tag:yaml.org,2002:null', 'null')

    if is_safe:
        yaml = ruyaml.main.YAML(typ='safe')
    else:
        yaml = ruyaml.main.YAML()
    yaml.preserve_quotes = True
    yaml.width = 200
    yaml.indent(mapping=2, sequence=4, offset=2)
    yaml.Representer.add_representer(type(None), _null_representer)
    yaml.default_flow_style = False
    return yaml


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


def convert_dict_to_yaml(d):
    if isinstance(d, ruyaml.CommentedMap):
        return d
    return ruyaml.CommentedMap(d)


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


def writeYamlToFile(filePath, contents):
    filePath = Path(filePath)
    logger.info(f"Writing yaml to file: {filePath}")
    os.makedirs(os.path.dirname(filePath), exist_ok=True)
    remove_empty_list_comments(contents)
    with open(filePath, 'w+') as f:
        yaml.dump(contents, f)
    return


def dumpYamlToStr(content):
    buffer = StringIO()
    yaml.dump(content, buffer)
    return buffer.getvalue()


def addHeaderToYaml(file_path: str, header_text: str):
    if (header_text):
        logger.debug(f'Adding header {header_text} to yaml: {file_path}')
        file_contents = openFileAsString(file_path)
        if not file_contents or file_contents[0] != "#":
            comment_text = "# " + header_text.replace("\n", "\n# ")
            writeToFile(file_path, comment_text + "\n" + file_contents)


def alignYamlFileComments(file_path):
    logger.debug(f'Alligning comments yaml: {file_path}')
    yamlData = openYaml(file_path)
    alignYamlComments(yamlData, 0)
    writeYamlToFile(file_path, yamlData)


def deleteCommentByKey(yamlContent, key):
    if yamlContent.ca:
        yamlContent.ca.items.pop(key, None)


def alignYamlComments(yamlContent, extra_indent=0):
    is_dict = isinstance(yamlContent, dict)
    if not is_dict and not isinstance(yamlContent, list):
        return None

    comments = yamlContent.ca.items.values()
    if comments:
        max_col = max(map(lambda x: x[2].column if x[2] else 0, comments), default=0)
        for comment in comments:
            if (comment[2]):
                comment[2].column = max_col + extra_indent
    for element in (yamlContent.values() if is_dict else yamlContent):
        alignYamlComments(element, extra_indent=extra_indent)
    return None


def sortYaml(yaml_data, schema_path, remove_additional_props):
    with open(schema_path, 'r') as f:
        schema_data = json.load(f)
    logger.debug(f'Checking yaml with schema: {schema_path}')
    jsonschema.validate(yaml_data, schema_data)
    sort_data = jschon_tools.process_json_doc(
        schema_data=schema_data,
        doc_data=yaml_data,
        sort=True,
        remove_additional_props=remove_additional_props
    )
    return sort_data


def get_nested_yaml_attribute_or_fail(yaml_content, attribute_str):
    keys = attribute_str.split('.')
    sub_content = yaml_content
    for key in keys:
        if not isinstance(sub_content, dict):
            raise ValueError(f"Failed to find attribute '{attribute_str}', key '{key}' is not a dictionary")
        if key not in sub_content:
            raise ValueError(f"Failed to find attribute '{attribute_str}', key '{key}' doesn't exist")
        sub_content = sub_content[key]
    return sub_content


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


def set_nested_yaml_attribute(yaml_content, attribute_str, value, comment="", is_overwriting=True):
    if value is None:
        return
    yaml_content, attribute = ensure_nested_attr_parents_exist(yaml_content, attribute_str)
    if attribute not in yaml_content:
        store_value_to_yaml(yaml_content, attribute, value, comment)
        logger.debug(f'Attribute {attribute_str} is set to {value}')
    elif is_overwriting:
        old_value = yaml_content[attribute]
        store_value_to_yaml(yaml_content, attribute, value, comment)
        logger.debug(f'Attribute {attribute_str} is changed to {value}. Old value was {old_value}')
    else:
        logger.debug(f'Setting {attribute_str} is skipped. Attribute already exists and is_overwriting is set to False')


primitiveTypes = (int, str, bool, float)


def merge_yaml_into_target(yaml_content, target_attribute_str, source_yaml, overwrite_existing_values=True,
                           overwrite_existing_comments=True):
    if source_yaml is None:
        return
    source_yaml = convert_dict_to_yaml(source_yaml)

    if target_attribute_str != '':
        yaml_content, last_key = ensure_nested_attr_exists(yaml_content, target_attribute_str, get_empty_yaml())
        target_yaml = yaml_content[last_key]
    else:
        target_yaml = yaml_content

    for k, v in source_yaml.items():
        if k not in target_yaml:
            target_yaml[k] = v
            target_yaml.ca.items[k] = source_yaml.ca.items.get(k, None)
            continue

        if overwrite_existing_comments:
            target_yaml.ca.items[k] = source_yaml.ca.items.get(k, None)

        if isinstance(target_yaml[k], dict) and isinstance(v, dict):
            merge_yaml_into_target(target_yaml[k], "", v, overwrite_existing_values, overwrite_existing_comments)
        elif isinstance(target_yaml[k], list) and isinstance(v, list):
            target_yaml[k].extend(v_el for v_el in v if v_el not in target_yaml[k] and (
                    isinstance(v_el, primitiveTypes) or isinstance(v_el, list)))
            src_dicts = {}
            for v_k, v_el in enumerate(v):
                if isinstance(v_el, dict):
                    src_dicts.update({v_k: v_el})
            for t_k, t_el in enumerate(target_yaml[k]):
                if not isinstance(t_el, dict):
                    continue
                if not t_k in src_dicts:
                    continue
                merge = False
                for t_el_k in t_el.keys():
                    if t_el_k in src_dicts[t_k].keys():
                        merge = True
                        break
                if merge:
                    target_yaml[k][t_k] = merge_yaml_into_target(t_el, '', src_dicts[t_k], overwrite_existing_values,
                                                                 overwrite_existing_comments)
                    del src_dicts[k]
            for _, src_dicts_el in src_dicts.items():
                target_yaml[k].append(src_dicts_el)
        elif overwrite_existing_values:
            target_yaml[k] = v


def store_value_to_yaml(yamlContent, key, value, comment=""):
    logger.debug(f"Updating key {key} with value {value} in yaml")
    if key in yamlContent:
        deleteCommentByKey(yamlContent, key)
        del yamlContent[key]
    yamlContent[key] = value
    if comment:
        yamlContent.insert(1, key, value, comment)
    else:
        yamlContent.insert(1, key, value)


def merge_dict_key_with_comment(targetKey, targetYaml, sourceKey, sourceYaml, comment=""):
    if sourceKey in sourceYaml:
        deleteCommentByKey(targetYaml, targetKey)
        deleteCommentByKey(sourceYaml, sourceKey)
        store_value_to_yaml(targetYaml, targetKey, sourceYaml[sourceKey], comment)


def beautifyYaml(file_path, schema_path="", header_text="", allign_comments=False, wrap_all_strings=False,
                 remove_additional_props=False):
    logger.info(f'Beautifying yaml: {file_path} with schema: {schema_path}')
    yamlData = openYaml(file_path)
    if schema_path:
        yamlData = sortYaml(yamlData, schema_path, remove_additional_props)
    if wrap_all_strings:
        make_quotes_for_all_strings(yamlData)
    else:
        make_quotes_for_strings(yamlData)

    writeYamlToFile(file_path, yamlData)
    addHeaderToYaml(file_path, header_text)
    align_spaces_before_comments(file_path)
    if allign_comments:
        alignYamlFileComments(file_path)


def findYamls(dir, pattern, notPattern="", additionalRegexpPattern="", additionalRegexpNotPattern=""):
    fileList = findAllYamlsInDir(dir)
    return findFiles(fileList, pattern, notPattern, additionalRegexpPattern, additionalRegexpNotPattern)


def findAllYamlsInDir(dir):
    result = []
    dirPointer = pathlib.Path(dir)
    fileList = list(dirPointer.rglob("*.yml"))
    fileListYaml = list(dirPointer.rglob("*.yaml"))
    if len(fileListYaml) > 0:
        fileList = fileList + fileListYaml
    for f in fileList:
        result.append(str(f))
    return result


def mergeYamlInDir(dir_path):
    result = {}
    if check_dir_exists(dir_path):
        yamlList = findAllYamlsInDir(dir_path)
        for yamlPath in yamlList:
            result.update(openYaml(yamlPath))
    return result


def make_quotes_for_all_strings(yaml_data):
    if isinstance(yaml_data, (dict, list, set)):
        for k, v in (yaml_data.items() if isinstance(yaml_data, dict) else enumerate(yaml_data)):
            if isinstance(v, str) and not isinstance(v, DoubleQuotedScalarString):
                yaml_data[k] = DoubleQuotedScalarString(v)
            make_quotes_for_all_strings(v)


def make_quotes_for_strings(yaml_data):
    if isinstance(yaml_data, (dict, list, set)):
        for k, v in (yaml_data.items() if isinstance(yaml_data, dict) else enumerate(yaml_data)):
            if isinstance(v, str) and not isinstance(v, DoubleQuotedScalarString) and not ("\n" in v):
                yaml_data[k] = DoubleQuotedScalarString(v)
            elif isinstance(v, DoubleQuotedScalarString) and ("\n" in v):
                yaml_data[k] = LiteralScalarString(v)
            else:
                make_quotes_for_strings(v)


def align_spaces_before_comments(filePath):
    result = ""
    f = open(filePath, 'r')
    fileLines = f.readlines()
    for line in fileLines:
        if re.match(r'^(.*):( +)#(.*)$', line):
            pattern = r'^(.*):( +)#(.*)$'
            alignedLine = re.sub(pattern, r'\1: #\3', line)
        else:
            alignedLine = line
        result += alignedLine

    writeToFile(filePath, result)


def copy_yaml_and_remove_empty_dicts(source_yaml):
    # copying yaml dict
    result = copy.deepcopy(source_yaml)
    # going to recursion for dict entities
    for key in result.keys():
        value = result[key]
        if isinstance(value, dict):
            result[key] = copy_yaml_and_remove_empty_dicts(value)
    # removing all empty keys
    empty_keys = [k for k, v in result.items() if v == {}]
    for k in empty_keys:
        del result[k]
    return result


def empty_yaml():
    result = yaml.load("{}")
    return result


def yaml_from_string(yaml_str):
    result = yaml.load(yaml_str)
    return result


def validate_yaml_by_scheme_or_fail(yaml_file_path: str = None, schema_file_path: str = None,
                                    input_yaml_content: dict = None, input_schema_content: dict = None,
                                    schemas_dir=None):
    yaml_content = openYaml(yaml_file_path) if yaml_file_path else input_yaml_content
    schema_content = openJson(schema_file_path) if schema_file_path else input_schema_content

    if schemas_dir:
        base_uri = Path(schemas_dir).absolute().as_uri() + "/"
        resolver = RefResolver(base_uri=base_uri, referrer=schema_content)
        errors = validate_yaml_data_by_scheme(yaml_content, schema_content, resolver=resolver)
    else:
        errors = validate_yaml_data_by_scheme(yaml_content, schema_content)
    if len(errors) > 0:
        if yaml_file_path:
            rel_path = getRelPath(yaml_file_path)
            logger.error(f"Validation of {rel_path} file has failed")
        for err in errors:
            log_jsonschema_validation_error(err)
        raise ValueError("Validation failed") from None


def validate_yaml_data_by_scheme(data, schema, cls=None, *args, **kwargs):
    if cls is None:
        cls = jsonschema.validators.validator_for(schema)
    cls.check_schema(schema)
    validator = cls(schema, *args, **kwargs)
    errors = sorted(validator.iter_errors(data), key=lambda e: e.path)
    return errors


def log_jsonschema_validation_error(err):
    key_path = '.'.join(str(index) for index in err.absolute_path)
    if isinstance(err.instance, OrderedDict):
        err.instance = convert_ordereddict_to_dict(err.instance)
    if "is not of type" in err.message:
        logger.error(f"Attribute {key_path} has value {err.instance}")
        logger.error(f"Value of type {err.validator_value} is expected instead")
    elif "is a required property" in err.message:
        if len(key_path) > 0: err.message += f" at '{key_path}' property"
        logger.error(err.message)
    else:
        logger.error(err.message)
    logger.error(f"\n")


def convert_ordereddict_to_dict(obj):
    if isinstance(obj, OrderedDict):
        return {k: convert_ordereddict_to_dict(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_ordereddict_to_dict(i) for i in obj]
    else:
        return obj


def find_all_yaml_files_by_stem(path: str):
    file_paths = []
    for ext in ["yaml", "yml"]:
        file_path = Path(f"{path}.{ext}")
        if file_path.exists():
            file_paths.append(file_path)
    return file_paths


jschon.create_catalog('2020-12')
yaml = create_yaml_processor()
safe_yaml = create_yaml_processor(is_safe=True)
