# System certificate use cases

- [System certificate use cases](#system-certificate-use-cases)
  - [Overview](#overview)
  - [Certificate source resolution](#certificate-source-resolution)
    - [UC-SC-SRC-1: Load and merge certificates from configured sources](#uc-sc-src-1-load-and-merge-certificates-from-configured-sources)
    - [UC-SC-SRC-2: Load default certificate when configured sources are empty](#uc-sc-src-2-load-default-certificate-when-configured-sources-are-empty)
  - [Source merging](#source-merging)
    - [UC-SC-MRG-1: One source valid and one source invalid](#uc-sc-mrg-1-one-source-valid-and-one-source-invalid)
    - [UC-SC-MRG-2: Duplicate certificates from different sources](#uc-sc-mrg-2-duplicate-certificates-from-different-sources)
  - [Validation failures](#validation-failures)
    - [UC-SC-VAL-1: Invalid CI/CD bundle fails pipeline](#uc-sc-val-1-invalid-cicd-bundle-fails-pipeline)
    - [UC-SC-VAL-2: Unreadable certificate file in folder fails pipeline](#uc-sc-val-2-unreadable-certificate-file-in-folder-fails-pipeline)
    - [UC-SC-VAL-3: Invalid certificate files in folder fail pipeline](#uc-sc-val-3-invalid-certificate-files-in-folder-fail-pipeline)
    - [UC-SC-VAL-4: File with valid and invalid PEM blocks](#uc-sc-val-4-file-with-valid-and-invalid-pem-blocks)
  - [Artifactory access](#artifactory-access)
    - [UC-SC-USG-1: Template download from Artifactory with system certificates](#uc-sc-usg-1-template-download-from-artifactory-with-system-certificates)

## Overview

This document covers use cases for [system certificate configuration](/docs/features/system-certificate.md).
For merge rules, validation, and default-certificate behaviour, see the feature specification.

The use cases below use a certificate-loading job as the trigger unless noted otherwise. One of the following instance
pipeline jobs runs:

1. `env-prepare`
2. `cmdb_import`

## Certificate source resolution

### UC-SC-SRC-1: Load and merge certificates from configured sources

**Pre-requisites:**

> [!NOTE]
> One or more configured sources are non-empty. Every non-empty source contains at least one valid certificate. Examples:

1. `SSL_CERTIFICATES_BUNDLE` only.
2. `/ca_bundle` only.
3. `/configuration/certs` only.
4. `SSL_CERTIFICATES_BUNDLE` and `/ca_bundle`.
5. `SSL_CERTIFICATES_BUNDLE` and `/configuration/certs`.
6. `/ca_bundle` and `/configuration/certs`.
7. All three configured sources.

**Trigger:**

A certificate-loading job runs. See [Overview](#overview).

**Steps:**

1. A certificate-loading job runs.
2. EnvGene loads valid certificates from every non-empty configured source as described in
   [Certificate validation](/docs/features/system-certificate.md#certificate-validation).
3. All loaded certificates are added to the system trusted root certificate store after one trust-store update.
4. `REQUESTS_CA_BUNDLE` is set.

**Results:**

1. Pipeline logs show certificates loaded from every non-empty configured source.
2. CA certificates from all non-empty sources are present in the runner trust store.
3. The job completes successfully.

### UC-SC-SRC-2: Load default certificate when configured sources are empty

**Pre-requisites:**

1. `SSL_CERTIFICATES_BUNDLE`, `/ca_bundle`, and `/configuration/certs` are all unset, absent, or empty.
2. The runner image ships `/default_cert.pem`. Images without the file skip this step and install no certificate.

**Trigger:**

A certificate-loading job runs. See [Overview](#overview).

**Steps:**

1. A certificate-loading job runs.
2. No configured source contributes certificates.
3. EnvGene applies `/default_cert.pem` from the runner image.

**Results:**

1. Pipeline logs show the default certificate was applied.
2. CA certificates from `/default_cert.pem` are present in the runner trust store.
3. The job completes successfully.

## Source merging

### UC-SC-MRG-1: One source valid and one source invalid

**Pre-requisites:**

1. At least two configured sources are non-empty.
2. One non-empty source contains only valid certificates.
3. Another non-empty source contains at least one file with a `-----BEGIN CERTIFICATE-----` block that fails PEM
   validation.

> [!NOTE]
> Examples:

1. `SSL_CERTIFICATES_BUNDLE` is valid and `/ca_bundle` contains an invalid PEM file.
2. `SSL_CERTIFICATES_BUNDLE` is valid and `/configuration/certs` contains an invalid PEM file.
3. `/ca_bundle` is valid and `/configuration/certs` contains an invalid PEM file.

**Trigger:**

A certificate-loading job runs. See [Overview](#overview).

**Steps:**

1. A certificate-loading job runs.
2. EnvGene validates every non-empty configured source.
3. PEM validation fails in one source.
4. After all sources are checked, the job fails with a certificate loading error.

**Results:**

1. The job fails with a non-zero exit status.
2. Pipeline log contains an explicit certificate loading error that identifies the invalid source.
3. No certificate is installed.

### UC-SC-MRG-2: Duplicate certificates from different sources

**Pre-requisites:**

1. The same CA certificate is present in `SSL_CERTIFICATES_BUNDLE` and in `/ca_bundle` (or `/configuration/certs`).

**Trigger:**

A certificate-loading job runs. See [Overview](#overview).

**Steps:**

1. A certificate-loading job runs.
2. EnvGene loads certificates from every non-empty configured source.

**Results:**

1. The duplicate certificate is applied from both sources without errors.
2. The job completes successfully.

## Validation failures

### UC-SC-VAL-1: Invalid CI/CD bundle fails pipeline

**Pre-requisites:**

> [!NOTE]
> One of the following conditions must be met:

1. `SSL_CERTIFICATES_BUNDLE` is set to a non-empty value that is not valid base64.
2. `SSL_CERTIFICATES_BUNDLE` decodes successfully but does not contain a `-----BEGIN CERTIFICATE-----` block.
3. `SSL_CERTIFICATES_BUNDLE` decodes to a PEM block that fails PEM validation.

**Trigger:**

A certificate-loading job runs. See [Overview](#overview).

**Steps:**

1. A certificate-loading job runs.
2. EnvGene loads `SSL_CERTIFICATES_BUNDLE`.
3. Base64 decoding, PEM block detection, or PEM validation fails.
4. After all sources are checked, the job fails with a certificate loading error.

**Results:**

1. The job fails with a non-zero exit status.
2. Pipeline log contains one error message that names `SSL_CERTIFICATES_BUNDLE` and lists every other validation
   problem found across the sources.
3. No certificate is installed.

### UC-SC-VAL-2: Unreadable certificate file in folder fails pipeline

**Pre-requisites:**

1. A folder source (`/ca_bundle` or `/configuration/certs`) contains at least one file that cannot be read, for example
   due to restrictive file permissions.

**Trigger:**

A certificate-loading job runs. See [Overview](#overview).

**Steps:**

1. A certificate-loading job runs.
2. EnvGene loads certificate files from the folder source.
3. Reading a file fails.
4. After all sources are checked, the job fails with a certificate loading error.

**Results:**

1. The job fails with a non-zero exit status.
2. Pipeline log identifies the unreadable file path.

### UC-SC-VAL-3: Invalid certificate files in folder fail pipeline

**Pre-requisites:**

1. A folder source (`/ca_bundle` or `/configuration/certs`) contains at least one file with a `-----BEGIN CERTIFICATE-----`
   block that fails PEM validation.

**Trigger:**

A certificate-loading job runs. See [Overview](#overview).

**Steps:**

1. A certificate-loading job runs.
2. EnvGene validates certificate files in the folder source.
3. One or more files fail PEM validation.
4. After all sources are checked, the job fails with a single certificate loading error that lists every invalid
   file path.

**Results:**

1. The job fails with a non-zero exit status.
2. Pipeline log lists every invalid file path in one error message.

### UC-SC-VAL-4: File with valid and invalid PEM blocks

**Pre-requisites:**

1. A folder source contains one file with two `-----BEGIN CERTIFICATE-----` blocks, where the first block is valid PEM
   and the second block is corrupted.

**Trigger:**

A certificate-loading job runs. See [Overview](#overview).

**Steps:**

1. A certificate-loading job runs.
2. EnvGene validates the file in the folder source.
3. PEM validation fails.
4. After all sources are checked, the job fails with a certificate loading error.

**Results:**

1. The job fails with a non-zero exit status.
2. Pipeline log contains an explicit certificate loading error that identifies the file path.

## Artifactory access

### UC-SC-USG-1: Template download from Artifactory with system certificates

**Pre-requisites:**

> [!NOTE]
> One of the following scenarios must be met:

1. `SSL_CERTIFICATES_BUNDLE` is set to a valid base64-encoded PEM CA certificate that trusts the Artifactory endpoint, and
   the template artifact is available in Artifactory.
2. `SSL_CERTIFICATES_BUNDLE` is set to a valid base64-encoded PEM CA certificate that does not trust the Artifactory
   endpoint, and the template artifact is available in Artifactory.
3. `SSL_CERTIFICATES_BUNDLE` is set to a valid base64-encoded PEM CA certificate, and Artifactory is unreachable.

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

```yaml
ENV_NAMES: <env_name>
ENV_BUILDER: true
ENV_TEMPLATE_VERSION: <application>:<version>
```

**Steps:**

1. The `env-prepare` job runs.
2. EnvGene loads certificates from `SSL_CERTIFICATES_BUNDLE`.
3. EnvGene resolves the template from `ENV_TEMPLATE_VERSION` and downloads the artifact from Artifactory over TLS.

**Results:**

1. Scenario 1: the template artifact is downloaded from Artifactory successfully and the job completes successfully.
2. Scenario 2: the job fails with a TLS error. The pipeline log does not report a connection error to an unknown host.
3. Scenario 3: the job fails with a connection error. The pipeline log does not report a certificate validation error as
   the primary failure cause.
