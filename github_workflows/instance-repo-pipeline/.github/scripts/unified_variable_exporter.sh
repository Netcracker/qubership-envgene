#!/bin/bash
# Unified Variable Exporter for EnvGene Pipeline Steps
# ===================================================
# This script provides a unified way to export all environment variables needed for:
# - Generate inventory
# - Credential Rotation  
# - Build Env
# - Generate Effective Set
# - Git Commit
#
# Supports two execution modes:
# 1. Manual Mode: Manual Inputs + pipeline_vars.yaml (NO GITHUB_PIPELINE_API_INPUT)
# 2. API Mode: API Inputs + GITHUB_PIPELINE_API_INPUT (NO pipeline_vars.yaml)
#
# Variable precedence:
# 1. Manual Mode: Manual Inputs + pipeline_vars.yaml + JSON variables
# 2. API Mode: API Inputs + GITHUB_PIPELINE_API_INPUT + JSON variables
#
# Usage: ./unified_variable_exporter.sh <matrix_environment> [variables_json]

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    local level="${2:-INFO}"
    local step_prefix="[${STEP_NAME:-UNIFIED}]"
    echo -e "${BLUE}🔧 ${step_prefix}${NC} $1" >&2
}

# Get script arguments
MATRIX_ENVIRONMENT="${1:-}"
VARIABLES_JSON="${2:-}"

if [ -z "$MATRIX_ENVIRONMENT" ]; then
    log "❌ ERROR: Missing required arguments" "ERROR"
    log "Usage: $0 <matrix_environment> [variables_json]"
    log "Example: $0 test-cluster/e01 '{\"MY_VAR\": \"value\"}'"
    exit 1
fi


# 1. Export pipeline variables from YAML
export_pipeline_vars_from_yaml() {
    # Check if we're in API mode - if so, don't load pipeline_vars.yaml
    local pipeline_mode="${PIPELINE_MODE:-MANUAL}"
    if [ "$pipeline_mode" = "API" ]; then
        return 0
    fi
    
    local pipeline_vars_file=".github/pipeline_vars.yaml"
    local exported_count=0
    
    if [ ! -f "$pipeline_vars_file" ]; then
        return 0
    fi
    
    # Use yq to properly parse YAML and only export simple values
    while IFS= read -r key && IFS= read -r value; do
        # Skip empty keys or null values
        if [ -n "$key" ] && [ -n "$value" ] && [ "$value" != "null" ]; then
            # Validate key name (must be valid bash variable name)
            if echo "$key" | grep -q '^[a-zA-Z_][a-zA-Z0-9_]*'; then
                echo "export \"$key\"=\"$value\""
                log "  $key = $value"
                exported_count=$((exported_count + 1))
            else
                log "  Skipping invalid variable name: $key"
            fi
        fi
    done < <(yq eval -o json "$pipeline_vars_file" | jq -r 'to_entries[] | select(.value | type == "string" or type == "number" or type == "boolean") | .key, (.value | tostring)')
}

# 2. Export GitHub workflow input variables (Manual Inputs)
export_github_inputs() {
    local exported_count=0
    
    # Manual input variables from workflow dispatch
    local manual_inputs="DEPLOYMENT_TICKET_ID ENV_BUILDER GET_PASSPORT CMDB_IMPORT ENV_TEMPLATE_VERSION GENERATE_EFFECTIVE_SET"
    
    for var in $manual_inputs; do
        local value=""
        eval "value=\${$var:-}"
        if [ -n "$value" ]; then
            echo "export \"$var\"=\"$value\""
            log "  $var = $value"
            exported_count=$((exported_count + 1))
        fi
    done
}

# 3. Export API input variables (API Inputs) - FIXED
export_api_input_variables() {
    local api_input="${GITHUB_PIPELINE_API_INPUT:-}"
    
    if [ -z "$api_input" ]; then
        return 0
    fi
    
    local exported_count=0
    
    # Try to parse as JSON first
    if command -v jq >/dev/null 2>&1 && echo "$api_input" | jq . >/dev/null 2>&1; then
        # Use jq to properly extract key-value pairs
        while IFS= read -r key && IFS= read -r value; do
            if [ -n "$key" ] && [ -n "$value" ] && [ "$value" != "null" ]; then
                echo "export \"$key\"=\"$value\""
                log "  $key = $value"
                exported_count=$((exported_count + 1))
            fi
        done < <(echo "$api_input" | jq -r 'to_entries[] | .key, .value')
    else
        # Fall back to key=value format
        while IFS= read -r line; do
            if echo "$line" | grep -q "^[^=]*="; then
                local key=$(echo "$line" | cut -d'=' -f1 | xargs)
                local value=$(echo "$line" | cut -d'=' -f2- | xargs)
                
                if [ -n "$key" ] && [ -n "$value" ]; then
                    echo "export \"$key\"=\"$value\""
                    log "  $key = $value"
                    exported_count=$((exported_count + 1))
                fi
            fi
        done < <(echo "$api_input")
    fi
}

# 6. Load variables from JSON into memory (without exporting) - FIXED
load_variables_from_json() {
    if [ -z "$VARIABLES_JSON" ] || [ "$VARIABLES_JSON" = "{}" ] || [ "$VARIABLES_JSON" = "null" ]; then
        return 0
    fi
    
    if command -v jq >/dev/null 2>&1 && echo "$VARIABLES_JSON" | jq . >/dev/null 2>&1; then
        # Load variables into current shell environment using proper jq parsing
        while IFS= read -r key && IFS= read -r value; do
            if [ -n "$key" ] && [ -n "$value" ] && [ "$value" != "null" ]; then
                export "$key"="$value"
            fi
        done < <(echo "$VARIABLES_JSON" | jq -r 'to_entries[] | .key, .value')
    fi
}

# 7. Export variables from JSON (overrides all previous variables) - FIXED
export_variables_from_json() {
    if [ -z "$VARIABLES_JSON" ] || [ "$VARIABLES_JSON" = "{}" ] || [ "$VARIABLES_JSON" = "null" ]; then
        return 0
    fi
    
    local pipeline_mode="${PIPELINE_MODE:-MANUAL}"
    local api_mode=false
    if [ "$pipeline_mode" = "API" ]; then
        api_mode=true
    fi
    
    local exported_count=0
    
    if command -v jq >/dev/null 2>&1 && echo "$VARIABLES_JSON" | jq . >/dev/null 2>&1; then
        # Use proper jq parsing to avoid colon splitting issues
        while IFS= read -r key && IFS= read -r value; do
            if [ -n "$key" ] && [ -n "$value" ] && [ "$value" != "null" ]; then
                echo "export \"$key\"=\"$value\""
                log "  $key = $value"
                exported_count=$((exported_count + 1))
            fi
        done < <(echo "$VARIABLES_JSON" | jq -r 'to_entries[] | .key, .value')
    else
        return 0
    fi
}

# 5. Export system variables
export_system_variables() {
    local exported_count=0
    
    # Essential system variables that should be available in all steps
    local system_vars="CI_PROJECT_DIR SECRET_KEY GITHUB_ACTIONS GITHUB_REPOSITORY GITHUB_REF_NAME GITHUB_USER_EMAIL GITHUB_USER_NAME GITHUB_TOKEN ENVGENE_AGE_PUBLIC_KEY ENVGENE_AGE_PRIVATE_KEY DOCKER_IMAGE_PIPEGENE DOCKER_IMAGE_ENVGENE DOCKER_IMAGE_EFFECTIVE_SET_GENERATOR"
    
    for var in $system_vars; do
        local value=""
        eval "value=\${$var:-}"
        if [ -n "$value" ]; then
            echo "export \"$var\"=\"$value\""
            log "  $var = $value"
            exported_count=$((exported_count + 1))
        fi
    done
}

# 6. Export environment-specific variables
export_environment_variables() {
    # Extract environment components
    local cluster_name=$(echo "$MATRIX_ENVIRONMENT" | cut -d'/' -f1)
    local environment_name=$(echo "$MATRIX_ENVIRONMENT" | cut -d'/' -f2 | xargs)
    
    # Export environment variables
    echo "export \"CI_PROJECT_DIR\"=\"${CI_PROJECT_DIR:-/work}\""
    echo "export \"GITHUB_TOKEN\"=\"${GITHUB_TOKEN:-}\""
    echo "export \"GITHUB_ACTIONS\"=\"${GITHUB_ACTIONS:-true}\""
    echo "export \"GITHUB_REPOSITORY\"=\"${GITHUB_REPOSITORY:-}\""
    echo "export \"GITHUB_REF_NAME\"=\"${GITHUB_REF_NAME:-}\""
    echo "export \"GITHUB_USER_EMAIL\"=\"${GITHUB_USER_EMAIL:-}\""
    echo "export \"GITHUB_USER_NAME\"=\"${GITHUB_USER_NAME:-}\""
    echo "export \"GITHUB_REF\"=\"${GITHUB_REF:-}\""
    echo "export \"GITHUB_SHA\"=\"${GITHUB_SHA:-}\""
    echo "export \"GITHUB_EVENT_NAME\"=\"${GITHUB_EVENT_NAME:-}\""
    echo "export \"FULL_ENV\"=\"$MATRIX_ENVIRONMENT\""
    echo "export \"ENV_NAMES\"=\"$MATRIX_ENVIRONMENT\""
    echo "export \"CLUSTER_NAME\"=\"$cluster_name\""
    echo "export \"ENVIRONMENT_NAME\"=\"$environment_name\""
    echo "export \"ENV_NAME\"=\"$environment_name\""
    echo "export \"ENV_NAME_SHORT\"=\"$(echo "$environment_name" | awk -F "/" '{print $NF}')\""
    echo "export \"PROJECT_DIR\"=\"${CI_PROJECT_DIR:-/work}\""
    
    log "  FULL_ENV = $MATRIX_ENVIRONMENT"
    log "  ENV_NAMES = $MATRIX_ENVIRONMENT"
    log "  CLUSTER_NAME = $cluster_name"
    log "  ENVIRONMENT_NAME = $environment_name"
    log "  ENV_NAME = $environment_name"
    log "  ENV_NAME_SHORT = $(echo "$environment_name" | awk -F "/" '{print $NF}')"
    log "  PROJECT_DIR = ${CI_PROJECT_DIR:-$(pwd)}"
    
    # Export common pipeline variables
    export_common_pipeline_variables
}

# 7. Export common pipeline variables
export_common_pipeline_variables() {
    # Common variables for all pipeline steps
    echo "export \"module_ansible_dir\"=\"/module/ansible\""
    echo "export \"module_inventory\"=\"${CI_PROJECT_DIR:-/work}/configuration/inventory.yaml\""
    echo "export \"module_ansible_cfg\"=\"/module/ansible/ansible.cfg\""
    echo "export \"module_config_default\"=\"/module/templates/defaults.yaml\""
    echo "export \"envgen_args\"=\" -vvv\""
    echo "export \"envgen_debug\"=\"true\""
    echo "export \"GIT_STRATEGY\"=\"none\""
    echo "export \"COMMIT_ENV\"=\"true\""
    
    log "  module_ansible_dir = /module/ansible"
    log "  module_inventory = ${CI_PROJECT_DIR:-/work}/configuration/inventory.yaml"
    log "  module_ansible_cfg = /module/ansible/ansible.cfg"
    log "  module_config_default = /module/templates/defaults.yaml"
    log "  envgen_args =  -vvv"
    log "  envgen_debug = true"
    log "  GIT_STRATEGY = none"
    log "  COMMIT_ENV = true"
}

# 8. Export manual mode variables (Manual Inputs + pipeline_vars)
export_manual_mode_variables() {
    # 1. Load variables from JSON first (to get PIPELINE_MODE)
    load_variables_from_json
    
    # 2. Export pipeline variables from YAML (now PIPELINE_MODE is available)
    export_pipeline_vars_from_yaml
    
    # 3. Export GitHub workflow inputs (manual inputs)
    export_github_inputs
    
    # 4. Export all variables from JSON
    export_variables_from_json
}

# 9. Export API mode variables (API Inputs only - NO pipeline_vars.yaml)
export_api_mode_variables() {
    # 1. Load variables from JSON first (to get PIPELINE_MODE)
    load_variables_from_json
    
    # 2. Export API input variables (highest priority)
    export_api_input_variables
    
    # 3. Export variables from JSON (if provided)
    export_variables_from_json
    
    # Note: pipeline_vars.yaml is NOT loaded in API mode
}

# Main execution
main() {
    # Determine execution mode
    local pipeline_mode="${PIPELINE_MODE:-MANUAL}"
    
    if [ "$pipeline_mode" = "API" ]; then
        export_api_mode_variables
    else
        export_manual_mode_variables
    fi
    
    # Always export system and environment variables
    export_system_variables
    export_environment_variables
}

# Run main function
main "$@"