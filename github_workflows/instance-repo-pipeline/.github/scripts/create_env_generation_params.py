#!/usr/bin/env python3
"""
Script to create ENV_GENERATION_PARAMS JSON from environment variables.
"""

import json
import os
import sys


def create_env_generation_params():
    """Create ENV_GENERATION_PARAMS JSON from non-empty environment variables."""
    
    # List of possible environment variables
    possible_vars = [
        "SD_SOURCE_TYPE",
        "SD_VERSION", 
        "SD_DATA",
        "SD_DELTA",
        "ENV_SPECIFIC_PARAMETERS",
        "ENV_TEMPLATE_NAME"
    ]
    
    # Get only non-empty environment variables
    params = {}
    for var in possible_vars:
        value = os.getenv(var, "").strip()
        if value:  # Only add non-empty variables
            params[var] = value
            print(f"  {var}: {value}")
    
    print(f"Creating ENV_GENERATION_PARAMS with {len(params)} variables:")
    
    # Create JSON or empty string if no variables
    if params:
        env_generation_params = json.dumps(params, separators=(',', ':'))
        print(f"Generated JSON: {env_generation_params}")
    else:
        env_generation_params = ""
        print("No variables found, setting empty string")
    
    # Write to GITHUB_ENV
    github_env_file = os.getenv("GITHUB_ENV")
    if not github_env_file:
        print("Error: GITHUB_ENV variable is not set!")
        sys.exit(1)
    
    with open(github_env_file, "a", encoding="utf-8") as f:
        f.write(f"ENV_GENERATION_PARAMS={env_generation_params}\n")
    
    print("✅ ENV_GENERATION_PARAMS written to GITHUB_ENV")


if __name__ == "__main__":
    create_env_generation_params()
