# SSL Certificate Processing Use Cases

- [SSL Certificate Processing Use Cases](#ssl-certificate-processing-use-cases)
  - [Overview](#overview)
  - [Use Cases](#use-cases)
    - [UC-SC-NEX-1: Download template artifact from Nexus with custom CA certificate](#uc-sc-nex-1-download-template-artifact-from-nexus-with-custom-ca-certificate)


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