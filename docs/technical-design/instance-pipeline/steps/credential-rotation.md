# `credential_rotation`

- [`credential_rotation`](#credential_rotation)
  - [Description](#description)
  - [Input parameters](#input-parameters)
  - [Processing flow](#processing-flow)
  - [Result](#result)
  - [Error handling](#error-handling)
  - [Related documentation](#related-documentation)

## Description

The `credential_rotation` step rotates sensitive parameter values for an Environment Instance by applying a
JSON payload that lists the parameters to update, locates the Credential files that back those parameters,
and writes the new values. The step runs only in **local mode**. In **external mode** the step aborts at
entry with an explicit error directing the operator to the
[Secret Store](/docs/features/external-creds.md#secret-store) rotation mechanism.

## Input parameters

| Parameter               | Source   | Required    | Default | Values / format             | Effect                                                                                        |
| ----------------------- | -------- | ----------- | ------- | --------------------------- | --------------------------------------------------------------------------------------------- |
| `ENV_NAMES`             | Pipeline | Yes         | None    | `<cluster-name>/<env-name>` | Selects the Environment Instance under `environments/<cluster-name>/<env-name>/`              |
| `CRED_ROTATION_PAYLOAD` | Pipeline | Yes         | None    | JSON or base64-encoded JSON | Carries the list of parameters to rotate. See [Payload format](#payload-format)               |
| `CRED_ROTATION_FORCE`   | Pipeline | No          | `false` | `true`, `false`             | When `true`, writes updates to credential files. When `false`, dry-run writes the report only |
| `GET_PASSPORT`          | Pipeline | Conditional | None    | `true`, `false`             | Mutually exclusive with `CRED_ROTATION_PAYLOAD`. The step fails at entry when both are set    |

### Payload format

```json
{
  "rotation_items": [
    {
      "namespace": "<namespace-name>",
      "application": "<application-name>",
      "parameter_key": "<parameter-key>",
      "context": "deployParameters",
      "parameter_value": "<new-secret-value>"
    }
  ]
}
```

The `application` field is optional. Omit it to rotate a Namespace-level parameter. The `context` field
selects the parameter container (for example `deployParameters`, `e2eParameters`).

## Processing flow

1. **Decide whether to run**

   The Instance pipeline runs this step when pipeline parameter `CRED_ROTATION_PAYLOAD` is set.

2. **Mode check**

   The step reads the Instance repository mode. The repository is in **external mode** when
   `/configuration/secret-stores.yml` is present, and in **local mode** when the file is absent. See
   [Mode detection](/docs/features/credential-processing.md#mode-detection).

   In external mode, the step fails at entry with a single error directing the operator to the
   [Secret Store](/docs/features/external-creds.md#secret-store) rotation mechanism. The step does not read
   `CRED_ROTATION_PAYLOAD` or scan Credential files.

3. **Validate inputs**

   1. The step validates the mutual exclusion with `GET_PASSPORT`. When both are set, the step fails.

   2. The step decodes `CRED_ROTATION_PAYLOAD`. The payload is accepted as raw JSON or base64-encoded
      JSON. SOPS-encrypted payloads are decrypted when `crypt_backend` is `SOPS`. Fernet-encrypted
      payloads are rejected.

   3. The step validates each `rotation_items` entry against the expected schema.

4. **Scan Credential files and parameter files**

   1. The step reads every Credential file under
      `environments/<cluster-name>/<env-name>/Credentials/` and every Credential file under the Instance
      repository Shared Credentials paths (environment, cluster, site).

   2. The step reads namespace and application YAML files under
      `environments/<cluster-name>/<env-name>/Namespaces/` to resolve each payload entry's parameter
      location.

5. **Compute affected parameters**

   For every `rotation_items` entry, the step finds the Credential ID referenced by the target parameter,
   then finds every other parameter that references the same Credential ID. The step builds the report
   file `affected-sensitive-parameters.yaml` listing all affected parameter references per rotation entry.

6. **Apply rotation**

   When `CRED_ROTATION_FORCE` is `true`, the step updates the Credential value in the resolved Credential
   file and re-encrypts the file. When `CRED_ROTATION_FORCE` is `false`, the step does not write.

## Result

1. File `affected-sensitive-parameters.yaml` at the Instance repository root lists every parameter affected
   by the rotation payload.

2. When `CRED_ROTATION_FORCE` is `true`, the step updates Credential files under
   `environments/<cluster-name>/<env-name>/Credentials/` and under the Shared Credentials paths. The step
   re-encrypts files it writes.

3. In external mode, no files change. The step fails at entry.

## Error handling

**2a.** The step fails when the Instance repository is in external mode. The error names the mode and
points to the [Secret Store](/docs/features/external-creds.md#secret-store) rotation mechanism. No
Credential files are read.

**3a.** The step fails when `CRED_ROTATION_PAYLOAD` and `GET_PASSPORT` are both set.

**3b.** The step fails when `CRED_ROTATION_PAYLOAD` is not valid JSON or valid base64-encoded JSON, or
when the payload is encrypted with Fernet.

**3c.** The step fails when a `rotation_items` entry references a Credential of `type: external`. External
Credentials are not rotatable by EnvGene. The error names the Credential ID.

**4a.** The step fails when a `rotation_items` entry names a parameter path that does not resolve to a
Namespace or Application YAML file. The error names the parameter key, namespace, and application.

## Related documentation

- [Credential processing](/docs/features/credential-processing.md)
- [External Credentials Management](/docs/features/external-creds.md)
- [Credential rotation](/docs/features/cred-rotation.md)
- [`env_build`](/docs/technical-design/instance-pipeline/steps/env-build.md)
