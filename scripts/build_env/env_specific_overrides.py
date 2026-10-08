from pathlib import Path

from envgenehelper import current_env_instance_store
from envgenehelper.business_helper import get_namespaces_path

ENV_SPECIFIC_TARGET_FIELDS = (
    "envSpecificParamsets",
    "envSpecificE2EParamsets",
    "envSpecificTechnicalParamsets",
    "envSpecificResourceProfiles",
)


def validate_env_specific_override_keys(env_dir: Path | str, env_definition: dict) -> None:
    env_dir = Path(env_dir)
    env_template = env_definition.get("envTemplate", {})

    namespaces_path = get_namespaces_path(env_dir)
    available_keys = {"cloud"}
    namespace_files = current_env_instance_store().list(namespaces_path / "*" / "namespace.yml")
    available_keys |= {p.parent.name for p in namespace_files}

    for field_name in ENV_SPECIFIC_TARGET_FIELDS:
        field_value = env_template.get(field_name)
        if not isinstance(field_value, dict):
            continue
        for key in sorted(field_value):
            if key in available_keys:
                continue

            sorted_keys = sorted(available_keys)
            available_label = ", ".join(f"'{available_key}'" for available_key in sorted_keys) or "(none)"
            message = (
                f"Invalid key '{key}' in envTemplate.{field_name}. "
                f"Expected 'cloud' or one of the namespace folders: {available_label}."
            )

            hints = []
            for suffix in ("-origin", "-peer"):
                candidate = f"{key}{suffix}"
                if candidate in available_keys:
                    hints.append(f"'{candidate}'")
            if hints:
                message += f" Did you mean {' or '.join(hints)}?"

            raise ReferenceError(message)
