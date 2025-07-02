# Standard library imports
import filecmp
import difflib
import os
import shutil

# Third party imports
import pytest
from ruamel.yaml import YAML
import json

# Local imports
from env_inventory_generation import handle_sd, Environment
from envgenehelper import *

# Initialize YAML parser with whitespace preservation
yaml = YAML()

# Test data configuration
TEST_CASES = [
    # (cluster_name, environment_name, test_case_name)
    ("cluster01", "env02", "TC-001-002"),
    ("cluster01", "env02", "TC-001-006")
]

# Directory paths configuration
TEST_SD_DIR = getAbsPath("../../test_data/test_handle_sd")               # Directory with test SD files
ETALON_ENV_DIR = getAbsPath("../../test_data/test_environments")  # Directory with etalon environments
OUTPUT_DIR = getAbsPath("../../tmp/test_handle_sd")                      # Directory for test output


def find_yaml_file(directory, base_name):
    logger.debug(f"Searching for YAML file:"
                f"\n\tDirectory: {directory}"
                f"\n\tBase name: {base_name}")
    
    for ext in ['yaml', 'yml']:
        file_path = os.path.join(directory, f"{base_name}.{ext}")
        if os.path.exists(file_path):
            logger.debug(f"Found YAML file: {file_path}")
            return file_path, f"{base_name}.{ext}"
    
    error_msg = f"YAML file '{base_name}' not found in directory: {directory}"
    logger.error(error_msg)
    raise FileNotFoundError(error_msg)


def load_yaml_file(file_path):
    logger.debug(f"Loading YAML file: {file_path}")
    with open(file_path, 'r') as f:
        return yaml.load(f)


def load_test_sd_data(test_case_name):
    logger.info(f"Loading test data for case: {test_case_name}")
    
    # Try both yaml and yml extensions
    test_file = None
    for ext in ['yaml', 'yml']:
        file_path = os.path.join(TEST_SD_DIR, test_case_name, f"{test_case_name}.{ext}")
        if os.path.exists(file_path):
            test_file = file_path
            break
    
    if test_file is None:
        error_msg = f"Test case file not found for {test_case_name} in {TEST_SD_DIR}/{test_case_name}/ (tried both .yaml and .yml)"
        logger.error(error_msg)
        raise FileNotFoundError(error_msg)
    
    test_data = load_yaml_file(test_file)
    
    # Extract SD parameters with defaults
    sd_data = test_data.get("SD_DATA", "{}")
    sd_source_type = test_data.get("SD_SOURCE_TYPE", "")
    sd_version = test_data.get("SD_VERSION", "")
    sd_delta = test_data.get("SD_DELTA", "")
    
    logger.info(f"Loaded SD parameters:"
               f"\n\tSD_SOURCE_TYPE: {sd_source_type}"
               f"\n\tSD_VERSION: {sd_version}"
               f"\n\tSD_DELTA: {sd_delta}")
    
    return sd_data, sd_source_type, sd_version, sd_delta


def compare_sd_files(expected_dir, actual_dir, sd_filename):
    logger.info(f"Comparing SD files:"
               f"\n\tEtalon SD dir: {expected_dir}"
               f"\n\tRendered test SD dir: {actual_dir}"
               f"\n\tFilename: {sd_filename}")
    
    # Find both files regardless of extension
    expected_file = None
    actual_file = None
    
    # Look for either .yaml or .yml in expected directory
    for ext in ['yaml', 'yml']:
        test_file = os.path.join(expected_dir, f"sd.{ext}")
        if os.path.exists(test_file):
            expected_file = test_file
            break
    
    # Look for either .yaml or .yml in actual directory
    for ext in ['yaml', 'yml']:
        test_file = os.path.join(actual_dir, f"sd.{ext}")
        if os.path.exists(test_file):
            actual_file = test_file
            break
    
    if not expected_file:
        logger.error(f"Expected SD file not found in: {expected_dir}")
        return False
        
    if not actual_file:
        logger.error(f"Generated SD file not found in: {actual_dir}")
        return False
    
    try:
        # Read files and normalize line endings
        with open(expected_file, 'r') as f1:
            expected_content = f1.read().rstrip('\n')
            expected_lines = expected_content.splitlines(keepends=True)
        with open(actual_file, 'r') as f2:
            actual_content = f2.read().rstrip('\n')
            actual_lines = actual_content.splitlines(keepends=True)
            
        # Compare contents ignoring final newline
        if expected_content != actual_content:
            # Prepare error message
            error_msg = [
                "\nSD files differ:",
                "\n=== Unified diff ===\n"
            ]
            
            # Add unified diff
            diff = difflib.unified_diff(
                expected_lines,
                actual_lines,
                fromfile="Etalon SD",
                tofile="Rendered SD",
                lineterm=''
            )
            error_msg.append('\n'.join(diff))
            
            # Add full content comparison
            error_msg.extend([
                "\n\n=== Full content comparison ===",
                "\n--- Etalon SD content ---\n",
                expected_content,
                "\n\n+++ Rendered SD content +++\n",
                actual_content
            ])
            
            # Add line count info if different
            if len(expected_lines) != len(actual_lines):
                error_msg.append(f"\n\nLine count differs: expected {len(expected_lines)}, got {len(actual_lines)} lines")
            
            # Log the complete error message
            logger.error('\n'.join(error_msg))
            return False
            
        # If we got here, files match exactly (ignoring final newline)
        logger.info("SD files match exactly (ignoring final newline)")
        return True
            
    except Exception as e:
        logger.error(f"Error comparing files: {e}")
        return False


@pytest.mark.parametrize("cluster_name, env_name, test_case_name", TEST_CASES)

def test_sd(cluster_name, env_name, test_case_name):
    """
    Test SD file generation and comparison.
    
    Args:
        cluster_name (str): Name of the cluster
        env_name (str): Name of the environment
        test_case_name (str): Name of the test case
    """
    logger.info(f"======TEST HANDLE_SD: {test_case_name}======")
    
    logger.info(f"Starting SD test:"
               f"\n\tCluster: {cluster_name}"
               f"\n\tEnvironment: {env_name}"
               f"\n\tTest case: {test_case_name}")
    
    # Load test data
    sd_data, sd_source_type, sd_version, sd_delta = load_test_sd_data(test_case_name)
    
    # Create base output directory with new structure
    base_output_path = os.path.join(OUTPUT_DIR, test_case_name)
    
    # Create Environment object for output
    env = Environment(base_output_path, cluster_name, env_name)
    
    # Source and target paths for Inventory/solution-descriptor
    source_sd_dir = os.path.join(TEST_SD_DIR, test_case_name, "Inventory", "solution-descriptor")
    target_sd_dir = os.path.join(env.env_path, "Inventory", "solution-descriptor")
    
    # Copy Inventory/solution-descriptor directory if it exists
    if os.path.exists(source_sd_dir):
        logger.info(f"Copying Inventory/solution-descriptor from {source_sd_dir} to {target_sd_dir}")
        # Create parent directory if it doesn't exist
        os.makedirs(os.path.dirname(target_sd_dir), exist_ok=True)
        # Copy the entire directory
        shutil.copytree(source_sd_dir, target_sd_dir)
    else:
        # If source doesn't exist, just create the target directory
        os.makedirs(target_sd_dir, exist_ok=True)
    
    # Generate SD file
    logger.info("Generating SD file...")
    handle_sd(env, sd_source_type, sd_version, sd_data, sd_delta)
    
    # Compare generated SD with etalon
    expected_dir = os.path.join(ETALON_ENV_DIR, cluster_name, env_name, "Inventory", "solution-descriptor")
    actual_dir = os.path.join(env.env_path, "Inventory", "solution-descriptor")
    
    # Verify files match - we don't care about the exact filename anymore
    assert compare_sd_files(expected_dir, actual_dir, "sd"), \
        "Generated SD file does not match the expected one"
        
    logger.info(f"=====SUCCESS - {test_case_name}======") 