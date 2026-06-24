"""
Pytest configuration (conftest.py) for an external project.

Place this file in your project's test root directory (e.g., tests/e2e/conftest.py).
"""

import pytest

from .workspace_template import ExternalWorkspace

@pytest.fixture
def workspace(tmp_path):
    """Provides the Workspace instance for all shared steps."""
    return ExternalWorkspace(tmp_path)
