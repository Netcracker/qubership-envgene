# External Credentials VALS Reference CLI

- [External Credentials VALS Reference CLI](#external-credentials-vals-reference-cli)
  - [Synopsis](#synopsis)
  - [Input](#input)
  - [Output](#output)
  - [Algorithm](#algorithm)
  - [Image location](#image-location)
  - [Usage](#usage)

## Synopsis

`vals-reference-cli` is a native binary shipped in the `qubership-envgene` image. It exposes the
VALS URI assembly logic used by the Effective Set calculator, as a command line utility so that Python jobs can resolve
external system credentials without reimplementing store-specific rules.

```bash
echo '<json>' | vals-reference-cli
```

OR:

```bash
vals-reference-cli --file request.json
```

## Input

The tool accepts configuration input either via standard input (stdin) or by specifying an input JSON file using the --file option. Each invocation processes a JSON containing single credential and its associated secret store configuration. The input payload must conform to the JSON structure defined below.

```json
{
  "credentialId": "app-custom-cred",
  "credential": {
    "remoteRefPath": "cluster/env/database",
    "secretStore": "vault_store"
  },
  "secretStore": {
    "type": "vault",
    "mountPath": "secret"
  }
}
```

| Field            | Required | Meaning                                                           |
|------------------|----------|-------------------------------------------------------------------|
| `credentialId`   | yes      | Unique credential identifier                                      |
| `credential`     | yes      | [Credential](/docs/features/external-creds.md#credential)         |
| `secretStore`    | yes      | Secret store details corresponding to the given credential [Secret Store](/docs/features/external-creds.md#secret-store) |

## Output

The output is a JSON object that maps credential ID to its corresponding VALS reference. The result is written to standard output (stdout). Any logs or errors encountered during execution are written to standard error (stderr).

**Sample output**:

```json
{
  "app-custom-cred": "ref+gcpsecrets://agf56hoji8/test-cluster-01--env-1--app-custom-cred?secret_store_id=maas_store"
}
```

**Error and Exit code**:

| Exit Code | Meaning          | Example                                      |
|-----------|------------------|----------------------------------------------|
| 0         | Success          | map of credential ID and it's vals reference |
| 1         | Unexpected error |                                              |
| 2         | Invalid input    | Invalid request: credId must not be blank    |

## Algorithm

The CLI delegates to `extcreds-vals-ref-core`, which implements:

1. [Normalization to `normalizedSecretName`](/docs/features/external-creds.md#normalization-to-normalizedsecretname)
2. [Base URI assembly](/docs/features/external-creds.md#vals-reference-generation) (step 3)

The Effective Set calculator calls the same core module in-process. For identical inputs the emitted
`normalizedSecretName` and `valsReference` are byte-identical to calculator output.

## Image location

In the `qubership-envgene` container:

```text
/module/scripts/vals-reference-cli
```

## Usage

No JRE is required to run the binary.
Python usage snippet.

```python
result = subprocess.run(
    ["/module/scripts/vals-reference-cli"],
    input=json.dumps(request),
    text=True,
    capture_output=True,
    check=True
)
vals_map = json.loads(result.stdout)[cred_id]
vals_ref = vals_map[cred_id]
```

To run locally in intellij

```text
-Dquarkus.args="--file <path to input JSON file> 
```
