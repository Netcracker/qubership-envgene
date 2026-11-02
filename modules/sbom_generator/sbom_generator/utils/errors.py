""" Module with custom errors """

import yaml
from pydantic_core import ValidationError


class NotFoundException(Exception):
    def __init__(self, msg='', *args):
        super().__init__(msg, *args)


class IllegalStateException(Exception):
    def __init__(self, msg='', *args):
        super().__init__(msg, *args)


class IllegalArgumentException(Exception):
    def __init__(self, msg='', *args):
        super().__init__(msg, *args)


def format_loc(loc: tuple[int | str, ...]) -> str:
    parts = []
    for item in loc:
        if isinstance(item, int):
            parts.append(f"[{item}]")
        else:
            parts.append(str(item))
    return ".".join(parts).replace(".[", "[")


def convert_errors(e: ValidationError, type_obj: str, src_data="", src_path="") -> list[dict]:
    new_errors: list = []
    for error in e.errors():
        input_data = error.get("input", '')
        message = error.get("msg", '')
        loc = error.get("loc", '')
        source = ""
        if src_path:
            source = src_path
        elif src_data:
            source = str(src_data)
        new_structure = {
            "validated_object_type": type_obj,
            "validated_object_location_or_object": source,
            "failed_attribute_path_in_the_object": format_loc(loc),
            "failed_attribute_value": input_data,
            "validation_error_message": message,
        }
        new_errors.append(new_structure)
    return new_errors


class PydanticValidationError(Exception):
    def __init__(self, original: ValidationError, type_obj: str, src_data="", src_path=""):
        self.errors = convert_errors(original, type_obj, src_data, src_path)
        super().__init__(f"{len(self.errors)} validation errors")

    def __str__(self):
        return "\n" + yaml.dump(self.errors, indent=2, sort_keys=False)
