#!/bin/bash
possible_vars=(
    "SD_SOURCE_TYPE"
    "SD_VERSION"
    "SD_DATA"
    "SD_DELTA"
    "ENV_SPECIFIC_PARAMETERS"
    "ENV_TEMPLATE_NAME"
)

# Create JSON string from non-empty environment variables
json_parts=()

# Loop through each variable in the array
for var in "${possible_vars[@]}"; do
    # Check if the variable exists in GitHub environment
    if [ -n "${!var}" ]; then
        json_parts+=("\"$var\": \"${!var}\"")
    fi
done

# Create the JSON string
if [ ${#json_parts[@]} -gt 0 ]; then
    json_content=$(
        IFS=,
        echo "{${json_parts[*]}}"
    )
    # Escape quotes for GitHub environment
    ENV_GENERATION_PARAMS=${json_content//\"/\\\"}
else
    ENV_GENERATION_PARAMS=\"{}\"
fi

echo "Generated ENV_GENERATION_PARAMS: $ENV_GENERATION_PARAMS"

# Add to GitHub environment
if [ -n "$GITHUB_ENV" ]; then
    echo "ENV_GENERATION_PARAMS=$ENV_GENERATION_PARAMS" >>"$GITHUB_ENV"
    echo "✅ ENV_GENERATION_PARAMS written to GITHUB_ENV"
else
    echo "❌ GITHUB_ENV variable is not set!"
    exit 1
fi
