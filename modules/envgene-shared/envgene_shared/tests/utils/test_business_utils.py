import pytest

from envgene_shared.utils.business_utils import to_bool


@pytest.mark.parametrize("value, expected", [
    (True, True), ("true", True), ("True", True), ("TRUE", True),
    (False, False), ("false", False), ("False", False), ("FALSE", False),
    (" true ", True), ("\tFalse\n", False),
    (None, False), ("", False), ("yes", False), (1, False),
])
def test_to_bool(value, expected):
    assert to_bool(value) is expected


@pytest.mark.parametrize("value, expected", [
    ("true", True), ("false", False), ("FALSE", False), (None, True), ("", True), ("yes", True),
])
def test_to_bool_default_true(value, expected):
    assert to_bool(value, default=True) is expected
