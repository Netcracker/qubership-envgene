# System Certificate Configuration Use Cases

- [System Certificate Configuration Use Cases](#system-certificate-configuration-use-cases)
  - [Overview](#overview)
  - [Certificate Loading and Fallback](#certificate-loading-and-fallback)
    - [UC-CERT-LF-1: Load certificates from `configuration/certs/`](#uc-cert-lf-1-load-certificates-from-configurationcerts)
    - [UC-CERT-LF-2: Fall back to `/default_cert.pem` when `configuration/certs/` is missing or empty](#uc-cert-lf-2-fall-back-to-default_certpem-when-configurationcerts-is-missing-or-empty)
  - [Java Truststore Import](#java-truststore-import)
    - [UC-CERT-JTS-1: Import repository certificates into Java truststore for Effective Set generation](#uc-cert-jts-1-import-repository-certificates-into-java-truststore-for-effective-set-generation)

## Overview

This document describes practical use cases for System Certificate Configuration in EnvGene instance pipelines. It focuses on how certificates from configuration/certs/ are applied during pipeline execution for secure connectivity.

## Certificate Loading and Fallback

This section covers how EnvGene loads certificates from the Instance repository at `configuration/certs/` and how it behaves when the directory is missing or empty.

### UC-CERT-LF-1: Load certificates from `configuration/certs/`

**Pre-requisites:**

1. Instance repository contains at least one certificate file under `/configuration/certs/`.
2. The pipeline is executed in a container/runner where the system CA trust store can be updated.

**Trigger:**

Instance pipeline (GitLab or GitHub) runs any job that executes certificate handling, for example `env_builder`, `process_sd`, or `generate_effective_set`.

**Steps:**

1. The job executes the certificate handling script.
2. The script checks `${CI_PROJECT_DIR}/configuration/certs` and finds one or more certificate files.
3. For each certificate file, the script:
   1. Copies it to the OS-specific CA trust location.
   2. Updates the system CA trust store.
   3. Sets `REQUESTS_CA_BUNDLE` to point to the system CA bundle file used by Python tools.

**Results:**

1. All certificate files from `/configuration/certs/` are imported into the runner trusted root store.
2. `REQUESTS_CA_BUNDLE` is set so Python-based tools use the updated CA store.

### UC-CERT-LF-2: Fall back to `/default_cert.pem` when `configuration/certs/` is missing or empty

**Pre-requisites:**

1. Instance repository does not contain any certificate files under `configuration/certs/` (the directory is missing or empty).
2. Default certificate file `/default_cert.pem` exists in the runner/container image.

**Trigger:**

Instance pipeline (GitLab or GitHub) runs a job that executes certificate handling.

**Steps:**

1. The job executes the certificate handling script.
2. The script detects that `${CI_PROJECT_DIR}/configuration/certs/` is missing or empty.
3. The script detects that `/default_cert.pem` exists and imports it into the system CA trust store.
4. The script sets `REQUESTS_CA_BUNDLE` to point to the system CA bundle file.

**Results:**

1. The runner trusted root store is updated using `/default_cert.pem`.
2. `REQUESTS_CA_BUNDLE` is set so Python-based tools use the updated CA store.

## Java Truststore Import

This section covers the Java truststore import that is performed for jobs that run Java-based tools (for example, Effective Set generator / Calculator CLI).

### UC-CERT-JTS-1: Import repository certificates into Java truststore for Effective Set generation

**Pre-requisites:**

1. Instance repository contains at least one certificate file under `/configuration/certs/`.
2. Instance pipeline is started with Effective Set generation enabled (`GENERATE_EFFECTIVE_SET: true`).

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `ENV_NAMES: <env_name>`
2. `GENERATE_EFFECTIVE_SET: true`

**Steps:**

1. The `generate_effective_set` job runs in the pipeline:
   1. Ensures `${CI_PROJECT_DIR}/configuration/certs/` exists and copies `/default_cert.pem` there if it exists in the job container.
   2. Iterates certificate files in `${CI_PROJECT_DIR}/configuration/certs/` and imports each into the Java truststore using `keytool`.
   3. Executes the Java-based Effective Set generator (Calculator CLI) after the truststore import completes.

**Results:**

1. Java truststore contains all certificates from `${CI_PROJECT_DIR}/configuration/certs/` that were present at job start (including `default_cert.pem` if it was copied).
2. Java-based tools executed by the job (Effective Set generator) can establish TLS connections to systems that require these certificates.

