import re
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from envgenehelper import NamespaceRole, get_env_instances_dir, open_current_env_instance_store, openYaml
from ruamel.yaml import YAML

from build_env.deployment_profile import (
    GENERATED_KEY_COMMENT,
    GENERATED_MARKER,
    GENERATED_PROFILES_MAP_KEY,
    PROFILE_DOC,
    apply_deployment_profile,
    apply_run_profile,
    assign_generated_overrides,
    build_profile_override,
    deployed_entities,
    deployed_groups,
    profile_override_name,
    write_profile_override,
)
from build_env.main import build_environment, cleanup_resulting_dir

POSTFIX = "bss"
NAME = profile_override_name(POSTFIX)


def _write_plan(env_dir: Path, file_name: str, versions: list[str], deploy_postfix: str = POSTFIX,
                namespace: str = "bss-pl") -> None:
    _write_plan_entries(env_dir, file_name, [(version, deploy_postfix, namespace) for version in versions])


def _write_plan_entries(env_dir: Path, file_name: str, entries: list[tuple[str, str, str]]) -> None:
    inventory = env_dir / "Inventory"
    inventory.mkdir(parents=True, exist_ok=True)
    plan = [{"wave": 0, "version": version, "deployPostfix": deploy_postfix, "namespace": namespace}
            for version, deploy_postfix, namespace in entries]
    with (inventory / file_name).open("w", encoding="utf-8") as f:
        YAML().dump(plan, f)


def _write_env_definition(env_dir: Path, profiles: dict) -> Path:
    inventory = env_dir / "Inventory"
    inventory.mkdir(parents=True, exist_ok=True)
    env_definition_path = inventory / "env_definition.yml"
    with env_definition_path.open("w", encoding="utf-8") as f:
        YAML().dump({"inventory": {"environmentName": env_dir.name},
                    "envTemplate": {"name": "simple", "envSpecificResourceProfiles": profiles}}, f)
    return env_definition_path


def _add_namespace(env_dir: Path, folder: str, name: str | None = None) -> None:
    namespace_dir = env_dir / "Namespaces" / folder
    namespace_dir.mkdir(parents=True, exist_ok=True)
    with (namespace_dir / "namespace.yml").open("w", encoding="utf-8") as f:
        YAML().dump({"name": name or folder}, f)


def _override_path(env_dir: Path, deploy_postfix: str = POSTFIX) -> Path:
    return env_dir / "Inventory" / "resource_profiles" / f"{profile_override_name(deploy_postfix)}.yml"


def _apply(env_dir: Path, env_definition_path: Path, profile_name: str = "prod") -> list[Path]:
    """Apply the profile as env build does: with the env definition this run has loaded."""
    return apply_deployment_profile(env_dir, profile_name, openYaml(env_definition_path))


def _assign(env_dir: Path, env_definition_path: Path, overrides: dict[str, str]) -> dict:
    env_definition = openYaml(env_definition_path)
    assign_generated_overrides(env_dir, overrides, env_definition)
    return env_definition


def _env_template(env_definition_path: Path) -> dict:
    return openYaml(env_definition_path, safe_load=True)["envTemplate"]


def _generated_map(env_definition_path: Path) -> dict:
    return _env_template(env_definition_path).get(GENERATED_PROFILES_MAP_KEY) or {}


def _env_specific_map(env_definition_path: Path) -> dict:
    return _env_template(env_definition_path).get("envSpecificResourceProfiles") or {}


def _write(env_dir: Path, profile_name: str = "prod", deploy_postfix: str = POSTFIX) -> Path:
    entities = [entity for entity in deployed_entities(env_dir) if entity.deploy_postfix == deploy_postfix]
    return write_profile_override(env_dir, deploy_postfix, entities, profile_name)


class TestProfileOverride:
    def test_step_creates_override_named_after_the_deploy_postfix(self):
        with tempfile.TemporaryDirectory(prefix="profile-override-") as tmp:
            env_dir = Path(tmp)
            _write_plan(env_dir, "deploy-plan.yml", ["billing:1.0.0", "crm:2.0.0"])

            override = build_profile_override(POSTFIX, deployed_entities(env_dir), "prod")

            assert override["name"] == NAME
            assert override["applications"] == [
                {"name": "billing", "baseline": "prod", "services": []},
                {"name": "crm", "baseline": "prod", "services": []},
            ]

    def test_one_application_deployed_twice_is_named_once(self):
        with tempfile.TemporaryDirectory(prefix="profile-override-") as tmp:
            env_dir = Path(tmp)
            _write_plan(env_dir, "deploy-plan.yml", ["billing:1.0.0", "billing:2.0.0"])

            override = build_profile_override(POSTFIX, deployed_entities(env_dir), "prod")

            assert [app["name"] for app in override["applications"]] == ["billing"]

    def test_delta_deploy_plan_is_used_when_present(self):
        with tempfile.TemporaryDirectory(prefix="profile-override-") as tmp:
            env_dir = Path(tmp)
            _write_plan(env_dir, "deploy-plan.yml", ["billing:1.0.0", "crm:2.0.0"])
            _write_plan(env_dir, "delta-deploy-plan.yml", ["crm:2.0.0"])

            override = build_profile_override(POSTFIX, deployed_entities(env_dir), "prod")

            assert [app["name"] for app in override["applications"]] == ["crm"]

    def test_delta_deploy_plan_without_applications_falls_back_to_deploy_plan(self):
        with tempfile.TemporaryDirectory(prefix="profile-override-") as tmp:
            env_dir = Path(tmp)
            _write_plan(env_dir, "deploy-plan.yml", ["billing:1.0.0", "crm:2.0.0"])
            _write_plan(env_dir, "delta-deploy-plan.yml", [])

            override = build_profile_override(POSTFIX, deployed_entities(env_dir), "prod")

            assert [app["name"] for app in override["applications"]] == ["billing", "crm"]

    def test_run_without_deploy_plan_generates_no_override(self):
        with tempfile.TemporaryDirectory(prefix="profile-override-") as tmp:
            env_dir = Path(tmp)

            assert deployed_entities(env_dir) is None
            assert apply_deployment_profile(env_dir, "prod", {}) == []
            assert not _override_path(env_dir).exists()

    def test_run_with_an_empty_plan_and_no_deploy_plan_generates_no_override(self):
        with tempfile.TemporaryDirectory(prefix="profile-override-") as tmp:
            env_dir = Path(tmp)
            _write_plan(env_dir, "delta-deploy-plan.yml", [])

            assert apply_deployment_profile(env_dir, "prod", {}) == []
            assert not _override_path(env_dir).exists()

    def test_run_without_deploy_plan_touches_nothing(self):
        with tempfile.TemporaryDirectory(prefix="profile-override-") as tmp:
            env_dir = Path(tmp)
            _add_namespace(env_dir, "bss-pl")
            env_definition_path = _write_env_definition(env_dir, {"bss": "hand-written"})
            before = env_definition_path.read_bytes()

            assert _apply(env_dir, env_definition_path) == []

            assert not _override_path(env_dir).exists()
            assert env_definition_path.read_bytes() == before

    def test_second_run_updates_existing_override(self):
        with tempfile.TemporaryDirectory(prefix="profile-override-") as tmp:
            env_dir = Path(tmp)
            _write_plan(env_dir, "deploy-plan.yml", ["billing:1.0.0"])
            _write(env_dir)
            _write_plan(env_dir, "deploy-plan.yml", ["billing:1.0.0", "crm:2.0.0"])

            path = _write(env_dir)

            assert path == _override_path(env_dir)
            assert sorted(list(Path(path).parent.iterdir())) == [path]
            override = openYaml(path, safe_load=True)
            assert [app["name"] for app in override["applications"]] == ["billing", "crm"]

    def test_generated_override_keeps_applications_of_the_previous_runs(self):
        with tempfile.TemporaryDirectory(prefix="profile-override-") as tmp:
            env_dir = Path(tmp)
            _write_plan(env_dir, "deploy-plan.yml", ["core:1.0.0"])
            _write(env_dir)
            _write_plan(env_dir, "deploy-plan.yml", ["billing:1.0.0"])

            path = _write(env_dir)

            override = openYaml(path, safe_load=True)
            assert override["applications"] == [
                {"name": "core", "baseline": "prod", "services": []},
                {"name": "billing", "baseline": "prod", "services": []},
            ]

    def test_generated_override_updates_only_the_deployed_applications(self):
        with tempfile.TemporaryDirectory(prefix="profile-override-") as tmp:
            env_dir = Path(tmp)
            _write_plan(env_dir, "deploy-plan.yml", ["billing:1.0.0", "core:1.0.0"])
            _write(env_dir)
            _write_plan(env_dir, "deploy-plan.yml", ["billing:1.0.0"])

            path = _write(env_dir, "prod2")

            override = openYaml(path, safe_load=True)
            assert override["applications"] == [
                {"name": "billing", "baseline": "prod2", "services": []},
                {"name": "core", "baseline": "prod", "services": []},
            ]

    def test_application_of_a_previous_run_keeps_its_baseline(self):
        with tempfile.TemporaryDirectory(prefix="profile-override-") as tmp:
            env_dir = Path(tmp)
            env_definition_path = _write_env_definition(env_dir, {})
            _add_namespace(env_dir, "bss", "bss-pl")
            _write_plan(env_dir, "deploy-plan.yml", ["core:1.0.0", "billing:1.0.0"])
            _apply(env_dir, env_definition_path)
            _write_plan(env_dir, "deploy-plan.yml", ["core:1.0.0"])

            _apply(env_dir, env_definition_path)

            override = openYaml(_override_path(env_dir), safe_load=True)
            assert {app["name"]: app["baseline"] for app in override["applications"]} == {
                "core": "prod", "billing": "prod"}

    def test_run_with_another_profile_name_rewrites_the_override(self):
        with tempfile.TemporaryDirectory(prefix="profile-override-") as tmp:
            env_dir = Path(tmp)
            _write_plan(env_dir, "deploy-plan.yml", ["billing:1.0.0"])
            _write(env_dir)

            path = _write(env_dir, "prod2")

            assert path == _override_path(env_dir)
            assert sorted(list(Path(path).parent.iterdir())) == [path]
            override = openYaml(path, safe_load=True)
            assert [app["baseline"] for app in override["applications"]] == ["prod2"]

    def test_override_written_by_hand_under_the_reserved_name_is_replaced_with_a_warning(self):
        with tempfile.TemporaryDirectory(prefix="profile-override-") as tmp:
            env_dir = Path(tmp)
            _write_plan(env_dir, "deploy-plan.yml", ["billing:1.0.0"])
            hand_written = _override_path(env_dir)
            hand_written.parent.mkdir(parents=True, exist_ok=True)
            hand_written.write_text(f"name: {NAME}\napplications:\n- name: billing\n  baseline: stage\n",
                                    encoding="utf-8")

            with patch("build_env.deployment_profile.logger") as logger:
                path = _write(env_dir)

            logger.warning.assert_called_once()
            assert path == hand_written
            assert openYaml(path, safe_load=True)["applications"][0]["baseline"] == "prod"

    def test_override_written_by_hand_is_replaced_not_merged(self):
        with tempfile.TemporaryDirectory(prefix="profile-override-") as tmp:
            env_dir = Path(tmp)
            _write_plan(env_dir, "deploy-plan.yml", ["billing:1.0.0"])
            hand_written = _override_path(env_dir)
            hand_written.parent.mkdir(parents=True, exist_ok=True)
            hand_written.write_text(f"name: {NAME}\napplications:\n- name: crm\n  baseline: stage\n", encoding="utf-8")

            with patch("build_env.deployment_profile.logger"):
                path = _write(env_dir)

            assert [app["name"] for app in openYaml(path, safe_load=True)["applications"]] == ["billing"]

    def test_rerun_rewrites_generated_override_without_a_warning(self):
        with tempfile.TemporaryDirectory(prefix="profile-override-") as tmp:
            env_dir = Path(tmp)
            _write_plan(env_dir, "deploy-plan.yml", ["billing:1.0.0"])
            _write(env_dir)

            with patch("build_env.deployment_profile.logger") as logger:
                path = _write(env_dir, "prod2")

            logger.warning.assert_not_called()
            assert openYaml(path, safe_load=True)["applications"][0]["baseline"] == "prod2"

    def test_generated_file_header_points_to_the_generated_override_doc(self):
        with tempfile.TemporaryDirectory(prefix="profile-override-") as tmp:
            env_dir = Path(tmp)
            _write_plan(env_dir, "deploy-plan.yml", ["billing:1.0.0"])

            override_path = _write(env_dir)

            header = override_path.read_text(encoding="utf-8")
            assert GENERATED_MARKER in header
            assert PROFILE_DOC in header

    def test_the_profile_doc_link_of_the_header_is_an_anchor_of_the_doc(self):
        doc_path = Path(__file__).resolve().parents[3] / "docs" / "features" / "resource-profile.md"
        doc = re.sub(r"^```.*?^```", "", doc_path.read_text(encoding="utf-8"), flags=re.MULTILINE | re.DOTALL)
        anchors = {re.sub(r"[^a-z0-9 -]", "", heading.lower()).replace(" ", "-")
                   for heading in re.findall(r"^#{1,6} (.+)$", doc, re.MULTILINE)}

        assert PROFILE_DOC.split("#")[1] in anchors


class TestDeployedGroups:
    def test_one_override_per_deploy_postfix(self):
        with tempfile.TemporaryDirectory(prefix="profile-override-") as tmp:
            env_dir = Path(tmp)
            _write_plan_entries(env_dir, "deploy-plan.yml", [("billing:1.0.0", "bss", "env-01-bss"),
                                                            ("core:1.0.0", "core", "env-01-core")])
            _add_namespace(env_dir, "bss", "env-01-bss")
            _add_namespace(env_dir, "core", "env-01-core")

            groups = deployed_groups(env_dir, deployed_entities(env_dir))

            assert groups == {"bss": ["bss"], "core": ["core"]}

    def test_namespace_folder_is_the_key_when_it_differs_from_the_deploy_postfix(self):
        with tempfile.TemporaryDirectory(prefix="profile-override-") as tmp:
            env_dir = Path(tmp)
            _write_plan(env_dir, "deploy-plan.yml", ["billing:1.0.0"], "bss", "env-01-bss")
            _add_namespace(env_dir, "bss-prod-eu", "env-01-bss")

            assert deployed_groups(env_dir, deployed_entities(env_dir)) == {"bss": ["bss-prod-eu"]}

    def test_entry_without_deploy_postfix_is_skipped(self):
        with tempfile.TemporaryDirectory(prefix="profile-override-") as tmp:
            env_dir = Path(tmp)
            _write_plan(env_dir, "deploy-plan.yml", ["billing:1.0.0"], "", "env-01-bss")
            _add_namespace(env_dir, "bss", "env-01-bss")

            with patch("build_env.deployment_profile.logger") as logger:
                groups = deployed_groups(env_dir, deployed_entities(env_dir))

            assert groups == {}
            logger.warning.assert_called()

    def test_a_namespace_the_run_did_not_render_is_skipped(self):
        with tempfile.TemporaryDirectory(prefix="profile-override-") as tmp:
            env_dir = Path(tmp)
            _write_plan_entries(env_dir, "deploy-plan.yml", [("billing:1.0.0", "app", "app-origin")])

            with patch("build_env.deployment_profile.logger") as logger:
                groups = deployed_groups(env_dir, deployed_entities(env_dir))

            assert groups == {}
            logger.warning.assert_called()

    def test_two_deploy_postfixes_write_two_overrides(self):
        with tempfile.TemporaryDirectory(prefix="profile-override-") as tmp:
            env_dir = Path(tmp)
            _write_plan_entries(env_dir, "deploy-plan.yml", [("billing:1.0.0", "bss", "env-01-bss"),
                                                            ("core:1.0.0", "core", "env-01-core")])
            env_definition_path = _write_env_definition(env_dir, {})
            _add_namespace(env_dir, "bss", "env-01-bss")
            _add_namespace(env_dir, "core", "env-01-core")

            _apply(env_dir, env_definition_path)

            assert _override_path(env_dir, "bss").is_file()
            assert _override_path(env_dir, "core").is_file()
            assert _generated_map(env_definition_path) == {"bss": profile_override_name("bss"),
                                                           "core": profile_override_name("core")}
            assert [app["name"] for app in openYaml(_override_path(env_dir, "core"), safe_load=True)
                    ["applications"]] == ["core"]


class TestGeneratedOverridesAssignment:
    def test_namespace_is_assigned_the_generated_override(self):
        with tempfile.TemporaryDirectory(prefix="profile-override-") as tmp:
            env_dir = Path(tmp)
            env_definition_path = _write_env_definition(env_dir, {"bss": "manual"})

            _assign(env_dir, env_definition_path, {"bss": NAME})

            assert _generated_map(env_definition_path) == {"bss": NAME}
            assert _env_specific_map(env_definition_path) == {"bss": "manual"}

    def test_assigned_key_says_it_is_generated(self):
        with tempfile.TemporaryDirectory(prefix='profile-override-') as tmp:
            env_dir = Path(tmp)
            env_definition_path = _write_env_definition(env_dir, {'bss': 'manual'})

            _assign(env_dir, env_definition_path, {'bss': NAME})

            assert GENERATED_KEY_COMMENT in env_definition_path.read_text(encoding='utf-8')

    def test_a_string_override_stays_untouched(self):
        with tempfile.TemporaryDirectory(prefix="profile-override-") as tmp:
            env_dir = Path(tmp)
            env_definition_path = _write_env_definition(env_dir, {"bss": "manual"})

            _assign(env_dir, env_definition_path, {"bss": NAME})

            assert _env_specific_map(env_definition_path) == {"bss": "manual"}
            assert _generated_map(env_definition_path) == {"bss": NAME}

    def test_assigned_namespace_is_not_assigned_again(self):
        with tempfile.TemporaryDirectory(prefix="profile-override-") as tmp:
            env_dir = Path(tmp)
            env_definition_path = _write_env_definition(env_dir, {"bss": "manual"})
            _assign(env_dir, env_definition_path, {"bss": NAME})
            written_before = env_definition_path.read_bytes()

            _assign(env_dir, env_definition_path, {"bss": NAME})

            assert _generated_map(env_definition_path) == {"bss": NAME}
            assert env_definition_path.read_bytes() == written_before

    def test_assignment_survives_the_env_build_cleanup(self):
        with tempfile.TemporaryDirectory(prefix="profile-override-") as tmp:
            env_dir = Path(tmp)
            _write_plan(env_dir, "deploy-plan.yml", ["billing:1.0.0"])
            env_definition_path = _write_env_definition(env_dir, {"bss": "manual"})
            _add_namespace(env_dir, "bss", "bss-pl")
            generated = env_dir / "Profiles"
            generated.mkdir(parents=True, exist_ok=True)
            (generated / "previous-run.yml").write_text("name: previous-run\n", encoding="utf-8")
            _write(env_dir)
            _assign(env_dir, env_definition_path, {"bss": NAME})

            cleanup_resulting_dir(env_dir)

            assert _override_path(env_dir).is_file()
            assert not generated.exists()
            assert _generated_map(env_definition_path) == {"bss": NAME}
            assert _env_specific_map(env_definition_path) == {"bss": "manual"}

    def test_blue_green_pair_shares_one_override(self):
        with tempfile.TemporaryDirectory(prefix="profile-override-") as tmp:
            env_dir = Path(tmp)
            _write_plan_entries(env_dir, "deploy-plan.yml", [("billing:1.0.0", "app", "env-01-app-origin"),
                                                            ("billing:1.0.0", "app", "env-01-app-peer")])
            env_definition_path = _write_env_definition(env_dir, {})
            _add_namespace(env_dir, "app-origin", "env-01-app-origin")
            _add_namespace(env_dir, "app-peer", "env-01-app-peer")

            _apply(env_dir, env_definition_path)

            assert _generated_map(env_definition_path) == {"app-origin": profile_override_name("app"),
                                                           "app-peer": profile_override_name("app")}
            written = sorted(path.name for path in (env_dir / "Inventory" / "resource_profiles").iterdir())
            assert written == [f"{profile_override_name('app')}.yml"]

    def test_the_deployed_namespace_is_keyed_by_the_folder_the_run_rendered(self):
        with tempfile.TemporaryDirectory(prefix="profile-override-") as tmp:
            env_dir = Path(tmp)
            _write_plan(env_dir, "deploy-plan.yml", ["billing:1.0.0"], "app", "env-01-app-origin")
            env_definition_path = _write_env_definition(env_dir, {})
            _add_namespace(env_dir, "app-origin", "env-01-app-origin")

            _apply(env_dir, env_definition_path)

            assert _generated_map(env_definition_path) == {"app-origin": profile_override_name("app")}

    def test_only_deployed_namespaces_are_assigned(self):
        with tempfile.TemporaryDirectory(prefix="profile-override-") as tmp:
            env_dir = Path(tmp)
            _write_plan(env_dir, "delta-deploy-plan.yml", ["billing:1.0.0"], "bss", "env-01-bss")
            env_definition_path = _write_env_definition(env_dir, {"core": "core-override"})
            _add_namespace(env_dir, "bss", "env-01-bss")
            _add_namespace(env_dir, "core", "env-01-core")

            _apply(env_dir, env_definition_path)

            assert _generated_map(env_definition_path) == {"bss": profile_override_name("bss")}
            assert _env_specific_map(env_definition_path) == {"core": "core-override"}

    def test_the_env_definition_of_the_run_gets_the_generated_entry(self):
        with tempfile.TemporaryDirectory(prefix="profile-override-") as tmp:
            env_dir = Path(tmp)
            _write_plan(env_dir, "deploy-plan.yml", ["billing:1.0.0"])
            env_definition_path = _write_env_definition(env_dir, {})
            _add_namespace(env_dir, "bss", "bss-pl")

            env_definition = openYaml(env_definition_path)
            apply_deployment_profile(env_dir, "prod", env_definition)

            assert env_definition["envTemplate"][GENERATED_PROFILES_MAP_KEY] == {"bss": NAME}
            assert _generated_map(env_definition_path) == {"bss": NAME}

    def test_a_namespace_the_run_did_not_render_gets_no_entry(self):
        with tempfile.TemporaryDirectory(prefix="profile-override-") as tmp:
            env_dir = Path(tmp)
            _write_plan(env_dir, "delta-deploy-plan.yml", ["billing:1.0.0"], "bss", "env-01-bss")
            env_definition_path = _write_env_definition(env_dir, {})

            with patch("build_env.deployment_profile.logger") as logger:
                _apply(env_dir, env_definition_path)

            assert _generated_map(env_definition_path) == {}
            assert not _override_path(env_dir).exists()
            logger.warning.assert_called()


def _as_arg(env_dir: Path, env_dir_kind: str) -> Path | str:
    """Give the environment directory the shape its caller in env build gives it."""
    return env_dir if env_dir_kind == "path" else str(env_dir)


def _run_profile(env_dir: Path | str, env_definition_path: Path, variables: dict):
    with patch("build_env.deployment_profile.getenv",
               side_effect=lambda name, default=None: variables.get(name, default)), \
            patch("build_env.deployment_profile.logger") as logger:
        apply_run_profile(env_dir, openYaml(env_definition_path))
    return logger


@pytest.mark.parametrize("env_dir_kind", ["path", "string"])
class TestRunProfile:
    def test_a_run_without_profile_changes_nothing(self, env_dir_kind):
        with tempfile.TemporaryDirectory(prefix="profile-override-") as tmp:
            env_dir = Path(tmp)
            _write_plan(env_dir, "deploy-plan.yml", ["billing:1.0.0"])
            env_definition_path = _write_env_definition(env_dir, {})
            _add_namespace(env_dir, "bss", "bss-pl")

            _run_profile(_as_arg(env_dir, env_dir_kind), env_definition_path, {})

            assert not _override_path(env_dir).exists()
            assert _generated_map(env_definition_path) == {}

    def test_a_run_that_does_not_deploy_warns_and_changes_nothing(self, env_dir_kind):
        with tempfile.TemporaryDirectory(prefix="profile-override-") as tmp:
            env_dir = Path(tmp)
            _write_plan(env_dir, "deploy-plan.yml", ["billing:1.0.0"])
            env_definition_path = _write_env_definition(env_dir, {})
            _add_namespace(env_dir, "bss", "bss-pl")

            logger = _run_profile(_as_arg(env_dir, env_dir_kind), env_definition_path,
                                  {"PROFILE": "prod", "OPERATION_TYPE": "CLEAN"})

            assert not _override_path(env_dir).exists()
            assert _generated_map(env_definition_path) == {}
            logger.warning.assert_called()

    def test_a_deploy_run_applies_the_profile(self, env_dir_kind):
        with tempfile.TemporaryDirectory(prefix="profile-override-") as tmp:
            env_dir = Path(tmp)
            _write_plan(env_dir, "deploy-plan.yml", ["billing:1.0.0"])
            env_definition_path = _write_env_definition(env_dir, {})
            _add_namespace(env_dir, "bss", "bss-pl")

            _run_profile(_as_arg(env_dir, env_dir_kind), env_definition_path, {"PROFILE": "prod"})

            assert _override_path(env_dir).is_file()
            assert _generated_map(env_definition_path) == {"bss": NAME}


class TestEnvBuildCallSite:
    def test_env_build_applies_the_profile_to_the_directories_it_rendered(self):
        with tempfile.TemporaryDirectory(prefix="profile-override-") as tmp:
            instances_dir = str(Path(tmp) / "environments")
            env_dir = get_env_instances_dir("env-01", "cluster-01", instances_dir)
            env_definition_path = _write_env_definition(Path(env_dir), {})
            _write_plan(Path(env_dir), "deploy-plan.yml", ["billing:1.0.0"])
            rendered = []

            def render(env_name, envvars):
                """The env build cleanup drops Namespaces, so only the render leaves them behind."""
                _add_namespace(Path(env_dir), "bss", "bss-pl")
                rendered.append(env_name)

            render_context = MagicMock()
            render_context.render_config_env.side_effect = render
            with open_current_env_instance_store(env_dir), \
                    tempfile.TemporaryDirectory(prefix="templates-") as templates_dir, \
                    patch.dict("os.environ", {"CI_PROJECT_DIR": tmp, "PROFILE": "prod"}), \
                    patch("build_env.main.cleanup_resulting_dir"), \
                    patch("build_env.main.copy_paramsets_to_render_workspace"), \
                    patch("build_env.main.load_env_inputs", side_effect=lambda *args: openYaml(env_definition_path)), \
                    patch("build_env.main.get_deployer_config", return_value=("cmdb", None, None)), \
                    patch("build_env.main.find_cloud_passport_definition", return_value=""), \
                    patch("build_env.main.EnvGenerator", return_value=render_context), \
                    patch("build_env.main.get_resource_profiles_map", return_value={}), \
                    patch("build_env.main.build_env"), \
                    patch("build_env.main.create_credentials"):
                build_environment("env-01", "cluster-01", {NamespaceRole.COMMON: templates_dir},
                                  env_dir, instances_dir, tmp)

            assert rendered == ["env-01"]
            assert _override_path(Path(env_dir)).is_file()
            assert _generated_map(env_definition_path) == {"bss": NAME}
