from .business_helper import getEnvDefinition
import pytest
import logging


# Enable logging ONLY for this file
@pytest.fixture(autouse=True)
def enable_logging():
    logging.basicConfig(level=logging.INFO, force=True)


test_logger = logging.getLogger("test_logger")


# ===================== TEST 1 =====================
def test_inventory_added_when_missing(monkeypatch):
    input_yaml = {"applications": []}

    monkeypatch.setattr(
        "envgenehelper.business_helper.getEnvDefinitionPath",
        lambda x: "dummy_path"
    )
    monkeypatch.setattr(
        "envgenehelper.business_helper.check_file_exists",
        lambda x: True
    )
    monkeypatch.setattr(
        "envgenehelper.business_helper.openYaml",
        lambda x: input_yaml.copy()
    )

    test_logger.info("\n===== TEST 1: Inventory Missing =====")
    test_logger.info("BEFORE: %s", input_yaml)
    test_logger.info("Inventory BEFORE? %s", "inventory" in input_yaml)

    result = getEnvDefinition("test_env")

    test_logger.info("AFTER: %s", result)
    test_logger.info("Inventory AFTER? %s", "inventory" in result)
    test_logger.info("Inventory content: %s", result.get("inventory"))

    assert "inventory" in result
    assert result["inventory"] == {}


# ===================== TEST 2 =====================
def test_inventory_not_overridden(monkeypatch):
    input_yaml = {"inventory": {"a": 1}}

    monkeypatch.setattr(
        "envgenehelper.business_helper.getEnvDefinitionPath",
        lambda x: "dummy_path"
    )
    monkeypatch.setattr(
        "envgenehelper.business_helper.check_file_exists",
        lambda x: True
    )
    monkeypatch.setattr(
        "envgenehelper.business_helper.openYaml",
        lambda x: input_yaml
    )

    test_logger.info("\n===== TEST 2: Inventory Exists =====")
    test_logger.info("BEFORE: %s", input_yaml)

    result = getEnvDefinition("test_env")

    test_logger.info("AFTER: %s", result)
    test_logger.info("Inventory unchanged? %s", result["inventory"] == input_yaml["inventory"])

    assert result == input_yaml
    assert result["inventory"] is input_yaml["inventory"]


# ===================== TEST 3 =====================
def test_file_not_found(monkeypatch):
    monkeypatch.setattr(
        "envgenehelper.business_helper.getEnvDefinitionPath",
        lambda x: "dummy_path"
    )
    monkeypatch.setattr(
        "envgenehelper.business_helper.check_file_exists",
        lambda x: False
    )

    test_logger.info("\n===== TEST 3: File Not Found =====")

    with pytest.raises(ReferenceError) as exc:
        getEnvDefinition("test_env")

    test_logger.info("Exception: %s", str(exc.value))


# ===================== TEST 4 =====================
def test_env_dir_fallback(monkeypatch):
    input_yaml = {"applications": []}

    monkeypatch.setattr(
        "envgenehelper.business_helper.get_current_env_dir_from_env_vars",
        lambda: "env_from_vars"
    )
    monkeypatch.setattr(
        "envgenehelper.business_helper.getEnvDefinitionPath",
        lambda x: "dummy_path"
    )
    monkeypatch.setattr(
        "envgenehelper.business_helper.check_file_exists",
        lambda x: True
    )
    monkeypatch.setattr(
        "envgenehelper.business_helper.openYaml",
        lambda x: input_yaml.copy()
    )

    test_logger.info("\n===== TEST 4: env_dir Fallback =====")
    test_logger.info("env_dir BEFORE: None")

    result = getEnvDefinition(None)

    test_logger.info("AFTER: %s", result)
    test_logger.info("Inventory added? %s", "inventory" in result)

    assert "inventory" in result


# ===================== TEST 5 =====================
def test_empty_yaml(monkeypatch):
    input_yaml = {}

    monkeypatch.setattr(
        "envgenehelper.business_helper.getEnvDefinitionPath",
        lambda x: "dummy"
    )
    monkeypatch.setattr(
        "envgenehelper.business_helper.check_file_exists",
        lambda x: True
    )
    monkeypatch.setattr(
        "envgenehelper.business_helper.openYaml",
        lambda x: input_yaml.copy()
    )

    test_logger.info("\n===== TEST 5: Empty YAML =====")
    test_logger.info("BEFORE: %s", input_yaml)

    result = getEnvDefinition("test_env")

    test_logger.info("AFTER: %s", result)
    test_logger.info("Inventory added? %s", "inventory" in result)
    test_logger.info("Inventory content: %s", result.get("inventory"))

    assert result["inventory"] == {}
