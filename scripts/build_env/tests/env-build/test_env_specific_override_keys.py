import tempfile
from pathlib import Path

import pytest
from ruamel.yaml import YAML

from env_specific_overrides import validate_env_specific_override_keys


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


def _write_namespace(env_dir: Path, postfix: str, name: str | None = None) -> None:
    ns_dir = env_dir / "Namespaces" / postfix
    ns_dir.mkdir(parents=True, exist_ok=True)
    namespace_name = name or postfix
    yaml = YAML()
    with (ns_dir / "namespace.yml").open("w", encoding="utf-8") as f:
        yaml.dump({"name": namespace_name}, f)


class TestEnvSpecificOverrideKeys:
    def test_accepts_known_keys(self):
        with tempfile.TemporaryDirectory(prefix="env-override-keys-") as tmp:
            env_dir = Path(tmp)
            _write_namespace(env_dir, "bss")
            _write_env_definition(
                env_dir,
                {
                    "name": "demo-template",
                    "envSpecificParamsets": {"bss": ["some-paramset"], "cloud": ["cloud-paramset"]},
                    "envSpecificResourceProfiles": {"bss": "bss-override"},
                },
            )

            validate_env_specific_override_keys(env_dir)

    def test_rejects_unknown_key(self):
        with tempfile.TemporaryDirectory(prefix="env-override-keys-") as tmp:
            env_dir = Path(tmp)
            _write_namespace(env_dir, "bss-peer")
            _write_env_definition(
                env_dir,
                {
                    "name": "demo-template",
                    "envSpecificParamsets": {"bss": ["some-paramset"]},
                },
            )

            with pytest.raises(ReferenceError, match="envTemplate.envSpecificParamsets"):
                validate_env_specific_override_keys(env_dir)

    def test_suggests_bgd_origin_suffix(self):
        with tempfile.TemporaryDirectory(prefix="env-override-keys-") as tmp:
            env_dir = Path(tmp)
            _write_namespace(env_dir, "bss-origin")
            _write_env_definition(
                env_dir,
                {
                    "name": "demo-template",
                    "envSpecificParamsets": {"bss": ["some-paramset"]},
                },
            )

            with pytest.raises(ReferenceError) as exc_info:
                validate_env_specific_override_keys(env_dir)

            message = str(exc_info.value)
            assert "Did you mean 'bss-origin'?" in message

    def test_empty_or_missing_maps_pass(self):
        with tempfile.TemporaryDirectory(prefix="env-override-keys-") as tmp:
            env_dir = Path(tmp)
            _write_namespace(env_dir, "bss")
            _write_env_definition(env_dir, {"name": "demo-template"})

            validate_env_specific_override_keys(env_dir)
