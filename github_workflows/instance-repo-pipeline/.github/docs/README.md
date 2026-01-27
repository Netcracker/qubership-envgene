# EnvGene GitHub Pipeline Usage Guide

- [EnvGene GitHub Pipeline Usage Guide](#envgene-github-pipeline-usage-guide)
  - [Overview](#overview)
  - [Available Parameters](#available-parameters)
  - [How to Trigger the Pipeline](#how-to-trigger-the-pipeline)
    - [Via GitHub Actions UI](#via-github-actions-ui)
    - [Via GitHub API Call](#via-github-api-call)
  - [Parameter Priority](#parameter-priority)
  - [`pipeline_vars.env`](#pipeline_varsenv)
  - [Pipeline Customization](#pipeline-customization)
  - [How to Get the Pipeline](#how-to-get-the-pipeline)

## Overview

The EnvGene pipeline (`Envgene.yaml`) is a GitHub Actions workflow that supports both manual UI triggers and API calls. It provides the same full EnvGene functionality as the GitLab pipeline.

## Available Parameters

GitHub's UI limits manual inputs to 10 parameters. To handle this limitation while maintaining full functionality, we expose the most frequently used parameters directly in the UI and group the remaining parameters within the [GH_ADDITIONAL_PARAMS](https://github.com/Netcracker/qubership-envgene/blob/main/docs/instance-pipeline-parameters.md#gh_additional_params) parameter.

Only a limited number of core parameters are available in the GitHub version of the pipeline:

- [ENV_NAMES](https://github.com/Netcracker/qubership-envgene/blob/main/docs/instance-pipeline-parameters.md#env_names)
- [DEPLOYMENT_TICKET_ID](https://github.com/Netcracker/qubership-envgene/blob/main/docs/instance-pipeline-parameters.md#deployment_ticket_id)
- [ENV_TEMPLATE_VERSION](https://github.com/Netcracker/qubership-envgene/blob/main/docs/instance-pipeline-parameters.md#env_template_version)
- [ENV_BUILDER](https://github.com/Netcracker/qubership-envgene/blob/main/docs/instance-pipeline-parameters.md#env_builder)
- [GENERATE_EFFECTIVE_SET](https://github.com/Netcracker/qubership-envgene/blob/main/docs/instance-pipeline-parameters.md#generate_effective_set)
- [GET_PASSPORT](https://github.com/Netcracker/qubership-envgene/blob/main/docs/instance-pipeline-parameters.md#get_passport)
- [CMDB_IMPORT](https://github.com/Netcracker/qubership-envgene/blob/main/docs/instance-pipeline-parameters.md#cmdb_import)
- [GH_ADDITIONAL_PARAMS](https://github.com/Netcracker/qubership-envgene/blob/main/docs/instance-pipeline-parameters.md#gh_additional_params)

The [GH_ADDITIONAL_PARAMS](https://github.com/Netcracker/qubership-envgene/blob/main/docs/instance-pipeline-parameters.md#gh_additional_params) parameter serves as a wrapper for all parameters except those listed above. This approach enables the transmission of all [Instance Pipeline parameters](https://github.com/Netcracker/qubership-envgene/blob/main/docs/instance-pipeline-parameters.md).

## How to Trigger the Pipeline

The pipeline can be triggered in two ways:

### Via GitHub Actions UI

1. Go to your GitHub repository
2. Navigate to the **Actions** tab
3. Select the **EnvGene Execution** workflow
4. Click **Run workflow**
5. Fill in the required parameters
6. Click **Run workflow**

### Via GitHub API Call

Use the GitHub API to trigger the workflow:

```bash
curl -X POST \
  -H "Authorization: token <github-token>" \
  -H "Accept: application/vnd.github.v3+json" \
  https://api.github.com/repos/<repository-owner>/<repository-name>/actions/workflows/Envgene.yaml/dispatches \
  -d '{
    "ref": "<branch-name>",
    "inputs": {
      "<instance-pipeline-parameter-key>": "<instance-pipeline-parameter-value>",
      "GH_ADDITIONAL_PARAMS": "KEY1=VALUE1,KEY2=VALUE2"
    }
  }'
```

**Example:**

```bash
curl -X POST \
  -H "Authorization: token token-placeholder-123" \
  -H "Accept: application/vnd.github.v3+json" \
  https://api.github.com/repos/qubership/instance-repo/actions/workflows/Envgene.yaml/dispatches \
  -d '{
        "ref": "main",
        "inputs": {
            "ENV_NAMES": "test-cluster/e01",
            "ENV_BUILDER": "true",
            "GENERATE_EFFECTIVE_SET": "true",
            "DEPLOYMENT_TICKET_ID": "QBSHP-0001",
            "GH_ADDITIONAL_PARAMS": "EFFECTIVE_SET_CONFIG={\"version\": \"v2.0\", \"app_chart_validation\": \"false\"}"
        }
      }'
```

## Parameter Priority

The pipeline allows parameters to be defined in multiple locations, listed in descending order of priority:

1. Pipeline execution input parameters
2. `pipeline_vars.env` file
3. Repository or repository group CI/CD variables

Together, these form the complete context used by EnvGene.
When parameter keys from different sources overlap, their values are replaced according to the priority order specified above.

Best practices for setting variables are:

- Define in CI/CD variables [EnvGene repository variables](https://github.com/Netcracker/qubership-envgene/blob/main/docs/envgene-repository-variables.md)
- Pass through GitHub Actions UI or GitHub API Call [Instance Pipeline parameters](https://github.com/Netcracker/qubership-envgene/blob/main/docs/instance-pipeline-parameters.md)
- Use `pipeline_vars.env` for debug purposes

## `pipeline_vars.env`

Variables in this file must be described in Dotenv format and follow POSIX shell variable syntax.

For example:

```text
ENV_SPECIFIC_PARAMS={"clusterParams":{"clusterEndpoint":"<value>","clusterToken":"<value>"},"additionalTemplateVariables":{"<key>":"<value>"},"cloudName":"<value>","envSpecificParamsets":{"<ns-template-name>":["paramsetA"],"cloud":["paramsetB"]},"paramsets":{"paramsetA":{"version":"<paramset-version>","name":"<paramset-name>","parameters":{"<key>":"<value>"},"applications":[{"appName":"<app-name>","parameters":{"<key>":"<value>"}}]},"paramsetB":{"version":"<paramset-version>","name":"<paramset-name>","parameters":{"<key>":"<value>"},"applications":[]}},"credentials":{"credX":{"type":"<credential-type>","data":{"username":"<value>","password":"<value>"}},"credY":{"type":"<credential-type>","data":{"secret":"<value>"}}}}
EFFECTIVE_SET_CONFIG={\"version\": \"v2.0\", \"app_chart_validation\": \"false\"}
```

Variables set in this file must NOT be wrapped with [GH_ADDITIONAL_PARAMS](https://github.com/Netcracker/qubership-envgene/blob/main/docs/instance-pipeline-parameters.md#gh_additional_params)

## Pipeline Customization

Pipeline customization is only possible in a limited number of cases:

- **Reducing** the number of input parameters in the UI
- Changing default values of input parameters in the UI
- Changing the mandatory status of input parameters in the UI

All these changes are made and described in the `Envgene.yaml` section:

```yaml
on:
  workflow_dispatch:
    inputs:
```

## How to Get the Pipeline

To get the pipeline, you need to copy the [.github](/github_workflows/instance-repo-pipeline/.github) directory to the root of your GitHub repository
