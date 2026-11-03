import pytest

from build_env.build_env import validate_applications
from envgenehelper import open_current_env_instance_store


def test_invalid_application_fails(tmp_path):
    env_dir = tmp_path / "env"
    applications = env_dir / "Namespaces" / "ns" / "Applications"
    with open_current_env_instance_store(env_dir) as store:
        store.put(applications / "good.yml", {"name": "good", "deployParameters": {},
                                              "technicalConfigurationParameters": {}})
        store.put(applications / "bad.yml", {"name": 1, "deployParameters": {},
                                             "technicalConfigurationParameters": {}})

        with pytest.raises(ValueError):
            validate_applications(applications)


def test_valid_applications_pass(tmp_path):
    env_dir = tmp_path / "env"
    applications = env_dir / "Namespaces" / "ns" / "Applications"
    with open_current_env_instance_store(env_dir) as store:
        store.put(applications / "good.yml", {"name": "good", "deployParameters": {},
                                              "technicalConfigurationParameters": {}})

        validate_applications(applications)
