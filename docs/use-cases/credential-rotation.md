# Credential Rotation Use Cases

- [Credential Rotation Use Cases](#credential-rotation-use-cases)
  - [Overview](#overview)
  - [UC-CR-TPR-1: Update Credential from Pipeline Parameter](#uc-cr-tpr-1-update-credential-from-pipeline-parameter)
  - [UC-CR-TPR-2: Update Credential from Deployment Parameter](#uc-cr-tpr-2-update-credential-from-deployment-parameter)
  - [UC-CR-TPR-3: Update Credentials from Multiple rotation_items](#uc-cr-tpr-3-update-credentials-from-multiple-rotation_items)
  - [Affected Credential Handling](#affected-credential-handling)
    - [UC-CR-LCH-1: Reject Affected Credential Update](#uc-cr-lch-1-reject-affected-credential-update)
    - [UC-CR-LCH-2: Update Affected Credentials in Force Mode](#uc-cr-lch-2-update-affected-credentials-in-force-mode)
    - [UC-CR-VAL-1: Fail When No Affected Parameters Found](#uc-cr-val-1-fail-when-no-affected-parameters-found)
  - [Encryption Processing](#encryption-processing)
    - [Successful Update with Encryption Enabled](#successful-update-with-encryption-enabled)
      - [UC-CR-ENC-1: Update Credentials with Plaintext Payload when Encryption Is Enabled](#uc-cr-enc-1-update-credentials-with-plaintext-payload-when-encryption-is-enabled)
      - [UC-CR-ENC-2: Update Credentials with Encrypted Payload when Encryption Is Enabled](#uc-cr-enc-2-update-credentials-with-encrypted-payload-when-encryption-is-enabled)
    - [Successful Update with Encryption Disabled](#successful-update-with-encryption-disabled)

## Overview

This document contains use cases for [Credential Rotation](/docs/features/cred-rotation.md).

It describes parameter targeting, affected-credentials handling with force mode, and encryption processing for `credential_rotation`.

### Successful Update without Affected Credentials

This group covers successful rotation when the target credential is not linked to other parameters.

### UC-CR-TPR-1: Update Credential from Pipeline Parameter

**Pre-requisites:**

1. `env_inventory_generation_job` must be launched in the pipeline run.
2. Environment Instance contains a Namespace with `name` matching `<namespace-name>`.
3. The Namespace contains a sensitive parameter in `e2eParameters` linked via the `cred` macro.
4. The referenced Credential exists in the Environment Credentials file or in a Shared Credentials file.
5. No other parameters reference the same `cred-id` and credential field.
6. `CRED_ROTATION_PAYLOAD` contains a valid `rotation_items` entry for Namespace-level pipeline context:

    ```json
    {
      "rotation_items": [
        {
          "namespace": "<namespace-name>",
          "context": "pipeline",
          "parameter_key": "<parameter-key>",
          "parameter_value": "<new-value>"
        }
      ]
    }
    ```

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `ENV_NAMES: <cluster-name>/<env-name>`
2. `CRED_ROTATION_PAYLOAD: <json-in-string>`
3. `CRED_ROTATION_FORCE: false`

**Steps:**

1. The `credential_rotation` job runs in the pipeline:
   1. Finds the target Namespace from the payload.
   2. Uses the `pipeline` context to look for the parameter in `e2eParameters`.
   3. Determines which credential field is linked to the target parameter.
   4. Searches for affected credentials linked to the same `cred-id` and credential field.
   5. Finds no affected credentials and continues the flow.
   6. Updates credential value for the target parameter.

**Results:**

1. The credential value is updated successfully.
2. The job completes with success status.

### UC-CR-TPR-2: Update Credential from Deployment Parameter

**Pre-requisites:**

1. `env_inventory_generation_job` must be launched in the pipeline run.
2. Environment Instance contains a Namespace with `name` matching `<namespace-name>`.
3. That Namespace contains an Application with `name` matching `<application-name>`.
4. The Application contains a sensitive parameter in `deployParameters`.
5. The parameter is linked via the `cred` macro to an existing credential.
6. No other parameters reference the same `cred-id` and credential field.
7. `CRED_ROTATION_PAYLOAD` contains a valid `rotation_items` entry for Application-level deployment context:

    ```json
    {
      "rotation_items": [
        {
          "namespace": "<namespace-name>",
          "application": "<application-name>",
          "context": "deployment",
          "parameter_key": "db.connection.password",
          "parameter_value": "<new-value>"
        }
      ]
    }
    ```

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `ENV_NAMES: <cluster-name>/<env-name>`
2. `CRED_ROTATION_PAYLOAD: <json-in-string>`
3. `CRED_ROTATION_FORCE: false`

**Steps:**

1. The `credential_rotation` job runs in the pipeline:
   1. Finds the target Namespace and the Application specified in the payload.
   2. Uses the `deployment` context to look for the parameter in `deployParameters`.
   3. Determines which credential field is linked to the target parameter.
   4. Searches for affected credentials linked to the same `cred-id` and credential field.
   5. Finds no affected credentials and continues the flow.
   6. Updates credential value for the target parameter.

**Results:**

1. The credential value is updated successfully.
2. The job completes with success status.

### UC-CR-TPR-3: Update Credentials from Multiple rotation_items

**Pre-requisites:**

1. `env_inventory_generation_job` must be launched in the pipeline run.
2. Environment Instance contains all target Namespace and Application objects referenced by the payload.
3. The payload contains multiple `rotation_items`.
4. The payload includes items from different supported contexts:

   - `pipeline`
   - `deployment`
   - `runtime`

5. Each payload item references an existing sensitive parameter linked via the `cred` macro.
6. For each payload item, the target credential is not linked to other parameters.
7. Any payload item with `context: pipeline` does not specify `application`, because Application-level pipeline rotation is rejected by the current implementation.

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `ENV_NAMES: <cluster-name>/<env-name>`
2. `CRED_ROTATION_PAYLOAD: <json-in-string-with-multiple-rotation-items>`
3. `CRED_ROTATION_FORCE: false`

**Steps:**

1. The `credential_rotation` job runs in the pipeline:
   1. Reads all `rotation_items` from `CRED_ROTATION_PAYLOAD`.
   2. Processes payload items one by one in the order they are provided.
   3. For each item, chooses the parameter section according to the requested context:
      1. `pipeline` uses `e2eParameters`
      2. `deployment` uses `deployParameters`
      3. `runtime` uses `technicalConfigurationParameters`
   4. For each payload item, searches for affected credentials linked to the same `cred-id` and credential field.
   5. Finds no affected credentials for the successful path and continues processing.
   6. Updates credential values for all valid payload items.
   7. Stops the whole job if any payload item is invalid or cannot be processed.

**Results:**

1. All target credential values are updated successfully.
2. The job completes with success status.

## Affected Credential Handling

This section covers scenarios where the target parameter shares the same credential reference with other sensitive parameters in the same or different environments. This is the main currently implemented execution path.

### Affected Credentials with Non-Force Mode

This group covers scenarios where dependencies are found and `CRED_ROTATION_FORCE=false`. In these cases, the job fails and generates affected parameters artifact.

### UC-CR-LCH-1: Reject Affected Credential Update

**Pre-requisites:**

1. `env_inventory_generation_job` must be launched in the pipeline run.
2. The target sensitive parameter exists and is linked via the `cred` macro.
3. One or more additional sensitive parameters reference the same `cred-id` and the same credential field (`username`, `password`, or `secret`).
4. The linked parameters may be located in:

   - The same Environment Credentials file
   - One or more Shared Credentials files
   - Other affected Environment Instances

5. `CRED_ROTATION_PAYLOAD` contains a valid rotation request.
6. `CRED_ROTATION_FORCE` is not provided or is explicitly set to `false`.

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `ENV_NAMES: <cluster-name>/<env-name>`
2. `CRED_ROTATION_PAYLOAD: <json-in-string>`
3. `CRED_ROTATION_FORCE: false`

**Steps:**

1. The `credential_rotation` job runs in the pipeline:
   1. Resolves the target parameter and the credential field linked to it.
   2. Finds all other parameters affected by the same credential change.
   3. Builds the full affected parameters report for the request.
   4. Checks `CRED_ROTATION_FORCE` and sees that force mode is disabled.
   5. Generates `affected-sensitive-parameters.yaml` artifact and finishes the job with error status without writing credential changes.

**Results:**

1. The `credential_rotation` job fails with a readable error message explaining that affected parameters exist.
2. No credential values are changed.
3. Repository state remains unchanged for all credential files involved in the request.
4. The `affected-sensitive-parameters.yaml` artifact is generated and lists all detected affected parameters.

### UC-CR-LCH-2: Update Affected Credentials in Force Mode

**Pre-requisites:**

1. `env_inventory_generation_job` must be launched in the pipeline run.
2. The target sensitive parameter exists and is linked via the `cred` macro.
3. One or more additional sensitive parameters reference the same `cred-id` and the same credential field.
4. The linked parameters span at least one of the following storage locations:

   - Environment Credentials file of the target Environment
   - Shared Credentials file
   - Environment Credentials file of another affected Environment

5. `CRED_ROTATION_PAYLOAD` contains a valid rotation request.
6. `CRED_ROTATION_FORCE` is set to `true`.

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `ENV_NAMES: <cluster-name>/<env-name>`
2. `CRED_ROTATION_PAYLOAD: <json-in-string>`
3. `CRED_ROTATION_FORCE: true`

**Steps:**

1. The `credential_rotation` job runs in the pipeline:
   1. Resolves the target parameter and the credential field linked to it.
   2. Finds all other parameters affected by the same credential change.
   3. Builds the full affected parameters report for the request.
   4. Checks `CRED_ROTATION_FORCE` and allows the rotation to continue.
   5. Updates all matched credential files that contain the affected credential.

**Results:**

1. The target credential field is updated to the new value.
2. All linked sensitive parameters now reference the rotated value through the shared credential linkage.
3. The `credential_rotation` job completes successfully.
4. The `affected-sensitive-parameters.yaml` artifact is generated.

### UC-CR-VAL-1: Fail When No Affected Parameters Found

**Pre-requisites:**

1. `env_inventory_generation_job` must be launched in the pipeline run.
2. `CRED_ROTATION_PAYLOAD` contains one or more valid `rotation_items`.
3. Each payload item points to an existing sensitive parameter linked via the `cred` macro.
4. None of the payload items has other affected parameters in the current implementation search scope.
5. `CRED_ROTATION_FORCE` is `true`.

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `ENV_NAMES: <cluster-name>/<env-name>`
2. `CRED_ROTATION_PAYLOAD: <json-in-string>`
3. `CRED_ROTATION_FORCE: true`

**Steps:**

1. The `credential_rotation` job runs in the pipeline:
   1. Processes all payload items from `CRED_ROTATION_PAYLOAD`.
   2. Tries to collect affected parameters for each payload item.
   3. Finishes payload processing without collecting any affected parameters.
   4. The job finishes with error status.

**Results:**

1. The `credential_rotation` job fails.
2. No credential files are updated.
3. `affected-sensitive-parameters.yaml` is not created.

## Encryption Processing

This section covers credential rotation behavior that is confirmed by the current implementation.

### Successful Update with Encryption Enabled

This group covers successful scenarios when encryption is enabled in `config.yml`.

### UC-CR-ENC-1: Update Credentials with Plaintext Payload when Encryption Is Enabled

**Pre-requisites:**

1. `env_inventory_generation_job` must be launched in the pipeline run.
2. The configuration file `/configuration/config.yml` contains `crypt: true`.
3. The target sensitive parameter exists and is linked via the `cred` macro.
4. `CRED_ROTATION_PAYLOAD` contains plaintext JSON in string form.
5. `CRED_ROTATION_FORCE=true`.
6. One or more additional sensitive parameters reference the same `cred-id` and the same credential field.

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `ENV_NAMES: <cluster-name>/<env-name>`
2. `CRED_ROTATION_PAYLOAD: <plaintext-json-in-string>`
3. `CRED_ROTATION_FORCE: true`

**Steps:**

1. The `credential_rotation` job runs in the pipeline:
   1. Reads the payload in plaintext form.
   2. Loads credential files for the Environment and decrypts them.
   3. Searches for affected credentials linked to the same `cred-id` and credential field.
   4. Finds no affected credentials for the successful path and continues processing.
   5. Applies the requested credential changes to the matched files.
   6. Re-encrypts updated credential files before finishing the job.

**Results:**

1. The plaintext payload is processed successfully.
2. Credential values are updated according to payload input.
3. Updated credential files remain encrypted in the repository.
4. The `credential_rotation` job completes with success status.

### UC-CR-ENC-2: Update Credentials with Encrypted Payload when Encryption Is Enabled

**Pre-requisites:**

1. `env_inventory_generation_job` must be launched in the pipeline run.
2. The configuration file `/configuration/config.yml` contains `crypt: true`, so encryption mode is enabled.
3. The target sensitive parameter exists and is linked via the `cred` macro.
4. `CRED_ROTATION_PAYLOAD` is passed in encrypted form and can be decrypted by EnvGene.
5. `CRED_ROTATION_FORCE=true`.
6. One or more additional sensitive parameters reference the same `cred-id` and the same credential field.

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `ENV_NAMES: <cluster-name>/<env-name>`
2. `CRED_ROTATION_PAYLOAD: <encrypted-json-in-string>`
3. `CRED_ROTATION_FORCE: true`

**Steps:**

1. The `credential_rotation` job runs in the pipeline:
   1. Decrypts the payload for processing.
   2. Loads credential files for the Environment and decrypts them.
   3. Searches for affected credentials linked to the same `cred-id` and credential field.
   4. Finds no affected credentials for the successful path and continues processing.
   5. Applies the requested credential changes to the matched files.
   6. Re-encrypts updated credential files before finishing the job.

**Results:**

1. The encrypted payload is processed successfully.
2. Credential values are updated according to payload input.
3. Updated credential files remain encrypted in the repository.
4. The `credential_rotation` job completes with success status.

### Successful Update with Encryption Disabled

This group covers successful scenarios when encryption is disabled in `config.yml`.

### UC-CR-ENC-3: Update Credentials with Plaintext Payload when Encryption Is Disabled

**Pre-requisites:**

1. `env_inventory_generation_job` must be launched in the pipeline run.
2. The configuration file `/configuration/config.yml` contains `crypt: false`.
3. The target sensitive parameter exists and is linked via the `cred` macro.
4. `CRED_ROTATION_PAYLOAD` contains plaintext JSON in string form.
5. `CRED_ROTATION_FORCE=true`.
6. One or more additional sensitive parameters reference the same `cred-id` and the same credential field.

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `ENV_NAMES: <cluster-name>/<env-name>`
2. `CRED_ROTATION_PAYLOAD: <plaintext-json-in-string>`
3. `CRED_ROTATION_FORCE: true`

**Steps:**

1. The `credential_rotation` job runs in the pipeline:
   1. Reads the payload in plaintext form.
   2. Loads credential files for the Environment without repository decryption.
   3. Searches for affected credentials linked to the same `cred-id` and credential field.
   4. Finds no affected credentials for the successful path and continues processing.
   5. Applies the requested credential changes to the matched files.
   6. Finishes without credential file re-encryption.

**Results:**

1. The plaintext payload is processed successfully.
2. Credential values are updated according to payload input.
3. The `credential_rotation` job completes with success status.

### UC-CR-ENC-4: Update Credentials with Encrypted Payload when Encryption Is Disabled

**Pre-requisites:**

1. `env_inventory_generation_job` must be launched in the pipeline run.
2. The EnvGene configuration file `/configuration/config.yml` contains `crypt: false`, so encryption mode is disabled.
3. The target sensitive parameter exists and is linked via the `cred` macro.
4. `CRED_ROTATION_PAYLOAD` is passed in encrypted form and can be decrypted by EnvGene.

5. `CRED_ROTATION_FORCE=true`.
6. One or more additional sensitive parameters reference the same `cred-id` and the same credential field.
7. The rotation request is otherwise valid.

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `ENV_NAMES: <cluster-name>/<env-name>`
2. `CRED_ROTATION_PAYLOAD: <encrypted-json-in-string>`

**Steps:**

1. The `credential_rotation` job runs in the pipeline:
   1. Reads the payload and decrypts it for further processing.
   2. Loads credential files for the Environment without repository decryption.
   3. Searches for affected credentials linked to the same `cred-id` and credential field.
   4. Finds no affected credentials for the successful path and continues processing.
   5. Applies the requested credential changes to the matched files.
   6. Finishes without credential file re-encryption.

**Results:**

1. The encrypted payload is processed successfully.
2. Credential values are updated according to payload input.
3. The `credential_rotation` job completes with success status.
