from .file_helper import *
import pytest


@pytest.fixture(autouse=True)
def change_test_dir(request, monkeypatch):
    monkeypatch.chdir(request.fspath.dirname+"/../../..")

#CONST
get_parent_dir_for_dir_test_data = [
    (getAbsPath('../../../test_data/test_environments'), getAbsPath("../../../test_data")),
    (getAbsPath('../../../test_data/test_environments/index.html'), getAbsPath("../../../test_data/test_environments")),
]

@pytest.mark.parametrize("test_dir, expected_dir", get_parent_dir_for_dir_test_data)
def test_get_parent_dir_for_dir(test_dir, expected_dir):
    assert get_parent_dir_for_dir(test_dir) == expected_dir, f"Calculated parent dir does not match expected: {expected_dir}"

#CONST
getParentDirName_test_data = [
    (getAbsPath('../../../test_data/test_environments'), getAbsPath("../../..")),
    (getAbsPath('../../../test_data/test_environments/index.html'), getAbsPath("../../../test_data")),
]
@pytest.mark.parametrize("test_dir, expected_dir", getParentDirName_test_data)
def test_getParentDirName(test_dir, expected_dir):
    assert getParentDirName(test_dir) == expected_dir, f"Calculated parent dir does not match expected: {expected_dir}"
