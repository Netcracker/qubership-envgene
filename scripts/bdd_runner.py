#!/usr/bin/env python3
"""
BDD Runner Endpoint for qubership-envgene.

This script acts as the entrypoint for running BDD tests from external projects
using the qubership-envgene Docker image.

Configured via Environment Variables:
- BDD_GIT_URL: (Optional) URL of the Git repository containing environment data and tests.
- BDD_GIT_BRANCH: (Optional) Branch of the Git repository to checkout (default: main).
- BDD_DATA_DIR: (Optional) Path to a local directory with data (used if BDD_GIT_URL is not set).
- BDD_TESTS_PATH: (Optional) Path relative to the data dir where external step_defs are located.
                 If not provided, standard tests from /module/tests/step_defs/ are run.
- BDD_SCENARIO: (Optional) Comma-separated list of scenario names or tags to run.

Example usage in CI/CD:
docker run -e BDD_GIT_URL="https://github.com/example-org/integration-tests.git" ghcr.io/netcracker/qubership-envgene:latest python /module/scripts/bdd_runner.py
"""

import os
import sys
import subprocess
import shutil
import tempfile
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

def clone_repo(url: str, branch: str, target_dir: str):
    logging.info(f"Cloning repository {url} (branch: {branch}) into {target_dir}")
    cmd = ["git", "clone", url, target_dir]
    if branch:
        cmd.extend(["-b", branch])
        
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        logging.error(f"Failed to clone repository: {result.stderr}")
        sys.exit(1)
    logging.info("Repository cloned successfully.")

def main():
    git_url = os.environ.get("BDD_GIT_URL")
    git_branch = os.environ.get("BDD_GIT_BRANCH", "")
    data_dir = os.environ.get("BDD_DATA_DIR")
    tests_path = os.environ.get("BDD_TESTS_PATH")
    bdd_scenario = os.environ.get("BDD_SCENARIO")
    
    # We will run tests from this directory context if external data is provided
    working_dir = None
    temp_dir = None

    if git_url:
        temp_dir = tempfile.mkdtemp(prefix="bdd_data_")
        clone_repo(git_url, git_branch, temp_dir)
        working_dir = temp_dir
    elif data_dir:
        working_dir = data_dir

    if working_dir:
        logging.info(f"Using external data directory: {working_dir}")
        os.chdir(working_dir)

    # Determine which tests to run
    target_tests = tests_path
    if not target_tests:
        # Default to internal standard tests
        internal_tests_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "tests", "step_defs")
        if os.path.exists(internal_tests_path):
             target_tests = internal_tests_path
        else:
             logging.error("No BDD_TESTS_PATH specified and internal tests not found.")
             sys.exit(1)
    else:
        if working_dir and not os.path.isabs(target_tests):
            target_tests = os.path.join(working_dir, target_tests)

    logging.info(f"Starting pytest on target: {target_tests}")
    
    # Prepend the working dir to PYTHONPATH if we are using external custom tests
    # so that they can import their own conftest.py and modules easily.
    env = os.environ.copy()
    if working_dir:
        current_pythonpath = env.get("PYTHONPATH", "")
        env["PYTHONPATH"] = f"{working_dir}:{current_pythonpath}" if current_pythonpath else working_dir
        
    cmd = [sys.executable, "-m", "pytest", target_tests, "-v"]
    
    if bdd_scenario:
        scenario_expr = " or ".join([s.strip() for s in bdd_scenario.split(",") if s.strip()])
        if scenario_expr:
            cmd.extend(["-k", scenario_expr])
    
    result = subprocess.run(cmd, env=env)
    
    if temp_dir and os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
        
    if result.returncode != 0:
        logging.error(f"Tests failed with exit code {result.returncode}")
        sys.exit(result.returncode)
    else:
        logging.info("All tests passed successfully.")
        sys.exit(0)

if __name__ == "__main__":
    main()
