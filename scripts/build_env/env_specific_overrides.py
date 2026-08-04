from pathlib import Path

from envgenehelper import check_dir_exists, getEnvDefinition
from envgenehelper.business_helper import get_namespaces_path

ENV_SPECIFIC_TARGET_FIELDS = (
    "envSpecificParamsets",
    "envSpecificE2EParamsets",
    "envSpecificTechnicalParamsets",
    "envSpecificResourceProfiles",
)


def validate_env_specific_override_keys(env_dir: Path | str) -> None:
    env_dir = Path(env_dir)
    env_template = getEnvDefinition(str(env_dir)).get("envTemplate", {})

    namespaces_path = get_namespaces_path(env_dir)
    available_keys = {"cloud"}
    if check_dir_exists(str(namespaces_path)):
        available_keys |= {p.name for p in namespaces_path.iterdir() if p.is_dir()}

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
                f"Key '{key}' in envTemplate.{field_name} does not match "
                f"'cloud' or any namespace folder name under Namespaces/ in the "
                f"Environment Instance. Keys must be the namespace folder name "
                f"(the folder under Namespaces/, or 'cloud' for the cloud template). "
                f"Available keys: {available_label}."
            )

            hints = []
            for suffix, role_label in (("-origin", "origin"), ("-peer", "peer")):
                candidate = f"{key}{suffix}"
                if candidate in available_keys:
                    hints.append(
                        f"Did you mean '{candidate}'? Blue-green namespace templates append "
                        f"'{suffix}' to the deploy postfix for the {role_label} namespace."
                    )
            if hints:
                message += " " + " ".join(hints)

            raise ReferenceError(message)
