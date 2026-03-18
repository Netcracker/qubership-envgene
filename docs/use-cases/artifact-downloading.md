# Artifact Downloading Use Cases

- [Artifact Downloading Use Cases](#artifact-downloading-use-cases)
  - [Overview](#overview)
  - [Supported Configurations](#supported-configurations)
    - [Valid Configuration Combinations for SD/DD Artifacts](#valid-configuration-combinations-for-sddd-artifacts)
    - [Valid Configuration Combinations for Environment Template Artifacts](#valid-configuration-combinations-for-environment-template-artifacts)
  - [SD/DD Artifact Download](#sddd-artifact-download)
    - [UC-AD-SD-1: Download SD from Artifactory with User/Password (AppDef v1 + RegDef v1)](#uc-ad-sd-1-download-sd-from-artifactory-with-userpassword-appdef-v1--regdef-v1)
    - [UC-AD-SD-2: Download SD from Artifactory with Anonymous Access (AppDef v1 + RegDef v1)](#uc-ad-sd-2-download-sd-from-artifactory-with-anonymous-access-appdef-v1--regdef-v1)
    - [UC-AD-SD-3: Download SD from Nexus with User/Password (AppDef v1 + RegDef v1)](#uc-ad-sd-3-download-sd-from-nexus-with-userpassword-appdef-v1--regdef-v1)
    - [UC-AD-SD-4: Download SD from Nexus with Anonymous Access (AppDef v1 + RegDef v1)](#uc-ad-sd-4-download-sd-from-nexus-with-anonymous-access-appdef-v1--regdef-v1)
    - [UC-AD-SD-5: Download SD from Artifactory with User/Password (AppDef v1 + RegDef v2)](#uc-ad-sd-5-download-sd-from-artifactory-with-userpassword-appdef-v1--regdef-v2)
    - [UC-AD-SD-6: Download SD from Artifactory with Anonymous Access (AppDef v1 + RegDef v2)](#uc-ad-sd-6-download-sd-from-artifactory-with-anonymous-access-appdef-v1--regdef-v2)
    - [UC-AD-SD-7: Download SD from Nexus with User/Password (AppDef v1 + RegDef v2)](#uc-ad-sd-7-download-sd-from-nexus-with-userpassword-appdef-v1--regdef-v2)
    - [UC-AD-SD-8: Download SD from Nexus with Anonymous Access (AppDef v1 + RegDef v2)](#uc-ad-sd-8-download-sd-from-nexus-with-anonymous-access-appdef-v1--regdef-v2)
    - [UC-AD-SD-9: Download SD from AWS CodeArtifact with Secret (AppDef v1 + RegDef v2)](#uc-ad-sd-9-download-sd-from-aws-codeartifact-with-secret-appdef-v1--regdef-v2)
    - [UC-AD-SD-10: Download SD from GCP Artifact Registry with Service Account (AppDef v1 + RegDef v2)](#uc-ad-sd-10-download-sd-from-gcp-artifact-registry-with-service-account-appdef-v1--regdef-v2)
    - [UC-AD-SD-11: Download Specific Version SD](#uc-ad-sd-11-download-specific-version-sd)
  - [Environment Template Artifact Download](#environment-template-artifact-download)
    - [UC-AD-ENV-9: Download Template from Artifactory with GAV notation](#uc-ad-env-9-download-template-from-artifactory-with-gav-notation)
    - [UC-AD-ENV-10: Download Template from Artifactory with GAV notation and Anonymous Access](#uc-ad-env-10-download-template-from-artifactory-with-gav-notation-and-anonymous-access)
    - [UC-AD-ENV-11: Download Template from Nexus with GAV notation](#uc-ad-env-11-download-template-from-nexus-with-gav-notation)
    - [UC-AD-ENV-12: Download Template from Nexus with GAV notation and Anonymous Access](#uc-ad-env-12-download-template-from-nexus-with-gav-notation-and-anonymous-access)
    - [UC-AD-ENV-13: Download Template with app ver notation from Artifactory (ArtDef v1)](#uc-ad-env-13-download-template-with-app-ver-notation-from-artifactory-artdef-v1)
    - [UC-AD-ENV-14: Download Template with app ver notation from Artifactory and Anonymous Access (ArtDef v1)](#uc-ad-env-14-download-template-with-app-ver-notation-from-artifactory-and-anonymous-access-artdef-v1)
    - [UC-AD-ENV-15: Download Template with app ver notation from Nexus (ArtDef v1)](#uc-ad-env-15-download-template-with-app-ver-notation-from-nexus-artdef-v1)
    - [UC-AD-ENV-16: Download Template with app ver notation from Nexus and Anonymous Access (ArtDef v1)](#uc-ad-env-16-download-template-with-app-ver-notation-from-nexus-and-anonymous-access-artdef-v1)
    - [UC-AD-ENV-17: Download Template from Artifactory with app ver notation (ArtDef v2)](#uc-ad-env-17-download-template-from-artifactory-with-app-ver-notation-artdef-v2)
    - [UC-AD-ENV-18: Download Template from Artifactory with app ver notation and Anonymous Access (ArtDef v2)](#uc-ad-env-18-download-template-from-artifactory-with-app-ver-notation-and-anonymous-access-artdef-v2)
    - [UC-AD-ENV-19: Download Template from Nexus with app ver notation (ArtDef v2)](#uc-ad-env-19-download-template-from-nexus-with-app-ver-notation-artdef-v2)
    - [UC-AD-ENV-20: Download Template from Nexus with app ver notation and Anonymous Access (ArtDef v2)](#uc-ad-env-20-download-template-from-nexus-with-app-ver-notation-and-anonymous-access-artdef-v2)
    - [UC-AD-ENV-21: Download Template from AWS CodeArtifact with app ver notation (ArtDef v2)](#uc-ad-env-21-download-template-from-aws-codeartifact-with-app-ver-notation-artdef-v2)
    - [UC-AD-ENV-22: Download Template from GCP Artifact Registry with app ver notation (ArtDef v2)](#uc-ad-env-22-download-template-from-gcp-artifact-registry-with-app-ver-notation-artdef-v2)
    - [UC-AD-ENV-23: Download SNAPSHOT Template Version](#uc-ad-env-23-download-snapshot-template-version)
    - [UC-AD-ENV-24: Download Specific Template Version](#uc-ad-env-24-download-specific-template-version)
  - [Error Handling](#error-handling)
    - [UC-AD-ERR-1: Handle Missing Application Definition](#uc-ad-err-1-handle-missing-application-definition)
    - [UC-AD-ERR-2: Handle Missing Registry Definition](#uc-ad-err-2-handle-missing-registry-definition)
    - [UC-AD-ERR-3: Handle Authentication Failure](#uc-ad-err-3-handle-authentication-failure)
    - [UC-AD-ERR-4: Handle Missing Artifact Definition](#uc-ad-err-4-handle-missing-artifact-definition)
  - [Configuration Examples](#configuration-examples)
    - [Registry Definition Examples](#registry-definition-examples)
      - [Artifactory / Nexus (RegDef v1.0)](#artifactory--nexus-regdef-v10)
      - [Artifactory (RegDef v2.0)](#artifactory-regdef-v20)
      - [Nexus (RegDef v2.0)](#nexus-regdef-v20)
      - [AWS CodeArtifact (RegDef v2.0)](#aws-codeartifact-regdef-v20)
      - [GCP Artifact Registry (RegDef v2.0)](#gcp-artifact-registry-regdef-v20)
    - [Artifact Definition Examples](#artifact-definition-examples)
      - [Artifact Definition v1.0](#artifact-definition-v10)
      - [Artifact Definition v2.0](#artifact-definition-v20)
    - [Credentials Configuration Examples](#credentials-configuration-examples)
      - [User/Password Authentication](#userpassword-authentication)
      - [AWS Secret Authentication](#aws-secret-authentication)
      - [GCP Service Account Authentication](#gcp-service-account-authentication)
    - [Environment Inventory Examples](#environment-inventory-examples)
      - [Template with GAV notation](#template-with-gav-notation)
      - [Template with app ver notation](#template-with-app-ver-notation)

## Overview

EnvGene downloads three types of artifacts:

1. **SD (Solution Descriptor)** - processed in `sd_processing` and `effective_set_generation`
2. **DD (Deployment Descriptor)** - processed in `effective_set_generation`
3. **Environment Template** - processed in `app_reg_def_process`

All artifacts are Maven artifacts and can be stored in various registry types with different authentication methods.

> [!TIP]
> Complete configuration examples (Registry Definitions, Application Definitions, Artifact Definitions) are available in the [Configuration Examples](#configuration-examples) section at the end of this document.

## Supported Configurations

This section provides a quick reference for valid configuration combinations across all supported registry types.

### Valid Configuration Combinations for SD/DD Artifacts

| Registry Type        | AppDef Version | RegDef Version | Auth Method      | Supported  | SNAPSHOT  | Notes                                                      |
|----------------------|----------------|----------------|------------------|------------|-----------|------------------------------------------------------------|
| Artifactory          | v1.0           | v1.0           | user_pass        | ✅ Yes     | ❌ No     | Legacy, maintained indefinitely                            |
| Artifactory          | v1.0           | v1.0           | anonymous        | ✅ Yes     | ❌ No     | Legacy, maintained indefinitely                            |
| Artifactory          | v1.0           | v2.0           | user_pass        | ✅ Yes     | ❌ No     | Recommended for new implementations                        |
| Artifactory          | v1.0           | v2.0           | anonymous        | ✅ Yes     | ❌ No     | Recommended for new implementations                        |
| Nexus                | v1.0           | v1.0           | user_pass        | ✅ Yes     | ❌ No     | Legacy, maintained indefinitely                            |
| Nexus                | v1.0           | v1.0           | anonymous        | ✅ Yes     | ❌ No     | Legacy, maintained indefinitely                            |
| Nexus                | v1.0           | v2.0           | user_pass        | ✅ Yes     | ❌ No     | Recommended for new implementations                        |
| Nexus                | v1.0           | v2.0           | anonymous        | ✅ Yes     | ❌ No     | Recommended for new implementations                        |
| AWS CodeArtifact     | v1.0           | v1.0           | any              | ❌ No      | ❌ No     | v1.0 RegDef cannot support AWS auth                        |
| AWS CodeArtifact     | v1.0           | v2.0           | secret           | ✅ Yes     | ❌ No     | Required for AWS. Only secret supported.                   |
| AWS CodeArtifact     | v1.0           | v2.0           | anonymous        | ❌ No      | ❌ No     | Anonymous access not supported for public cloud registries |
| AWS CodeArtifact     | v1.0           | v2.0           | assume_role      | ❌ No      | ❌ No     | Not supported                                              |
| GCP GAR              | v1.0           | v1.0           | any              | ❌ No      | ❌ No     | v1.0 RegDef cannot support GCP auth                        |
| GCP GAR              | v1.0           | v2.0           | service_account  | ✅ Yes     | ❌ No     | Required for GCP. Only service_account supported.          |
| GCP GAR              | v1.0           | v2.0           | anonymous        | ❌ No      | ❌ No     | Anonymous access not supported for public cloud registries |
| GCP GAR              | v1.0           | v2.0           | federation       | ❌ No      | ❌ No     | Not supported                                              |
| Azure Artifacts      | any            | any            | oauth2           | ❌ No      | ❌ No     | Azure not supported                                        |

### Valid Configuration Combinations for Environment Template Artifacts

| Registry Type        | Notation | ArtDef Version | Auth Method      | Supported  | SNAPSHOT  | Notes                                                      |
|----------------------|----------|----------------|------------------|------------|-----------|------------------------------------------------------------|
| Artifactory          | GAV      | N/A (Legacy)   | user_pass        | ✅ Yes     | ✅ Yes    | Legacy logic, does NOT use Artifact Definitions            |
| Artifactory          | GAV      | N/A (Legacy)   | anonymous        | ✅ Yes     | ✅ Yes    | Legacy logic, does NOT use Artifact Definitions            |
| Artifactory          | app:ver  | v1.0           | user_pass        | ✅ Yes     | ✅ Yes    | Legacy, maintained indefinitely                            |
| Artifactory          | app:ver  | v1.0           | anonymous        | ✅ Yes     | ✅ Yes    | Legacy, maintained indefinitely                            |
| Artifactory          | app:ver  | v2.0           | user_pass        | ✅ Yes     | ✅ Yes    | Recommended for new implementations                        |
| Artifactory          | app:ver  | v2.0           | anonymous        | ✅ Yes     | ✅ Yes    | Recommended for new implementations                        |
| Nexus                | GAV      | N/A (Legacy)   | user_pass        | ✅ Yes     | ✅ Yes    | Legacy logic, does NOT use Artifact Definitions            |
| Nexus                | GAV      | N/A (Legacy)   | anonymous        | ✅ Yes     | ✅ Yes    | Legacy logic, does NOT use Artifact Definitions            |
| Nexus                | app:ver  | v1.0           | user_pass        | ✅ Yes     | ✅ Yes    | Legacy, maintained indefinitely                            |
| Nexus                | app:ver  | v1.0           | anonymous        | ✅ Yes     | ✅ Yes    | Legacy, maintained indefinitely                            |
| Nexus                | app:ver  | v2.0           | user_pass        | ✅ Yes     | ✅ Yes    | Recommended for new implementations                        |
| Nexus                | app:ver  | v2.0           | anonymous        | ✅ Yes     | ✅ Yes    | Recommended for new implementations                        |
| AWS CodeArtifact     | GAV      | N/A            | any              | ❌ No      | ❌ No     | GAV notation limited to Artifactory/Nexus                  |
| AWS CodeArtifact     | app:ver  | v1.0           | any              | ❌ No      | ❌ No     | v1.0 cannot support AWS auth                               |
| AWS CodeArtifact     | app:ver  | v2.0           | secret           | ✅ Yes     | ✅ Yes    | Required for AWS. Only secret supported.                   |
| AWS CodeArtifact     | app:ver  | v2.0           | anonymous        | ❌ No      | ❌ No     | Anonymous access not supported for public cloud registries |
| AWS CodeArtifact     | app:ver  | v2.0           | assume_role      | ❌ No      | ❌ No     | Not supported                                              |
| GCP GAR              | GAV      | N/A            | any              | ❌ No      | ❌ No     | GAV notation limited to Artifactory/Nexus                  |
| GCP GAR              | app:ver  | v1.0           | any              | ❌ No      | ❌ No     | v1.0 cannot support GCP auth                               |
| GCP GAR              | app:ver  | v2.0           | service_account  | ✅ Yes     | ✅ Yes    | Required for GCP. Only service_account supported.          |
| GCP GAR              | app:ver  | v2.0           | anonymous        | ❌ No      | ❌ No     | Anonymous access not supported for public cloud registries |
| GCP GAR              | app:ver  | v2.0           | federation       | ❌ No      | ❌ No     | Not supported                                              |
| Azure Artifacts      | any      | any            | oauth2           | ❌ No      | ❌ No     | Azure not supported                                        |

## SD/DD Artifact Download

This group covers use cases for downloading Solution Descriptors (SD) and Deployment Descriptors (DD) from various registries. DD artifacts follow the same patterns as SD artifacts.

### UC-AD-SD-1: Download SD from Artifactory with User/Password (AppDef v1 + RegDef v1)

**Pre-requisites:**

1. Application Definition v1.0 exists for SD application
2. Registry Definition v1.0 exists with Artifactory configuration
   (See [Artifactory / Nexus RegDef v1.0 example](#artifactory--nexus-regdef-v10))
3. Credentials stored in `/configuration/credentials/credentials.yml`
   (See [User/Password authentication example](#userpassword-authentication))

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `ENV_NAMES: <env_name>`
2. `SD_SOURCE_TYPE: artifact`
3. `SD_VERSION: <application:version>`

**Steps:**

1. The `process_sd` job runs in the pipeline:
   1. Parses `SD_VERSION` parameter (format: `application:version`)
   2. Resolves application name to Application Definition v1.0
   3. Extracts `registryName` from AppDef
   4. Resolves registry to Registry Definition v1.0
   5. Extracts Maven coordinates and Artifactory URL
   6. Authenticates using username/password from credentials
   7. Downloads SD artifact from Artifactory

**Results:**

1. SD artifact is downloaded successfully
2. Artifact is available for SD processing in subsequent pipeline jobs

### UC-AD-SD-2: Download SD from Artifactory with Anonymous Access (AppDef v1 + RegDef v1)

**Pre-requisites:**

1. Application Definition v1.0 exists for SD application
2. Registry Definition v1.0 exists with Artifactory configuration
3. Registry Definition **does NOT have** `credentialsId` configured (anonymous access)
4. Artifactory registry allows anonymous/public access

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `ENV_NAMES: <env_name>`
2. `SD_SOURCE_TYPE: artifact`
3. `SD_VERSION: <application:version>`

**Steps:**

1. The `process_sd` job runs in the pipeline:
   1. Parses `SD_VERSION` parameter (format: `application:version`)
   2. Resolves application name to Application Definition v1.0
   3. Extracts `registryName` from AppDef
   4. Resolves registry to Registry Definition v1.0
   5. Extracts Maven coordinates and Artifactory URL
   6. Downloads SD artifact from Artifactory without authentication

**Results:**

1. SD artifact is downloaded successfully without authentication
2. Artifact is available for SD processing in subsequent pipeline jobs

### UC-AD-SD-3: Download SD from Nexus with User/Password (AppDef v1 + RegDef v1)

**Pre-requisites:**

1. Application Definition v1.0 exists for SD application
2. Registry Definition v1.0 exists with Nexus configuration
3. Credentials stored in `/configuration/credentials/credentials.yml`

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `ENV_NAMES: <env_name>`
2. `SD_SOURCE_TYPE: artifact`
3. `SD_VERSION: <application:version>`

**Steps:**

1. The `process_sd` job runs in the pipeline:
   1. Parses `SD_VERSION` parameter (format: `application:version`)
   2. Resolves application name to Application Definition v1.0
   3. Extracts `registryName` from AppDef
   4. Resolves registry to Registry Definition v1.0
   5. Extracts Maven coordinates and Nexus URL
   6. Authenticates using username/password from credentials
   7. Downloads SD artifact from Nexus

**Results:**

1. SD artifact is downloaded successfully
2. Artifact is available for SD processing in subsequent pipeline jobs

### UC-AD-SD-4: Download SD from Nexus with Anonymous Access (AppDef v1 + RegDef v1)

**Pre-requisites:**

1. Application Definition v1.0 exists for SD application
2. Registry Definition v1.0 exists with Nexus configuration
3. Registry Definition **does NOT have** `credentialsId` configured (anonymous access)
4. Nexus registry allows anonymous/public access

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `ENV_NAMES: <env_name>`
2. `SD_SOURCE_TYPE: artifact`
3. `SD_VERSION: <application:version>`

**Steps:**

1. The `process_sd` job runs in the pipeline:
   1. Parses `SD_VERSION` parameter (format: `application:version`)
   2. Resolves application name to Application Definition v1.0
   3. Extracts `registryName` from AppDef
   4. Resolves registry to Registry Definition v1.0
   5. Extracts Maven coordinates and Nexus URL
   6. Downloads SD artifact from Nexus without authentication

**Results:**

1. SD artifact is downloaded successfully without authentication
2. Artifact is available for SD processing in subsequent pipeline jobs

### UC-AD-SD-5: Download SD from Artifactory with User/Password (AppDef v1 + RegDef v2)

**Pre-requisites:**

1. Application Definition v1.0 exists for SD application
2. Registry Definition v2.0 exists with `authConfig` section
   (See [Artifactory RegDef v2.0 example](#artifactory-regdef-v20))
3. Credentials stored in `/configuration/credentials/credentials.yml`
   (See [User/Password authentication example](#userpassword-authentication))

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `ENV_NAMES: <env_name>`
2. `SD_SOURCE_TYPE: artifact`
3. `SD_VERSION: <application:version>`

**Steps:**

1. The `process_sd` job runs in the pipeline:
   1. Parses `SD_VERSION` parameter (format: `application:version`)
   2. Resolves application name to Application Definition v1.0
   3. Resolves registry to Registry Definition v2.0
   4. Extracts `mavenConfig.authConfig` reference
   5. Resolves to specific `authConfig` block with `authMethod: user_pass`
   6. Authenticates using username/password from credentials
   7. Downloads SD artifact from Artifactory

**Results:**

1. SD artifact is downloaded successfully using RegDef v2.0 enhanced authentication
2. Artifact is available for SD processing in subsequent pipeline jobs

### UC-AD-SD-6: Download SD from Artifactory with Anonymous Access (AppDef v1 + RegDef v2)

**Pre-requisites:**

1. Application Definition v1.0 exists for SD application
2. Registry Definition v2.0 exists with Artifactory configuration
3. Registry Definition **does NOT have** `authConfig` section configured (anonymous access)
4. Artifactory registry allows anonymous/public access

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `ENV_NAMES: <env_name>`
2. `SD_SOURCE_TYPE: artifact`
3. `SD_VERSION: <application:version>`

**Steps:**

1. The `process_sd` job runs in the pipeline:
   1. Parses `SD_VERSION` parameter (format: `application:version`)
   2. Resolves application name to Application Definition v1.0
   3. Resolves registry to Registry Definition v2.0
   4. Extracts `mavenConfig` (without authConfig reference)
   5. Downloads SD artifact from Artifactory without authentication

**Results:**

1. SD artifact is downloaded successfully without authentication using RegDef v2.0
2. Artifact is available for SD processing in subsequent pipeline jobs

### UC-AD-SD-7: Download SD from Nexus with User/Password (AppDef v1 + RegDef v2)

**Pre-requisites:**

1. Application Definition v1.0 exists for SD application
2. Registry Definition v2.0 exists with `authConfig` section for Nexus
3. Credentials stored in `/configuration/credentials/credentials.yml`

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `ENV_NAMES: <env_name>`
2. `SD_SOURCE_TYPE: artifact`
3. `SD_VERSION: <application:version>`

**Steps:**

1. The `process_sd` job runs in the pipeline:
   1. Parses `SD_VERSION` parameter (format: `application:version`)
   2. Resolves application name to Application Definition v1.0
   3. Resolves registry to Registry Definition v2.0
   4. Extracts `mavenConfig.authConfig` reference
   5. Resolves to specific `authConfig` block with `authMethod: user_pass`
   6. Authenticates using username/password from credentials
   7. Downloads SD artifact from Nexus

**Results:**

1. SD artifact is downloaded successfully using RegDef v2.0 enhanced authentication
2. Artifact is available for SD processing in subsequent pipeline jobs

### UC-AD-SD-8: Download SD from Nexus with Anonymous Access (AppDef v1 + RegDef v2)

**Pre-requisites:**

1. Application Definition v1.0 exists for SD application
2. Registry Definition v2.0 exists with Nexus configuration
3. Registry Definition **does NOT have** `authConfig` section configured (anonymous access)
4. Nexus registry allows anonymous/public access

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `ENV_NAMES: <env_name>`
2. `SD_SOURCE_TYPE: artifact`
3. `SD_VERSION: <application:version>`

**Steps:**

1. The `process_sd` job runs in the pipeline:
   1. Parses `SD_VERSION` parameter (format: `application:version`)
   2. Resolves application name to Application Definition v1.0
   3. Resolves registry to Registry Definition v2.0
   4. Extracts `mavenConfig` (without authConfig reference)
   5. Downloads SD artifact from Nexus without authentication

**Results:**

1. SD artifact is downloaded successfully without authentication using RegDef v2.0
2. Artifact is available for SD processing in subsequent pipeline jobs

### UC-AD-SD-9: Download SD from AWS CodeArtifact with Secret (AppDef v1 + RegDef v2)

**Pre-requisites:**

1. Application Definition v1.0 exists for SD application
2. Registry Definition v2.0 exists with `provider: aws` and `authMethod: secret`
   (See [AWS CodeArtifact RegDef v2.0 example](#aws-codeartifact-regdef-v20))
3. AWS access key and secret stored in credentials
   (See [AWS Secret authentication example](#aws-secret-authentication))

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `ENV_NAMES: <env_name>`
2. `SD_SOURCE_TYPE: artifact`
3. `SD_VERSION: <application:version>`

**Steps:**

1. The `process_sd` job runs in the pipeline:
   1. Parses `SD_VERSION` parameter (format: `application:version`)
   2. Resolves application name to Application Definition v1.0
   3. Resolves registry to Registry Definition v2.0
   4. Extracts AWS configuration (`awsRegion`, `awsDomain`)
   5. Authenticates using AWS access key/secret from credentials
   6. Gets temporary CodeArtifact token
   7. Downloads SD Maven artifact from AWS CodeArtifact

**Results:**

1. SD artifact is downloaded successfully from AWS CodeArtifact
2. Artifact is available for SD processing in subsequent pipeline jobs

### UC-AD-SD-10: Download SD from GCP Artifact Registry with Service Account (AppDef v1 + RegDef v2)

**Pre-requisites:**

1. Application Definition v1.0 exists for SD application
2. Registry Definition v2.0 exists with `provider: gcp` and `authMethod: service_account`
   (See [GCP Artifact Registry RegDef v2.0 example](#gcp-artifact-registry-regdef-v20))
3. Service account JSON key stored as credential
   (See [GCP Service Account authentication example](#gcp-service-account-authentication))

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `ENV_NAMES: <env_name>`
2. `SD_SOURCE_TYPE: artifact`
3. `SD_VERSION: <application:version>`

**Steps:**

1. The `process_sd` job runs in the pipeline:
   1. Parses `SD_VERSION` parameter (format: `application:version`)
   2. Resolves application name to Application Definition v1.0
   3. Resolves registry to Registry Definition v2.0
   4. Extracts GCP configuration (`gcpProject`, `gcpRegion`)
   5. Loads service account JSON key from credentials
   6. Authenticates to GCP using service account
   7. Downloads SD Maven artifact from GCP Artifact Registry

**Results:**

1. SD artifact is downloaded successfully from GCP Artifact Registry
2. Artifact is available for SD processing in subsequent pipeline jobs

### UC-AD-SD-11: Download Specific Version SD

**Pre-requisites:**

1. `SD_VERSION` parameter specifies exact version (e.g., `solution:1.2.3`)
2. Application Definition and Registry Definition are configured

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `ENV_NAMES: <env_name>`
2. `SD_SOURCE_TYPE: artifact`
3. `SD_VERSION: <application:version>` (specific version, NOT SNAPSHOT)

**Steps:**

1. The `process_sd` job runs in the pipeline:
   1. Parses specific version from `SD_VERSION` parameter
   2. Downloads exact version from configured registry

**Results:**

1. Specific SD artifact version is downloaded successfully
2. Artifact is available for SD processing in subsequent pipeline jobs

## Environment Template Artifact Download

This group covers use cases for downloading Environment Template artifacts from various registries using GAV notation or app:ver notation.

### UC-AD-ENV-9: Download Template from Artifactory with GAV notation

**Pre-requisites:**

1. Environment Inventory exists and specifies template with GAV notation:

   ```yaml
   templateArtifact:
     registry: "sandbox"
     artifact:
       group_id: "org.qubership"
       artifact_id: "env-template"
       version: "1.2.3"
   ```

2. `registry.yml` exists with Artifactory configuration
   (See [Artifactory / Nexus RegDef v1.0 example](#artifactory--nexus-regdef-v10))
3. Credentials configured for Artifactory
   (See [User/Password authentication example](#userpassword-authentication))

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `ENV_NAMES: <env_name>`
2. `ENV_BUILDER: true`

**Steps:**

1. The `app_reg_def_process` job runs in the pipeline:
   1. Reads Environment Inventory from `/environments/<cluster>/<env>/Inventory/env_definition.yml`
   2. Parses GAV coordinates from `templateArtifact` section
   3. Resolves registry from `registry.yml`
   4. Authenticates using credentials
   5. Downloads template artifact from Artifactory using Maven coordinates

**Results:**

1. Template artifact is downloaded successfully
2. Template is available for Environment Instance generation

### UC-AD-ENV-10: Download Template from Artifactory with GAV notation and Anonymous Access

**Pre-requisites:**

1. Environment Inventory exists and specifies template with GAV notation:

   ```yaml
   templateArtifact:
     registry: "sandbox"
     artifact:
       group_id: "org.qubership"
       artifact_id: "env-template"
       version: "1.2.3"
   ```

2. `registry.yml` exists with Artifactory configuration
3. `registry.yml` **does NOT have** `credentialsId` configured (anonymous access)
4. Artifactory registry allows anonymous/public access

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `ENV_NAMES: <env_name>`
2. `ENV_BUILDER: true`

**Steps:**

1. The `app_reg_def_process` job runs in the pipeline:
   1. Reads Environment Inventory
   2. Parses GAV coordinates from `templateArtifact` section
   3. Resolves registry from `registry.yml`
   4. Downloads template artifact from Artifactory without authentication

**Results:**

1. Template artifact is downloaded successfully without authentication
2. Template is available for Environment Instance generation

### UC-AD-ENV-11: Download Template from Nexus with GAV notation

**Pre-requisites:**

1. Environment Inventory exists and specifies template with GAV notation (similar to UC-AD-ENV-9, but with Nexus registry)
2. `registry.yml` exists with Nexus configuration
3. Credentials configured for Nexus

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `ENV_NAMES: <env_name>`
2. `ENV_BUILDER: true`

**Steps:**

1. The `app_reg_def_process` job runs in the pipeline:
   1. Reads Environment Inventory
   2. Parses GAV coordinates from `templateArtifact` section
   3. Resolves registry from `registry.yml`
   4. Authenticates using credentials
   5. Downloads template artifact from Nexus

**Results:**

1. Template artifact is downloaded successfully
2. Template is available for Environment Instance generation

### UC-AD-ENV-12: Download Template from Nexus with GAV notation and Anonymous Access

**Pre-requisites:**

1. Environment Inventory exists and specifies template with GAV notation (similar to UC-AD-ENV-9)
2. `registry.yml` exists with Nexus configuration
3. `registry.yml` **does NOT have** `credentialsId` configured (anonymous access)
4. Nexus registry allows anonymous/public access

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `ENV_NAMES: <env_name>`
2. `ENV_BUILDER: true`

**Steps:**

1. The `app_reg_def_process` job runs in the pipeline:
   1. Reads Environment Inventory
   2. Parses GAV coordinates from `templateArtifact` section
   3. Resolves registry from `registry.yml`
   4. Downloads template artifact from Nexus without authentication

**Results:**

1. Template artifact is downloaded successfully without authentication
2. Template is available for Environment Instance generation

### UC-AD-ENV-13: Download Template with app ver notation from Artifactory (ArtDef v1)

**Pre-requisites:**

1. Environment Inventory exists and specifies template with `application:version` notation:

   ```yaml
   envTemplate:
     artifact: "env-template:1.2.3"
   ```

2. Artifact Definition v1.0 exists at `/configuration/artifact_definitions/env-template.yaml`
3. Registry configuration in Artifact Definition points to Artifactory
4. Credentials configured

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `ENV_NAMES: <env_name>`
2. `ENV_BUILDER: true`

**Steps:**

1. The `app_reg_def_process` job runs in the pipeline:
   1. Reads Environment Inventory
   2. Parses `application:version` from `envTemplate.artifact`
   3. Resolves to Artifact Definition v1.0
   4. Extracts Maven GAV coordinates and registry information
   5. Authenticates using credentials
   6. Downloads template artifact from Artifactory

**Results:**

1. Template artifact is downloaded successfully using ArtDef v1.0
2. Template is available for Environment Instance generation

### UC-AD-ENV-14: Download Template with app ver notation from Artifactory and Anonymous Access (ArtDef v1)

**Pre-requisites:**

1. Environment Inventory exists and specifies template with `application:version` notation:

   ```yaml
   envTemplate:
     artifact: "env-template:1.2.3"
   ```

2. Artifact Definition v1.0 exists at `/configuration/artifact_definitions/env-template.yaml`
3. Registry configuration in Artifact Definition **does NOT have** `credentialsId` (anonymous access)
4. Artifactory registry allows anonymous/public access

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `ENV_NAMES: <env_name>`
2. `ENV_BUILDER: true`

**Steps:**

1. The `app_reg_def_process` job runs in the pipeline:
   1. Reads Environment Inventory
   2. Parses `application:version` from `envTemplate.artifact`
   3. Resolves to Artifact Definition v1.0
   4. Extracts Maven GAV coordinates and registry information
   5. Downloads template artifact from Artifactory without authentication

**Results:**

1. Template artifact is downloaded successfully without authentication using ArtDef v1.0
2. Template is available for Environment Instance generation

### UC-AD-ENV-15: Download Template with app ver notation from Nexus (ArtDef v1)

**Pre-requisites:**

1. Environment Inventory exists and specifies template with `application:version` notation:

   ```yaml
   envTemplate:
     artifact: "env-template:1.2.3"
   ```

2. Artifact Definition v1.0 exists at `/configuration/artifact_definitions/env-template.yaml`
   (See [Artifact Definition v1.0 example](#artifact-definition-v10))
3. Registry configuration in Artifact Definition points to Nexus
   (See [Artifactory / Nexus RegDef v1.0 example](#artifactory--nexus-regdef-v10))
4. Credentials configured
   (See [User/Password authentication example](#userpassword-authentication))

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `ENV_NAMES: <env_name>`
2. `ENV_BUILDER: true`

**Steps:**

1. The `app_reg_def_process` job runs in the pipeline:
   1. Reads Environment Inventory
   2. Parses `application:version` from `envTemplate.artifact`
   3. Resolves to Artifact Definition v1.0
   4. Extracts Maven GAV coordinates and registry information
   5. Authenticates using credentials
   6. Downloads template artifact from Nexus

**Results:**

1. Template artifact is downloaded successfully using ArtDef v1.0
2. Template is available for Environment Instance generation

### UC-AD-ENV-16: Download Template with app ver notation from Nexus and Anonymous Access (ArtDef v1)

**Pre-requisites:**

1. Environment Inventory exists and specifies template with `application:version` notation (similar to UC-AD-ENV-15)
2. Artifact Definition v1.0 exists with Nexus registry configuration
3. Registry configuration **does NOT have** `credentialsId` (anonymous access)
4. Nexus registry allows anonymous/public access

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `ENV_NAMES: <env_name>`
2. `ENV_BUILDER: true`

**Steps:**

1. The `app_reg_def_process` job runs in the pipeline:
   1. Reads Environment Inventory
   2. Parses `application:version` from `envTemplate.artifact`
   3. Resolves to Artifact Definition v1.0
   4. Extracts Maven GAV coordinates and registry information
   5. Downloads template artifact from Nexus without authentication

**Results:**

1. Template artifact is downloaded successfully without authentication using ArtDef v1.0
2. Template is available for Environment Instance generation

### UC-AD-ENV-17: Download Template from Artifactory with app ver notation (ArtDef v2)

**Pre-requisites:**

1. Environment Inventory specifies template with `application:version` format
   (See [Template with app:ver notation example](#template-with-app-ver-notation))
2. Artifact Definition v2.0 exists with `authConfig` section
   (See [Artifact Definition v2.0 example](#artifact-definition-v20))
3. `authConfig` specifies `authMethod: user_pass`
4. Credentials configured
   (See [User/Password authentication example](#userpassword-authentication))

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `ENV_NAMES: <env_name>`
2. `ENV_BUILDER: true`

**Steps:**

1. The `app_reg_def_process` job runs in the pipeline:
   1. Reads Environment Inventory
   2. Parses `application:version` from `envTemplate.artifact`
   3. Resolves to Artifact Definition v2.0
   4. Extracts `authConfig` reference
   5. Authenticates using username/password from credentials
   6. Downloads template artifact from Artifactory

**Results:**

1. Template artifact is downloaded successfully using ArtDef v2.0 with enhanced authentication
2. Template is available for Environment Instance generation

### UC-AD-ENV-18: Download Template from Artifactory with app ver notation and Anonymous Access (ArtDef v2)

**Pre-requisites:**

1. Environment Inventory specifies template with `application:version` format
2. Artifact Definition v2.0 exists
3. **No** `authConfig` section in ArtDef v2.0 (anonymous access)
4. Artifactory registry allows anonymous/public access

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `ENV_NAMES: <env_name>`
2. `ENV_BUILDER: true`

**Steps:**

1. The `app_reg_def_process` job runs in the pipeline:
   1. Reads Environment Inventory
   2. Parses `application:version` from `envTemplate.artifact`
   3. Resolves to Artifact Definition v2.0
   4. Extracts `mavenConfig` (without authConfig reference)
   5. Downloads template artifact from Artifactory without authentication

**Results:**

1. Template artifact is downloaded successfully without authentication using ArtDef v2.0
2. Template is available for Environment Instance generation

### UC-AD-ENV-19: Download Template from Nexus with app ver notation (ArtDef v2)

**Pre-requisites:**

1. Environment Inventory specifies template with `application:version` format
2. Artifact Definition v2.0 exists for Nexus
3. `authConfig` specifies `authMethod: user_pass`
4. Credentials configured

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `ENV_NAMES: <env_name>`
2. `ENV_BUILDER: true`

**Steps:**

1. The `app_reg_def_process` job runs in the pipeline:
   1. Reads Environment Inventory
   2. Parses `application:version` from `envTemplate.artifact`
   3. Resolves to Artifact Definition v2.0
   4. Extracts `authConfig` reference
   5. Authenticates using username/password from credentials
   6. Downloads template artifact from Nexus

**Results:**

1. Template artifact is downloaded successfully using ArtDef v2.0 with enhanced authentication
2. Template is available for Environment Instance generation

### UC-AD-ENV-20: Download Template from Nexus with app ver notation and Anonymous Access (ArtDef v2)

**Pre-requisites:**

1. Environment Inventory specifies template with `application:version` format
2. Artifact Definition v2.0 exists for Nexus
3. **No** `authConfig` section in ArtDef v2.0 (anonymous access)
4. Nexus registry allows anonymous/public access

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `ENV_NAMES: <env_name>`
2. `ENV_BUILDER: true`

**Steps:**

1. The `app_reg_def_process` job runs in the pipeline:
   1. Reads Environment Inventory
   2. Parses `application:version` from `envTemplate.artifact`
   3. Resolves to Artifact Definition v2.0
   4. Extracts `mavenConfig` (without authConfig reference)
   5. Downloads template artifact from Nexus without authentication

**Results:**

1. Template artifact is downloaded successfully without authentication using ArtDef v2.0
2. Template is available for Environment Instance generation

### UC-AD-ENV-21: Download Template from AWS CodeArtifact with app ver notation (ArtDef v2)

**Pre-requisites:**

1. Environment Inventory specifies template with `application:version` format
2. Artifact Definition v2.0 exists with `provider: aws` and `authMethod: secret`
3. AWS credentials configured (access key + secret)

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `ENV_NAMES: <env_name>`
2. `ENV_BUILDER: true`

**Steps:**

1. The `app_reg_def_process` job runs in the pipeline:
   1. Reads Environment Inventory
   2. Parses `application:version` from `envTemplate.artifact`
   3. Resolves to Artifact Definition v2.0
   4. Authenticates to AWS using access key/secret from credentials
   5. Gets temporary CodeArtifact token
   6. Downloads template Maven artifact from AWS CodeArtifact

**Results:**

1. Template artifact is downloaded successfully from AWS CodeArtifact
2. Template is available for Environment Instance generation

### UC-AD-ENV-22: Download Template from GCP Artifact Registry with app ver notation (ArtDef v2)

**Pre-requisites:**

1. Environment Inventory specifies template with `application:version` format
2. Artifact Definition v2.0 exists with `provider: gcp` and `authMethod: service_account`
3. GCP service account JSON key configured

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `ENV_NAMES: <env_name>`
2. `ENV_BUILDER: true`

**Steps:**

1. The `app_reg_def_process` job runs in the pipeline:
   1. Reads Environment Inventory
   2. Parses `application:version` from `envTemplate.artifact`
   3. Resolves to Artifact Definition v2.0
   4. Loads service account JSON key
   5. Authenticates to GCP using service account
   6. Downloads template Maven artifact from GCP Artifact Registry

**Results:**

1. Template artifact is downloaded successfully from GCP Artifact Registry
2. Template is available for Environment Instance generation

### UC-AD-ENV-23: Download SNAPSHOT Template Version

**Pre-requisites:**

1. Environment Inventory specifies template with SNAPSHOT version
2. Registry supports SNAPSHOT resolution

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `ENV_NAMES: <env_name>`
2. `ENV_BUILDER: true`

**Steps:**

1. The `app_reg_def_process` job runs in the pipeline:
   1. Reads Environment Inventory
   2. Detects SNAPSHOT version in template specification
   3. Resolves SNAPSHOT to latest available version in registry
   4. Downloads latest artifact version

**Results:**

1. Latest SNAPSHOT template artifact is downloaded successfully
2. Template is available for Environment Instance generation

### UC-AD-ENV-24: Download Specific Template Version

**Pre-requisites:**

1. Environment Inventory specifies template with exact version (not SNAPSHOT)

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `ENV_NAMES: <env_name>`
2. `ENV_BUILDER: true`

**Steps:**

1. The `app_reg_def_process` job runs in the pipeline:
   1. Reads Environment Inventory
   2. Parses exact version from template specification
   3. Downloads specified version from registry

**Results:**

1. Specific template artifact version is downloaded successfully
2. Template is available for Environment Instance generation

## Error Handling

This group covers error scenarios that can occur during artifact download operations.

### UC-AD-ERR-1: Handle Missing Application Definition

**Pre-requisites:**

1. Pipeline parameter specifies `SD_VERSION` or `DD_VERSION` with `application:version` format
2. Application Definition for specified application does NOT exist

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters that trigger artifact download (e.g., `SD_VERSION: <application:version>`)

**Steps:**

1. Artifact download process attempts to resolve Application Definition
2. Definition file is not found at expected location
3. Pipeline job fails with clear error message indicating missing AppDef

**Results:**

1. Pipeline execution fails
2. Error message clearly indicates which Application Definition is missing
3. Error message includes expected file path

### UC-AD-ERR-2: Handle Missing Registry Definition

**Pre-requisites:**

1. Application Definition or Artifact Definition references a registry
2. Registry Definition for specified registry does NOT exist

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters that trigger artifact download

**Steps:**

1. Artifact download process attempts to resolve Registry Definition
2. Definition file is not found at expected location
3. Pipeline job fails with clear error message indicating missing RegDef

**Results:**

1. Pipeline execution fails
2. Error message clearly indicates which Registry Definition is missing
3. Error message includes expected file path and registry name

### UC-AD-ERR-3: Handle Authentication Failure

**Pre-requisites:**

1. Artifact download requires authentication
2. Authentication credentials are invalid, expired, or missing

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters that trigger artifact download from authenticated registry

**Steps:**

1. Artifact download process attempts authentication
2. Authentication fails (invalid credentials, network issue, or authorization problem)
3. Pipeline implements retry logic for transient failures
4. If retries exhausted, pipeline job fails with clear error message

**Results:**

1. For transient failures: Retry mechanism attempts to recover
2. For permanent failures: Pipeline execution fails with clear error message
3. Error message indicates authentication failure and suggests troubleshooting steps

### UC-AD-ERR-4: Handle Missing Artifact Definition

**Pre-requisites:**

1. Environment Inventory specifies template with `application:version` notation
2. Artifact Definition for specified application does NOT exist

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `ENV_NAMES: <env_name>`
2. `ENV_BUILDER: true`

**Steps:**

1. Template download process attempts to resolve Artifact Definition
2. Definition file is not found at expected location
3. Pipeline job fails with clear error message indicating missing ArtDef

**Results:**

1. Pipeline execution fails
2. Error message clearly indicates which Artifact Definition is missing
3. Error message includes expected file path

## Configuration Examples

This section provides complete configuration examples for definitions referenced in the use cases above.

### Registry Definition Examples

#### Artifactory / Nexus (RegDef v1.0)

> [!NOTE]
> The structure is identical for both Artifactory and Nexus. Only the values differ (registry names, URLs, repository names).
>
> RegDef v1.0 does NOT have a `version` field - the absence of this field indicates v1.0.
>
> This example shows only `mavenConfig` section relevant to Maven artifact download use cases. Full Registry Definition v1.0 requires additional sections (`dockerConfig`, `helmConfig`, etc.) - see [Registry Definition schema](/docs/envgene-objects.md#registry-definition-v10) for complete structure.

```yaml
name: "artifactory-maven"
credentialsId: "artifactory-creds"
mavenConfig:
  repositoryDomainName: "artifactory.example.com"
  fullRepositoryUrl: "https://artifactory.example.com/artifactory"
  targetSnapshot: "libs-snapshot-local"
  targetStaging: "libs-staging-local"
  targetRelease: "libs-release-local"
  snapshotGroup: "libs-snapshot"
  releaseGroup: "libs-release"
dockerConfig:
  snapshotUri: ""
  stagingUri: ""
  releaseUri: ""
  groupUri: ""
  snapshotRepoName: ""
  stagingRepoName: ""
  releaseRepoName: ""
  groupName: ""
```

#### Artifactory (RegDef v2.0)

> [!NOTE]
> For `provider: nexus` or `provider: artifactory`, the `repositoryDomainName` field contains a full URL.
> For cloud providers (`aws`, `gcp`, `azure`), it also contains a full URL.
> This is a known gap in the model naming convention and will be addressed in future versions.

```yaml
version: "2.0"
name: "artifactory-maven"
authConfig:
  artifactory-auth:
    provider: "artifactory"
    authMethod: "user_pass"
    credentialsId: "artifactory-creds"
mavenConfig:
  authConfig: "artifactory-auth"
  repositoryDomainName: "https://artifactory.example.com/artifactory"
  targetSnapshot: "libs-snapshot-local"
  targetStaging: "libs-staging-local"
  targetRelease: "libs-release-local"
  snapshotGroup: "libs-snapshot"
  releaseGroup: "libs-release"
```

#### Nexus (RegDef v2.0)

> [!NOTE]
> For `provider: nexus` or `provider: artifactory`, the `repositoryDomainName` field contains a full URL.
> For cloud providers (`aws`, `gcp`, `azure`), it also contains a full URL.
> This is a known gap in the model naming convention and will be addressed in future versions.

```yaml
version: "2.0"
name: "nexus-maven"
authConfig:
  nexus-auth:
    provider: "nexus"
    authMethod: "user_pass"
    credentialsId: "nexus-creds"
mavenConfig:
  authConfig: "nexus-auth"
  repositoryDomainName: "https://nexus.example.com/repository"
  targetSnapshot: "maven-snapshots"
  targetStaging: "maven-staging"
  targetRelease: "maven-releases"
  snapshotGroup: "maven-public-snapshots"
  releaseGroup: "maven-public"
```

#### AWS CodeArtifact (RegDef v2.0)

> [!NOTE]
> For `provider: nexus` or `provider: artifactory`, the `repositoryDomainName` field contains a full URL.
> For cloud providers (`aws`, `gcp`, `azure`), it also contains a full URL.
> This is a known gap in the model naming convention and will be addressed in future versions.

```yaml
version: "2.0"
name: "aws-codeartifact"
authConfig:
  aws-auth:
    provider: "aws"
    authMethod: "secret"
    credentialsId: "aws-secret-creds"
    awsRegion: "us-east-1"
    awsDomain: "my-domain"
mavenConfig:
  authConfig: "aws-auth"
  repositoryDomainName: "https://my-domain-123456789012.d.codeartifact.us-east-1.amazonaws.com/maven/maven-central-store"
```

#### GCP Artifact Registry (RegDef v2.0)

> [!NOTE]
> For `provider: nexus` or `provider: artifactory`, the `repositoryDomainName` field contains a full URL.
> For cloud providers (`aws`, `gcp`, `azure`), it also contains a full URL.
> This is a known gap in the model naming convention and will be addressed in future versions.

```yaml
version: "2.0"
name: "gcp-artifact-registry"
authConfig:
  gcp-auth:
    provider: "gcp"
    authMethod: "service_account"
    credentialsId: "gcp-sa-key"
    gcpRegion: "us-central1"
mavenConfig:
  authConfig: "gcp-auth"
  repositoryDomainName: "https://us-central1-maven.pkg.dev/my-project/maven-repo"
```

### Artifact Definition Examples

#### Artifact Definition v1.0

```yaml
name: "env-template"
groupId: "com.example.templates"
artifactId: "env-template"
registry:
  name: "artifactory-maven"
  credentialsId: "artifactory-creds"
  mavenConfig:
    repositoryDomainName: "https://artifactory.example.com"
    targetSnapshot: "libs-snapshot-local"
    targetStaging: "libs-staging-local"
    targetRelease: "libs-release-local"
```

#### Artifact Definition v2.0

```yaml
version: "2.0"
name: "env-template"
groupId: "com.example.templates"
artifactId: "env-template"
registry:
  name: "artifactory-maven"
  authConfig:
    artifactory-auth:
      provider: "artifactory"
      authMethod: "user_pass"
      credentialsId: "artifactory-creds"
  mavenConfig:
    authConfig: "artifactory-auth"
    repositoryDomainName: "https://artifactory.example.com"
    targetSnapshot: "libs-snapshot-local"
    targetStaging: "libs-staging-local"
    targetRelease: "libs-release-local"
    snapshotGroup: "libs-snapshot"
    releaseGroup: "libs-release"
```

### Credentials Configuration Examples

#### User/Password Authentication

```yaml
artifactory-auth:
  type: usernamePassword
  data:
    username: "user-placeholder-123"
    password: "pass-placeholder-123"
```

#### AWS Secret Authentication

```yaml
aws-secret-creds:
  type: secret
  data:
    secret: TBD
```

#### GCP Service Account Authentication

```yaml
gcp-sa-key:
  type: secret
  data:
    secret: TBD
```

### Environment Inventory Examples

#### Template with GAV notation

```yaml
templateArtifact:
  registry: "artifactory-maven"
  artifact:
    group_id: "com.example.templates"
    artifact_id: "env-template"
    version: "1.2.3"
```

#### Template with app ver notation

```yaml
envTemplate:
  artifact: "env-template:1.2.3"
```
