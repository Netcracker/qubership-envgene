#!/usr/bin/env python3
import sys
import yaml
import json
import os


def getenv_and_log(key, default=""):
    value = os.getenv(key, default)
    print(f"{key}: {value}")
    return value


def sanitize_json(value):
    try:
        json_object = json.loads(value)
        return json.dumps(json_object)
    except (json.JSONDecodeError, TypeError):
        raise ValueError(f"Invalid JSON provided: {value}")


def convert_to_github_env(value):
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, str) and value.lower() in ["true", "false"]:
        return value.lower()
    return value


def validate_boolean(value, key):
    if isinstance(value, bool) or (isinstance(value, str) and value.lower() in ["true", "false"]):
        return convert_to_github_env(value)
    raise ValueError(f"{key} should be a boolean (true/false). Got: {value}")


def validate_json(value, key):
    try:
        if isinstance(value, str):
            value = value.strip().replace('\n', ' ')
        parsed_json = json.loads(value)
        return json.dumps(parsed_json)
    except (json.JSONDecodeError, TypeError):
        raise ValueError(f"{key} must be a valid JSON object")


def validate_string(value, key):
    if isinstance(value, str):
        return value
    raise ValueError(f"{key} must be a string. Got {type(value).__name__}")


def main():
    if len(sys.argv) < 2:
        print("Usage: load_env_params.py <yaml_config_file>")
        sys.exit(1)

    config_file = sys.argv[1]

    with open(config_file, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)

    github_env_file = os.getenv('GITHUB_ENV')
    github_output_file = os.getenv('GITHUB_OUTPUT')

    if not github_env_file or not github_output_file:
        print("Error: GITHUB_ENV or GITHUB_OUTPUT variable is not set!")
        sys.exit(1)

    validators = {
        "ENV_TEMPLATE_TEST": validate_boolean,
        "ENV_TEMPLATE_NAME": validate_string,
        "SD_DATA": validate_json,
        "SD_VERSION": validate_string,
        "SD_REPO_MERGE_MODE": validate_string,
        "SD_SOURCE_TYPE": validate_string,
        "SD_DELTA": validate_boolean,
        "ENV_SPECIFIC_PARAMETERS": validate_json,
    }

    validated_data = {}

    for key, validator in validators.items():
        raw_value = data.get(key, "")

        if validator == validate_boolean:
            if isinstance(raw_value, bool):
                validated_data[key] = convert_to_github_env(raw_value)
            elif isinstance(raw_value, str) and raw_value.lower() in ["true", "false"]:
                validated_data[key] = raw_value.lower()
            else:
                raise ValueError(f"{key} should be boolean (true/false). Got: {raw_value}")
        elif validator == validate_json:
            if not raw_value:
                validated_data[key] = "{}"
            else:
                validated_data[key] = validate_json(raw_value, key)
        else:  # string
            validated_data[key] = validate_string(raw_value, key)

    with open(github_env_file, 'a', encoding='utf-8') as env_file, \
            open(github_output_file, 'a', encoding='utf-8') as output_file:

        for key, value in validated_data.items():
            env_file.write(f"{key}={convert_to_github_env(value)}\n")
            output_file.write(f"{key}={convert_to_github_env(value)}\n")

        env_generation_params = {
            "SD_SOURCE_TYPE": validated_data["SD_SOURCE_TYPE"],
            "SD_VERSION": validated_data["SD_VERSION"],
            "SD_DATA": validated_data["SD_DATA"],
            "SD_DELTA": validated_data["SD_DELTA"],
            "SD_REPO_MERGE_MODE": validated_data["SD_REPO_MERGE_MODE"],
            "ENV_SPECIFIC_PARAMETERS": json.loads(validated_data.get("ENV_SPECIFIC_PARAMETERS", "{}")),
            "ENV_TEMPLATE_NAME": data.get("ENV_TEMPLATE_NAME", "")
        }

        env_file.write(f'ENV_GENERATION_PARAMS={json.dumps(env_generation_params)}\n')
        output_file.write(f'ENV_GENERATION_PARAMS={json.dumps(env_generation_params)}\n')


if __name__ == "__main__":
    main()