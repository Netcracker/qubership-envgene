import os
import json
import re
from pathlib import Path
import pytest

from envgene_shared.utils.file_utils import *


def test_file_operations_and_paths(tmp_path, monkeypatch):
    test_file = tmp_path / "test.json"
    data = {"key": "value"}
    test_file.write_text(json.dumps(data))
    monkeypatch.setenv('CI_PROJECT_DIR', str(tmp_path))

    assert check_file_exists(str(test_file)) is True
    assert check_file_exists(str(tmp_path / "missing.json")) is False

    assert openJson(str(test_file)) == data

    assert getRelPath(str(test_file)) == "test.json"
    assert getRelPath(str(test_file), start_path=str(tmp_path)) == "test.json"


def test_get_files_with_filter(tmp_path):
    sub_dir = tmp_path / "sub"
    sub_dir.mkdir()
    file1 = tmp_path / "match.txt"
    file2 = sub_dir / "skip.log"
    file1.touch()
    file2.touch()

    dummy_filter = lambda fp: fp.endswith('.txt')
    result = get_files_with_filter(str(tmp_path), dummy_filter)

    assert result == {str(file1)}


@pytest.mark.parametrize("path, expected", [
    ("/configuration/credentials.yaml", True),   # Matches all criteria
    ("/environments/Credentials/any.yml", True), # Matches TARGET_DIR_REGEX
    ("/configuration/normal.yaml", False),       # Valid extension/parent but no name match
    ("/configuration/credentials.txt", False),    # Invalid extension (.txt)
    ("/wrong_dir/credentials.yaml", False),      # Invalid parent directory structure
])
def test_is_cred_file(path, expected):
    """Parametrized test to hit every conditional branch in is_cred_file."""
    assert is_cred_file(path) == expected