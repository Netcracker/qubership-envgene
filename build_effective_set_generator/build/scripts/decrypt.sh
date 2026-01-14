#!/bin/bash
set -e

# Ensure externally provided variables are defined to satisfy shellcheck
env_name="${env_name:-}"
encrypt_file_path="${encrypt_file_path:-}"
DECRYPT_TYPE="${DECRYPT_TYPE:-}"
module_fernet_key_name="${module_fernet_key_name:-}"
module_age_key_name="${module_age_key_name:-}"

FERNET_KEY="CREDENTIALS_SECRET_KEY_${env_name}"
SOPS_AGE_PRIVATE_KEY="AGE_SECRET_KEY_${env_name}"

if [ -n "${module_fernet_key_name}" ]; then
      FERNET_KEY="${module_fernet_key_name}"
fi
if [ -n "${module_age_key_name}" ]; then
      SOPS_AGE_PRIVATE_KEY="${module_age_key_name}"
fi

if [ -n "${!FERNET_KEY}" ] && [ -f "${encrypt_file_path}" ] && [ "${DECRYPT_TYPE}" = 'fernet' ]; then

      echo "${encrypt_file_path} exists and key variable is defined"
      python /module/scripts/decrypt_fernet.py decrypt_cred_file --file_path "${encrypt_file_path}" --secret_key "${!FERNET_KEY}"
elif [ -n "${!SOPS_AGE_PRIVATE_KEY}" ] && [ -f "${encrypt_file_path}" ] && [ "${DECRYPT_TYPE}" = 'sops' ]; then
      SOPS_AGE_KEY="${!SOPS_AGE_PRIVATE_KEY}"
      export SOPS_AGE_KEY
      sops --decrypt -i "${encrypt_file_path}"
      echo "${encrypt_file_path} was decrypted"
elif [ "${DECRYPT_TYPE}" == 'none' ]; then
      echo "Skipping decryption...."
else
      echo "Variable encrypt_file_path not exists or key variable is undefined. encrypt_file_path: '$encrypt_file_path'"
fi
