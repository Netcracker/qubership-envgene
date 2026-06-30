"""
Pytest configuration (conftest.py) for an external project.

Place this file in your project's test root directory (e.g., tests/conftest.py).
This file registers the Workspace fixture which is required by all the 
unified pipeline steps from EnvGene.
"""

import pytest

from .workspace_template import ExternalWorkspace

@pytest.fixture
def workspace(tmp_path):
    """
    Provides the Workspace instance for all shared steps.
    The unified steps expect a fixture named exactly 'workspace'.
    `tmp_path` is a built-in pytest fixture that provides a temporary directory for each test.
    """
    return ExternalWorkspace(tmp_path)
