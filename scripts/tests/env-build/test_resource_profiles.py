import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from envgenehelper import dumpYamlToStr, open_current_env_instance_store, readYaml, writeYamlToFile

from build_env.deployment_profile import GENERATED_PROFILES_MAP_KEY, PROFILE_OVERRIDE_SUFFIX, profile_override_name
from build_env.resource_profiles import drop_profiles_without_object, get_resource_profiles_map, \
    has_valid_profile_name, merge_resource_profiles, override_by_env_specific_profiles, set_object_profile_field, \
    validate_resource_profiles, warn_on_profile_name_collisions

RP_SCHEMA = str(Path(__file__).resolve().parents[3] / "schemas" / "resource-profile.schema.json")


def _profile(name, baseline=None, params=None):
    profile = {"name": name}
    if baseline is not None:
        profile["baseline"] = baseline
    if params is not None:
        profile["applications"] = [{
            "name": "app",
            "services": [{"name": "svc", "parameters": [{"name": k, "value": v} for k, v in params.items()]}],
        }]
    return readYaml(json.dumps(profile))


def _render_context(merge):
    context = MagicMock()
    context.ctx.env_definition = {"inventory": {"config": {"mergeEnvSpecificResourceProfiles": merge}}}
    return context


def _apps_profile(name, baseline, apps):
    profile = {"name": name, "baseline": baseline, "applications": apps}
    return readYaml(json.dumps(profile))


def _app(name, baseline, param=None):
    app = {"name": name, "baseline": baseline, "services": []}
    if param:
        key, value = param
        app["services"] = [{"name": "svc", "parameters": [{"name": key, "value": value}]}]
    return app


def _params_of(profile):
    return {param["name"]: param["value"]
            for app in profile.get("applications") or []
            for service in app["services"]
            for param in service["parameters"]}


def _apps_of(profile):
    return {app["name"]: app.get("baseline") for app in profile.get("applications") or []}


@pytest.fixture
def env_instance_store(tmp_path):
    with open_current_env_instance_store(tmp_path) as opened_store:
        yield opened_store


class TestMergeResourceProfiles:
    def test_env_specific_baseline_wins(self):
        template = _profile("tmpl", baseline="dev")
        merge_resource_profiles(template, _profile("env", baseline="prod"), "env")
        assert template["baseline"] == "prod"

    def test_template_baseline_kept_when_env_specific_has_none(self):
        template = _profile("tmpl", baseline="dev", params={"replicas": 1})
        merge_resource_profiles(template, _profile("env", params={"replicas": 2}), "env")
        assert template["baseline"] == "dev"
        assert template["applications"][0]["services"][0]["parameters"][0]["value"] == 2

    @pytest.mark.parametrize("baseline", ["", "   "])
    def test_blank_env_specific_baseline_is_absent(self, baseline):
        template = _profile("tmpl", baseline="dev")
        merge_resource_profiles(template, _profile("env", baseline=baseline), "env")
        assert template["baseline"] == "dev"

    def test_warns_on_baseline_change_with_template_parameters(self):
        template = _profile("tmpl", baseline="dev", params={"replicas": 1})
        with patch("build_env.resource_profiles.logger") as logger:
            merge_resource_profiles(template, _profile("env", baseline="prod"), "env")
        logger.warning.assert_called_once()

    def test_no_warning_for_baseline_only_template(self):
        template = _profile("tmpl", baseline="dev")
        with patch("build_env.resource_profiles.logger") as logger:
            merge_resource_profiles(template, _profile("env", baseline="prod"), "env")
        logger.warning.assert_not_called()

    def test_no_warning_when_env_specific_has_no_baseline(self):
        template = _profile("tmpl", baseline="dev", params={"replicas": 1})
        with patch("build_env.resource_profiles.logger") as logger:
            merge_resource_profiles(template, _profile("env", params={"replicas": 2}), "env")
        logger.warning.assert_not_called()

    def test_baseline_only_override_keeps_template_parameters(self):
        template = _profile("tmpl", baseline="dev", params={"replicas": 1})
        merge_resource_profiles(template, _profile("env", baseline="prod"), "env")
        assert template["baseline"] == "prod"
        assert template["applications"][0]["services"][0]["parameters"][0]["value"] == 1

    def test_template_without_applications_gets_env_specific_applications(self):
        template = _profile("tmpl", baseline="dev")
        merge_resource_profiles(template, _profile("env", params={"replicas": 2}), "env")
        assert template["applications"][0]["name"] == "app"

    def test_no_warning_when_baselines_are_equal(self):
        template = _profile("tmpl", baseline="dev", params={"replicas": 1})
        with patch("build_env.resource_profiles.logger") as logger:
            merge_resource_profiles(template, _profile("env", baseline="dev"), "env")
        logger.warning.assert_not_called()

    def test_no_warning_when_object_baseline_equals_env_specific(self):
        template = _profile("tmpl", params={"replicas": 1})
        with patch("build_env.resource_profiles.logger") as logger:
            merge_resource_profiles(template, _profile("env", baseline="dev"), "env", "dev")
        logger.warning.assert_not_called()

    def test_warns_when_object_baseline_differs_from_env_specific(self):
        template = _profile("tmpl", params={"replicas": 1})
        with patch("build_env.resource_profiles.logger") as logger:
            merge_resource_profiles(template, _profile("env", baseline="prod"), "env", "dev")
        logger.warning.assert_called_once()

    def test_template_baseline_takes_precedence_over_object_baseline(self):
        template = _profile("tmpl", baseline="prod", params={"replicas": 1})
        with patch("build_env.resource_profiles.logger") as logger:
            merge_resource_profiles(template, _profile("env", baseline="prod"), "env", "dev")
        logger.warning.assert_not_called()

    def test_no_warning_when_template_services_have_no_parameters(self):
        template = readYaml("name: tmpl\nbaseline: dev\napplications:\n"
                            "  - name: app\n    services:\n      - name: svc\n        parameters: []\n")
        with patch("build_env.resource_profiles.logger") as logger:
            merge_resource_profiles(template, _profile("env", baseline="prod"), "env")
        logger.warning.assert_not_called()

    def test_application_missing_in_template_is_added(self):
        template = _profile("tmpl", params={"replicas": 1})
        env_specific = readYaml("name: env\napplications:\n  - name: other\n    services:\n"
                                "      - name: svc\n        parameters:\n          - name: cpu\n            value: 2\n")
        merge_resource_profiles(template, env_specific, "env")
        assert [app["name"] for app in template["applications"]] == ["app", "other"]
        assert template["applications"][1]["services"][0]["parameters"][0]["value"] == 2

    def test_service_missing_in_template_is_added(self):
        template = _profile("tmpl", params={"replicas": 1})
        env_specific = readYaml("name: env\napplications:\n  - name: app\n    services:\n"
                                "      - name: other\n        parameters:\n          - name: cpu\n            value: 2\n")
        merge_resource_profiles(template, env_specific, "env")
        assert [svc["name"] for svc in template["applications"][0]["services"]] == ["svc", "other"]

    def test_parameter_missing_in_template_is_added(self):
        template = _profile("tmpl", params={"replicas": 1})
        merge_resource_profiles(template, _profile("env", params={"cpu": 2}), "env")
        params = template["applications"][0]["services"][0]["parameters"]
        assert {p["name"]: p["value"] for p in params} == {"replicas": 1, "cpu": 2}

    def test_parameter_only_in_template_is_kept(self):
        template = _profile("tmpl", params={"replicas": 1, "cpu": 1})
        merge_resource_profiles(template, _profile("env", params={"replicas": 2}), "env")
        params = template["applications"][0]["services"][0]["parameters"]
        assert {p["name"]: p["value"] for p in params} == {"replicas": 2, "cpu": 1}

    def test_application_version_and_sd_come_from_env_specific(self):
        template = readYaml("name: tmpl\napplications:\n  - name: app\n    version: '1.0'\n    services: []\n")
        env_specific = readYaml("name: env\napplications:\n  - name: app\n    version: '2.0'\n    sd: sd-2\n"
                                "    services: []\n")
        merge_resource_profiles(template, env_specific, "env")
        assert template["applications"][0]["version"] == "2.0"
        assert template["applications"][0]["sd"] == "sd-2"

    def test_application_baseline_comes_from_env_specific(self):
        template = _apps_profile("tmpl", "dev", [_app("Core", "dev", ("replicas", 1)), _app("Billing", "dev-ha")])
        env_specific = _apps_profile("env", "prod", [_app("Core", "prod")])
        merge_resource_profiles(template, env_specific, "env")
        baselines = {app["name"]: app["baseline"] for app in template["applications"]}
        assert baselines == {"Core": "prod", "Billing": "dev-ha"}

    def test_application_baseline_is_added_to_application_missing_in_template(self):
        template = _apps_profile("tmpl", "dev", [_app("Core", "dev")])
        env_specific = _apps_profile("env", "prod", [_app("Billing", "prod-nonha")])
        merge_resource_profiles(template, env_specific, "env")
        baselines = {app["name"]: app["baseline"] for app in template["applications"]}
        assert baselines == {"Core": "dev", "Billing": "prod-nonha"}


class TestOverrideByEnvSpecificProfiles:
    def test_standalone_override_is_attached(self, tmp_path, env_instance_store):
        env_profile = tmp_path / "env-over.yml"
        env_instance_store.put(env_profile, _profile("env-over", baseline="prod"))
        result = override_by_env_specific_profiles({}, {"bss": str(env_profile)}, _render_context("true"), {})
        assert result == {"bss": str(env_profile)}

    def test_merge_writes_env_specific_baseline(self, tmp_path, env_instance_store):
        template_profile = tmp_path / "tmpl.yml"
        env_profile = tmp_path / "env-over.yml"
        env_instance_store.put(template_profile, _profile("tmpl", baseline="dev"))
        env_instance_store.put(env_profile, _profile("env-over", baseline="prod"))
        result = override_by_env_specific_profiles({"bss": str(template_profile)}, {"bss": str(env_profile)},
                                                   _render_context("true"), {})
        assert result == {}
        assert env_instance_store.get(template_profile)["baseline"] == "prod"

    def test_application_baseline_selects_that_application_baseline(self, tmp_path, env_instance_store):
        template_profile = tmp_path / "tmpl.yml"
        env_profile = tmp_path / "env-over.yml"
        env_instance_store.put(template_profile, _apps_profile("tmpl", "dev",
                                                               [_app("Core", "dev", ("replicas", 1)),
                                                                _app("Billing", "dev-ha")]))
        env_instance_store.put(env_profile, _apps_profile("env-over", "prod", [_app("Core", "prod")]))
        result = override_by_env_specific_profiles({"bss": str(template_profile)}, {"bss": str(env_profile)},
                                                   _render_context("true"), {})
        assert result == {}
        merged = env_instance_store.get(template_profile)
        baselines = {app["name"]: app["baseline"] for app in merged["applications"]}
        assert baselines == {"Core": "prod", "Billing": "dev-ha"}

    def test_template_only_is_untouched(self, tmp_path, env_instance_store):
        template_profile = tmp_path / "tmpl.yml"
        env_instance_store.put(template_profile, _profile("tmpl", baseline="dev", params={"replicas": 3}))
        result = override_by_env_specific_profiles({"bss": str(template_profile)}, {}, _render_context("true"), {})
        assert result == {}
        assert env_instance_store.get(template_profile)["baseline"] == "dev"

    def test_standalone_override_is_attached_in_replace_mode(self, tmp_path, env_instance_store):
        env_profile = tmp_path / "env-over.yml"
        env_instance_store.put(env_profile, _profile("env-over", baseline="prod"))
        result = override_by_env_specific_profiles({}, {"bss": str(env_profile)}, _render_context("false"), {})
        assert result == {"bss": str(env_profile)}

    def test_replace_drops_template_profile(self, tmp_path, env_instance_store):
        template_profile = tmp_path / "tmpl.yml"
        env_profile = tmp_path / "env-over.yml"
        env_instance_store.put(template_profile, _profile("tmpl", baseline="dev", params={"replicas": 3}))
        env_instance_store.put(env_profile, _profile("env-over", baseline="prod", params={"cpu": 2}))
        result = override_by_env_specific_profiles({"bss": str(template_profile)}, {"bss": str(env_profile)},
                                                   _render_context("false"), {})
        assert result == {"bss": str(env_profile)}
        assert env_instance_store.get(template_profile)["baseline"] == "dev"

    def test_merge_compares_with_object_baseline(self, tmp_path, env_instance_store):
        template_profile = tmp_path / "tmpl.yml"
        env_profile = tmp_path / "env-over.yml"
        env_instance_store.put(template_profile, _profile("tmpl", params={"replicas": 1}))
        env_instance_store.put(env_profile, _profile("env-over", baseline="dev"))
        with patch("build_env.resource_profiles.logger") as logger:
            override_by_env_specific_profiles({"bss": str(template_profile)}, {"bss": str(env_profile)},
                                              _render_context("true"), {"bss": "dev"})
        logger.warning.assert_not_called()

    def test_boolean_false_mode_replaces(self, tmp_path, env_instance_store):
        template_profile = tmp_path / "tmpl.yml"
        env_profile = tmp_path / "env-over.yml"
        env_instance_store.put(template_profile, _profile("tmpl", baseline="dev"))
        env_instance_store.put(env_profile, _profile("env-over", baseline="prod"))
        result = override_by_env_specific_profiles({"bss": str(template_profile)}, {"bss": str(env_profile)},
                                                   _render_context(False), {})
        assert result == {"bss": str(env_profile)}
        assert env_instance_store.get(template_profile)["baseline"] == "dev"

    def test_merge_is_default_when_mode_not_configured(self, tmp_path, env_instance_store):
        template_profile = tmp_path / "tmpl.yml"
        env_profile = tmp_path / "env-over.yml"
        env_instance_store.put(template_profile, _profile("tmpl", baseline="dev"))
        env_instance_store.put(env_profile, _profile("env-over", baseline="prod"))
        context = MagicMock()
        context.ctx.env_definition = {"inventory": {}}
        result = override_by_env_specific_profiles({"bss": str(template_profile)}, {"bss": str(env_profile)},
                                                   context, {})
        assert result == {}
        assert env_instance_store.get(template_profile)["baseline"] == "prod"

    def test_generated_override_alone_becomes_the_profile(self, tmp_path, env_instance_store):
        generated = tmp_path / "bss-profile-override.yml"
        env_instance_store.put(generated, _profile("bss-profile-override", baseline="prod"))

        result = override_by_env_specific_profiles({}, {}, _render_context("true"), {}, {"bss": str(generated)})

        assert result == {"bss": str(tmp_path / "Profiles" / "bss-profile-override.yml")}
        assert _apps_of(env_instance_store.get(result["bss"])) == {}
        assert env_instance_store.get(result["bss"])["baseline"] == "prod"

    def test_generated_override_wins_over_the_env_profile(self, tmp_path, env_instance_store):
        env_profile = tmp_path / "core-tuning.yml"
        generated = tmp_path / "bss-profile-override.yml"
        env_instance_store.put(env_profile, _apps_profile("core-tuning", "stage", [_app("Core", "dev",
                                                                                        ("replicas", 3))]))
        env_instance_store.put(generated, _apps_profile("bss-profile-override", "", [_app("Core", "prod",
                                                                                          ("replicas", 9))]))

        result = override_by_env_specific_profiles({}, {"bss": str(env_profile)}, _render_context("true"), {},
                                                   {"bss": str(generated)})

        assert result == {"bss": str(tmp_path / "Profiles" / "core-tuning.yml")}
        merged = env_instance_store.get(result["bss"])
        assert merged["name"] == "core-tuning"
        assert merged["baseline"] == "stage"
        assert _apps_of(merged) == {"Core": "prod"}
        assert _params_of(merged) == {"replicas": 9}
        assert _apps_of(env_instance_store.get(env_profile)) == {"Core": "dev"}
        assert _params_of(env_instance_store.get(env_profile)) == {"replicas": 3}

    def test_generated_override_adds_the_applications_the_env_profile_lacks(self, tmp_path, env_instance_store):
        env_profile = tmp_path / "core-tuning.yml"
        generated = tmp_path / "bss-profile-override.yml"
        env_instance_store.put(env_profile, _apps_profile("core-tuning", "stage", [_app("Core", "dev")]))
        env_instance_store.put(generated, _apps_profile("bss-profile-override", "", [_app("Core", "prod"),
                                                                                    _app("Reporting", "prod")]))

        result = override_by_env_specific_profiles({}, {"bss": str(env_profile)}, _render_context("true"), {},
                                                   {"bss": str(generated)})

        assert _apps_of(env_instance_store.get(result["bss"])) == {"Core": "prod", "Reporting": "prod"}

    def test_generated_override_is_the_last_layer_of_the_template_profile(self, tmp_path, env_instance_store):
        template_profile = tmp_path / "tmpl.yml"
        env_profile = tmp_path / "core-tuning.yml"
        generated = tmp_path / "bss-profile-override.yml"
        env_instance_store.put(template_profile, _apps_profile("tmpl", "dev", [_app("Core", "dev"),
                                                                              _app("Billing", "dev")]))
        env_instance_store.put(env_profile, _apps_profile("core-tuning", "", [_app("Core", "stage")]))
        env_instance_store.put(generated, _apps_profile("bss-profile-override", "", [_app("Core", "prod"),
                                                                                    _app("Billing", "prod"),
                                                                                    _app("Reporting", "prod")]))

        result = override_by_env_specific_profiles({"bss": str(template_profile)}, {"bss": str(env_profile)},
                                                   _render_context("true"), {}, {"bss": str(generated)})

        assert result == {}
        merged = env_instance_store.get(template_profile)
        assert merged["name"] == "tmpl"
        assert _apps_of(merged) == {"Core": "prod", "Billing": "prod", "Reporting": "prod"}

    def test_generated_override_takes_the_baseline_of_a_template_profile(self, tmp_path, env_instance_store):
        template_profile = tmp_path / "tmpl.yml"
        generated = tmp_path / "bss-profile-override.yml"
        env_instance_store.put(template_profile, _apps_profile("tmpl", "dev", [_app("Core", "dev")]))
        env_instance_store.put(generated, _apps_profile("bss-profile-override", "prod", [_app("Core", "prod"),
                                                                                        _app("Reporting", "prod")]))

        result = override_by_env_specific_profiles({"bss": str(template_profile)}, {}, _render_context("true"), {},
                                                   {"bss": str(generated)})

        assert result == {}
        merged = env_instance_store.get(template_profile)
        assert merged["baseline"] == "prod"
        assert _apps_of(merged) == {"Core": "prod", "Reporting": "prod"}

    def test_generated_override_is_applied_on_top_in_replace_mode(self, tmp_path, env_instance_store):
        env_profile = tmp_path / "core-tuning.yml"
        generated = tmp_path / "bss-profile-override.yml"
        env_instance_store.put(env_profile, _apps_profile("core-tuning", "stage", [_app("Core", "dev",
                                                                                        ("replicas", 3))]))
        env_instance_store.put(generated, _apps_profile("bss-profile-override", "", [_app("Core", "prod"),
                                                                                    _app("Reporting", "prod")]))

        result = override_by_env_specific_profiles({}, {"bss": str(env_profile)}, _render_context("false"), {},
                                                   {"bss": str(generated)})

        assert result == {"bss": str(tmp_path / "Profiles" / "bss-profile-override.yml")}
        assembled = env_instance_store.get(result["bss"])
        assert assembled["name"] == "bss-profile-override"
        assert _apps_of(assembled) == {"Core": "prod", "Reporting": "prod"}
        assert _params_of(assembled) == {"replicas": 3}
        assert _apps_of(env_instance_store.get(env_profile)) == {"Core": "dev"}

    def test_generated_override_replaces_the_template_profile_in_replace_mode(self, tmp_path, env_instance_store):
        template_profile = tmp_path / "tmpl.yml"
        generated = tmp_path / "bss-profile-override.yml"
        env_instance_store.put(template_profile, _apps_profile("tmpl", "dev", [_app("Core", "dev")]))
        env_instance_store.put(generated, _apps_profile("bss-profile-override", "prod", [_app("Core", "prod"),
                                                                                        _app("Reporting", "prod")]))

        result = override_by_env_specific_profiles({"bss": str(template_profile)}, {}, _render_context("false"), {},
                                                   {"bss": str(generated)})

        assert result == {"bss": str(tmp_path / "Profiles" / "bss-profile-override.yml")}
        assembled = env_instance_store.get(result["bss"])
        assert assembled["name"] == "bss-profile-override"
        assert _apps_of(assembled) == {"Core": "prod", "Reporting": "prod"}
        assert _apps_of(env_instance_store.get(template_profile)) == {"Core": "dev"}

    def test_env_profiles_of_the_same_name_are_merged_per_key(self, tmp_path, env_instance_store):
        shared = tmp_path / "shared.yml"
        generated = tmp_path / "bss-profile-override.yml"
        env_instance_store.put(shared, _profile("shared", params={"a": 1}))
        env_instance_store.put(generated, _profile("bss-profile-override", params={"b": 2}))

        with patch("build_env.resource_profiles.logger") as logger:
            result = override_by_env_specific_profiles({}, {"bss": str(shared), "oss": str(shared)},
                                                       _render_context("true"), {},
                                                       {"bss": str(generated), "oss": str(generated)})

        assert result["bss"] == str(tmp_path / "Profiles" / "shared.yml")
        assert result["oss"] == str(tmp_path / "Profiles" / "shared-oss.yml")
        logger.warning.assert_called()
        assert _params_of(env_instance_store.get(result["bss"])) == {"a": 1, "b": 2}
        assert env_instance_store.get(result["oss"])["name"] == "shared-oss"
        assert _params_of(env_instance_store.get(shared)) == {"a": 1}

    def test_an_assembled_profile_never_shares_a_name_with_a_standalone_override(self, tmp_path, env_instance_store):
        shared = tmp_path / "Inventory" / "resource_profiles" / "shared.yml"
        generated = tmp_path / "bss-profile-override.yml"
        env_instance_store.put(shared, _profile("shared", params={"a": 1}))
        env_instance_store.put(generated, _profile("bss-profile-override", params={"b": 2}))

        with patch("build_env.resource_profiles.logger") as logger:
            result = override_by_env_specific_profiles({}, {"bss": str(shared), "oss": str(shared)},
                                                       _render_context("true"), {}, {"bss": str(generated)})

        assert result["oss"] == str(shared)
        assert result["bss"] == str(tmp_path / "Profiles" / "shared-bss.yml")
        logger.warning.assert_called()
        assert _params_of(env_instance_store.get(result["bss"])) == {"a": 1, "b": 2}
        assert _params_of(env_instance_store.get(shared)) == {"a": 1}


class TestDropProfilesWithoutObject:

    def test_a_key_without_an_object_is_dropped(self):
        all_profiles = {"bss-origin": "/tmpl/bss-origin.yml"}
        generated_map = {"bss": str(Path("Profiles") / "bss-profile-override.yml")}
        object_paths = {"cloud": "/cloud.yml", "bss-origin": "/ns/bss-origin/namespace.yml"}

        with patch("build_env.resource_profiles.logger") as logger:
            dropped = drop_profiles_without_object(object_paths, all_profiles, generated_map)

        assert dropped == ["bss"]
        assert all_profiles == {"bss-origin": "/tmpl/bss-origin.yml"}
        assert generated_map == {}
        logger.warning.assert_called()

    def test_every_key_with_an_object_is_kept(self):
        all_profiles = {"bss": "/tmpl/bss.yml"}
        generated_map = {"cloud": str(Path("Profiles") / "cloud-profile-override.yml")}
        object_paths = {"cloud": "/cloud.yml", "bss": "/ns/bss/namespace.yml"}

        with patch("build_env.resource_profiles.logger") as logger:
            dropped = drop_profiles_without_object(object_paths, all_profiles, generated_map)

        assert dropped == []
        assert all_profiles == {"bss": "/tmpl/bss.yml"}
        assert generated_map == {"cloud": str(Path("Profiles") / "cloud-profile-override.yml")}
        logger.warning.assert_not_called()

    def test_the_warning_names_the_sides_a_blue_green_key_missed(self):
        generated_map = {"bss": str(Path("Profiles") / "bss-profile-override.yml")}
        object_paths = {"bss-origin": "/ns/bss-origin/namespace.yml", "bss-peer": "/ns/bss-peer/namespace.yml"}

        with patch("build_env.resource_profiles.logger") as logger:
            drop_profiles_without_object(object_paths, generated_map)

        message = logger.warning.call_args.args[0]
        assert GENERATED_PROFILES_MAP_KEY in message
        assert "'bss-origin' or 'bss-peer'" in message


class TestWarnOnProfileNameCollisions:

    def test_two_files_of_one_name_are_reported(self):
        all_profiles = {"bss": "/templates/Profiles/foo.yml", "oss": "/env/Inventory/resource_profiles/foo.yml"}

        with patch("build_env.resource_profiles.logger") as logger:
            collisions = warn_on_profile_name_collisions(all_profiles)

        assert collisions == [("foo.yml", "/templates/Profiles/foo.yml", "/env/Inventory/resource_profiles/foo.yml")]
        assert logger.warning.call_count == 1

    def test_two_objects_of_one_file_are_not_a_collision(self):
        all_profiles = {"bss": "/env/Inventory/resource_profiles/foo.yml",
                        "oss": "/env/Inventory/resource_profiles/foo.yml"}

        with patch("build_env.resource_profiles.logger") as logger:
            collisions = warn_on_profile_name_collisions(all_profiles)

        assert collisions == []
        logger.warning.assert_not_called()

    def test_distinct_names_are_not_reported(self):
        all_profiles = {"bss": "/templates/Profiles/foo.yml", "oss": "/env/resource_profiles/bar.yml"}

        with patch("build_env.resource_profiles.logger") as logger:
            collisions = warn_on_profile_name_collisions(all_profiles)

        assert collisions == []
        logger.warning.assert_not_called()


class TestSetObjectProfileField:
    def test_sets_name_when_object_has_no_profile(self, tmp_path, env_instance_store):
        ns_file = tmp_path / "namespace.yml"
        namespace = env_instance_store.put(ns_file, readYaml("name: bss"))
        set_object_profile_field(ns_file, "name", "env-over")
        assert namespace["profile"]["name"] == "env-over"

    def test_sets_name_when_profile_is_null(self, tmp_path, env_instance_store):
        ns_file = tmp_path / "namespace.yml"
        namespace = env_instance_store.put(ns_file, readYaml("name: bss\nprofile:\n"))
        set_object_profile_field(ns_file, "name", "env-over")
        assert namespace["profile"]["name"] == "env-over"

    def test_replaces_name_and_baseline_of_existing_profile(self, tmp_path, env_instance_store):
        ns_file = tmp_path / "namespace.yml"
        namespace = env_instance_store.put(ns_file, readYaml("name: bss\nprofile:\n  name: tmpl\n  baseline: dev\n"))
        set_object_profile_field(ns_file, "name", "env-over")
        set_object_profile_field(ns_file, "baseline", "prod")
        assert namespace["profile"] == {"name": "env-over", "baseline": "prod"}

    def test_same_value_leaves_object_untouched(self, tmp_path, env_instance_store):
        ns_file = tmp_path / "namespace.yml"
        content = "name: bss\nprofile:\n    baseline:   dev\n    name: tmpl\n"
        namespace = env_instance_store.put(ns_file, readYaml(content))
        text_before = dumpYamlToStr(namespace)
        set_object_profile_field(ns_file, "baseline", "dev")
        assert dumpYamlToStr(namespace) == text_before


class TestHasValidProfileName:
    @pytest.mark.parametrize("content", [
        "name: bss",
        "name: bss\nprofile:\n",
        "name: bss\nprofile: tmpl",
        "name: bss\nprofile:\n  name: ''",
    ])
    def test_object_without_profile_name(self, content):
        assert not has_valid_profile_name(readYaml(content))

    def test_object_with_profile_name(self):
        assert has_valid_profile_name(readYaml("name: bss\nprofile:\n  name: tmpl"))


class TestValidateResourceProfiles:
    @staticmethod
    def _write(tmp_path, name, content):
        path = tmp_path / f"{name}.yml"
        path.write_text(content, encoding="utf-8")
        return str(path)

    def test_no_referenced_profiles(self, tmp_path):
        assert validate_resource_profiles({}, tmp_path, RP_SCHEMA) == {}

    def test_referenced_profiles_found_and_valid(self, tmp_path, env_instance_store):
        path = self._write(tmp_path, "tmpl", "name: tmpl\nbaseline: dev\n")
        assert validate_resource_profiles({"bss": "tmpl"}, tmp_path, RP_SCHEMA) == {"bss": path}

    def test_last_profile_with_the_same_name_is_used(self, tmp_path, env_instance_store):
        self._write(tmp_path, "tmpl", "name: tmpl\nbaseline: dev\n")
        (tmp_path / "nested").mkdir()
        last_path = tmp_path / "nested" / "tmpl.yaml"
        last_path.write_text("name: tmpl\nbaseline: prod\n", encoding="utf-8")
        assert validate_resource_profiles({"bss": "tmpl"}, tmp_path, RP_SCHEMA) == {"bss": str(last_path)}

    def test_referenced_profile_not_found_fails(self, tmp_path, env_instance_store):
        self._write(tmp_path, "tmpl", "name: tmpl\n")
        with pytest.raises(ReferenceError):
            validate_resource_profiles({"bss": "tmpl", "core": "missing"}, tmp_path, RP_SCHEMA)

    def test_referenced_profile_invalid_by_schema_fails(self, tmp_path, env_instance_store):
        self._write(tmp_path, "tmpl", "name: tmpl\napplications: wrong\n")
        with pytest.raises(ReferenceError):
            validate_resource_profiles({"bss": "tmpl"}, tmp_path, RP_SCHEMA)


class TestGetEnvSpecificResourceProfiles:
    @pytest.fixture
    def env_dir(self, tmp_path):
        env_dir = tmp_path / "instances" / "cluster-01" / "env-01"
        (env_dir / "Inventory").mkdir(parents=True)
        return env_dir

    @staticmethod
    def _env_definition(profiles, generated=None):
        env_template = {"name": "tmpl"}
        if profiles is not None:
            env_template["envSpecificResourceProfiles"] = profiles
        if generated is not None:
            env_template[GENERATED_PROFILES_MAP_KEY] = generated
        return {"envTemplate": env_template}

    @staticmethod
    def _write_profile(folder, name, baseline):
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / f"{name}.yml"
        writeYamlToFile(path, _profile(name, baseline=baseline))
        return path

    def test_no_section_returns_empty(self, env_dir, env_instance_store):
        assert get_resource_profiles_map(env_dir, env_dir.parents[1], RP_SCHEMA,
                                                   self._env_definition(None)) == {}

    def test_finds_profile_in_environment_folder(self, env_dir, env_instance_store):
        path = self._write_profile(env_dir / "Inventory" / "resource_profiles", "bss-over", "prod")
        assert get_resource_profiles_map(env_dir, env_dir.parents[1], RP_SCHEMA,
                                                   self._env_definition({"bss": "bss-over"})) == {"bss": str(path)}

    def test_environment_level_wins_over_cluster_and_global(self, env_dir, env_instance_store):
        self._write_profile(env_dir.parents[1] / "resource_profiles", "bss-over", "global")
        self._write_profile(env_dir.parent / "resource_profiles", "bss-over", "cluster")
        path = self._write_profile(env_dir / "Inventory" / "resource_profiles", "bss-over", "env")
        assert get_resource_profiles_map(env_dir, env_dir.parents[1], RP_SCHEMA,
                                                   self._env_definition({"bss": "bss-over"})) == {"bss": str(path)}

    def test_falls_back_to_cluster_level(self, env_dir, env_instance_store):
        self._write_profile(env_dir.parents[1] / "resource_profiles", "bss-over", "global")
        path = self._write_profile(env_dir.parent / "resource_profiles", "bss-over", "cluster")
        assert get_resource_profiles_map(env_dir, env_dir.parents[1], RP_SCHEMA,
                                                   self._env_definition({"bss": "bss-over"})) == {"bss": str(path)}

    def test_missing_profile_fails(self, env_dir, env_instance_store):
        with pytest.raises(ReferenceError):
            get_resource_profiles_map(env_dir, env_dir.parents[1], RP_SCHEMA,
                                               self._env_definition({"bss": "bss-over"}))

    def test_generated_profiles_are_resolved_by_name(self, env_dir, env_instance_store):
        generated_name = profile_override_name("bss")
        assert generated_name.endswith(PROFILE_OVERRIDE_SUFFIX)
        path = self._write_profile(env_dir / "Inventory" / "resource_profiles", generated_name, "prod")
        assert get_resource_profiles_map(env_dir, env_dir.parents[1], RP_SCHEMA,
                                                   self._env_definition(None, {
                                                       "bss": generated_name}),
                                                   GENERATED_PROFILES_MAP_KEY) == {"bss": str(path)}

    def test_no_generated_section_returns_empty(self, env_dir, env_instance_store):
        assert get_resource_profiles_map(env_dir, env_dir.parents[1], RP_SCHEMA,
                                                   self._env_definition({"bss": "bss-over"}),
                                                   GENERATED_PROFILES_MAP_KEY) == {}

    def test_reserved_name_is_ignored_in_the_user_map(self, env_dir, env_instance_store):
        generated_name = profile_override_name("bss")
        self._write_profile(env_dir / "Inventory" / "resource_profiles", generated_name, "stage")
        with patch("build_env.resource_profiles.logger") as logger:
            found = get_resource_profiles_map(env_dir, env_dir.parents[1], RP_SCHEMA,
                                                        self._env_definition({"bss": generated_name}))
        assert found == {}
        logger.warning.assert_called()

    def test_another_name_is_kept_in_the_user_map(self, env_dir, env_instance_store):
        path = self._write_profile(env_dir / "Inventory" / "resource_profiles", "bss-profile", "stage")
        assert get_resource_profiles_map(env_dir, env_dir.parents[1], RP_SCHEMA,
                                                   self._env_definition({"bss": "bss-profile"})) == {"bss": str(path)}
