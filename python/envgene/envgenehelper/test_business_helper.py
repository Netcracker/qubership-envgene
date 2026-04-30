from .business_helper import getEnvDefinition
import pytest
import logging

# Enable logging ONLY for this file
@pytest.fixture(autouse=True)
def enable_logging():
    logging.basicConfig(level=logging.INFO, force=True)
    logging.info("getEnvDefinition method of business_helper.py is being tested...")


test_logger = logging.getLogger("test_logger")


# ===================== TEST CASES =====================
test_cases = [
    {
        "name": "Inventory Missing",
        "input_yaml": {"applications": []},
        "file_exists": True,
        "expected_inventory": {},
        "expect_exception": None,
        "env_dir": "test_env",
    },
    {
        "name": "Inventory Exists",
        "input_yaml": {"inventory": {"a": 1}},
        "file_exists": True,
        "expected_inventory": {"a": 1},
        "expect_exception": None,
        "env_dir": "test_env",
    },
    {
        "name": "File Not Found",
        "input_yaml": None,
        "file_exists": False,
        "expected_inventory": None,
        "expect_exception": ReferenceError,
        "env_dir": "test_env",
    },
    {
        "name": "Env Dir Fallback",
        "input_yaml": {"applications": []},
        "file_exists": True,
        "expected_inventory": {},
        "expect_exception": None,
        "env_dir": None,
    },
    {
        "name": "Empty YAML",
        "input_yaml": {},
        "file_exists": True,
        "expected_inventory": {},
        "expect_exception": None,
        "env_dir": "test_env",
    },
]


# ===================== PARAMETRIZED TEST =====================
@pytest.mark.parametrize(
    "case",
    test_cases,
    ids=[case["name"] for case in test_cases]
)
def test_get_env_definition(case, monkeypatch):
    test_logger.info(f"\n===== {case['name']} =====")
    test_logger.info("INPUT YAML: %s", case["input_yaml"])

    # Mock path
    monkeypatch.setattr(
        "envgenehelper.business_helper.getEnvDefinitionPath",
        lambda x: "dummy_path"
    )

    # Mock file existence
    monkeypatch.setattr(
        "envgenehelper.business_helper.check_file_exists",
        lambda x: case["file_exists"]
    )

    # Mock YAML loading
    if case["input_yaml"] is not None:
        monkeypatch.setattr(
            "envgenehelper.business_helper.openYaml",
            lambda x: case["input_yaml"].copy()
        )

    # Mock env fallback
    monkeypatch.setattr(
        "envgenehelper.business_helper.get_current_env_dir_from_env_vars",
        lambda: "env_from_vars"
    )

    # ===================== EXECUTION =====================
    if case["expect_exception"]:
        with pytest.raises(case["expect_exception"]):
            getEnvDefinition(case["env_dir"])
        return

    result = getEnvDefinition(case["env_dir"])

    test_logger.info("RESULT: %s", result)

    # ===================== ASSERTIONS =====================
    assert "inventory" in result
    assert result["inventory"] == case["expected_inventory"]

    # Special case: ensure inventory not overridden
    if case["name"] == "Inventory Exists":
        assert result["inventory"] == case["input_yaml"]["inventory"]
