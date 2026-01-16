#!/bin/bash
set -e

# build_env_job.sh
# This script implements the logic from prepare_env_build_job function
# It performs environment build operations including certificate updates,
# template version setting, environment building, and cleanup

# Activate Python virtual environment
source /module/venv/bin/activate

# Enable debug mode if envgen_debug is set
if [ "${envgen_debug}" == "true" ]; then
  set -o xtrace
fi

# Update CA certificates if certs directory exists
if [ -d "${CI_PROJECT_DIR}/configuration/certs" ]; then
  cert_path=$(ls -A "${CI_PROJECT_DIR}/configuration/certs")
  for path in $cert_path; do
    bash /module/scripts/update_ca_cert.sh "${CI_PROJECT_DIR}/configuration/certs/$path"
  done
fi

# Set template version if ENV_TEMPLATE_VERSION is provided and not in test mode
if [ -n "${ENV_TEMPLATE_VERSION}" ] && [ "${ENV_TEMPLATE_VERSION}" != "" ] && [ "${ENV_TEMPLATE_TEST}" != "true" ]; then
  echo "Setting template version to ${ENV_TEMPLATE_VERSION}"
  python3 /build_env/scripts/build_env/env_template/set_template_version.py
fi

# Execute build_env.yaml playbook
echo "Executing build_env.yaml playbook..."
if ! /module/scripts/prepare.sh "build_env.yaml"; then
  echo "Failed to execute build_env.yaml playbook"
  exit 1
fi

# Execute main.py to build the environment
echo "Executing main.py to build environment..."
cd /build_env
if ! python3 /build_env/scripts/build_env/main.py; then
  echo "Failed to execute main.py"
  exit 1
fi

# Determine environment name based on test mode
if [ "${ENV_TEMPLATE_TEST}" == "true" ]; then
  if [ -f "set_variable.txt" ]; then
    env_name=$(cat set_variable.txt)
    # Replace envgeneNullValue with test_value in credentials
    if [ -f "${CI_PROJECT_DIR}/environments/${env_name}/Credentials/credentials.yml" ]; then
      sed -i "s|\"envgeneNullValue\"|\"test_value\"|g" "${CI_PROJECT_DIR}/environments/${env_name}/Credentials/credentials.yml"
    fi
  else
    echo "Warning: set_variable.txt not found in template test mode"
    exit 1
  fi
else
  # Extract environment name from ENV_NAME (last part after /)
  # shellcheck disable=SC2153
  env_name=$(echo "${ENV_NAME}" | awk -F '/' '{print $NF}')
  export env_name
fi

# Set permissions on Credentials files
# Use find without sudo if running as root, otherwise use sudo
env_path=$(find "${CI_PROJECT_DIR}/environments" -type d -name "${env_name}" 2>/dev/null || sudo find "${CI_PROJECT_DIR}/environments" -type d -name "${env_name}")

for path in $env_path; do
  if [ -d "${path}/Credentials" ]; then
    # Try without sudo first, fallback to sudo if needed
    chmod ugo+rw "${path}/Credentials"/* 2>/dev/null || sudo chmod ugo+rw "${path}/Credentials"/* || true
  fi
done

# After script: Copy tmp files from /build_env/tmp to CI_PROJECT_DIR/tmp
echo "Copying tmp files..."
mkdir -p "${CI_PROJECT_DIR}/tmp"
if [ -d "/build_env/tmp" ]; then
  cp -r /build_env/tmp/* "${CI_PROJECT_DIR}/tmp" 2>/dev/null || true
fi

echo "Build environment job completed successfully"
