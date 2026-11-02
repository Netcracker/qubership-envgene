"""Unit tests for validate_parameters - envgeneNullValue detection in parameters.

Covers the parameter scope of the use cases in
docs/use-cases/envgene-null-value-validation.md (UC-NVV-1, UC-NVV-3, UC-NVV-4).
"""
import yaml
import pytest

from .errors import ValidationError
from .params_helper import validate_parameters

TENANT = {
    "name": "dummy-tenant",
    "deployParameters": {"TENANT_KEY": "resolved"},
    "e2eParameters": {},
    "technicalConfigurationParameters": {},
}
CLOUD = {"name": "dummy-cloud", "cloudParameters": {}, "deployParameters": {}}


def _write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.dump(data), encoding="utf-8")


@pytest.fixture
def env_dir(tmp_path):
    """A minimal fully-resolved environment instance (UC-NVV-3 pre-requisites)."""
    d = tmp_path / "env"
    _write(d / "tenant.yml", TENANT)
    _write(d / "cloud.yml", CLOUD)
    (d / "Namespaces" / "core").mkdir(parents=True, exist_ok=True)
    _write(d / "Namespaces" / "core" / "namespace.yml",
           {"name": "core", "deployParameters": {"API_URL": "https://api.example.com"}})
    return d


def _error_lines(exc_info):
    return [line.strip() for line in str(exc_info.value).splitlines()]


def test_all_resolved_passes(env_dir):
    validate_parameters(str(env_dir))


def test_unresolved_deploy_parameter_blocks_pipeline(env_dir):
    ns_file = env_dir / "Namespaces" / "core" / "namespace.yml"
    ns = yaml.safe_load(ns_file.read_text(encoding="utf-8"))
    ns["deployParameters"]["API_URL"] = "envgeneNullValue"
    _write(ns_file, ns)

    with pytest.raises(ValidationError) as exc_info:
        validate_parameters(str(env_dir))

    lines = _error_lines(exc_info)
    assert lines[0] == "Error while validating parameters:"
    assert "namespace.core.deployParameters.API_URL - is not set" in lines


def test_unresolved_values_in_all_param_types_reported(env_dir):
    tenant_file = env_dir / "tenant.yml"
    tenant = yaml.safe_load(tenant_file.read_text(encoding="utf-8"))
    tenant["e2eParameters"]["E2E_KEY"] = "envgeneNullValue"
    _write(tenant_file, tenant)

    cloud_file = env_dir / "cloud.yml"
    cloud = yaml.safe_load(cloud_file.read_text(encoding="utf-8"))
    cloud["technicalConfigurationParameters"]["TC_KEY"] = "envgeneNullValue"
    _write(cloud_file, cloud)

    ns_file = env_dir / "Namespaces" / "core" / "namespace.yml"
    ns = yaml.safe_load(ns_file.read_text(encoding="utf-8"))
    ns["deployParameters"]["API_URL"] = "envgeneNullValue"
    _write(ns_file, ns)

    with pytest.raises(ValidationError) as exc_info:
        validate_parameters(str(env_dir))

    lines = _error_lines(exc_info)
    assert "dummy-tenant.e2eParameters.E2E_KEY - is not set" in lines
    assert "dummy-cloud.technicalConfigurationParameters.TC_KEY - is not set" in lines
    assert "namespace.core.deployParameters.API_URL - is not set" in lines


def test_multiple_unresolved_parameters_reported_together(env_dir):
    ns_file = env_dir / "Namespaces" / "core" / "namespace.yml"
    ns = yaml.safe_load(ns_file.read_text(encoding="utf-8"))
    ns["deployParameters"]["API_URL"] = "envgeneNullValue"
    ns["deployParameters"]["DB_HOST"] = "envgeneNullValue"
    _write(ns_file, ns)

    with pytest.raises(ValidationError) as exc_info:
        validate_parameters(str(env_dir))

    lines = _error_lines(exc_info)
    assert lines.count("Error while validating parameters:") == 1
    assert "namespace.core.deployParameters.API_URL - is not set" in lines
    assert "namespace.core.deployParameters.DB_HOST - is not set" in lines


def test_non_string_values_are_ignored(env_dir):
    ns_file = env_dir / "Namespaces" / "core" / "namespace.yml"
    ns = yaml.safe_load(ns_file.read_text(encoding="utf-8"))
    ns["deployParameters"]["PORT"] = 8080
    ns["deployParameters"]["ENABLED"] = True
    _write(ns_file, ns)

    validate_parameters(str(env_dir))


def test_matching_is_case_insensitive(env_dir):
    ns_file = env_dir / "Namespaces" / "core" / "namespace.yml"
    ns = yaml.safe_load(ns_file.read_text(encoding="utf-8"))
    ns["deployParameters"]["API_URL"] = "EnvGeneNullValue"
    _write(ns_file, ns)

    with pytest.raises(ValidationError) as exc_info:
        validate_parameters(str(env_dir))

    assert "namespace.core.deployParameters.API_URL - is not set" in _error_lines(exc_info)
