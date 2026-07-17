import subprocess
import yaml
from functools import lru_cache
import json
from pathlib import Path
from typing import Any, Optional
from unittest import result

from envgenehelper import logger
from envgenehelper.business_helper import getenv_with_error
from envgenehelper.errors import ValidationError
from envgenehelper.models import ExternalCredential, SecretStore
from envgenehelper.yaml_helper import openYaml

from qubership_pipelines_common_library.v2.secret_manager.providers.multi_store_provider import MultiStoreProvider
from qubership_pipelines_common_library.v2.secret_manager.secret_manager import SecretManager

SECRET_STORE_FILE = "secret-stores.yml"
CONFIGURATION_DIR = "configuration"


def resolve_external_credential_reference(credential_reference: dict, credentials_config: dict,) -> str:
    cred_id = extract_external_cred(credential_reference)
    property_name = credential_reference.get("property")
    external_credential  = find_external_credential_by_id(cred_id, credentials_config)
    secret_store_type, secret_payload = _get_secret_store_payload_cached(cred_id, external_credential.model_dump_json())
    return _get_property_value(cred_id, property_name, secret_store_type, secret_payload)


def extract_external_cred(cred_map: dict) -> Optional[str]:
    if not is_external_credential_reference(cred_map):
        return None
    cred_id = cred_map.get("credId")
    if not isinstance(cred_id, str) or not cred_id.strip():
        raise ValueError(f"Invalid credRef: 'credId' is missing or empty in {cred_map}")
    return cred_id

    
def find_external_credential_by_id(cred_id: str, credentials_config: dict) -> ExternalCredential:
    credential = credentials_config.get(cred_id)
    if credential is None:
        raise ValidationError(f"Credential '{cred_id}' not found in credentials file")    
    external_credential = ExternalCredential.model_validate(credential)
    if external_credential.create:
        raise ValidationError(f"System Credential '{cred_id}' must not have create=true")
    return external_credential


@lru_cache(maxsize=50)
def _get_secret_store_payload_cached(cred_id: str, external_credential_json: str) -> Any:
    logger.info(f"Cache MISS for cred_id='{cred_id}'. Going to extract data from external secret store.")
    external_credential = ExternalCredential.model_validate_json(external_credential_json)
    secret_store = find_secret_store_by_id(external_credential.secretStore, cred_id)
    vals_reference_uri = _build_vals_reference(cred_id, external_credential, secret_store)
    secret_payload = _fetch_secret_from_store(vals_reference_uri)
    return secret_store.type, secret_payload


def find_secret_store_by_id(secret_store_id: str, cred_id: str) -> SecretStore:
    secret_stores_config = load_all_secret_stores()

    raw_store = secret_stores_config.get(secret_store_id)
    if raw_store is None:
        raise ValidationError(f"System credential '{cred_id}' references secret store '{secret_store_id}' "
             f"'which is not defined in base_dir/'{CONFIGURATION_DIR}/{SECRET_STORE_FILE}'")
    
    secret_store = SecretStore.model_validate(raw_store)

    return secret_store


def load_all_secret_stores(base_dir: Optional[Path] = None) -> dict:
    base_dir = Path(base_dir or getenv_with_error('CI_PROJECT_DIR'))    
    secret_store_config = base_dir / CONFIGURATION_DIR / SECRET_STORE_FILE
    if not secret_store_config.is_file():
        return {}
    return openYaml(secret_store_config) or {} 


def _build_vals_reference(cred_id: str, external_credential: ExternalCredential, secret_store: SecretStore) -> str:
    payload = json.dumps({
        "credentialId": cred_id,
        "credential": external_credential.model_dump(),
        "secretStore": secret_store.model_dump(),
    })

    logger.info(f"Calling vals-reference-cli for credId={cred_id}")
    cmd = ["/module/scripts/vals-reference-cli"]

    try:
        result = subprocess.run(cmd, input=payload, capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError as e:
        logger.error(f"Error occurred while calling vals-reference-cli: {e.stderr}")
        raise ValueError("Failed to build vals reference for external credential") from e
    
    output = json.loads(result.stdout) 
    return output.get(cred_id)

    
def _fetch_secret_from_store(vals_reference_uri: str) -> dict[str, Any] | str | None:
    logger.info(f"Fetching secret from external secret store using vals reference: {vals_reference_uri}")
    secret_manager = SecretManager(secret_provider=MultiStoreProvider())
    raw_payload = secret_manager.read_secret(vals_reference_uri, fail_on_missing=True)  
    parsed_payload = _parse_secret_payload(raw_payload)  
    return parsed_payload

def _parse_secret_payload(raw_payload: dict) -> dict[str, Any] | str | None:
    if raw_payload is None or not raw_payload.strip():
        return None
    try:
        parsed_payload = yaml.safe_load(raw_payload)
    except yaml.YAMLError:
        raise ValueError("Credential store returned a payload that is not valid YAML or JSON.")
    
    if isinstance(parsed_payload, (dict, str)):
        return parsed_payload
    
    raise ValueError(f"Unsupported secret payload type: {type(parsed_payload).__name__}")
    
def _get_property_value(cred_id: str, property_name: str | None, secret_store_type: str, secret_payload: Any,) -> str:
    if isinstance(secret_payload, dict):
        key = property_name or ("value" if secret_store_type == "vault" else None)

        if key is None:
            return str(secret_payload)

        if key not in secret_payload:
            raise ValueError(f"Secret store did not return expected property '{key}' for credential {cred_id}.")

        return str(secret_payload[key])

    return str(secret_payload)

def resolve_external_credential_data(
    cred_id: str,
    credentials_config: dict,
) -> dict[str, str]:
    external_credential = find_external_credential_by_id(cred_id, credentials_config)

    secret_store_type, secret_payload = _get_secret_store_payload_cached(cred_id, external_credential.model_dump_json())
    
    if external_credential.properties:
        return {
            prop.name: _get_property_value(cred_id, prop.name, secret_store_type, secret_payload,)
            for prop in external_credential.properties
        }

    return {
        "secret": _get_property_value(cred_id, None, secret_store_type, secret_payload,)
    }


def is_external_credential_reference(credential_ref: dict) -> bool:
    return (
        isinstance(credential_ref, dict)
        and credential_ref.get("$type") == "credRef"
    )


def has_external_creds(creds_map):
    return any(
        isinstance(v, dict) and v.get("type") == "external"
        for v in creds_map.values()
    )