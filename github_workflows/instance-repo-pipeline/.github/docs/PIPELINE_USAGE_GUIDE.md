# EnvGene Pipeline Usage Guide

## Overview

The EnvGene pipeline (`pipeline.yml`) is a comprehensive GitHub Actions workflow that supports both manual UI triggers and API calls. It provides environment generation, credential rotation, and various deployment capabilities.

## Table of Contents

1. [Triggering Methods](#triggering-methods)
2. [UI Mode (Manual Trigger)](#ui-mode-manual-trigger)
3. [API Mode](#api-mode)
4. [Available Variables](#available-variables)
5. [Examples](#examples)
6. [Troubleshooting](#troubleshooting)

## Triggering Methods

The pipeline can be triggered in two ways:

### 1. UI Mode (Manual Trigger)
- Triggered through GitHub Actions UI
- Uses individual input fields
- Best for manual testing and development

### 2. API Mode
- Triggered via GitHub API
- Uses a single JSON string with all parameters
- Best for automation and CI/CD integration

## UI Mode (Manual Trigger)

### How to Trigger
1. Go to your GitHub repository
2. Navigate to **Actions** tab
3. Select **EnvGene Execution** workflow
4. Click **Run workflow**
5. Fill in the required parameters
6. Click **Run workflow**

### Available Input Fields

| Field | Required | Type | Description | Default |
|-------|----------|------|-------------|---------|
| `ENV_NAMES` | Yes | String | Comma-separated environment names | - |
| `DEPLOYMENT_TICKET_ID` | No | String | Deployment ticket ID | "" |
| `ENV_TEMPLATE_VERSION` | No | String | Environment template version | "" |
| `ENV_BUILDER` | No | Choice | Enable environment building | "true" |
| `GET_PASSPORT` | No | Choice | Enable passport retrieval | "false" |
| `CMDB_IMPORT` | No | Choice | Enable CMDB import | "false" |
| `GITHUB_PIPELINE_API_INPUT` | No | String | API input string (for API mode) | - |

### UI Mode Example

**Basic Environment Generation:**
- `ENV_NAMES`: `test-cluster/e01,test-cluster/e02`
- `ENV_BUILDER`: `true`
- `DEPLOYMENT_TICKET_ID`: `TICKET-123`
- `ENV_TEMPLATE_VERSION`: `qubership_envgene_templates:0.0.2`

## API Mode

### How to Trigger

Use the GitHub API to trigger the workflow:

```bash
curl -X POST \
  -H "Authorization: token YOUR_GITHUB_TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  https://api.github.com/repos/OWNER/REPO/actions/workflows/pipeline.yml/dispatches \
  -d '{
    "ref": "main",
    "inputs": {
      "GITHUB_PIPELINE_API_INPUT": "YOUR_API_INPUT_STRING"
    }
  }'
```

### API Input Formats

The `GITHUB_PIPELINE_API_INPUT` can be provided in three formats:

#### 1. JSON Format (Recommended)
```json
{
  "ENV_NAMES": "test-cluster/e01,test-cluster/e02",
  "ENV_BUILDER": "true",
  "DEPLOYMENT_TICKET_ID": "TICKET-123",
  "ENV_TEMPLATE_VERSION": "qubership_envgene_templates:0.0.2",
  "GET_PASSPORT": "false",
  "CMDB_IMPORT": "false"
}
```

#### 2. Key-Value Format
```
ENV_NAMES=test-cluster/e01,test-cluster/e02
ENV_BUILDER=true
DEPLOYMENT_TICKET_ID=TICKET-123
ENV_TEMPLATE_VERSION=qubership_envgene_templates:0.0.2
GET_PASSPORT=false
CMDB_IMPORT=false
```

#### 3. YAML Format
```yaml
ENV_NAMES: test-cluster/e01,test-cluster/e02
ENV_BUILDER: true
DEPLOYMENT_TICKET_ID: TICKET-123
ENV_TEMPLATE_VERSION: qubership_envgene_templates:0.0.2
GET_PASSPORT: false
CMDB_IMPORT: false
```

## Available Variables

### Required Variables
| Variable | Type | Description |
|----------|------|-------------|
| `ENV_NAMES` | String | Comma-separated list of environment names |

### Boolean Variables
| Variable | Default | Description |
|----------|---------|-------------|
| `ENV_BUILDER` | true | Enable environment building |
| `GET_PASSPORT` | false | Enable passport retrieval |
| `CMDB_IMPORT` | false | Enable CMDB import |
| `ENV_INVENTORY_INIT` | false | Initialize environment inventory |
| `GENERATE_EFFECTIVE_SET` | false | Generate effective set |
| `ENV_TEMPLATE_TEST` | false | Test environment template |
| `SD_DELTA` | false | Enable SD delta processing |
| `CRED_ROTATION_FORCE` | false | Force credential rotation |

### String Variables
| Variable | Default | Description |
|----------|---------|-------------|
| `DEPLOYMENT_TICKET_ID` | "" | Deployment ticket ID |
| `ENV_TEMPLATE_VERSION` | "" | Environment template version |
| `ENV_TEMPLATE_NAME` | "" | Environment template name |
| `SD_VERSION` | "" | SD version |
| `SD_SOURCE_TYPE` | "" | SD source type |

### JSON Variables
| Variable | Default | Description |
|----------|---------|-------------|
| `SD_DATA` | "{}" | SD data in JSON format |
| `ENV_SPECIFIC_PARAMETERS` | "{}" | Environment-specific parameters |
| `CRED_ROTATION_PAYLOAD` | "{}" | Credential rotation payload |

## Examples

### Example 1: Basic Environment Generation

**API Call:**
```bash
curl -X POST \
  -H "Authorization: token YOUR_GITHUB_TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  https://api.github.com/repos/OWNER/REPO/actions/workflows/pipeline.yml/dispatches \
  -d '{
    "ref": "main",
    "inputs": {
      "GITHUB_PIPELINE_API_INPUT": "{\"ENV_NAMES\": \"test-cluster/e01,test-cluster/e02\", \"ENV_BUILDER\": \"true\", \"DEPLOYMENT_TICKET_ID\": \"TICKET-123\", \"ENV_TEMPLATE_VERSION\": \"qubership_envgene_templates:0.0.2\"}"
    }
  }'
```

**Key-Value Format:**
```bash
curl -X POST \
  -H "Authorization: token YOUR_GITHUB_TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  https://api.github.com/repos/OWNER/REPO/actions/workflows/pipeline.yml/dispatches \
  -d '{
    "ref": "main",
    "inputs": {
      "GITHUB_PIPELINE_API_INPUT": "ENV_NAMES=test-cluster/e01,test-cluster/e02\nENV_BUILDER=true\nDEPLOYMENT_TICKET_ID=TICKET-123\nENV_TEMPLATE_VERSION=qubership_envgene_templates:0.0.2"
    }
  }'
```

### Example 2: Environment Generation with Credential Rotation

**API Call:**
```bash
curl -X POST \
  -H "Authorization: token YOUR_GITHUB_TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  https://api.github.com/repos/OWNER/REPO/actions/workflows/pipeline.yml/dispatches \
  -d '{
    "ref": "main",
    "inputs": {
      "GITHUB_PIPELINE_API_INPUT": "{\"ENV_NAMES\": \"test-cluster/e01\", \"ENV_BUILDER\": \"true\", \"DEPLOYMENT_TICKET_ID\": \"TICKET-123\", \"ENV_TEMPLATE_VERSION\": \"qubership_envgene_templates:0.0.2\", \"CRED_ROTATION_PAYLOAD\": \"{\\\"rotation_items\\\":[{\\\"namespace\\\":\\\"e01-bss\\\",\\\"application\\\":\\\"postgres\\\",\\\"context\\\":\\\"deployment\\\",\\\"parameter_key\\\":\\\"POSTGRES_DBA_USER\\\",\\\"parameter_value\\\":\\\"new_user\\\"}]}\", \"CRED_ROTATION_FORCE\": \"true\"}"
    }
  }'
```

**Key-Value Format:**
```bash
curl -X POST \
  -H "Authorization: token YOUR_GITHUB_TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  https://api.github.com/repos/OWNER/REPO/actions/workflows/pipeline.yml/dispatches \
  -d '{
    "ref": "main",
    "inputs": {
      "GITHUB_PIPELINE_API_INPUT": "ENV_NAMES=test-cluster/e01\nENV_BUILDER=true\nDEPLOYMENT_TICKET_ID=TICKET-123\nENV_TEMPLATE_VERSION=qubership_envgene_templates:0.0.2\nCRED_ROTATION_PAYLOAD={\"rotation_items\":[{\"namespace\":\"e01-bss\",\"application\":\"postgres\",\"context\":\"deployment\",\"parameter_key\":\"POSTGRES_DBA_USER\",\"parameter_value\":\"new_user\"}]}\nCRED_ROTATION_FORCE=true"
    }
  }'
```

### Example 3: Complex Environment with Multiple Features

**API Call:**
```bash
curl -X POST \
  -H "Authorization: token YOUR_GITHUB_TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  https://api.github.com/repos/OWNER/REPO/actions/workflows/pipeline.yml/dispatches \
  -d '{
    "ref": "main",
    "inputs": {
      "GITHUB_PIPELINE_API_INPUT": "{\"ENV_NAMES\": \"test-cluster/e01,test-cluster/e02\", \"ENV_BUILDER\": \"true\", \"GET_PASSPORT\": \"true\", \"CMDB_IMPORT\": \"true\", \"GENERATE_EFFECTIVE_SET\": \"true\", \"DEPLOYMENT_TICKET_ID\": \"TICKET-123\", \"ENV_TEMPLATE_VERSION\": \"qubership_envgene_templates:0.0.2\", \"ENV_TEMPLATE_NAME\": \"standard-template\", \"SD_DATA\": \"{\\\"version\\\":\\\"1.0\\\",\\\"environment\\\":\\\"test\\\"}\", \"ENV_SPECIFIC_PARAMETERS\": \"{\\\"custom_param\\\":\\\"value\\\"}\"}"
    }
  }'
```

## CRED_ROTATION_PAYLOAD Structure

When using credential rotation, the `CRED_ROTATION_PAYLOAD` must follow this structure:

```json
{
  "rotation_items": [
    {
      "namespace": "e01-bss",
      "application": "postgres",
      "context": "deployment",
      "parameter_key": "POSTGRES_DBA_USER",
      "parameter_value": "new_user"
    }
  ]
}
```

### CRED_ROTATION_PAYLOAD Fields

| Field | Required | Description |
|-------|----------|-------------|
| `namespace` | Yes | Target namespace |
| `application` | No | Application name |
| `context` | Yes | Context: `pipeline`, `deployment`, or `runtime` |
| `parameter_key` | Yes | Parameter key to rotate |
| `parameter_value` | Yes | New parameter value |

## Troubleshooting

### Common Issues

#### 1. ENV_NAMES Not Found
**Error:** `ENV_NAMES is required for API mode but not found in input`

**Solution:** Ensure your API input contains `ENV_NAMES` with valid environment names:
```json
{
  "ENV_NAMES": "test-cluster/e01,test-cluster/e02"
}
```

#### 2. Invalid JSON Format
**Error:** `CRED_ROTATION_PAYLOAD must be a valid JSON object`

**Solution:** Use proper JSON format with escaped quotes:
```json
{
  "CRED_ROTATION_PAYLOAD": "{\\\"rotation_items\\\":[{\\\"namespace\\\":\\\"e01-bss\\\"}]}"
}
```

#### 3. Empty Matrix Error
**Error:** `Matrix vector 'environment' does not contain any values`

**Solution:** Ensure `ENV_NAMES` contains valid environment names with proper format (e.g., `cluster/environment`).

#### 4. YAML Parsing Issues
**Error:** YAML parsing fails with unquoted values

**Solution:** Use JSON format instead of YAML-like strings, or ensure proper quoting.

### Debug Information

The pipeline provides extensive debug information:

- **API Mode Detection:** Shows whether the pipeline is running in API mode
- **Variable Processing:** Shows which variables were loaded from API input vs. defaults
- **Validation Results:** Shows validation status for each variable
- **Environment Processing:** Shows how environment names are processed

### Debug Commands

1. **Check Pipeline Logs:** Look for "🔍" prefixed debug messages
2. **Verify Environment Variables:** Check the "Input Parameters Processing" job
3. **Validate JSON:** Use online JSON validators for complex payloads
4. **Test API Calls:** Use tools like Postman or curl for API testing

### Best Practices

1. **Use JSON Format:** Prefer JSON format for API input when possible
2. **Escape Quotes Properly:** Use double escaping for nested JSON: `\\\"`
3. **Validate Input:** Test your API input before sending
4. **Use Descriptive Ticket IDs:** Include meaningful deployment ticket IDs
5. **Version Control:** Always specify `ENV_TEMPLATE_VERSION` for reproducibility

## Support

For issues and questions:
1. Check the pipeline logs for detailed error messages
2. Verify your API input format
3. Test with simple examples first
4. Review the validation rules in the documentation 