# External Credentials VALS Reference CLI

- [External Credentials VALS Reference CLI](#external-credentials-vals-reference-cli)
  - [Synopsis](#synopsis)
  - [Arguments](#arguments)
  - [Input files](#input-files)
  - [Output format](#output-format)
  - [Algorithm](#algorithm)
  - [Image location](#image-location)

## Synopsis

`extcreds-vals-ref` is a native binary shipped in the `qubership-envgene` image. It exposes the same
normalization and VALS URI assembly logic used by the Effective Set calculator so Python jobs can resolve
external system credentials without reimplementing store-specific rules.

```bash
extcreds-vals-ref --credentials /configuration/credentials/credentials.yml \
  --secret-stores /configuration/secret-stores.yml
```

Resolve a specific property for a multi-field credential:

```bash
extcreds-vals-ref \
  --credentials /configuration/credentials/credentials.yml \
  --secret-stores /configuration/secret-stores.yml \
  --requests /tmp/vals-ref-requests.json
```

## Arguments

| Flag | Required | Default | Meaning |
|------|----------|---------|---------|
| `-c`, `--credentials` | yes | — | Path to credentials YAML |
| `-s`, `--secret-stores` | yes | — | Path to secret-stores YAML |
| `-r`, `--requests` | no | all `type: external` credentials | Batch request file (YAML or JSON) |
| `-f`, `--fields` | no | `both` | Output fields: `normalized`, `vals`, or `both` |

When `--requests` is omitted, every credential with `type: external` in the credentials file is processed
once with no `property` (single-value semantics).

## Input files

**Credentials** and **secret-stores** use the same YAML shapes as EnvGene configuration files. See
[Credential](/docs/envgene-objects.md#credential) and
[Secret Store](/docs/features/external-creds.md#secret-store).

**Requests** (optional) is a YAML or JSON document:

```yaml
requests:
  - credId: self-token-cred
  - credId: artifactory-cred
    property: username
```

## Output format

The CLI writes a single JSON document to stdout:

```json
{
  "results" : [ {
    "credId" : "app-sidecar-token",
    "normalizedSecretName" : "test_cluster_01/env-1/app-sidecar-token",
    "valsReference" : "ref+vault://secret/data/app/data/test_cluster_01/env-1/app-sidecar-token#/value"
  } ],
  "errors" : [ ]
}
```

| Field | Present when | Meaning |
|-------|--------------|---------|
| `credId` | always | Credential identifier |
| `property` | request carried `property` | Property from the credRef |
| `normalizedSecretName` | `--fields normalized` or `both` | Store-specific normalized secret name |
| `valsReference` | `--fields vals` or `both` | Full VALS URI including fragment when applicable |

Exit code is `0` when all requests succeed; `1` when any entry in `errors` is present.

## Algorithm

The CLI delegates to `extcreds-vals-ref-core`, which implements:

1. [Normalization to `normalizedSecretName`](/docs/features/external-creds.md#normalization-to-normalizedsecretname)
2. [URI fragment selection](/docs/features/external-creds.md#vals-reference-generation) (step 2)
3. [Base URI assembly](/docs/features/external-creds.md#vals-reference-generation) (step 3)

The Effective Set calculator calls the same core module in-process. For identical inputs the emitted
`normalizedSecretName` and `valsReference` are byte-identical to calculator output.

## Image location

In the `qubership-envgene` container:

```text
/module/bin/extcreds-vals-ref
```

No JRE is required to run the binary.
