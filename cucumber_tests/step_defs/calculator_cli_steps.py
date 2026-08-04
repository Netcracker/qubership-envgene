"""Step definitions for Calculator CLI BDD scenarios (UC-CC-DP-*, UC-CC-MR-*, UC-CC-HR-*, UC-CC-CR-*).

All generic Given/When/Then steps come from shared_steps and are imported in test_calculator_cli.py.
This file installs a smarter Calculator CLI mock that validates the rules the real Java CLI enforces.
"""
import os
from pathlib import Path

from pytest_bdd import given

from cucumber_tests.framework.workspace import EnvGeneWorkspace

# Path to the smart CLI mock script (lives next to this file)
_MOCK_SCRIPT = Path(__file__).parent / "_calculator_cli_mock.py"


# ── Given step: install smart CLI mock ────────────────────────────────────────

@given("the Calculator CLI mock validates rules")
def install_smart_cli_mock(workspace: EnvGeneWorkspace) -> None:
    _install_cli_mock(workspace)


def _install_cli_mock(workspace: EnvGeneWorkspace) -> None:
    mock_py = _MOCK_SCRIPT.resolve()

    # Use distinct filenames so run_module() cannot overwrite them when it
    # re-creates the default "run_effective_set_cli.bat" mock at test time.
    bat = workspace.base_dir / "_smart_cli_mock.bat"
    bat.write_text(
        f'@echo off\npython "{mock_py}" %*\n',
        encoding="utf-8",
    )
    sh = workspace.base_dir / "_smart_cli_mock.sh"
    sh.write_text(
        f'#!/bin/sh\nexec python "{mock_py}" "$@"\n',
        encoding="utf-8",
    )
    os.chmod(sh, 0o755)

    if not hasattr(workspace, "extra_env"):
        workspace.extra_env = {}
    workspace.extra_env["EFFECTIVE_SET_CLI_PATH"] = str(bat)
