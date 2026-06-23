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
- [Other scenarios](#other-scenarios)
  - [Rotate the CA bundle](#rotate-the-ca-bundle)
  - [Remove system certificates from pipeline runs](#remove-system-certificates-from-pipeline-runs)
- [Related documentation](#related-documentation)

> For background, see [System certificate configuration](/docs/features/system-certificate.md).

## UC-SC-01: How to configure system certificates with the SSL_CERTIFICATES_BUNDLE CI/CD variable

### Description

Store your corporate CA certificate or bundle in the GitLab CI/CD variable `SSL_CERTIFICATES_BUNDLE`. EnvGene decodes
the value at the start of each pipeline job and installs the certificates into the runner trust store before connecting
to external systems.

This is the recommended way to supply system certificates. You do not commit certificate files to the instance repository.

`SSL_CERTIFICATES_BUNDLE` is a pipeline-level variable. When set, it applies to every environment processed in that
pipeline run.

> [!IMPORTANT]
> If `SSL_CERTIFICATES_BUNDLE` is set but the value is not valid base64 or does not decode to valid PEM content, the
> pipeline job fails. EnvGene does not fall back to another certificate source.

### Prerequisites

- Maintainer access (or equivalent) to the GitLab project that hosts the instance repository pipeline.
- A PEM file with the CA certificate or certificate chain your pipeline must trust (for example `ca-bundle.pem`).
- The instance repository pipeline is configured and can run EnvGene jobs.

### Steps

#### 1. Prepare the PEM CA bundle

Confirm the CA content is in PEM format with `-----BEGIN CERTIFICATE-----` and `-----END CERTIFICATE-----` boundaries.

For a multi-level chain, combine every certificate into one `.pem` file in order: root CA first, then intermediate CAs,
then the end-entity certificate last. See [Certificate chain ordering](/docs/features/system-certificate.md#certificate-chain-ordering)
for the full rule.

To obtain certificates from a target service, see
[How to obtain required certificates](/docs/features/system-certificate.md#how-to-obtain-required-certificates).

Verify the file before encoding:

```bash
openssl x509 -in ca-bundle.pem -text -noout
```

The command prints certificate details without error.

#### 2. Base64-encode the PEM file

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

> [!WARNING]
> Do not add quotes, newlines, or spaces around the encoded string. Extra characters cause base64 decoding to fail and
> the pipeline job aborts.

#### 3. Create the GitLab CI/CD variable

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

#### 4. Run an EnvGene pipeline job

Trigger the instance pipeline. Any EnvGene job loads certificates at job start, including:

- `app_reg_def_process`
- `process_sd`
- `env_build`
- `generate_effective_set`
- `git_commit`

For a minimal check that TLS to Artifactory works, start the pipeline with `ENV_BUILDER: true` and a valid
`ENV_TEMPLATE_VERSION`. See [UC-SC-USG-1](/docs/use-cases/system-certificate.md#uc-sc-usg-1-template-download-from-artifactory-with-system-certificates).

Wait until the job finishes.

#### 5. Verify certificate loading in the job log

Open the job log for the pipeline run.

Confirm the log shows `SSL_CERTIFICATES_BUNDLE` as the resolved certificate source.

Confirm the log contains a successful certificate import message (for example `certs from … added to trusted root`).

Confirm the job exits with success.

To inspect `REQUESTS_CA_BUNDLE` in a debug run, set `ENVGENE_LOG_LEVEL: DEBUG` and check the job log for the
OS-specific system CA bundle path. See
[Technical implementation](/docs/features/system-certificate.md#technical-implementation) for expected paths.

### Results

After a successful run:

- GitLab project CI/CD variable `SSL_CERTIFICATES_BUNDLE` holds the base64-encoded PEM bundle.
- Pipeline job logs show `SSL_CERTIFICATES_BUNDLE` as the resolved certificate source.
- CA certificates from the decoded bundle are present in the runner trust store.
- `REQUESTS_CA_BUNDLE` points to the OS-specific system CA bundle path in the job environment.
- The job completes successfully.

No certificate files are added to the instance repository.

### Other scenarios

#### Rotate the CA bundle

Repeat steps 1 to 3 with the new PEM file. Update the existing `SSL_CERTIFICATES_BUNDLE` variable value. Re-run the
pipeline. Confirm the job log shows successful certificate loading.

#### Remove system certificates from pipeline runs

Delete the `SSL_CERTIFICATES_BUNDLE` CI/CD variable from the GitLab project, or clear its value. Re-run the pipeline.
EnvGene no longer loads certificates from this source.

## Related documentation

- [System certificate configuration](/docs/features/system-certificate.md)
- [System certificate use cases](/docs/use-cases/system-certificate.md)
