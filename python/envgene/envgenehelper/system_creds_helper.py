import json
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

from envgenehelper.errors import ValidationError

from .logger import logger

DEFAULT_SECRET_STORE = "default_store"
EXTERNAL_CRED_TYPE = "external"
SUPPORTED_SYSTEM_STORE_TYPES = {"vault", "gcp"}
UNSUPPORTED_SYSTEM_STORE_TYPES = {"aws", "azure"}


def resolve_secret_store_id(credential: dict) -> str:
    store = credential.get("secretStore")
    if not isinstance(store, str) or not store.strip():
        return DEFAULT_SECRET_STORE
    return store


def get_secret_stores_config(base_dir: Optional[Path] = None) -> dict:
    base = Path(base_dir or os.environ.get("CI_PROJECT_DIR", "."))
    stores_path = base / "configuration" / "secret-stores.yml"
    if not stores_path.exists():
        return {}
    from .yaml_helper import openYaml
    return openYaml(stores_path) or {}


def validate_system_credential(cred_id: str, credential: dict, secret_stores: dict) -> None:
    if not isinstance(credential, dict) or credential.get("type") != EXTERNAL_CRED_TYPE:
        return
    if credential.get("create") is True:
        raise ValidationError(
            f"System credential '{cred_id}' must not declare create: true; "
            "system credentials are pre-created in the external Secret Store"
        )
    store_id = resolve_secret_store_id(credential)
    store = secret_stores.get(store_id)
    if store is None:
        raise ValidationError(
            f"System credential '{cred_id}' references secret store '{store_id}' "
            "which is not defined in /configuration/secret-stores.yml"
        )
    store_type = store.get("type")
    if store_type in UNSUPPORTED_SYSTEM_STORE_TYPES:
        raise ValidationError(
            f"System credential '{cred_id}' uses secret store '{store_id}' with type '{store_type}'; "
            "only vault and gcp are supported for system credentials"
        )


def validate_system_credentials(cred_config: dict, secret_stores: Optional[dict] = None) -> None:
    if not cred_config:
        return
    stores = secret_stores if secret_stores is not None else get_secret_stores_config()
    for cred_id, credential in cred_config.items():
        validate_system_credential(cred_id, credential, stores)


def _vals_ref_cli_path() -> str:
    return os.environ.get("EXTCREDS_VALS_REF_CLI", "/module/bin/extcreds-vals-ref")


def _system_cred_paths(base_dir: Optional[Path] = None) -> tuple[Path, Path]:
    base = Path(base_dir or os.environ.get("CI_PROJECT_DIR", "."))
    credentials_path = base / "configuration" / "credentials" / "credentials.yml"
    secret_stores_path = base / "configuration" / "secret-stores.yml"
    return credentials_path, secret_stores_path


def build_vals_reference(
    cred_id: str,
    property_name: Optional[str],
    base_dir: Optional[Path] = None,
) -> str:
    credentials_path, secret_stores_path = _system_cred_paths(base_dir)
    if not credentials_path.exists():
        raise ValueError(f"System credentials file not found: {credentials_path}")
    if not secret_stores_path.exists():
        raise ValueError(f"Secret stores file not found: {secret_stores_path}")

    request = {"credId": cred_id}
    if property_name:
        request["property"] = property_name

    requests_payload = {"requests": [request]}
    requests_file = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as handle:
            json.dump(requests_payload, handle)
            requests_file = handle.name

        cmd = [
            _vals_ref_cli_path(),
            "--credentials", str(credentials_path),
            "--secret-stores", str(secret_stores_path),
            "--requests", requests_file,
            "--fields", "vals",
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if result.returncode != 0:
            detail = result.stderr.strip() or result.stdout.strip() or "unknown error"
            raise ValueError(f"extcreds-vals-ref failed for credential '{cred_id}': {detail}")

        output = json.loads(result.stdout)
        errors = output.get("errors") or []
        if errors:
            raise ValueError(errors[0].get("message", f"Failed to build VALS reference for '{cred_id}'"))

        results = output.get("results") or []
        if not results or not results[0].get("valsReference"):
            raise ValueError(f"No VALS reference produced for credential '{cred_id}'")
        return results[0]["valsReference"]
    finally:
        if requests_file and os.path.exists(requests_file):
            os.unlink(requests_file)


def read_secret_from_vals(vals_reference: str) -> str:
    from qubership_pipelines_common_library.v2.secret_manager.providers.multi_store_provider import (
        MultiStoreProvider,
    )
    from qubership_pipelines_common_library.v2.secret_manager.secret_manager import SecretManager

    secret_manager = SecretManager(secret_provider=MultiStoreProvider())
    value = secret_manager.read_secret(vals_reference, fail_on_missing=True)
    if value is None:
        raise ValueError(f"Secret not found for VALS reference: {vals_reference}")
    return str(value)


def resolve_external_cred(
    cred_id: str,
    property_name: Optional[str],
    cred_config: dict,
    base_dir: Optional[Path] = None,
    secret_stores: Optional[dict] = None,
) -> str:
    credential = cred_config.get(cred_id)
    if not isinstance(credential, dict):
        raise ValueError(f"Credential '{cred_id}' not found in system credentials catalog")
    if credential.get("type") != EXTERNAL_CRED_TYPE:
        raise ValueError(f"Credential '{cred_id}' is not external")

    stores = secret_stores if secret_stores is not None else get_secret_stores_config(base_dir)
    validate_system_credential(cred_id, credential, stores)

    vals_reference = build_vals_reference(cred_id, property_name, base_dir)
    logger.debug(f"Resolved VALS reference for system credential '{cred_id}'")
    return read_secret_from_vals(vals_reference)


def resolve_cred_ref(
    cred_ref: dict,
    cred_config: dict,
    base_dir: Optional[Path] = None,
    secret_stores: Optional[dict] = None,
) -> str:
    from .creds_helper import extract_external_cred

    cred_id = extract_external_cred(cred_ref)
    property_name = cred_ref.get("property")
    return resolve_external_cred(cred_id, property_name, cred_config, base_dir, secret_stores)


def resolve_credential_data(
    cred_id: str,
    cred_config: dict,
    base_dir: Optional[Path] = None,
    secret_stores: Optional[dict] = None,
) -> dict:
    credential = cred_config.get(cred_id)
    if not isinstance(credential, dict):
        raise ValueError(f"Credential '{cred_id}' not found in system credentials catalog")

    if credential.get("type") == EXTERNAL_CRED_TYPE:
        properties = credential.get("properties") or []
        if properties:
            return {
                prop["name"]: resolve_external_cred(
                    cred_id, prop["name"], cred_config, base_dir, secret_stores
                )
                for prop in properties
                if isinstance(prop, dict) and prop.get("name")
            }
        return {
            "secret": resolve_external_cred(cred_id, None, cred_config, base_dir, secret_stores)
        }
    return credential.get("data", {})


def resolve_integration_param(
    integration_config: dict,
    param_name: str,
    env_var_names: list[str],
    cred_config: dict,
    base_dir: Optional[Path] = None,
) -> Optional[str]:
    if not integration_config or param_name not in integration_config:
        return _first_env_var(env_var_names)

    value = integration_config.get(param_name)
    if value is None or value == "":
        return _first_env_var(env_var_names)

    from .creds_helper import check_is_envgen_cred, fetch_cred_value

    if isinstance(value, dict) and value.get("$type") == "credRef":
        return fetch_cred_value(value, cred_config, base_dir=base_dir)
    if isinstance(value, str) and check_is_envgen_cred(value):
        return fetch_cred_value(value, cred_config, base_dir=base_dir)
    if isinstance(value, str):
        return value
    raise ValueError(f"Unsupported value for integration parameter '{param_name}': {value}")


def _first_env_var(env_var_names: list[str]) -> Optional[str]:
    for name in env_var_names:
        value = os.environ.get(name)
        if value:
            return value
    return None
