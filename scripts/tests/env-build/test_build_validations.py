import pytest

from build_env.render_config_env import EnvGenerator
from envgenehelper import open_current_env_instance_store

BGD = {
    "name": "bgd",
    "originNamespace": {"name": "env-origin"},
    "peerNamespace": {"name": "env-peer"},
    "controllerNamespace": {"name": "env-controller"},
}


def _validate_bgd(env_dir, namespace_names):
    with open_current_env_instance_store(env_dir) as env_instance_store:
        env_instance_store.put(env_dir / "bg_domain.yml", dict(BGD))
        for name in namespace_names:
            env_instance_store.put(env_dir / "Namespaces" / name / "namespace.yml", {"name": name})
        EnvGenerator().validate_bgd()


class TestValidateBgd:
    def test_matching_names_pass(self, tmp_path):
        _validate_bgd(tmp_path / "env", ["env-origin", "env-peer", "env-controller"])

    def test_mismatched_name_fails(self, tmp_path):
        with pytest.raises(ValueError, match="env-controller"):
            _validate_bgd(tmp_path / "env", ["env-origin", "env-peer", "controller"])

    def test_ignores_namespaces_on_disk(self, tmp_path):
        env_dir = tmp_path / "env"
        stale = env_dir / "Namespaces" / "env-controller" / "namespace.yml"
        stale.parent.mkdir(parents=True)
        stale.write_text("name: env-controller\n")

        with pytest.raises(ValueError):
            _validate_bgd(env_dir, ["env-origin", "env-peer"])


def _paramset(path, name, parameters="{}"):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"name: {name}\nparameters: {parameters}\napplications: []\n")


def _generate(params_dir, used_names):
    generator = EnvGenerator()
    generator.ctx.render_parameters_dir = str(params_dir)
    generator.generate_paramset_templates(used_names)
    generator.validate_used_paramsets(used_names)


class TestGenerateParamsetTemplates:
    def test_unused_invalid_paramset_is_ignored(self, tmp_path):
        params = tmp_path / "parameters"
        _paramset(params / "from_template" / "used.yml", "used")
        _paramset(params / "from_template" / "unused.yml", "other")
        _paramset(params / "from_template" / "unused_j2.yml.j2", "other", "[]")

        _generate(params, {"used"})

        assert (params / "from_template" / "unused_j2.yml.j2").exists()

    def test_used_paramset_with_wrong_name_fails(self, tmp_path):
        params = tmp_path / "parameters"
        _paramset(params / "from_instance" / "used.yml", "other")

        with pytest.raises(ReferenceError):
            _generate(params, {"used"})

    def test_used_paramset_invalid_by_schema_fails(self, tmp_path):
        params = tmp_path / "parameters"
        _paramset(params / "from_template" / "used.yml", "used", "[]")

        with pytest.raises(ReferenceError):
            _generate(params, {"used"})

    def test_used_template_is_rendered(self, tmp_path):
        params = tmp_path / "parameters"
        _paramset(params / "from_template" / "used.yml.j2", "{{ 'us' ~ 'ed' }}")

        _generate(params, {"used"})

        assert (params / "from_template" / "used.yml").read_text() == "name: used\nparameters: {}\napplications: []\n"
        assert not (params / "from_template" / "used.yml.j2").exists()

    def test_used_template_rendered_invalid_fails(self, tmp_path):
        params = tmp_path / "parameters"
        _paramset(params / "from_template" / "used.yml.j2", "{{ 'other' }}")

        with pytest.raises(ReferenceError):
            _generate(params, {"used"})

    def test_duplicate_in_one_template_fails(self, tmp_path):
        params = tmp_path / "parameters" / "from_template"
        _paramset(params / "a" / "used.yml", "used")
        _paramset(params / "b" / "used.yaml.j2", "used")

        with pytest.raises(ReferenceError):
            _generate(params.parent, {"used"})

    def test_same_name_on_different_levels_is_override(self, tmp_path):
        params = tmp_path / "parameters"
        _paramset(params / "from_template" / "used.yml", "used")
        _paramset(params / "from_origin_template" / "used.yml", "used")
        _paramset(params / "used.yml", "used")
        _paramset(params / "from_instance" / "used.yml", "used")

        _generate(params, {"used"})
