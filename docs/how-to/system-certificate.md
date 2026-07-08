# Configure system certificates

- [Description](#description)
- [Prerequisites](#prerequisites)
- [Steps](#steps)
  - [1. Prepare the PEM CA bundle](#1-prepare-the-pem-ca-bundle)
  - [2. Base64-encode the PEM file](#2-base64-encode-the-pem-file)
  - [3. Create the GitLab CI/CD variable](#3-create-the-gitlab-cicd-variable)
  - [4. Run an EnvGene pipeline job](#4-run-an-envgene-pipeline-job)
  - [5. Verify certificate loading in the job log](#5-verify-certificate-loading-in-the-job-log)
- [Results](#results)
- [Related documentation](#related-documentation)

> For background, see [System certificate configuration](/docs/features/system-certificate.md).

## Description

Store your corporate CA certificate or bundle in the CI/CD variable `SSL_CERTIFICATES_BUNDLE` when the bundle fits in a
CI/CD variable.

For other certificate sources and how EnvGene merges them, see
[Certificate sources](/docs/features/system-certificate.md#certificate-sources).

> [!WARNING]
> GitLab limits a CI/CD variable value to 10,000 characters. A single CA or a short chain of two or three certificates
> usually fits. For larger bundles, store certificate files in `ca_bundle` or `configuration/certs` instead (see
> [Certificate sources](/docs/features/system-certificate.md#certificate-sources)).

## Prerequisites

- Maintainer access (or equivalent) to the GitLab project that hosts the instance repository pipeline.
- A PEM file with the CA certificate or certificate chain your pipeline must trust (for example `ca-bundle.pem`).
- The instance repository pipeline is configured and can run EnvGene jobs.

> [!IMPORTANT]
> If `SSL_CERTIFICATES_BUNDLE` is set but invalid, the job fails. See
> [Certificate validation](/docs/features/system-certificate.md#certificate-validation).

## Steps

### 1. Prepare the PEM CA bundle

Confirm the CA content is in PEM format with `-----BEGIN CERTIFICATE-----` and `-----END CERTIFICATE-----` boundaries.

For a multi-level chain, see [Certificate chain ordering](/docs/features/system-certificate.md#certificate-chain-ordering).
To obtain certificates from a target service, see
[How to obtain required certificates](/docs/features/system-certificate.md#how-to-obtain-required-certificates).

Verify the file before encoding:

```bash
openssl x509 -in ca-bundle.pem -text -noout
openssl x509 -in ca-bundle.pem -noout -dates
```

The first command prints certificate details without error. In the second output, confirm `notAfter` is a future date.
If the PEM file contains multiple certificates, check the expiry date for each certificate block.

Confirm the certificate is not expired before you continue.

### 2. Base64-encode the PEM file

Encode the PEM file as a single line with no line breaks.

On Linux (GNU `base64`):

```bash
base64 -w 0 ca-bundle.pem
```

On macOS:

```bash
base64 -i ca-bundle.pem | tr -d '\n'
```

Copy the full output string. You use it as the variable value in the next step.

Confirm the encoded string does not exceed 10,000 characters. GitLab rejects longer CI/CD variable values.

On Linux (GNU `base64`):

```bash
base64 -w 0 ca-bundle.pem | wc -c
```

On macOS:

```bash
base64 -i ca-bundle.pem | tr -d '\n' | wc -c
```

The count must be 10,000 or less. If it is larger, use `ca_bundle` or `configuration/certs` instead (see
[Certificate sources](/docs/features/system-certificate.md#certificate-sources)).

> [!WARNING]
> Do not add quotes, newlines, or spaces around the encoded string. Extra characters cause base64 decoding to fail and
> the pipeline job aborts.

### 3. Create the GitLab CI/CD variable

1. Open the GitLab project for the instance repository.
1. Go to **Settings** → **CI/CD** → **Variables**.
1. Select **Add variable**.
1. Set the fields:

| Field    | Value                                      |
|----------|--------------------------------------------|
| Key      | `SSL_CERTIFICATES_BUNDLE`                  |
| Value    | Output from the base64 command in step 2   |
| Type     | Variable                                   |
| Flags    | Masked (recommended)                       |

1. Save the variable.

Confirm `SSL_CERTIFICATES_BUNDLE` appears in the project CI/CD variable list with the expected key name.

> [!NOTE]
> GitLab may refuse to mask values that do not meet masking rules. If masking fails, save the variable unmasked and
> restrict project access instead.

### 4. Run an EnvGene pipeline job

Trigger the instance pipeline. Jobs that load system certificates at job start include:

- `app_reg_def_process`
- `process_sd`
- `env_build`
- `generate_effective_set`
- `git_commit`
- `get_passport`

For a minimal TLS check to Artifactory, start the pipeline with `ENV_BUILDER: true` and a valid `ENV_TEMPLATE_VERSION`.
See [Template download from Artifactory with system certificates](/docs/use-cases/system-certificate.md#uc-sc-usg-1-template-download-from-artifactory-with-system-certificates).

Wait until the job finishes.

### 5. Verify certificate loading in the job log

Open the job log for the pipeline run.

Confirm the log shows certificates loaded from `SSL_CERTIFICATES_BUNDLE` and contains a successful import message (for
example `certs from … added to trusted root`). Confirm the job exits with success.

To inspect `REQUESTS_CA_BUNDLE`, set `ENVGENE_LOG_LEVEL: DEBUG` and see
[Technical implementation](/docs/features/system-certificate.md#technical-implementation).

## Results

After a successful run, `SSL_CERTIFICATES_BUNDLE` is set in GitLab CI/CD, certificates from the bundle are in the
runner trust store, and the job completes successfully.

## Related documentation

- [System certificate configuration](/docs/features/system-certificate.md)
- [System certificate use cases](/docs/use-cases/system-certificate.md)
