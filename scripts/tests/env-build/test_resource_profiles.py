import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from envgenehelper import openYaml, readYaml, writeYamlToFile

from build_env.resource_profiles import get_env_specific_resource_profiles, has_valid_profile_name, \
    merge_resource_profiles, override_by_env_specific_profiles, set_object_profile_field, validate_resource_profiles

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

    def test_empty_env_specific_baseline_is_absent(self):
        template = _profile("tmpl", baseline="dev")
        merge_resource_profiles(template, _profile("env", baseline=""), "env")
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


class TestOverrideByEnvSpecificProfiles:
    def test_standalone_override_is_attached(self, tmp_path):
        env_profile = tmp_path / "env-over.yml"
        writeYamlToFile(env_profile, _profile("env-over", baseline="prod"))
        result = override_by_env_specific_profiles({}, {"bss": str(env_profile)}, _render_context("true"), {})
        assert result == {"bss": str(env_profile)}

    def test_template_only_is_untouched(self, tmp_path):
        template_profile = tmp_path / "tmpl.yml"
        writeYamlToFile(template_profile, _profile("tmpl", baseline="dev", params={"replicas": 3}))
        result = override_by_env_specific_profiles({"bss": str(template_profile)}, {}, _render_context("true"), {})
        assert result == {}
        assert openYaml(template_profile)["baseline"] == "dev"

    def test_standalone_override_is_attached_in_replace_mode(self, tmp_path):
        env_profile = tmp_path / "env-over.yml"
        writeYamlToFile(env_profile, _profile("env-over", baseline="prod"))
        result = override_by_env_specific_profiles({}, {"bss": str(env_profile)}, _render_context("false"), {})
        assert result == {"bss": str(env_profile)}

    def test_replace_drops_template_profile(self, tmp_path):
        template_profile = tmp_path / "tmpl.yml"
        env_profile = tmp_path / "env-over.yml"
        writeYamlToFile(template_profile, _profile("tmpl", baseline="dev", params={"replicas": 3}))
        writeYamlToFile(env_profile, _profile("env-over", baseline="prod", params={"cpu": 2}))
        result = override_by_env_specific_profiles({"bss": str(template_profile)}, {"bss": str(env_profile)},
                                                   _render_context("false"), {})
        assert result == {"bss": str(env_profile)}
        assert openYaml(template_profile)["baseline"] == "dev"

    def test_merge_writes_env_specific_baseline(self, tmp_path):
        template_profile = tmp_path / "tmpl.yml"
        env_profile = tmp_path / "env-over.yml"
        writeYamlToFile(template_profile, _profile("tmpl", baseline="dev"))
        writeYamlToFile(env_profile, _profile("env-over", baseline="prod"))
        result = override_by_env_specific_profiles({"bss": str(template_profile)}, {"bss": str(env_profile)},
                                                   _render_context("true"), {})
        assert result == {}
        assert openYaml(template_profile)["baseline"] == "prod"

    def test_merge_compares_with_object_baseline(self, tmp_path):
        template_profile = tmp_path / "tmpl.yml"
        env_profile = tmp_path / "env-over.yml"
        writeYamlToFile(template_profile, _profile("tmpl", params={"replicas": 1}))
        writeYamlToFile(env_profile, _profile("env-over", baseline="dev"))
        with patch("build_env.resource_profiles.logger") as logger:
            override_by_env_specific_profiles({"bss": str(template_profile)}, {"bss": str(env_profile)},
                                              _render_context("true"), {"bss": "dev"})
        logger.warning.assert_not_called()

    def test_boolean_false_mode_replaces(self, tmp_path):
        template_profile = tmp_path / "tmpl.yml"
        env_profile = tmp_path / "env-over.yml"
        writeYamlToFile(template_profile, _profile("tmpl", baseline="dev"))
        writeYamlToFile(env_profile, _profile("env-over", baseline="prod"))
        result = override_by_env_specific_profiles({"bss": str(template_profile)}, {"bss": str(env_profile)},
                                                   _render_context(False), {})
        assert result == {"bss": str(env_profile)}
        assert openYaml(template_profile)["baseline"] == "dev"

    def test_merge_is_default_when_mode_not_configured(self, tmp_path):
        template_profile = tmp_path / "tmpl.yml"
        env_profile = tmp_path / "env-over.yml"
        writeYamlToFile(template_profile, _profile("tmpl", baseline="dev"))
        writeYamlToFile(env_profile, _profile("env-over", baseline="prod"))
        context = MagicMock()
        context.ctx.env_definition = {"inventory": {}}
        result = override_by_env_specific_profiles({"bss": str(template_profile)}, {"bss": str(env_profile)},
                                                   context, {})
        assert result == {}
        assert openYaml(template_profile)["baseline"] == "prod"


class TestSetObjectProfileField:
    def test_sets_name_when_object_has_no_profile(self, tmp_path):
        ns_file = tmp_path / "namespace.yml"
        writeYamlToFile(ns_file, readYaml("name: bss"))
        set_object_profile_field(ns_file, "name", "env-over")
        assert openYaml(ns_file)["profile"]["name"] == "env-over"

    def test_sets_name_when_profile_is_null(self, tmp_path):
        ns_file = tmp_path / "namespace.yml"
        Path(ns_file).write_text("name: bss\nprofile:\n", encoding="utf-8")
        set_object_profile_field(ns_file, "name", "env-over")
        assert openYaml(ns_file)["profile"]["name"] == "env-over"

    def test_replaces_name_and_baseline_of_existing_profile(self, tmp_path):
        ns_file = tmp_path / "namespace.yml"
        writeYamlToFile(ns_file, readYaml("name: bss\nprofile:\n  name: tmpl\n  baseline: dev\n"))
        set_object_profile_field(ns_file, "name", "env-over")
        set_object_profile_field(ns_file, "baseline", "prod")
        assert openYaml(ns_file)["profile"] == {"name": "env-over", "baseline": "prod"}

    def test_same_value_leaves_file_untouched(self, tmp_path):
        ns_file = tmp_path / "namespace.yml"
        content = "name: bss\nprofile:\n    baseline:   dev\n    name: tmpl\n"
        Path(ns_file).write_text(content, encoding="utf-8")
        set_object_profile_field(ns_file, "baseline", "dev")
        assert Path(ns_file).read_text(encoding="utf-8") == content


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

    def test_no_referenced_profiles(self):
        assert validate_resource_profiles({}, {}, RP_SCHEMA) == {}

    def test_referenced_profiles_found_and_valid(self, tmp_path):
        path = self._write(tmp_path, "tmpl", "name: tmpl\nbaseline: dev\n")
        assert validate_resource_profiles({"bss": "tmpl"}, {"tmpl": path}, RP_SCHEMA) == {"bss": path}

    def test_referenced_profile_not_found_fails(self, tmp_path):
        path = self._write(tmp_path, "tmpl", "name: tmpl\n")
        with pytest.raises(ReferenceError):
            validate_resource_profiles({"bss": "tmpl", "core": "missing"}, {"tmpl": path}, RP_SCHEMA)

    def test_referenced_profile_invalid_by_schema_fails(self, tmp_path):
        path = self._write(tmp_path, "tmpl", "name: tmpl\napplications: wrong\n")
        with pytest.raises(ReferenceError):
            validate_resource_profiles({"bss": "tmpl"}, {"tmpl": path}, RP_SCHEMA)


class TestGetEnvSpecificResourceProfiles:
    @pytest.fixture
    def env_dir(self, tmp_path):
        env_dir = tmp_path / "instances" / "cluster-01" / "env-01"
        (env_dir / "Inventory").mkdir(parents=True)
        return env_dir

    @staticmethod
    def _write_inventory(env_dir, profiles):
        env_template = {"name": "tmpl"}
        if profiles is not None:
            env_template["envSpecificResourceProfiles"] = profiles
        writeYamlToFile(env_dir / "Inventory" / "env_definition.yml", {"envTemplate": env_template})

    @staticmethod
    def _write_profile(folder, name, baseline):
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / f"{name}.yml"
        writeYamlToFile(path, _profile(name, baseline=baseline))
        return path

    def test_no_section_returns_empty(self, env_dir):
        self._write_inventory(env_dir, None)
        assert get_env_specific_resource_profiles(env_dir, env_dir.parents[1], RP_SCHEMA) == {}

    def test_finds_profile_in_environment_folder(self, env_dir):
        self._write_inventory(env_dir, {"bss": "bss-over"})
        path = self._write_profile(env_dir / "Inventory" / "resource_profiles", "bss-over", "prod")
        assert get_env_specific_resource_profiles(env_dir, env_dir.parents[1], RP_SCHEMA) == {"bss": str(path)}

    def test_environment_level_wins_over_cluster_and_global(self, env_dir):
        self._write_inventory(env_dir, {"bss": "bss-over"})
        self._write_profile(env_dir.parents[1] / "resource_profiles", "bss-over", "global")
        self._write_profile(env_dir.parent / "resource_profiles", "bss-over", "cluster")
        path = self._write_profile(env_dir / "Inventory" / "resource_profiles", "bss-over", "env")
        assert get_env_specific_resource_profiles(env_dir, env_dir.parents[1], RP_SCHEMA) == {"bss": str(path)}

    def test_falls_back_to_cluster_level(self, env_dir):
        self._write_inventory(env_dir, {"bss": "bss-over"})
        self._write_profile(env_dir.parents[1] / "resource_profiles", "bss-over", "global")
        path = self._write_profile(env_dir.parent / "resource_profiles", "bss-over", "cluster")
        assert get_env_specific_resource_profiles(env_dir, env_dir.parents[1], RP_SCHEMA) == {"bss": str(path)}

    def test_missing_profile_fails(self, env_dir):
        self._write_inventory(env_dir, {"bss": "bss-over"})
        with pytest.raises(ReferenceError):
            get_env_specific_resource_profiles(env_dir, env_dir.parents[1], RP_SCHEMA)
