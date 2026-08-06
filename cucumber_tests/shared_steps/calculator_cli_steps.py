"""Step definitions for Calculator CLI BDD scenarios (UC-CC-DP-*, UC-CC-MR-*, UC-CC-HR-*, UC-CC-CR-*).

All generic Given/When/Then steps come from shared_steps and are imported in test_calculator_cli.py.
This file wires the real effective-set-generator JAR into the BDD runner.
"""
import os
import yaml
from pathlib import Path

from pytest_bdd import given

from cucumber_tests.framework.workspace import EnvGeneWorkspace

# Real JAR location (built with ./mvnw package -DskipTests)
_REPO_ROOT = Path(__file__).parent.parent.parent.resolve()
_JAR = _REPO_ROOT / "build_effective_set_generator" / "effective-set-generator" / "target" / \
       "effective-set-generator-master-SNAPSHOT-runner.jar"
# corretto-17 JAVA_HOME
_JAVA_HOME = Path.home() / ".jdks" / "corretto-17.0.10"

# mock-reg registry definition matching the purl in test SBOM files
_MOCK_REGISTRY = {
    "mock-reg": {
        "name": "mock-reg",
        "mavenConfig": {
            "targetSnapshot": "snapshot",
            "targetStaging": "staging",
            "targetRelease": "release",
            "repositoryDomainName": "http://localhost:8000/",
        },
    }
}


@given("the Calculator CLI mock validates rules")
def install_real_cli(workspace: EnvGeneWorkspace) -> None:
    """Install a wrapper that invokes the real effective-set-generator JAR."""
    if not _JAR.exists():
        raise FileNotFoundError(
            f"Real CLI JAR not found: {_JAR}\n"
            "Build it first: cd build_effective_set_generator && ./mvnw package -DskipTests -q"
        )

    java = _JAVA_HOME / "bin" / "java.exe"
    if not java.exists():
        java = _JAVA_HOME / "bin" / "java"

    # Add mock-reg to the workspace registry.yml so the real CLI can resolve
    # SBOM purl entries with registry_id=mock-reg.
    registry_file = workspace.config_dir / "registry.yml"
    existing = {}
    if registry_file.exists():
        existing = yaml.safe_load(registry_file.read_text(encoding="utf-8")) or {}
    existing.update(_MOCK_REGISTRY)
    registry_file.write_text(yaml.dump(existing), encoding="utf-8")

    # Use a filename distinct from "run_effective_set_cli.bat" so workspace.run_module()
    # cannot overwrite our wrapper when it writes its default exit-0 stub.
    #
    # The entrypoint builds the CLI command with bash-style $CI_PROJECT_DIR variables
    # (e.g. --registries=$CI_PROJECT_DIR/... --sboms-path=$CI_PROJECT_DIR/...).
    # We use a Python wrapper that performs the substitution before invoking java,
    # which works identically on Windows and Linux.
    wrapper_py = workspace.base_dir / "_real_cli_wrapper.py"
    wrapper_py.write_text(
        "import os, subprocess, sys\n"
        "ci = os.environ.get('CI_PROJECT_DIR', '')\n"
        "args = [a.replace('${CI_PROJECT_DIR}', ci).replace('$CI_PROJECT_DIR', ci) for a in sys.argv[1:]]\n"
        f'sys.exit(subprocess.call([r"{java}", "-jar", r"{_JAR}"] + args))\n',
        encoding="utf-8",
    )
    bat = workspace.base_dir / "_real_cli_wrapper.bat"
    bat.write_text(
        f'@echo off\npython "{wrapper_py}" %*\n',
        encoding="utf-8",
    )
    sh = workspace.base_dir / "_real_cli_wrapper.sh"
    sh.write_text(
        f'#!/bin/sh\nexec python "{wrapper_py}" "$@"\n',
        encoding="utf-8",
    )
    os.chmod(sh, 0o755)

    if not hasattr(workspace, "extra_env"):
        workspace.extra_env = {}
    workspace.extra_env["EFFECTIVE_SET_CLI_PATH"] = str(bat)
