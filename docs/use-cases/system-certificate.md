# System certificate use cases

- [System certificate use cases](#system-certificate-use-cases)
  - [Overview](#overview)
  - [Certificate source resolution](#certificate-source-resolution)
    - [UC-SC-SRC-1: Load certificates from GitLab CI/CD variable](#uc-sc-src-1-load-certificates-from-gitlab-cicd-variable)
    - [UC-SC-SRC-2: Load certificates from Cloud Passport](#uc-sc-src-2-load-certificates-from-cloud-passport)
    - [UC-SC-SRC-3: Load certificates from `ca_bundle` folder](#uc-sc-src-3-load-certificates-from-ca_bundle-folder)
    - [UC-SC-SRC-4: Load certificates from `configuration/certs`](#uc-sc-src-4-load-certificates-from-configurationcerts)
    - [UC-SC-SRC-5: No system certificates loaded](#uc-sc-src-5-no-system-certificates-loaded)
  - [Priority resolution](#priority-resolution)
    - [UC-SC-PRI-1: Higher-priority source hides lower-priority sources](#uc-sc-pri-1-higher-priority-source-hides-lower-priority-sources)
  - [Validation failures](#validation-failures)
    - [UC-SC-VAL-1: Invalid base64-encoded bundle fails pipeline](#uc-sc-val-1-invalid-base64-encoded-bundle-fails-pipeline)
    - [UC-SC-VAL-2: Unreadable certificate file in folder fails pipeline](#uc-sc-val-2-unreadable-certificate-file-in-folder-fails-pipeline)
    - [UC-SC-VAL-3: Invalid certificate file in folder fails pipeline](#uc-sc-val-3-invalid-certificate-file-in-folder-fails-pipeline)
  - [Artifactory access](#artifactory-access)
    - [UC-SC-USG-1: Template download from Artifactory with system certificates](#uc-sc-usg-1-template-download-from-artifactory-with-system-certificates)

## Overview

This document covers use cases for [system certificate configuration](/docs/features/system-certificate.md). EnvGene loads
system certificates at the start of pipeline jobs. EnvGene evaluates four sources in fixed priority order, selects the first
non-empty source, and does not merge certificates across sources.

## Certificate source resolution

### UC-SC-SRC-1: Load certificates from GitLab CI/CD variable

**Pre-requisites:**

1. GitLab project has CI/CD variable `SSL_CERTIFICATES_BUNDLE` set to a non-empty value.
2. Variable value is valid base64-encoded PEM CA certificate or bundle content.

**Trigger:**

> [!NOTE]
> One of the following jobs runs in the instance pipeline (GitLab or GitHub):

1. `app_reg_def_process`
2. `process_sd`
3. `env_build`
4. `generate_effective_set`
5. `git_commit`

**Steps:**

1. A pipeline job runs.
2. EnvGene resolves `SSL_CERTIFICATES_BUNDLE` as the certificate source and loads the decoded certificates.
3. CA certificates are added to the system trusted root certificate store.
4. `REQUESTS_CA_BUNDLE` is set to the OS-specific system CA bundle path.

**Results:**

1. Pipeline logs show `SSL_CERTIFICATES_BUNDLE` as the resolved certificate source.
2. CA certificates from the decoded bundle are present in the runner trust store.
3. The job completes successfully.

### UC-SC-SRC-2: Load certificates from Cloud Passport

**Pre-requisites:**

1. `SSL_CERTIFICATES_BUNDLE` is unset or empty.
2. Resolved Cloud Passport has non-empty `Devops.CA_BUNDLE_CERTIFICATE`.
3. Value is valid base64-encoded PEM CA certificate or bundle content.

**Trigger:**

> [!NOTE]
> One of the following jobs runs in the instance pipeline (GitLab or GitHub):

1. `app_reg_def_process`
2. `process_sd`
3. `env_build`
4. `generate_effective_set`
5. `git_commit`

**Steps:**

1. A pipeline job runs.
2. EnvGene resolves `CA_BUNDLE_CERTIFICATE` from Cloud Passport as the certificate source and loads the decoded
   certificates.
3. CA certificates are added to the system trusted root certificate store.
4. `REQUESTS_CA_BUNDLE` is set to the OS-specific system CA bundle path.

**Results:**

1. Pipeline logs show `CA_BUNDLE_CERTIFICATE` as the resolved certificate source.
2. CA certificates from the decoded bundle are present in the runner trust store.
3. `REQUESTS_CA_BUNDLE` is set in the job environment.

### UC-SC-SRC-3: Load certificates from `ca_bundle` folder

**Pre-requisites:**

1. `SSL_CERTIFICATES_BUNDLE` is unset or empty.
2. `Devops.CA_BUNDLE_CERTIFICATE` is unset or empty in the resolved Cloud Passport.
3. `/ca_bundle` exists at the repository root and contains at least one `.crt` or `.pem` certificate file, for example
   `/ca_bundle/ca.pem`.

**Trigger:**

> [!NOTE]
> One of the following jobs runs in the instance pipeline (GitLab or GitHub):

1. `app_reg_def_process`
2. `process_sd`
3. `env_build`
4. `generate_effective_set`
5. `git_commit`

**Steps:**

1. A pipeline job runs.
2. EnvGene resolves `ca_bundle` as the certificate source and loads every `.crt` or `.pem` file in the folder.
3. CA certificates are added to the system trusted root certificate store.
4. `REQUESTS_CA_BUNDLE` is set to the OS-specific system CA bundle path.

**Results:**

1. Pipeline logs show `ca_bundle` as the resolved certificate source.
2. Every `.crt` or `.pem` file in `/ca_bundle/` is processed.
3. CA certificates from `/ca_bundle/` are present in the runner trust store.
4. `REQUESTS_CA_BUNDLE` is set in the job environment.

### UC-SC-SRC-4: Load certificates from `configuration/certs`

**Pre-requisites:**

1. `SSL_CERTIFICATES_BUNDLE` is unset or empty.
2. `Devops.CA_BUNDLE_CERTIFICATE` is unset or empty in the resolved Cloud Passport.
3. `/ca_bundle` is absent or empty at the repository root.
4. `/configuration/certs` exists and contains at least one `.crt` or `.pem` certificate file, for example
   `/configuration/certs/ca.pem`.

**Trigger:**

> [!NOTE]
> One of the following jobs runs in the instance pipeline (GitLab or GitHub):

1. `app_reg_def_process`
2. `process_sd`
3. `env_build`
4. `generate_effective_set`
5. `git_commit`

**Steps:**

1. A pipeline job runs.
2. EnvGene resolves `configuration/certs` as the certificate source and loads every `.crt` or `.pem` file in the folder.
3. CA certificates are added to the system trusted root certificate store.
4. `REQUESTS_CA_BUNDLE` is set to the OS-specific system CA bundle path.

**Results:**

1. Pipeline logs show `configuration/certs` as the resolved certificate source.
2. Every `.crt` or `.pem` file in `/configuration/certs/` is processed.
3. CA certificates from `/configuration/certs/` are present in the runner trust store.
4. `REQUESTS_CA_BUNDLE` is set in the job environment.

### UC-SC-SRC-5: No system certificates loaded

**Pre-requisites:**

1. `SSL_CERTIFICATES_BUNDLE` is unset or empty.
2. `Devops.CA_BUNDLE_CERTIFICATE` is unset or empty in the resolved Cloud Passport.
3. `/ca_bundle` is absent or empty at the repository root.
4. `/configuration/certs` is absent or empty.

**Trigger:**

> [!NOTE]
> One of the following jobs runs in the instance pipeline (GitLab or GitHub):

1. `app_reg_def_process`
2. `process_sd`
3. `env_build`
4. `generate_effective_set`
5. `git_commit`

**Steps:**

1. A pipeline job runs.
2. EnvGene evaluates certificate sources in priority order.
3. No non-empty source is found.

**Results:**

1. Pipeline logs show that no system certificates were loaded.
2. The job completes successfully.

## Priority resolution

### UC-SC-PRI-1: Higher-priority source hides lower-priority sources

**Pre-requisites:**

1. `SSL_CERTIFICATES_BUNDLE` is set to a non-empty valid base64-encoded PEM value.
2. `/ca_bundle` or `/configuration/certs` also contains certificate files.

**Trigger:**

> [!NOTE]
> One of the following jobs runs in the instance pipeline (GitLab or GitHub):

1. `app_reg_def_process`
2. `process_sd`
3. `env_build`
4. `generate_effective_set`
5. `git_commit`

**Steps:**

1. A pipeline job runs.
2. EnvGene loads certificates from `SSL_CERTIFICATES_BUNDLE`.
3. Lower-priority sources are not evaluated.

**Results:**

1. Pipeline logs show `SSL_CERTIFICATES_BUNDLE` as the resolved certificate source.
2. Certificate data from lower-priority sources is not loaded.

## Validation failures

### UC-SC-VAL-1: Invalid base64-encoded bundle fails pipeline

**Pre-requisites:**

1. `SSL_CERTIFICATES_BUNDLE` is set to a non-empty value that is not valid base64 or does not decode to valid PEM content.

**Trigger:**

> [!NOTE]
> One of the following jobs runs in the instance pipeline (GitLab or GitHub):

1. `app_reg_def_process`
2. `process_sd`
3. `env_build`
4. `generate_effective_set`
5. `git_commit`

**Steps:**

1. A pipeline job runs.
2. EnvGene attempts to decode and load `SSL_CERTIFICATES_BUNDLE`.
3. Base64 decoding or PEM validation fails.
4. The job aborts with a certificate loading error.

**Results:**

1. The job fails with a non-zero exit status.
2. Pipeline log contains an explicit error for `SSL_CERTIFICATES_BUNDLE`.
3. Lower-priority sources are not used.

### UC-SC-VAL-2: Unreadable certificate file in folder fails pipeline

**Pre-requisites:**

1. `SSL_CERTIFICATES_BUNDLE` is unset or empty.
2. `Devops.CA_BUNDLE_CERTIFICATE` is unset or empty in the resolved Cloud Passport.
3. The selected folder source (`/ca_bundle` or `/configuration/certs`) contains at least one certificate file that
   cannot be read, for example due to restrictive file permissions.

**Trigger:**

> [!NOTE]
> One of the following jobs runs in the instance pipeline (GitLab or GitHub):

1. `app_reg_def_process`
2. `process_sd`
3. `env_build`
4. `generate_effective_set`
5. `git_commit`

**Steps:**

1. A pipeline job runs.
2. EnvGene resolves a folder source and attempts to load certificate files.
3. Reading a certificate file fails.
4. The job aborts with a certificate loading error.

**Results:**

1. The job fails with a non-zero exit status.
2. Pipeline log identifies the unreadable certificate file path.
3. Remaining certificate files in the folder are not loaded.

### UC-SC-VAL-3: Invalid certificate file in folder fails pipeline

**Pre-requisites:**

1. `SSL_CERTIFICATES_BUNDLE` is unset or empty.
2. `Devops.CA_BUNDLE_CERTIFICATE` is unset or empty in the resolved Cloud Passport.
3. The selected folder source (`/ca_bundle` or `/configuration/certs`) contains at least one `.crt` or `.pem` file that
   cannot be parsed as a valid certificate.

**Trigger:**

> [!NOTE]
> One of the following jobs runs in the instance pipeline (GitLab or GitHub):

1. `app_reg_def_process`
2. `process_sd`
3. `env_build`
4. `generate_effective_set`
5. `git_commit`

**Steps:**

1. A pipeline job runs.
2. EnvGene resolves a folder source and attempts to load certificate files.
3. Parsing a `.crt` or `.pem` file fails.
4. The job aborts with a certificate loading error.

**Results:**

1. The job fails with a non-zero exit status.
2. Pipeline log identifies the invalid certificate file path.
3. Remaining certificate files in the folder are not loaded.

## Artifactory access

### UC-SC-USG-1: Template download from Artifactory with system certificates

**Pre-requisites:**

1. Instance repository exists.
2. GitLab project has CI/CD variable `SSL_CERTIFICATES_BUNDLE` set to a valid base64-encoded PEM CA certificate for
   Artifactory.
3. Template artifact referenced by the pipeline parameter is available in Artifactory.

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

```yaml
ENV_NAMES: <env_name>
ENV_BUILDER: true
ENV_TEMPLATE_VERSION: <application>:<version>
```

**Steps:**

1. The `app_reg_def_process` job runs.
2. EnvGene loads certificates from `SSL_CERTIFICATES_BUNDLE`.
3. EnvGene resolves the template from `ENV_TEMPLATE_VERSION` and downloads the artifact from Artifactory over TLS.

**Results:**

1. Template artifact is downloaded from Artifactory successfully.
2. The job completes successfully.
