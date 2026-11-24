import tempfile
from pathlib import Path
from unittest.mock import patch

from envgenehelper import openYaml
from ruamel.yaml import YAML

from build_env.deployment_profile import (
    DEPLOYMENT_PROFILE_NAME,
    append_override_to_env_definition,
    apply_deployment_profile,
    build_deployment_profile_override,
    deployed_entities,
    write_deployment_profile_override,
)
from build_env.main import cleanup_resulting_dir


def _write_plan(env_dir: Path, file_name: str, versions: list[str], deploy_postfix: str = "bss",
                namespace: str = "bss-pl") -> None:
    inventory = env_dir / "Inventory"
    inventory.mkdir(parents=True, exist_ok=True)
    entries = [{"wave": 0, "version": version, "deployPostfix": deploy_postfix, "namespace": namespace}
               for version in versions]
    with (inventory / file_name).open("w", encoding="utf-8") as f:
        YAML().dump(entries, f)


def _write_env_definition(env_dir: Path, profiles: dict) -> Path:
    inventory = env_dir / "Inventory"
    inventory.mkdir(parents=True, exist_ok=True)
    env_definition_path = inventory / "env_definition.yml"
    with env_definition_path.open("w", encoding="utf-8") as f:
        YAML().dump({"envTemplate": {"name": "simple", "envSpecificResourceProfiles": profiles}}, f)
    return env_definition_path


def _add_namespace(env_dir: Path, folder: str, name: str | None = None) -> None:
    namespace_dir = env_dir / "Namespaces" / folder
    namespace_dir.mkdir(parents=True, exist_ok=True)
    with (namespace_dir / "namespace.yml").open("w", encoding="utf-8") as f:
        YAML().dump({"name": name or folder}, f)


def _override_path(env_dir: Path) -> Path:
    return env_dir / "Inventory" / "resource_profiles" / f"{DEPLOYMENT_PROFILE_NAME}.yml"


class TestDeploymentProfileOverride:
    def test_step_creates_override_with_named_baseline(self):
        with tempfile.TemporaryDirectory(prefix="deployment-profile-") as tmp:
            env_dir = Path(tmp)
            _write_plan(env_dir, "deploy-plan.yml", ["billing:1.0.0", "crm:2.0.0"])

            override = build_deployment_profile_override(deployed_entities(env_dir), "prod")

            assert override["name"] == DEPLOYMENT_PROFILE_NAME
            assert override["applications"] == [
                {"name": "billing", "baseline": "prod", "services": []},
                {"name": "crm", "baseline": "prod", "services": []},
            ]

    def test_one_application_deployed_twice_is_named_once(self):
        with tempfile.TemporaryDirectory(prefix="deployment-profile-") as tmp:
            env_dir = Path(tmp)
            _write_plan(env_dir, "deploy-plan.yml", ["billing:1.0.0", "billing:2.0.0"])

            override = build_deployment_profile_override(deployed_entities(env_dir), "prod")

            assert [app["name"] for app in override["applications"]] == ["billing"]

    def test_delta_deploy_plan_is_used_when_present(self):
        with tempfile.TemporaryDirectory(prefix="deployment-profile-") as tmp:
            env_dir = Path(tmp)
            _write_plan(env_dir, "deploy-plan.yml", ["billing:1.0.0", "crm:2.0.0"])
            _write_plan(env_dir, "delta-deploy-plan.yml", ["crm:2.0.0"])

            override = build_deployment_profile_override(deployed_entities(env_dir), "prod")

            assert [app["name"] for app in override["applications"]] == ["crm"]

    def test_delta_deploy_plan_without_applications_falls_back_to_deploy_plan(self):
        with tempfile.TemporaryDirectory(prefix="deployment-profile-") as tmp:
            env_dir = Path(tmp)
            _write_plan(env_dir, "deploy-plan.yml", ["billing:1.0.0", "crm:2.0.0"])
            _write_plan(env_dir, "delta-deploy-plan.yml", [])

            override = build_deployment_profile_override(deployed_entities(env_dir), "prod")

            assert [app["name"] for app in override["applications"]] == ["billing", "crm"]

    def test_run_without_deploy_plan_generates_no_override(self):
        with tempfile.TemporaryDirectory(prefix="deployment-profile-") as tmp:
            env_dir = Path(tmp)

            assert deployed_entities(env_dir) is None
            assert apply_deployment_profile(env_dir, "prod") is None
            assert not _override_path(env_dir).exists()

    def test_run_with_an_empty_plan_and_no_deploy_plan_generates_no_override(self):
        with tempfile.TemporaryDirectory(prefix="deployment-profile-") as tmp:
            env_dir = Path(tmp)
            _write_plan(env_dir, "delta-deploy-plan.yml", [])

            assert apply_deployment_profile(env_dir, "prod") is None
            assert not _override_path(env_dir).exists()

    def test_run_without_deploy_plan_touches_nothing(self):
        with tempfile.TemporaryDirectory(prefix="deployment-profile-") as tmp:
            env_dir = Path(tmp)
            _add_namespace(env_dir, "bss-pl")
            env_definition_path = _write_env_definition(env_dir, {"bss-pl": ["hand-written"]})
            before = env_definition_path.read_bytes()

            assert apply_deployment_profile(env_dir, "prod") is None

            assert not _override_path(env_dir).exists()
            assert env_definition_path.read_bytes() == before

    def test_second_run_updates_existing_override(self):
        with tempfile.TemporaryDirectory(prefix="deployment-profile-") as tmp:
            env_dir = Path(tmp)
            _write_plan(env_dir, "deploy-plan.yml", ["billing:1.0.0"])
            write_deployment_profile_override(env_dir, deployed_entities(env_dir), "prod")
            _write_plan(env_dir, "deploy-plan.yml", ["billing:1.0.0", "crm:2.0.0"])

            path = write_deployment_profile_override(env_dir, deployed_entities(env_dir), "prod")

            assert path == _override_path(env_dir)
            assert sorted(list(Path(path).parent.iterdir())) == [path]
            override = openYaml(path, safe_load=True)
            assert [app["name"] for app in override["applications"]] == ["billing", "crm"]

    def test_run_with_another_profile_name_rewrites_shared_override(self):
        with tempfile.TemporaryDirectory(prefix="deployment-profile-") as tmp:
            env_dir = Path(tmp)
            _write_plan(env_dir, "deploy-plan.yml", ["billing:1.0.0"])
            write_deployment_profile_override(env_dir, deployed_entities(env_dir), "prod")

            path = write_deployment_profile_override(env_dir, deployed_entities(env_dir), "prod2")

            assert path == _override_path(env_dir)
            assert sorted(list(Path(path).parent.iterdir())) == [path]
            override = openYaml(path, safe_load=True)
            assert [app["baseline"] for app in override["applications"]] == ["prod2"]

    def test_override_written_by_hand_under_the_reserved_name_is_replaced_with_a_warning(self):
        with tempfile.TemporaryDirectory(prefix="deployment-profile-") as tmp:
            env_dir = Path(tmp)
            _write_plan(env_dir, "deploy-plan.yml", ["billing:1.0.0"])
            hand_written = _override_path(env_dir)
            hand_written.parent.mkdir(parents=True, exist_ok=True)
            hand_written.write_text("name: deployment-profile\napplications:\n- name: billing\n  baseline: stage\n",
                                    encoding="utf-8")

            with patch("build_env.deployment_profile.logger") as logger:
                path = write_deployment_profile_override(env_dir, deployed_entities(env_dir), "prod")

            logger.warning.assert_called_once()
            assert path == hand_written
            assert openYaml(path, safe_load=True)["applications"][0]["baseline"] == "prod"


    def test_rerun_rewrites_generated_override_without_a_warning(self):
        with tempfile.TemporaryDirectory(prefix="deployment-profile-") as tmp:
            env_dir = Path(tmp)
            _write_plan(env_dir, "deploy-plan.yml", ["billing:1.0.0"])
            write_deployment_profile_override(env_dir, deployed_entities(env_dir), "prod")

            with patch("build_env.deployment_profile.logger") as logger:
                path = write_deployment_profile_override(env_dir, deployed_entities(env_dir), "prod2")

            logger.warning.assert_not_called()
            assert openYaml(path, safe_load=True)["applications"][0]["baseline"] == "prod2"


class TestDeploymentProfileInOverrideLists:
    def test_override_is_appended_last(self):
        with tempfile.TemporaryDirectory(prefix="deployment-profile-") as tmp:
            env_dir = Path(tmp)
            env_definition_path = _write_env_definition(env_dir, {"bss": ["manual"]})
            _add_namespace(env_dir, "bss")

            append_override_to_env_definition(env_dir, ["bss"])

            profiles = openYaml(env_definition_path, safe_load=True)["envTemplate"]["envSpecificResourceProfiles"]
            assert profiles["bss"] == ["manual", DEPLOYMENT_PROFILE_NAME]
            assert "cloud" not in profiles

    def test_single_entry_list_is_made_after_the_existing_override(self):
        with tempfile.TemporaryDirectory(prefix="deployment-profile-") as tmp:
            env_dir = Path(tmp)
            env_definition_path = _write_env_definition(env_dir, {"bss": "manual"})
            _add_namespace(env_dir, "bss")

            append_override_to_env_definition(env_dir, ["bss"])

            profiles = openYaml(env_definition_path, safe_load=True)["envTemplate"]["envSpecificResourceProfiles"]
            assert profiles["bss"] == ["manual", DEPLOYMENT_PROFILE_NAME]

    def test_existing_override_is_not_appended_again(self):
        with tempfile.TemporaryDirectory(prefix="deployment-profile-") as tmp:
            env_dir = Path(tmp)
            env_definition_path = _write_env_definition(env_dir, {"bss": ["manual", DEPLOYMENT_PROFILE_NAME]})
            _add_namespace(env_dir, "bss")

            append_override_to_env_definition(env_dir, ["bss"])

            profiles = openYaml(env_definition_path, safe_load=True)["envTemplate"]["envSpecificResourceProfiles"]
            assert profiles["bss"] == ["manual", DEPLOYMENT_PROFILE_NAME]

    def test_override_survives_the_env_build_cleanup(self):
        with tempfile.TemporaryDirectory(prefix="deployment-profile-") as tmp:
            env_dir = Path(tmp)
            _write_plan(env_dir, "deploy-plan.yml", ["billing:1.0.0"])
            env_definition_path = _write_env_definition(env_dir, {"bss": ["manual"]})
            _add_namespace(env_dir, "bss")
            generated = env_dir / "Profiles"
            generated.mkdir(parents=True, exist_ok=True)
            (generated / "previous-run.yml").write_text("name: previous-run\n", encoding="utf-8")
            write_deployment_profile_override(env_dir, deployed_entities(env_dir), "prod")
            append_override_to_env_definition(env_dir, ["bss"])

            cleanup_resulting_dir(env_dir)

            assert _override_path(env_dir).is_file()
            assert not generated.exists()
            profiles = openYaml(env_definition_path, safe_load=True)["envTemplate"]["envSpecificResourceProfiles"]
            assert profiles["bss"] == ["manual", DEPLOYMENT_PROFILE_NAME]

    def test_blue_green_pair_shares_one_override(self):
        with tempfile.TemporaryDirectory(prefix="deployment-profile-") as tmp:
            env_dir = Path(tmp)
            _write_plan(env_dir, "deploy-plan.yml", ["billing:1.0.0"], "app", "env-01-app-origin")
            _write_plan(env_dir, "delta-deploy-plan.yml", ["billing:1.0.0"], "app", "env-01-app-peer")
            env_definition_path = _write_env_definition(env_dir, {})
            _add_namespace(env_dir, "app-origin", "env-01-app-origin")
            _add_namespace(env_dir, "app-peer", "env-01-app-peer")
            apply_deployment_profile(env_dir, "prod")
            _write_plan(env_dir, "delta-deploy-plan.yml", ["billing:1.0.0"], "app", "env-01-app-origin")

            apply_deployment_profile(env_dir, "prod")

            profiles = openYaml(env_definition_path, safe_load=True)["envTemplate"]["envSpecificResourceProfiles"]
            assert profiles["app-origin"] == [DEPLOYMENT_PROFILE_NAME]
            assert profiles["app-peer"] == [DEPLOYMENT_PROFILE_NAME]
            written = sorted(path.name for path in (env_dir / "Inventory" / "resource_profiles").iterdir())
            assert written == [f"{DEPLOYMENT_PROFILE_NAME}.yml"]

    def test_override_is_referenced_only_by_deployed_namespaces(self):
        with tempfile.TemporaryDirectory(prefix="deployment-profile-") as tmp:
            env_dir = Path(tmp)
            _write_plan(env_dir, "delta-deploy-plan.yml", ["billing:1.0.0"], "bss", "env-01-bss")
            env_definition_path = _write_env_definition(env_dir, {"core": "core-override"})
            _add_namespace(env_dir, "bss", "env-01-bss")
            _add_namespace(env_dir, "core", "env-01-core")

            apply_deployment_profile(env_dir, "prod")

            profiles = openYaml(env_definition_path, safe_load=True)["envTemplate"]["envSpecificResourceProfiles"]
            assert profiles["bss"] == [DEPLOYMENT_PROFILE_NAME]
            assert profiles["core"] == "core-override"
            assert "cloud" not in profiles

    def test_namespace_not_built_yet_is_keyed_by_deploy_postfix(self):
        with tempfile.TemporaryDirectory(prefix="deployment-profile-") as tmp:
            env_dir = Path(tmp)
            _write_plan(env_dir, "delta-deploy-plan.yml", ["billing:1.0.0"], "bss", "env-01-bss")
            env_definition_path = _write_env_definition(env_dir, {})

            apply_deployment_profile(env_dir, "prod")

            profiles = openYaml(env_definition_path, safe_load=True)["envTemplate"]["envSpecificResourceProfiles"]
            assert profiles == {"bss": [DEPLOYMENT_PROFILE_NAME]}
