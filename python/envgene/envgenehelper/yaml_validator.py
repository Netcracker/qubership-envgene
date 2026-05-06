from .logger import logger
from .collections_helper import dump_as_yaml_format
import re
import copy

VALIDATION_DATA_TYPES = [
    "string",
    "number",
    "boolean",
    "object"
]

def checkByWhiteList(yamlContent, whiteList, removeEmptyDicts=False, isComplex=False):
    yamlCompare = remove_empty_dicts_recursive(yamlContent) if removeEmptyDicts else copy.deepcopy(yamlContent)
    whiteListCompare = remove_empty_dicts_recursive(whiteList) if removeEmptyDicts else copy.deepcopy(whiteList)
    logger.debug(f"Yaml to check: {dump_as_yaml_format(yamlCompare)}")
    logger.debug(f"White list: {dump_as_yaml_format(whiteListCompare)}")
    errors = {
        "extraKeys": [],
        "absentKeys": [],
        "checkMismatch": []
    }
    recursive_compare(yamlCompare, whiteListCompare, errors, isComplex=isComplex)
    return errors

def checkByBlackList(yamlContent, whiteList):
    return True

def remove_empty_dicts_recursive(map, result=None):
    if not result:
        result = copy.deepcopy(map)
    for k in map:
        if isinstance(map[k], dict):
            remove_empty_dicts_recursive(map[k], result[k])
            if not result[k]:
                del result[k]
    return result

def recursive_compare(yamlContent, whiteList, errors, level='', isComplex=False):
    if isinstance(yamlContent, dict) and isinstance(whiteList, dict) and not checkDictIsSchemaValidator(whiteList):
        if yamlContent.keys() != whiteList.keys():
            s1 = set(yamlContent.keys())
            s2 = set(whiteList.keys())
            extraKeys = s1 -s2
            for extraKey in extraKeys:
                errors["extraKeys"].append(f"{level}.{extraKey}" if level else extraKey)
            absentKeys = s2 - s1
            for absentKey in absentKeys:
                errors["absentKeys"].append(f"{level}.{absentKey}" if level else absentKey)
            common_keys = s1 & s2
        else:
            common_keys = set(yamlContent.keys())

        for k in common_keys:
            recursive_compare(yamlContent[k], whiteList[k], errors, level=f"{level}.{k}" if level else k, isComplex=isComplex)
    else:
        if isComplex:
            complex_dict_value_comparator(whiteList, yamlContent, errors, level)
        else:
            simple_dict_value_comparator(whiteList, yamlContent, errors, level)

def simple_dict_value_comparator(whiteList, yamlContent, errors, level):
    if isinstance(whiteList, dict) or isinstance(whiteList, str):
        validator = SchemaValidatorDefinition(definition=whiteList) if isinstance(whiteList, dict) else SchemaValidatorDefinition(type=whiteList)
        if validator.type in VALIDATION_DATA_TYPES:
            if yamlContent == None:
                if not validator.allowNone:
                    errors["checkMismatch"].append(getMismatchErrorStruct(level, yamlContent, validator.type, "ALLOW_NONE"))
            elif validator.type == "string":
                if not isinstance(yamlContent, str):
                    errors["checkMismatch"].append(getMismatchErrorStruct(level, yamlContent, validator.type, "TYPE"))
            elif validator.type == "number":
                if not isinstance(yamlContent, int) and not isinstance(yamlContent, float):
                    errors["checkMismatch"].append(getMismatchErrorStruct(level, yamlContent, validator.type, "TYPE"))
            elif validator.type == "boolean":
                if not isinstance(yamlContent, bool):
                    errors["checkMismatch"].append(getMismatchErrorStruct(level, yamlContent, validator.type, "TYPE"))
            elif validator.type == "object":
                if not isinstance(yamlContent, dict) and not isinstance(yamlContent, list):
                    errors["checkMismatch"].append(getMismatchErrorStruct(level, yamlContent, validator.type, "TYPE"))
            if validator.regexpPattern and not re.match(validator.regexpPattern, str(yamlContent)):
                errors["checkMismatch"].append(getMismatchErrorStruct(level, yamlContent, validator.type, "REGEXP_PATTERN", regexpPattern=validator.regexpPattern))
        else:
            raise ReferenceError(f"Unknown white list validation item for {level}: \n{dump_as_yaml_format(whiteList)}")
    else:
            raise ReferenceError(f"Unknown white list validation item for {level}: \n{dump_as_yaml_format(whiteList)}")

def complex_dict_value_comparator(whiteList, yamlContent, errors, level):
    if isinstance(whiteList, dict) or isinstance(whiteList, str):
        validator = SchemaValidatorDefinition(definition=whiteList) if isinstance(whiteList, dict) else SchemaValidatorDefinition(type=whiteList)
        if validator.type in VALIDATION_DATA_TYPES:
            paramValue = yamlContent["value"]
            paramsetText = f" in paramset \"{yamlContent['paramsetName']}\""
            if paramValue == None:
                if not validator.allowNone:
                    errors["checkMismatch"].append(getMismatchErrorStruct(level, paramValue, validator.type, "ALLOW_NONE", additionalText=paramsetText))
            elif validator.type == "string":
                if not isinstance(paramValue, str):
                    errors["checkMismatch"].append(getMismatchErrorStruct(level, paramValue, validator.type, "TYPE", additionalText=paramsetText))
            elif validator.type == "number":
                if not isinstance(paramValue, int) and not isinstance(paramValue, float):
                    errors["checkMismatch"].append(getMismatchErrorStruct(level, paramValue, validator.type, "TYPE", additionalText=paramsetText))
            elif validator.type == "boolean":
                if not isinstance(paramValue, bool):
                    errors["checkMismatch"].append(getMismatchErrorStruct(level, paramValue, validator.type, "TYPE", additionalText=paramsetText))
            elif validator.type == "object":
                if not isinstance(paramValue, dict) and not isinstance(paramValue, list):
                    errors["checkMismatch"].append(getMismatchErrorStruct(level, paramValue, validator.type, "TYPE", additionalText=paramsetText))
            if validator.regexpPattern and not re.match(validator.regexpPattern, str(paramValue)):
                errors["checkMismatch"].append(getMismatchErrorStruct(level, paramValue, validator.type, "REGEXP_PATTERN", regexpPattern=validator.regexpPattern, additionalText=paramsetText))
        else:
            raise ReferenceError(f"Unknown white list validation item for {level}: \n{dump_as_yaml_format(validator)}")
    else:
            raise ReferenceError(f"Unknown white list validation item for {level}: \n{dump_as_yaml_format(whiteList)}")

def getMismatchErrorStruct(key, value, expectedType, checkType, regexpPattern="", additionalText=""):
    struct = {
        "key": key,
        "value": value,
        "type": type(value),
        "expectedType": expectedType,
        "regexpPattern": regexpPattern,
        "checkType": checkType,
    }
    if struct["checkType"] == "TYPE":
        struct["message"] = f"{struct['key']}: type mismatch - expected '{struct['expectedType']}' got value={struct['value']} of type '{struct['type']}'{additionalText}"
    elif struct["checkType"] == "ALLOW_NONE":
        struct["message"] = f"{struct['key']}: key is present{additionalText}, but does not contain value. Please fill value or specify 'allowNone' in schema"
    elif struct["checkType"] == "REGEXP_PATTERN":
        struct["message"] = f"{struct['key']}{additionalText}: value '{struct['value']}' failed regexp '{struct['regexpPattern']}' validation"
    return struct


def checkDictIsSchemaValidator(item):
    if isinstance(item, dict):
        validator = SchemaValidatorDefinition(definition=item)
        return validator.type in VALIDATION_DATA_TYPES
    return False

def checkSchemaValidationFailed(errors):
    return len(errors["extraKeys"]) > 0 or len(errors["absentKeys"]) or len(errors["checkMismatch"])

def getSchemaValidationErrorMessage(entity, errors):
    output = ""
    if len(errors["absentKeys"]) > 0 :
        output += f"\nFollowing keys are not found in {entity}, but should be present by schema:"
        for key in errors["absentKeys"]:
            output += f"\n\t {key}"
    if len(errors["extraKeys"]) > 0 :
        output += f"\nFollowing keys are not present in schema and should be removed from {entity}:"
        for key in errors["extraKeys"]:
            output += f"\n\t {key}"
    if len(errors["checkMismatch"]) > 0 :
        output += f"\nValidation for following keys failed:"
        for checkResult in errors["checkMismatch"]:
            output += f"\n\t{checkResult['message']}"
    return output

class SchemaValidatorDefinition:
    def __init__(self, type="", definition={}):
        if type:
            self.type = type
            self.allowNone = False
            self.regexpPattern = None
        else:
            self.type = definition["type"] if "type" in definition else None
            self.allowNone = definition["allowNone"] if "allowNone" in definition else False
            self.regexpPattern = definition["regexpPattern"] if "regexpPattern" in definition else None

    def __str__(self):
        return f'SchemaValidatorDefinition(type="{self.type}", allowNone={self.allowNone}, regexpPattern="{self.regexpPattern}")'

    def __repr__(self):
        return f'SchemaValidatorDefinition(type="{self.type}", allowNone={self.allowNone}, regexpPattern="{self.regexpPattern}")'
