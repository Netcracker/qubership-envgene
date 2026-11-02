import tempfile
from pathlib import Path

import pytest
from ruamel.yaml import YAML

from build_env.env_specific_overrides import validate_env_specific_override_keys
from envgenehelper import open_current_env_instance_store


def _write_env_definition(env_dir: Path, env_template: dict) -> None:
    inventory_dir = env_dir / "Inventory"
    inventory_dir.mkdir(parents=True, exist_ok=True)

    env_definition = {
        "inventory": {"environmentName": "demo-env"},
        "envTemplate": env_template,
    }

    yaml = YAML()
    with (inventory_dir / "env_definition.yml").open("w", encoding="utf-8") as f:
        yaml.dump(env_definition, f)


def _validate_override_keys(env_dir: Path, namespace_postfixes: list[str]) -> None:
    with open_current_env_instance_store(env_dir) as env_instance_store:
        for postfix in namespace_postfixes:
            env_instance_store.put(env_dir / "Namespaces" / postfix / "namespace.yml", {"name": postfix})
        env_definition = YAML().load((env_dir / "Inventory" / "env_definition.yml").read_text(encoding="utf-8"))
        validate_env_specific_override_keys(env_dir, env_definition)


class TestEnvSpecificOverrideKeys:
    def test_accepts_known_keys(self):
        with tempfile.TemporaryDirectory(prefix="env-override-keys-") as tmp:
            env_dir = Path(tmp)
            _write_env_definition(
                env_dir,
                {
                    "name": "demo-template",
                    "envSpecificParamsets": {"bss": ["some-paramset"], "cloud": ["cloud-paramset"]},
                    "envSpecificResourceProfiles": {"bss": "bss-override"},
                },
            )

            _validate_override_keys(env_dir, ["bss"])

    def test_rejects_unknown_key(self):
        with tempfile.TemporaryDirectory(prefix="env-override-keys-") as tmp:
            env_dir = Path(tmp)
            _write_env_definition(
                env_dir,
                {
                    "name": "demo-template",
                    "envSpecificParamsets": {"bss": ["some-paramset"]},
                },
            )

            with pytest.raises(ReferenceError, match="envTemplate.envSpecificParamsets"):
                _validate_override_keys(env_dir, ["bss-peer"])

    def test_suggests_bgd_origin_suffix(self):
        with tempfile.TemporaryDirectory(prefix="env-override-keys-") as tmp:
            env_dir = Path(tmp)
            _write_env_definition(
                env_dir,
                {
                    "name": "demo-template",
                    "envSpecificParamsets": {"bss": ["some-paramset"]},
                },
            )

            with pytest.raises(ReferenceError) as exc_info:
                _validate_override_keys(env_dir, ["bss-origin", "bss-peer"])

            message = str(exc_info.value)
            assert (
                "Invalid key 'bss' in envTemplate.envSpecificParamsets. "
                "Expected 'cloud' or one of the namespace folders: "
                "'bss-origin', 'bss-peer', 'cloud'. "
                "Did you mean 'bss-origin' or 'bss-peer'?"
            ) == message

    def test_empty_or_missing_maps_pass(self):
        with tempfile.TemporaryDirectory(prefix="env-override-keys-") as tmp:
            env_dir = Path(tmp)
            _write_env_definition(env_dir, {"name": "demo-template"})

            _validate_override_keys(env_dir, ["bss"])
