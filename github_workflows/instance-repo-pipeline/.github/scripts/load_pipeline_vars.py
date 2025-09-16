#!/usr/bin/env python3
"""
Simple utility to load variables from pipeline_vars.yaml file.
All variables must be of string type - validation will fail otherwise.
"""

import os
import json
from typing import Dict, Any, Optional


def validate_string_type(value: str, var_name: str) -> None:
    """
    Validate that the value is a proper string type.
    
    Args:
        value: The value to validate
        var_name: Name of the variable for error reporting
        
    Raises:
        ValueError: If the value is not a valid string type
    """
    # Check for common non-string patterns
    if value.lower() in ["true", "false"] and not (value.startswith('"') or value.startswith("'")):
        raise ValueError(f"Variable '{var_name}' has boolean value '{value}' without quotes. All variables must be strings. Use '{var_name}: \"{value}\"' instead.")
    
    # Check for unquoted numbers
    try:
        float(value)
        if not (value.startswith('"') or value.startswith("'")):
            raise ValueError(f"Variable '{var_name}' has numeric value '{value}' without quotes. All variables must be strings. Use '{var_name}: \"{value}\"' instead.")
    except ValueError:
        pass  # Not a number, which is fine
    
    # Check for unquoted JSON objects/arrays
    if (value.startswith('{') or value.startswith('[')) and not (value.startswith('"') or value.startswith("'")):
        raise ValueError(f"Variable '{var_name}' has JSON value '{value}' without quotes. All variables must be strings. Use '{var_name}: \"{value}\"' instead.")


def parse_pipeline_vars_yaml(file_path: str = ".github/pipeline_vars.yaml") -> Dict[str, str]:
    """
    Parse pipeline_vars.yaml file and extract commented variables.
    Validates that all variables are of string type.
    
    Args:
        file_path: Path to the pipeline_vars.yaml file
        
    Returns:
        Dictionary with variable names and their string values
        
    Raises:
        ValueError: If any variable is not of string type
    """
    variables = {}
    errors = []
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            # Skip empty lines and commented lines
            if not line or line.startswith("#"):
                continue
            
            # Use the line content directly (no comment prefix to remove)
            content = line
            
            # Check if it's a variable assignment
            if ":" in content:
                key, value = content.split(":", 1)
                key = key.strip()
                value = value.strip()
                
                # Validate string type before processing
                try:
                    validate_string_type(value, key)
                except ValueError as e:
                    errors.append(f"Line {line_num}: {str(e)}")
                    continue
                
                # Remove quotes if present
                if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
                    value = value[1:-1]
                
                variables[key] = value
                print(f"Loaded variable: {key} = {value}")
    
    except FileNotFoundError:
        print(f"Warning: pipeline_vars.yaml file not found at {file_path}")
    except Exception as e:
        print(f"Error parsing pipeline_vars.yaml: {e}")
    
    # If there were validation errors, raise them
    if errors:
        error_message = "String type validation failed:\n" + "\n".join(errors)
        raise ValueError(error_message)
    
    return variables


def get_pipeline_var(var_name: str, default: str = "", file_path: str = ".github/pipeline_vars.yaml") -> str:
    """
    Get a specific pipeline variable by name.
    
    Args:
        var_name: Name of the variable to retrieve
        default: Default value if variable is not found
        file_path: Path to the pipeline_vars.yaml file
        
    Returns:
        Variable value as string, or default if not found
        
    Raises:
        ValueError: If any variable in the file is not of string type
    """
    variables = parse_pipeline_vars_yaml(file_path)
    return variables.get(var_name, default)


def get_pipeline_vars(file_path: str = ".github/pipeline_vars.yaml") -> Dict[str, str]:
    """
    Get all pipeline variables as a dictionary.
    
    Args:
        file_path: Path to the pipeline_vars.yaml file
        
    Returns:
        Dictionary with all pipeline variables
        
    Raises:
        ValueError: If any variable in the file is not of string type
    """
    return parse_pipeline_vars_yaml(file_path)


def main():
    """
    Main function for command-line usage.
    """
    import sys
    
    try:
        if len(sys.argv) > 1:
            var_name = sys.argv[1]
            value = get_pipeline_var(var_name)
            print(value)
        else:
            # Print all variables and write to github_output
            variables = get_pipeline_vars()
            
            # Write to github_env
            github_env = os.getenv("GITHUB_ENV")
            
            if github_env:
                # Read existing variables from GITHUB_ENV file to avoid overriding
                existing_env_vars = {}
                try:
                    with open(github_env, "r", encoding="utf-8") as f:
                        for line in f:
                            line = line.strip()
                            if "=" in line:
                                key_existing, value_existing = line.split("=", 1)
                                existing_env_vars[key_existing] = value_existing
                except FileNotFoundError:
                    pass
                
                defaults_set = 0
                with open(github_env, "a", encoding="utf-8") as f:
                    for key, value in variables.items():
                        # Check both os.getenv and GITHUB_ENV file
                        existing_os_value = os.getenv(key)
                        existing_file_value = existing_env_vars.get(key)
                        
                        if (existing_os_value is None or existing_os_value == "") and (existing_file_value is None or existing_file_value == ""):
                            f.write(f"{key}={value}\n")
                            defaults_set += 1
                
                if defaults_set > 0:
                    print(f"✅ Set {defaults_set} default values from pipeline_vars.yaml")
                
    except ValueError as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
