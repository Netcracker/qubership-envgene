import json
import os
import time
from typing import List

import envgenehelper.logger as logger
from core_rotation import process_entry_in_payload
from envgenehelper import crypt
from envgenehelper.errors import RuntimeError, ValidationError, ValueError
from models import PayloadEntry, RotationResult, EnvConfig
from utils.cred_utils import (
    collect_shared_credentials,
    decrypt_file,
    read_env_cred_files,
    read_shared_cred_files,
    update_cred_content,
    write_updated_cred_into_file,
)
from utils.error_constants import *
from utils.file_utils import scan_and_get_yaml_files, write_cred_file_path
from utils.yaml_utils import convert_json_to_yaml, write_yaml_to_file

def validate_env_vars(is_encrypted: bool, encrypt_type: str):
    missing_params = []
    values = {}
    creds_path = "/tmp/payload.yml"
    def check_env(var_name):
        value = os.getenv(var_name)
        if value is None or value.strip() == "":
            missing_params.append(var_name)
        else:
            values[var_name] = value

    # Always required
    check_env("ENV_NAME")
    check_env("CRED_ROTATION_FORCE")
    check_env("CRED_ROTATION_PAYLOAD")
    check_env("CLUSTER_NAME")
    check_env("CI_PROJECT_DIR")

    cred_payload = load_payload(values["CRED_ROTATION_PAYLOAD"])
    payload_data = cred_payload
    if is_encrypted:
        if encrypt_type == "Fernet":
            raise ValidationError(
                ErrorMessages.INVALID_ENCRYPT_TYPE,
                error_code=ErrorCodes.INVALID_CONFIG_CODE,
            )
        elif encrypt_type == "SOPS":
            # Decrypt the Payload file if encrypted with SOPS
            convert_json_to_yaml(creds_path, cred_payload)
            payload_data = decrypt_file(
                os.getenv("ENVGENE_AGE_PUBLIC_KEY"),
                creds_path,
                True,
                "SOPS",
                ErrorMessages.PAYLOAD_DECRYPT_ERROR,
                ErrorCodes.INVALID_CONFIG_CODE,
            )


    if missing_params:
        raise ValueError(
            ErrorMessages.MISSING_ENV.format(params=missing_params),
            error_code=ErrorCodes.INVALID_INPUT_CODE,
        )

    return EnvConfig(
        env_name=values["ENV_NAME"],
        envgene_age_public_key=values.get("ENVGENE_AGE_PUBLIC_KEY"),
        creds_rotation_enabled=values["CRED_ROTATION_FORCE"] == "true",
        payload_data=payload_data,
        cluster_name=values["CLUSTER_NAME"],
        work_dir=values["CI_PROJECT_DIR"]
    )


def load_payload(payload: str):
    if isinstance(payload, str):
        try:
            # Check for hidden characters
            if payload.startswith("\ufeff"):
                payload = payload.lstrip("\ufeff")

            # Remove extra whitespace and newlines around edges
            payload = payload.strip()

            # Check if YAML block scalar remains
            if payload.startswith("|"):
                payload = payload.lstrip("|\n ").strip()

            # Remove possible extra newlines inside JSON
            if "\n" in payload:
                import re

                payload = re.sub(r"\n\s*", "", payload)

            # Try to decode as base64 first
            try:
                import base64

                decoded_payload = base64.b64decode(payload.encode("utf-8")).decode(
                    "utf-8"
                )
                config = json.loads(decoded_payload)
                return config
            except Exception:
                # Fallback to direct JSON parsing
                config = json.loads(payload)
                return config
        except json.JSONDecodeError as e:
            raise ValidationError(
                ErrorMessages.INVALID_JSON.format(e=str(e)),
                error_code=ErrorCodes.INVALID_CONFIG_CODE,
            )
    else:
        raise ValidationError(
            ErrorMessages.INCORRECT_TYPE, error_code=ErrorCodes.INVALID_CONFIG_CODE
        )


def cred_rotation():
    start = time.time()
    encrypt_type, is_encrypted = crypt.get_configured_encryption_type()
    config = validate_env_vars(is_encrypted, encrypt_type)
    
    logger.info(f"Starting rotation for: CLUSTER={config.cluster_name}, WORKDIR={config.work_dir}")
 
    logger.info(f"Detected encryption={is_encrypted}, type={encrypt_type}")

    base_env_path = f"{config.work_dir}/environments/{config.cluster_name}/{config.env_name}"
    cluster_path = f"{config.work_dir}/environments/{config.cluster_name}"
    output_path = f"{config.work_dir}/affected-sensitive-parameters.yaml"

    logger.info(f"base env path is {base_env_path}")

   
    fileread = time.time()
    # Scan and read all required files
    entity_files_map, env_files_map, env_creds_files = scan_and_get_yaml_files(
        cluster_path
    )
    shared_creds = collect_shared_credentials(env_files_map)
    shared_content_map = read_shared_cred_files(
        shared_creds, cluster_path, config.work_dir, is_encrypted, config.envgene_age_public_key
    )
    env_cred_map = read_env_cred_files(
        env_creds_files, is_encrypted, config.envgene_age_public_key
    )
    logger.info(f"✅ Fileread Completed in {round(time.time() - fileread, 2)} seconds.")

    payload_raw = config.payload_data.get("rotation_items", [])
    payload_objects: List[PayloadEntry] = [
        PayloadEntry.from_dict(entry) for entry in payload_raw
    ]

    final_result: List[RotationResult] = []
    processed_cred_and_files = {}
    # Collect affected parameters from ns and app files
    for entry in payload_objects:
        try:
            result = process_entry_in_payload(
                entry,
                config.env_name,
                config.cluster_name,
                shared_content_map,
                env_cred_map,
                entity_files_map,
                processed_cred_and_files,
            )
            if result:
                final_result.append(result)
        except Exception as e:
            raise RuntimeError(f"Failed to process the payload {entry} due to {e}")
    if final_result:
        write_yaml_to_file(output_path, [r.to_dict() for r in final_result])
    else:
        raise ValidationError(
            ErrorMessages.EMPTY_PARAM, error_code=ErrorCodes.INVALID_STATE_CODE
        )

    if not config.creds_rotation_enabled:
        logger.info(
            f"✅ Cred Rotation without file updation completed in {round(time.time() - start, 2)} seconds."
        )
        raise ValidationError(
            ErrorMessages.CRED_UPDATION_FALSE.format(file=output_path),
            error_code=ErrorCodes.INVALID_STATE_CODE,
        )
    if processed_cred_and_files:
        updated_content, original_content = update_cred_content(
            processed_cred_and_files
        )
        write_updated_cred_into_file(
            updated_content, original_content, is_encrypted, config.envgene_age_public_key
        )
        write_cred_file_path(
            list(processed_cred_and_files.keys()), f"{config.work_dir}/environments"
        )
    else:
        logger.error(
            "Credential IDs are not found in environment and shared credential files. Please check the files"
        )

    logger.info(
        f"✅ Cred Rotation completed in {round(time.time() - start, 2)} seconds."
    )


if __name__ == "__main__":
    cred_rotation()
