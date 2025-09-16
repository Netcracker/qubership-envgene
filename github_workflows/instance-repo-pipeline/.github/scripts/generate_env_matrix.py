#!/usr/bin/env python3
"""
Generate environment matrix from ENV_NAMES
Creates a JSON array of environments for GitHub Actions matrix strategy
"""

import os
import sys
import json


def log(message):
    """Log messages with prefix"""
    print(f"🔧 [env_matrix] {message}")


def generate_env_matrix(env_names):
    """
    Generate environment matrix from ENV_NAMES string.
    
    Args:
        env_names (str): Comma-separated list of environment names
        
    Returns:
        str: JSON array string for GitHub Actions matrix
    """
    log("Generating environment matrix from ENV_NAMES...")
    log(f"ENV_NAMES value: '{env_names}'")
    log(f"ENV_NAMES length: {len(env_names)}")
    log(f"ENV_NAMES contains comma: {env_names.count(',')}")
    
    # Check if ENV_NAMES is empty
    if not env_names:
        log("❌ ERROR: ENV_NAMES is empty or not set!")
        log("This likely means the input processing failed.")
        log("Creating empty matrix to skip downstream jobs...")
        return "env_matrix=[]"
    
    # Validate ENV_NAMES is not just whitespace
    if not env_names.strip():
        log("❌ ERROR: ENV_NAMES contains only whitespace!")
        log("Creating empty matrix to skip downstream jobs...")
        return "env_matrix=[]"
    
    # Parse environment names
    environments = []
    for name in env_names.split(','):
        name = name.strip()
        if name:  # Skip empty names
            log(f"Processing environment: '{name}'")
            environments.append(name)
    
    # Check if any valid environments were found
    if not environments:
        log("❌ ERROR: No valid environments found in ENV_NAMES!")
        log("Creating empty matrix to skip downstream jobs...")
        return "env_matrix=[]"
    
    # Create JSON array
    matrix_json = json.dumps(environments)
    log(f"Generated matrix with {len(environments)} environment(s): {matrix_json}")
    
    return f"env_matrix={matrix_json}"


def main():
    """Main function"""
    # Get ENV_NAMES from environment variable
    env_names = os.getenv("ENV_NAMES", "")
    
    # Generate matrix
    matrix_output = generate_env_matrix(env_names)
    
    # Write to GitHub Actions output
    github_output = os.getenv("GITHUB_OUTPUT")
    if github_output:
        try:
            with open(github_output, "a", encoding="utf-8") as f:
                f.write(f"{matrix_output}\n")
            log("✅ Matrix written to GITHUB_OUTPUT")
        except Exception as e:
            log(f"⚠️  Error writing to GITHUB_OUTPUT: {e}")
            print(matrix_output)
    else:
        print(matrix_output)
        log("⚠️  GITHUB_OUTPUT not available, printing to stdout")


if __name__ == "__main__":
    main()
