#!/usr/bin/env python3
import os
import sys


def sanitize_value(value):
    """Sanitize and convert value to string"""
    if isinstance(value, str):
        return value.strip()
    return str(value)


def parse_api_input(api_input_string):
    """Parse API input string as key=value pairs"""
    variables = {}

    if not api_input_string or api_input_string.strip() == "":
        return variables

    # Parse as key=value pairs
    lines = api_input_string.split("\n")
    for line in lines:
        line = line.strip()
        if "=" in line and not line.startswith("#"):
            # Pre-process line to handle spaces around = sign
            if " = " in line:
                line = line.replace(" = ", "=")
            
            # Simple split on first =
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip()
            
            # Do NOT remove quotes - values might be JSON strings that need their quotes!
            
            variables[key] = sanitize_value(value)

    return variables


def validate_variable(key, value):
    """Validate variable - all variables are treated as strings"""
    return str(value)


def main():
    api_input = os.getenv("GITHUB_PIPELINE_API_INPUT", "")

    if not api_input:
        print("❌ No GITHUB_PIPELINE_API_INPUT provided, skipping API input processing")
        return

    print(f"✅ Processing GITHUB_PIPELINE_API_INPUT ({len(api_input)} chars)")
    print(f"📝 Full GITHUB_PIPELINE_API_INPUT content:")
    print(f"'{api_input}'")
    print("--- End of content ---")

    # Parse the API input string
    variables = parse_api_input(api_input)

    if not variables:
        print("No variables parsed from GITHUB_PIPELINE_API_INPUT")
        print("This could be due to invalid JSON/YAML format or empty input")
        return

    github_env_file = os.getenv("GITHUB_ENV")

    if not github_env_file:
        print("Error: GITHUB_ENV variable is not set!")
        sys.exit(1)

    print(f"📋 Parsed variables from API input:")
    for key, value in variables.items():
        print(f"  {key} = {value}")

    with open(github_env_file, "a", encoding="utf-8") as env_file:
        # First, preserve the original GITHUB_PIPELINE_API_INPUT
        env_file.write(f"GITHUB_PIPELINE_API_INPUT={api_input}\n")
        
        # Then write parsed variables
        for key, value in variables.items():
            validated_value = validate_variable(key, value)
            env_file.write(f"{key}={validated_value}\n")

    print(f"✅ Processed {len(variables)} variables from API input and preserved original GITHUB_PIPELINE_API_INPUT")


if __name__ == "__main__":
    main()
