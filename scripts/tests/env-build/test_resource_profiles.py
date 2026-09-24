import json
from pathlib import Path
from unittest.mock import MagicMock, patch

from envgenehelper import openYaml, readYaml, writeYamlToFile

from build_env.resource_profiles import merge_resource_profiles, override_by_env_specific_profiles, \
    update_profile_name


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

    def test_missing_applications_on_both_sides(self):
        template = _profile("tmpl", baseline="dev")
        merge_resource_profiles(template, _profile("env", params={"replicas": 2}), "env")
        assert template["applications"][0]["name"] == "app"


class TestOverrideByEnvSpecificProfiles:
    def test_standalone_override_is_attached(self, tmp_path):
        env_profile = tmp_path / "env-over.yml"
        writeYamlToFile(env_profile, _profile("env-over", baseline="prod"))
        result = override_by_env_specific_profiles({}, {"bss": str(env_profile)}, _render_context("true"))
        assert result == {"bss": str(env_profile)}

    def test_template_only_is_untouched(self, tmp_path):
        template_profile = tmp_path / "tmpl.yml"
        writeYamlToFile(template_profile, _profile("tmpl", baseline="dev", params={"replicas": 3}))
        result = override_by_env_specific_profiles({"bss": str(template_profile)}, {}, _render_context("true"))
        assert result == {}
        assert openYaml(template_profile)["baseline"] == "dev"

    def test_standalone_override_is_attached_in_replace_mode(self, tmp_path):
        env_profile = tmp_path / "env-over.yml"
        writeYamlToFile(env_profile, _profile("env-over", baseline="prod"))
        result = override_by_env_specific_profiles({}, {"bss": str(env_profile)}, _render_context("false"))
        assert result == {"bss": str(env_profile)}

    def test_replace_drops_template_profile(self, tmp_path):
        template_profile = tmp_path / "tmpl.yml"
        env_profile = tmp_path / "env-over.yml"
        writeYamlToFile(template_profile, _profile("tmpl", baseline="dev", params={"replicas": 3}))
        writeYamlToFile(env_profile, _profile("env-over", baseline="prod", params={"cpu": 2}))
        result = override_by_env_specific_profiles({"bss": str(template_profile)}, {"bss": str(env_profile)},
                                                   _render_context("false"))
        assert result == {"bss": str(env_profile)}
        assert openYaml(template_profile)["baseline"] == "dev"

    def test_merge_writes_env_specific_baseline(self, tmp_path):
        template_profile = tmp_path / "tmpl.yml"
        env_profile = tmp_path / "env-over.yml"
        writeYamlToFile(template_profile, _profile("tmpl", baseline="dev"))
        writeYamlToFile(env_profile, _profile("env-over", baseline="prod"))
        result = override_by_env_specific_profiles({"bss": str(template_profile)}, {"bss": str(env_profile)},
                                                   _render_context("true"))
        assert result == {}
        assert openYaml(template_profile)["baseline"] == "prod"


class TestUpdateProfileName:
    def test_sets_name_when_object_has_no_profile(self, tmp_path):
        ns_file = tmp_path / "namespace.yml"
        writeYamlToFile(ns_file, readYaml("name: bss"))
        update_profile_name(ns_file, "env-over")
        assert openYaml(ns_file)["profile"]["name"] == "env-over"

    def test_sets_name_when_profile_is_null(self, tmp_path):
        ns_file = tmp_path / "namespace.yml"
        Path(ns_file).write_text("name: bss\nprofile:\n", encoding="utf-8")
        update_profile_name(ns_file, "env-over")
        assert openYaml(ns_file)["profile"]["name"] == "env-over"
