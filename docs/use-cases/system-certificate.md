# SSL Certificate Processing Use Cases

- [SSL Certificate Processing Use Cases](#ssl-certificate-processing-use-cases)
  - [Overview](#overview)
  - [Use Cases](#use-cases)
    - [UC-SC-NEX-1: Download template artifact from Nexus with custom CA certificate](#uc-sc-nex-1-download-template-artifact-from-nexus-with-custom-ca-certificate)
    - [UC-SC-NEX-2: Download template artifact from Nexus with client certificate authentication](#uc-sc-nex-2-download-template-artifact-from-nexus-with-client-certificate-authentication)
    - [UC-SC-ERR-1 (Negative): Reject connection with invalid or incomplete certificate chain](#uc-sc-err-1-negative-reject-connection-with-invalid-or-incomplete-certificate-chain)
    - [UC-SC-ERR-2 (Negative): Fail secure connection when required certificate is missing](#uc-sc-err-2-negative-fail-secure-connection-when-required-certificate-is-missing)
    - [UC-SC-ERR-3 (Negative): Continue GENERATE_EFFECTIVE_SET when default runtime certificate is unavailable](#uc-sc-err-3-negative-continue-generate_effective_set-when-default-runtime-certificate-is-unavailable)

## Overview

This document covers use cases for [System Certificate Configuration](/docs/features/system-certificate.md) focusing on secure endpoint access in instance pipelines.

EnvGene loads certificates from `configuration/certs/` and applies them during job execution for TLS trust and repository access.

These use cases describe certificate-driven flows for:

- Nexus template artifact download
- TLS error handling for invalid or missing certificates

## Use Cases

### UC-SC-NEX-1: Download template artifact from Nexus with custom CA certificate

**Pre-requisites:**

1. Template artifact is uploaded to Nexus and available for download.
2. Pipeline uses Registry Definition pointing to this Nexus endpoint for template artifact download.
3. Nexus endpoint uses certificate chain signed by private or internal CA.
4. Instance repository contains CA certificate chain file in `configuration/certs/`.

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with template artifact source configured to Nexus.

**Steps:**

1. Jobs run in the pipeline:

   1. Resolves template artifact source and Nexus endpoint from pipeline configuration.
   2. Loads CA certificates from `configuration/certs/` into runner trust.
   3. Connects to Nexus over TLS and downloads template artifact.

**Results:**

1. TLS connection to Nexus is established successfully.
2. Template artifact is downloaded successfully.
3. No `CERTIFICATE_VERIFY_FAILED` or trust errors appear in logs.

### UC-SC-NEX-2: Download template artifact from Nexus with client certificate authentication

**Pre-requisites:**

1. Nexus endpoint is configured to require client certificate authentication.
2. Pipeline is configured to download template artifact from Nexus.
3. Template artifact is uploaded to Nexus and available for download.
4. Instance repository contains CA certificate chain and client certificate files in `configuration/certs/`.

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with template artifact source configured to Nexus endpoint that requires client authentication.

**Steps:**

1. Jobs run in the pipeline:

   1. Loads CA and client certificate files from `configuration/certs/`.
   2. Resolves target Nexus endpoint and template coordinates.
   3. Authenticates with client certificate and downloads template artifact.

**Results:**

1. Client certificate is used for repository authentication.
2. Nexus access is authorized.
3. Template artifact is downloaded successfully.

### UC-SC-ERR-1 (Negative): Reject connection with invalid or incomplete certificate chain

**Pre-requisites:**

1. Target endpoint requires valid full certificate chain.
2. `configuration/certs/` contains invalid chain (wrong order, missing intermediate, or malformed PEM boundaries).
3. Control run with valid chain is available.

**Trigger:**

Instance pipeline (GitLab or GitHub) is started for secure endpoint access that requires full certificate chain.

**Steps:**

1. First run (negative dataset):
   1. Provide invalid chain file in `configuration/certs/`.
   2. Run pipeline and execute secure endpoint call.
   3. Capture TLS logs and job status.
2. Second run (control dataset):
   1. Replace invalid chain with valid chain.
   2. Run the same flow with unchanged settings.

**Results:**

1. Run with invalid chain fails TLS validation.
2. Logs contain certificate verification or chain validation error.
3. Control run with valid chain succeeds.

### UC-SC-ERR-2 (Negative): Fail secure connection when required certificate is missing

**Pre-requisites:**

1. Target repository or internal endpoint requires custom CA and/or client certificate.
2. Required file is not present in `configuration/certs/`.

**Trigger:**

Instance pipeline (GitLab or GitHub) is started for flow that must access protected endpoint.

**Steps:**

1. Start pipeline with required CA or client certificate file removed from `configuration/certs/`.
2. Execute the protected endpoint call in the same flow.
3. Capture failure logs and job status.

**Results:**

1. Secure connection or authentication fails in expected step.
2. Logs contain clear reason related to missing trust or missing client certificate.
3. Failure is diagnosable and reproducible.

### UC-SC-ERR-3 (Negative): Continue GENERATE_EFFECTIVE_SET when default runtime certificate is unavailable

**Pre-requisites:**

1. `GENERATE_EFFECTIVE_SET` is enabled in pipeline configuration.
2. Instance repository does not contain certificate files in `configuration/certs/`.
3. Runtime image does not provide default certificate file.

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with `GENERATE_EFFECTIVE_SET` enabled.

**Steps:**

1. Start pipeline with empty or missing `configuration/certs/`.
2. Run `GENERATE_EFFECTIVE_SET` flow in runtime without default certificate file.
3. Capture logs and job status.

**Results:**

1. `GENERATE_EFFECTIVE_SET` does not fail only because default runtime certificate is unavailable.
