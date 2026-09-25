# Configuring cloud artifact registries for AWS and GCP

- [Configuring cloud artifact registries for AWS and GCP](#configuring-cloud-artifact-registries-for-aws-and-gcp)
  - [Two registry contexts in EnvGene](#two-registry-contexts-in-envgene)
  - [Prerequisites](#prerequisites)
  - [AWS CodeArtifact configuration](#aws-codeartifact-configuration)
    - [AWS-side: required permissions](#aws-side-required-permissions)
    - [Step 1: Create the credential entry](#step-1-create-the-credential-entry)
    - [Step 2: Create the registry definition](#step-2-create-the-registry-definition)
    - [Step 3: Reference the registry in an Artifact or Application Definition](#step-3-reference-the-registry-in-an-artifact-or-application-definition)
    - [AWS authentication flow](#aws-authentication-flow)
    - [GitLab CI: pulling images from AWS ECR](#gitlab-ci-pulling-images-from-aws-ecr)
  - [GCP Artifact Registry configuration](#gcp-artifact-registry-configuration)
    - [GCP-side: required permissions](#gcp-side-required-permissions)
    - [Step 1: Create the GCP credential entry](#step-1-create-the-gcp-credential-entry)
    - [Step 2: Create the GCP registry definition](#step-2-create-the-gcp-registry-definition)
    - [Step 3: Reference the GCP registry in an Artifact or Application Definition](#step-3-reference-the-gcp-registry-in-an-artifact-or-application-definition)
    - [GCP authentication flow](#gcp-authentication-flow)
  - [Placing configuration files](#placing-configuration-files)
  - [Supported auth methods reference](#supported-auth-methods-reference)
  - [Troubleshooting](#troubleshooting)
  - [See also](#see-also)

EnvGene downloads Maven artifacts ([Solution Descriptors](/docs/envgene-objects.md#solution-descriptor), Deployment Descriptors, and environment templates) from external cloud registries like AWS CodeArtifact and GCP Artifact Registry
using [Registry Definition v2.0](/docs/envgene-objects.md#registry-definition-v20) with an
`authConfig` block. This guide walks through each provider step by step.

> [!IMPORTANT]
> **Pulling EnvGene Docker images from cloud registries (GAR, ECR) during pipeline execution is
> supported in the GitHub workflow only** via the `DOCKER_REGISTRY` and `DOCKER_CLOUD_REGISTRY_PROVIDER`
> variables. For GitLab CI pipelines, set `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` as
> masked CI/CD variables and configure the runner with the Amazon ECR credential helper -
> see [GitLab CI: pulling images from AWS ECR](#gitlab-ci-pulling-images-from-aws-ecr).
>
> **Publishing environment template build artifacts to external cloud registries (GAR, ECR) is not
> currently supported.**.

## Running this guide

**No installation needed** — run with `npx`. Fill in your values using the template in [Required Inputs](#required-inputs), save to any file (e.g. `my-inputs.txt`), then run:

`(set -a; source my-inputs.txt; npx runme run --all --filename configure-cloud-artifact-registries.md)`

See [How to run guides with runme](/docs/how-to/how-to-run-guides-with-runme.md) for full CLI, VS Code, pipeline, and AI agent instructions.

Steps marked **Manual step — cannot be automated** are blockquotes — runme skips them automatically.

## Required Inputs

Create a file with your values (any filename, e.g. `my-inputs.txt`) and load it with `source` before running.

| Variable | Required | Example | Description |
|---|---|---|---|
| `PROVIDER` | Yes | `aws` | Which provider to configure: `aws`, `gcp`, or `both` |
| `AWS_CRED_KEY` | AWS | `aws-codeartifact-creds` | Key name for the AWS credential entry in `credentials.yml` |
| `AWS_ACCESS_KEY_ID` | AWS | `AKIAIOSFODNN7EXAMPLE` | AWS IAM access key ID |
| `AWS_SECRET_ACCESS_KEY` | AWS | `wJalrXUtnFEMI/K7MDENG/...` | AWS IAM secret access key |
| `AWS_REGION` | AWS | `us-east-1` | AWS region where CodeArtifact domain is hosted |
| `AWS_DOMAIN` | AWS | `my-domain` | CodeArtifact domain name |
| `AWS_REPO_URL` | AWS | `https://my-domain-123456789012.d.codeartifact.us-east-1.amazonaws.com/maven/my-repo` | Full Maven endpoint URL from the AWS CodeArtifact console |
| `AWS_REGDEF_NAME` | AWS | `aws-codeartifact` | Filename (no extension) for the registry definition file |
| `GCP_CRED_KEY` | GCP | `gcp-artifact-registry-key` | Key name for the GCP credential entry in `credentials.yml` |
| `GCP_SA_KEY_FILE` | GCP | `/path/to/sa-key.json` | Local path to your GCP service account JSON key file |
| `GCP_REGION` | GCP | `us-central1` | GCP region where the Artifact Registry repository is hosted |
| `GCP_PROJECT_ID` | GCP | `my-project` | GCP project ID |
| `GCP_MAVEN_REPO` | GCP | `my-maven-repo` | Maven repository name in Artifact Registry |
| `GCP_REGDEF_NAME` | GCP | `gcp-artifact-registry` | Filename (no extension) for the registry definition file |

**Template** — copy, fill in your values, save as any filename:

```bash {"excludeFromRunAll":true,"name":"input-template"}
PROVIDER=aws
AWS_CRED_KEY=aws-codeartifact-creds
AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
AWS_REGION=us-east-1
AWS_DOMAIN=my-domain
AWS_REPO_URL=https://my-domain-123456789012.d.codeartifact.us-east-1.amazonaws.com/maven/my-repo
AWS_REGDEF_NAME=aws-codeartifact
GCP_CRED_KEY=gcp-artifact-registry-key
GCP_SA_KEY_FILE=/path/to/sa-key.json
GCP_REGION=us-central1
GCP_PROJECT_ID=my-project
GCP_MAVEN_REPO=my-maven-repo
GCP_REGDEF_NAME=gcp-artifact-registry
```

Validate inputs (first runnable cell — fails immediately if a required variable is missing):

```bash
# validate-inputs
: "${PROVIDER:?PROVIDER is required — set to 'aws', 'gcp', or 'both'}"
case "$PROVIDER" in
  aws|gcp|both) echo "Provider: $PROVIDER" ;;
  *) echo "ERROR: PROVIDER must be 'aws', 'gcp', or 'both'"; exit 1 ;;
esac
if [ "$PROVIDER" = "aws" ] || [ "$PROVIDER" = "both" ]; then
  : "${AWS_ACCESS_KEY_ID:?AWS_ACCESS_KEY_ID is required for PROVIDER=$PROVIDER}"
  : "${AWS_SECRET_ACCESS_KEY:?AWS_SECRET_ACCESS_KEY is required for PROVIDER=$PROVIDER}"
  : "${AWS_REGION:?AWS_REGION is required for PROVIDER=$PROVIDER}"
  : "${AWS_DOMAIN:?AWS_DOMAIN is required for PROVIDER=$PROVIDER}"
  : "${AWS_REPO_URL:?AWS_REPO_URL is required for PROVIDER=$PROVIDER}"
  AWS_CRED_KEY="${AWS_CRED_KEY:-aws-codeartifact-creds}"
  AWS_REGDEF_NAME="${AWS_REGDEF_NAME:-aws-codeartifact}"
fi
if [ "$PROVIDER" = "gcp" ] || [ "$PROVIDER" = "both" ]; then
  : "${GCP_SA_KEY_FILE:?GCP_SA_KEY_FILE is required for PROVIDER=$PROVIDER}"
  [ -f "$GCP_SA_KEY_FILE" ] || { echo "ERROR: GCP_SA_KEY_FILE not found: $GCP_SA_KEY_FILE"; exit 1; }
  : "${GCP_REGION:?GCP_REGION is required for PROVIDER=$PROVIDER}"
  : "${GCP_PROJECT_ID:?GCP_PROJECT_ID is required for PROVIDER=$PROVIDER}"
  : "${GCP_MAVEN_REPO:?GCP_MAVEN_REPO is required for PROVIDER=$PROVIDER}"
  GCP_CRED_KEY="${GCP_CRED_KEY:-gcp-artifact-registry-key}"
  GCP_REGDEF_NAME="${GCP_REGDEF_NAME:-gcp-artifact-registry}"
fi
echo "Inputs OK: PROVIDER=$PROVIDER"
```

## Two registry contexts in EnvGene

EnvGene uses the term "registry" in two distinct contexts. Keep them separate when you read
documentation or configure the system.

| Context                  | Purpose                                              | Configured via                                                                                                                                       |
|--------------------------|------------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------|
| A. Artifact registries   | Download Maven artifacts (SD, DD, env templates)     | [RegDef v2.0](/docs/envgene-objects.md#registry-definition-v20) or [ArtDef v2.0](/docs/envgene-objects.md#artifact-definition-v20) with `authConfig` |
| B. Image registries      | Pull EnvGene's own container images in CI            | GitHub repository variables (`DOCKER_REGISTRY`, `DOCKER_CLOUD_REGISTRY_PROVIDER`, `GCP_SA_KEY`)                                                      |

This guide covers Context A only. For image registry configuration (Context B), see
[Using Docker Registries in EnvGene GitHub Workflow](/docs/how-to/docker-registry-configuration.md).

## Prerequisites

- An instance repository with the EnvGene workflow installed.
- Write access to `configuration/registry_definitions/` and `configuration/credentials/` in the
  instance repository.
- AWS or GCP credentials ready (see the provider-specific sections below).

## AWS CodeArtifact configuration

> [!WARNING]
> AWS CodeArtifact support is not tested end-to-end. The `authMethod: secret` implementation is
> present in code but has not been validated against a live CodeArtifact repository. Use with
> caution and report issues if encountered.

### AWS-side: required permissions

The IAM user or role whose access key you use must have the following CodeArtifact permissions on
the target domain and repository:

| Permission                              | Purpose                                         |
|-----------------------------------------|-------------------------------------------------|
| `codeartifact:GetAuthorizationToken`    | Obtain a temporary download token               |
| `codeartifact:GetRepositoryEndpoint`    | Resolve the Maven repository URL                |
| `codeartifact:ReadFromRepository`       | Download artifacts from the repository          |
| `sts:GetServiceBearerToken`             | Exchange credentials for an authorisation token |

To create an IAM user or role with these permissions and generate an access key, follow the official
AWS guides:

- [Create an IAM user](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_users_create.html)
- [CodeArtifact permissions reference](https://docs.aws.amazon.com/codeartifact/latest/ug/auth-and-access-control-iam-access-control-identity-based.html)
- [Create an IAM access key](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_credentials_access-keys.html)

### Step 1: Create the credential entry

Add an entry to `configuration/credentials/credentials.yml` in the instance repository:

> **Manual step — cannot be automated:** Credential files contain secrets and must be edited
> carefully. Add the following entry to `configuration/credentials/credentials.yml`, then encrypt
> it — see [Credential Encryption](/docs/how-to/credential-encryption.md).

```yaml {"excludeFromRunAll":true}
aws-codeartifact-creds:
  type: usernamePassword
  data:
    username: "AKIAIOSFODNN7EXAMPLE"        # AWS access key ID
    password: "wJalrXUtnFEMI/K7MDENG/..."  # AWS secret access key
```

> [!IMPORTANT]
> The credential type must be `usernamePassword`, with `username` set to the AWS access key ID and
> `password` set to the AWS secret access key. Using `type: secret` is incorrect and causes an
> authentication failure.

### Step 2: Create the registry definition

Create `configuration/registry_definitions/$AWS_REGDEF_NAME.yaml` with your values:

```bash
if [ "$PROVIDER" = "gcp" ] || [ "$PROVIDER" = "both" ]; then echo "AWS not selected individually (PROVIDER=$PROVIDER) — use parallel section below for both"; exit 0; fi
mkdir -p configuration/registry_definitions
cat > "configuration/registry_definitions/$AWS_REGDEF_NAME.yaml" <<EOF
version: "2.0"
name: "$AWS_REGDEF_NAME"
authConfig:
  aws-auth:
    provider: "aws"
    authMethod: "secret"
    credentialsId: "$AWS_CRED_KEY"
    awsRegion: "$AWS_REGION"
    awsDomain: "$AWS_DOMAIN"
mavenConfig:
  authConfig: "aws-auth"
  repositoryDomainName: "$AWS_REPO_URL"
EOF
echo "Created: configuration/registry_definitions/$AWS_REGDEF_NAME.yaml"
```

Verify the file was written with values substituted:

```bash
if [ "$PROVIDER" = "gcp" ] || [ "$PROVIDER" = "both" ]; then exit 0; fi
cat "configuration/registry_definitions/$AWS_REGDEF_NAME.yaml"
# Expected: YAML with actual values for name, region, domain, and repo URL
```

File reference (example with placeholder values):

```yaml {"excludeFromRunAll":true}
version: "2.0"
name: "aws-codeartifact"
authConfig:
  aws-auth:
    provider: "aws"
    authMethod: "secret"
    credentialsId: "aws-codeartifact-creds"
    awsRegion: "us-east-1"
    awsDomain: "my-domain"
mavenConfig:
  authConfig: "aws-auth"
  repositoryDomainName: "https://my-domain-123456789012.d.codeartifact.us-east-1.amazonaws.com/maven/my-repo"
```

Field reference:

| Field                              | Description                                                                     |
|------------------------------------|---------------------------------------------------------------------------------|
| `authConfig.<key>.provider`        | Must be `aws`                                                                   |
| `authConfig.<key>.authMethod`      | Must be `secret` (the only implemented AWS auth method)                         |
| `authConfig.<key>.credentialsId`   | Must match the key in `credentials.yml`                                         |
| `authConfig.<key>.awsRegion`       | AWS region where the CodeArtifact domain is hosted (for example, `us-east-1`)   |
| `authConfig.<key>.awsDomain`       | CodeArtifact domain name, without the account suffix                            |
| `mavenConfig.authConfig`           | Must match the auth config key defined above (for example, `aws-auth`)          |
| `mavenConfig.repositoryDomainName` | Full Maven endpoint URL from the AWS CodeArtifact console                       |

To find the `repositoryDomainName`, open the AWS CodeArtifact console, select your repository, and
copy the **Connection instructions - Maven** endpoint URL.

### Step 3: Reference the registry in an Artifact or Application Definition

**For SD/DD artifacts ([Application Definition v1.0](/docs/envgene-objects.md#application-definition) + [Registry Definition v2.0](/docs/envgene-objects.md#registry-definition-v20)):**

```yaml {"excludeFromRunAll":true}
# configuration/app_definitions/my-app.yaml
name: "my-app"
registryName: "aws-codeartifact"
groupId: "com.example"
artifactId: "my-app"
```

**For environment templates ([Artifact Definition v2.0](/docs/envgene-objects.md#artifact-definition-v20)):**

```yaml {"excludeFromRunAll":true}
# configuration/artifact_definitions/env-template.yaml
version: "2.0"
name: "env-template"
groupId: "com.example.templates"
artifactId: "env-template"
registry:
  name: "aws-codeartifact"
  authConfig:
    aws-auth:
      provider: "aws"
      authMethod: "secret"
      credentialsId: "aws-codeartifact-creds"
      awsRegion: "us-east-1"
      awsDomain: "my-domain"
  mavenConfig:
    authConfig: "aws-auth"
    repositoryDomainName: "https://my-domain-123456789012.d.codeartifact.us-east-1.amazonaws.com/maven/my-repo"
```

> [!NOTE]
> With a standalone RegDef v2.0, the `authConfig` lives in the RegDef file and the AppDef
> references the registry by name. With an ArtDef v2.0, the `authConfig` is embedded inside the
> ArtDef's `registry` block.

### AWS authentication flow

1. EnvGene resolves the `authConfig` block with `provider: aws` and `authMethod: secret`.
2. The credential identified by `credentialsId` is loaded from `credentials.yml`. The `username`
   field is the AWS access key ID and `password` is the secret access key.
3. EnvGene calls the AWS CodeArtifact `GetAuthorizationToken` API. The token is scoped to
   `awsDomain` and `awsRegion`.
4. The short-lived bearer token is attached to all Maven download requests as
   `Authorization: Bearer <token>`.
5. Maven artifacts are downloaded from the `repositoryDomainName` endpoint.

### GitLab CI: pulling images from AWS ECR

To pull Docker images from AWS ECR in a GitLab CI pipeline, provide AWS credentials as masked
CI/CD variables. The GitLab Runner uses these variables together with the
[Amazon ECR credential helper](https://github.com/awslabs/amazon-ecr-credential-helper) to
authenticate automatically on each pipeline run - no static token or manual rotation needed.

> [!IMPORTANT]
> **Prerequisite: ECR credential helper must be configured on the runner.**
> Confirm with your runner administrator that the runner's `config.toml` includes:
>
> ```toml
> [[runners]]
>   [runners.docker]
>     credential_helpers = ["ecr-login"]
> ```
>
> This is a one-time runner-level setup. Without it, Docker cannot authenticate to ECR
> automatically. For details, see
> [GitLab Runner advanced configuration](https://docs.gitlab.com/runner/configuration/advanced-configuration.html).

#### Set CI/CD variables

In **Settings → CI/CD → Variables**, add the following masked variables:

| Variable                | Description             |
|-------------------------|-------------------------|
| `AWS_ACCESS_KEY_ID`     | IAM user access key ID  |
| `AWS_SECRET_ACCESS_KEY` | IAM user secret access key |

`AWS_REGION` is not required. The ECR credential helper parses the region directly from the
registry URL (`<account-id>.dkr.ecr.<region>.amazonaws.com`).

With the runner configured and these variables set, Docker calls `docker-credential-ecr-login`
automatically for any ECR registry URL and exchanges the AWS credentials for a fresh ECR token
on each pull.

> [!NOTE]
> `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` authenticate Docker image pulls for GitLab CI
> jobs. They are separate from the Maven artifact registry configuration described in the sections
> above, which uses `credentials.yml` and Registry Definitions.

## GCP Artifact Registry configuration

### GCP-side: required permissions

The service account used for authentication must have the following IAM role on the Artifact
Registry repository:

| Role                            | Purpose                                         |
|---------------------------------|-------------------------------------------------|
| `roles/artifactregistry.reader` | Read and download artifacts from the repository |

To set up a service account with this role and download its JSON key, follow the official Google
Cloud guides:

- [Create and manage service accounts](https://cloud.google.com/iam/docs/service-accounts-create)
- [Grant an IAM role on an Artifact Registry repository](https://cloud.google.com/artifact-registry/docs/access-control#grant-repo)
- [Create and manage service account keys](https://cloud.google.com/iam/docs/keys-create-delete)

### Step 1: Create the GCP credential entry

Add an entry to `configuration/credentials/credentials.yml` in the instance repository.

> **Manual step — cannot be automated:** Credential files contain secrets and must be edited
> carefully. The `secret` field must contain the complete JSON of your GCP service account key
> file. After adding the entry, encrypt it — see
> [Credential Encryption](/docs/how-to/credential-encryption.md).

```yaml {"excludeFromRunAll":true}
gcp-artifact-registry-key:
  type: secret
  data:
    secret: |
      {
        "type": "service_account",
        "project_id": "my-project",
        "private_key_id": "key-id-placeholder",
        "private_key": "-----BEGIN RSA PRIVATE KEY-----\n...\n-----END RSA PRIVATE KEY-----\n",
        "client_email": "envgene-artifact-reader@my-project.iam.gserviceaccount.com",
        "client_id": "123456789",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token"
      }
```

The `secret` field must contain the complete JSON content of the GCP service account key file
(`GCP_SA_KEY_FILE`). The guide uses this file in the registry definition creation step below.

### Step 2: Create the GCP registry definition

Create `configuration/registry_definitions/$GCP_REGDEF_NAME.yaml` with your values:

```bash
if [ "$PROVIDER" = "aws" ] || [ "$PROVIDER" = "both" ]; then echo "GCP not selected individually (PROVIDER=$PROVIDER) — use parallel section below for both"; exit 0; fi
mkdir -p configuration/registry_definitions
cat > "configuration/registry_definitions/$GCP_REGDEF_NAME.yaml" <<EOF
version: "2.0"
name: "$GCP_REGDEF_NAME"
authConfig:
  gcp-auth:
    provider: "gcp"
    authMethod: "service_account"
    credentialsId: "$GCP_CRED_KEY"
    gcpRegion: "$GCP_REGION"
mavenConfig:
  authConfig: "gcp-auth"
  repositoryDomainName: "https://$GCP_REGION-maven.pkg.dev/$GCP_PROJECT_ID/$GCP_MAVEN_REPO"
EOF
echo "Created: configuration/registry_definitions/$GCP_REGDEF_NAME.yaml"
```

Verify the file was written with values substituted:

```bash
if [ "$PROVIDER" = "aws" ] || [ "$PROVIDER" = "both" ]; then exit 0; fi
cat "configuration/registry_definitions/$GCP_REGDEF_NAME.yaml"
# Expected: YAML with actual values for name, region, project, and repo
```

File reference (example with placeholder values):

```yaml {"excludeFromRunAll":true}
version: "2.0"
name: "gcp-artifact-registry"
authConfig:
  gcp-auth:
    provider: "gcp"
    authMethod: "service_account"
    credentialsId: "gcp-artifact-registry-key"
    gcpRegion: "us-central1"
mavenConfig:
  authConfig: "gcp-auth"
  repositoryDomainName: "https://us-central1-maven.pkg.dev/my-project/my-maven-repo"
```

Field reference:

| Field                              | Description                                                                        |
|------------------------------------|------------------------------------------------------------------------------------|
| `authConfig.<key>.provider`        | Must be `gcp`                                                                      |
| `authConfig.<key>.authMethod`      | Must be `service_account` (the only implemented GCP auth method)                   |
| `authConfig.<key>.credentialsId`   | Must match the key in `credentials.yml`                                            |
| `authConfig.<key>.gcpRegion`       | GCP region where the repository is hosted (for example, `us-central1`)             |
| `mavenConfig.authConfig`           | Must match the auth config key defined above (for example, `gcp-auth`)             |
| `mavenConfig.repositoryDomainName` | Full Maven endpoint URL: `https://REGION-maven.pkg.dev/PROJECT_ID/REPOSITORY_NAME` |

To find the `repositoryDomainName`, open the GCP Artifact Registry console, select your Maven
repository, and copy the endpoint URL from the repository details panel.

### Step 3: Reference the GCP registry in an Artifact or Application Definition

**For SD/DD artifacts ([Application Definition v1.0](/docs/envgene-objects.md#application-definition) + [Registry Definition v2.0](/docs/envgene-objects.md#registry-definition-v20)):**

```yaml {"excludeFromRunAll":true}
# configuration/app_definitions/my-app.yaml
name: "my-app"
registryName: "gcp-artifact-registry"
groupId: "com.example"
artifactId: "my-app"
```

**For environment templates ([Artifact Definition v2.0](/docs/envgene-objects.md#artifact-definition-v20)):**

```yaml {"excludeFromRunAll":true}
# configuration/artifact_definitions/env-template.yaml
version: "2.0"
name: "env-template"
groupId: "com.example.templates"
artifactId: "env-template"
registry:
  name: "gcp-artifact-registry"
  authConfig:
    gcp-auth:
      provider: "gcp"
      authMethod: "service_account"
      credentialsId: "gcp-artifact-registry-key"
      gcpRegion: "us-central1"
  mavenConfig:
    authConfig: "gcp-auth"
    repositoryDomainName: "https://us-central1-maven.pkg.dev/my-project/my-maven-repo"
```

### GCP authentication flow

1. EnvGene resolves the `authConfig` block with `provider: gcp` and `authMethod: service_account`.
2. The credential identified by `credentialsId` is loaded from `credentials.yml`. The `secret`
   field must contain the full JSON of a GCP service account key.
3. EnvGene exchanges the service account key for a short-lived OAuth 2.0 access token using the
   GCP credentials provider library.
4. The access token is attached to all Maven download requests as `Authorization: Bearer <token>`.
5. Maven artifacts are downloaded from the `repositoryDomainName` endpoint.

## Placing configuration files

Files can be placed at two levels. EnvGene resolves them with per-environment overriding root-level.

| Level           | Path                                                                          | Scope                        |
|-----------------|-------------------------------------------------------------------------------|------------------------------|
| Root            | `configuration/registry_definitions/<name>.yaml`                              | All environments             |
| Per-environment | `environments/<cluster>/<env>/configuration/registry_definitions/<name>.yaml` | This environment only        |

Credentials follow the same pattern:

| Level           | Path                                                                     |
|-----------------|--------------------------------------------------------------------------|
| Root            | `configuration/credentials/credentials.yml`                              |
| Per-environment | `environments/<cluster>/<env>/configuration/credentials/credentials.yml` |

Use root-level placement for registries shared across environments. Use per-environment placement
when different environments use different registries or accounts.

## Supported auth methods reference

| Provider       | Auth method        | Implemented       | Credential type    | Credential fields                                   |
|----------------|--------------------|-------------------|--------------------|-----------------------------------------------------|
| `aws`          | `secret`           | Yes               | `usernamePassword` | `username` = access key ID, `password` = secret key |
| `aws`          | `assume_role`      | No (raises error) | -                  | -                                                   |
| `gcp`          | `service_account`  | Yes               | `secret`           | `secret` = full JSON of GCP service account key     |
| `gcp`          | `federation`       | No (raises error) | -                  | -                                                   |
| `nexus`        | `user_pass`        | Yes               | `usernamePassword` | `username`, `password`                              |
| `artifactory`  | `user_pass`        | Yes               | `usernamePassword` | `username`, `password`                              |
| any            | `anonymous`        | Yes               | none               | -                                                   |

> [!WARNING]
> The `assume_role` (AWS) and `federation` (GCP) auth methods appear in the schema but are not
> implemented. Using them causes a runtime error. Use `secret` for AWS and `service_account` for
> GCP.

## Troubleshooting

### "AWS secret auth requires both username and password in credentials"

The credential type is wrong. AWS requires `type: usernamePassword` - not `type: secret`. Check
that your `credentials.yml` entry matches the example in
[Step 1: Create the credential entry](#step-1-create-the-credential-entry).

### "GCP service_account requires credential with 'secret' field containing SA JSON key"

The credential is missing the `secret` field, or the type is not `secret`. Check that your
`credentials.yml` entry uses `type: secret` with `data.secret` containing the full service account
JSON.

### "GCP service account key is stored as a YAML mapping instead of a JSON string"

The `data.secret` value was parsed as a YAML mapping (nested keys) instead of as a plain string.
This happens when the service account key JSON is pasted inline without a YAML literal block scalar.
Fix by adding `|` after `secret:` so YAML treats the content as a string:

```yaml {"excludeFromRunAll":true}
gcp-artifact-registry-key:
  type: secret
  data:
    secret: |
      {
        "type": "service_account",
        ...
      }
```

### "GCP service account key must be a valid JSON string"

The value in `data.secret` is not a valid JSON string. Paste the raw content of the service account
key file. Do not base64-encode or otherwise transform it. Ensure the `|` literal block scalar is
present so YAML does not parse the braces as a mapping.

### "AuthConfig 'X' not found in registry 'Y'"

The `mavenConfig.authConfig` value in your RegDef or ArtDef does not match any key under
`authConfig`. The value is case-sensitive - check for typos at both ends.

### Credential not found

The `credentialsId` in your `authConfig` block does not match any top-level key in
`credentials.yml`. Check the spelling at both ends.

### AWS token request fails with "access denied"

The IAM user does not have `codeartifact:GetAuthorizationToken` or `sts:GetServiceBearerToken`
permissions. Review the policy in
[AWS-side: required permissions](#aws-side-required-permissions).

### GCP returns 403 Forbidden on artifact download

The service account does not have `roles/artifactregistry.reader` on the target repository. Run
the `gcloud artifacts repositories add-iam-policy-binding` command from
[GCP-side: required permissions](#gcp-side-required-permissions).

## Commit and verify

Stage and commit the registry definition file(s) created above:

```bash
git add configuration/registry_definitions/
git commit -m "Add ${PROVIDER} artifact registry configuration"
git push
```

Verify the commit was created:

```bash
git log --oneline -1
# Expected: commit message matching "Add <provider> artifact registry configuration"
```

> **Manual step — cannot be automated:** After committing, trigger the instance pipeline from
> the GitLab UI or API. The pipeline will use the new registry definition for artifact downloads.

## Parallel creation: configuring both providers at once

When `PROVIDER=both`, create both registry definition files simultaneously using background
processes (`&`) and `wait`:

```bash
if [ "$PROVIDER" != "both" ]; then echo "PROVIDER=$PROVIDER — parallel step only runs when PROVIDER=both"; exit 0; fi
mkdir -p configuration/registry_definitions

create_aws() {
  cat > "configuration/registry_definitions/$AWS_REGDEF_NAME.yaml" <<EOF
version: "2.0"
name: "$AWS_REGDEF_NAME"
authConfig:
  aws-auth:
    provider: "aws"
    authMethod: "secret"
    credentialsId: "$AWS_CRED_KEY"
    awsRegion: "$AWS_REGION"
    awsDomain: "$AWS_DOMAIN"
mavenConfig:
  authConfig: "aws-auth"
  repositoryDomainName: "$AWS_REPO_URL"
EOF
  echo "[aws] Created: configuration/registry_definitions/$AWS_REGDEF_NAME.yaml"
}

create_gcp() {
  cat > "configuration/registry_definitions/$GCP_REGDEF_NAME.yaml" <<EOF
version: "2.0"
name: "$GCP_REGDEF_NAME"
authConfig:
  gcp-auth:
    provider: "gcp"
    authMethod: "service_account"
    credentialsId: "$GCP_CRED_KEY"
    gcpRegion: "$GCP_REGION"
mavenConfig:
  authConfig: "gcp-auth"
  repositoryDomainName: "https://$GCP_REGION-maven.pkg.dev/$GCP_PROJECT_ID/$GCP_MAVEN_REPO"
EOF
  echo "[gcp] Created: configuration/registry_definitions/$GCP_REGDEF_NAME.yaml"
}

create_aws &
create_gcp &
wait
echo "Both registry definition files created in parallel"
ls configuration/registry_definitions/
```

## See also

- [Registry Definition v2.0 schema](/docs/envgene-objects.md#registry-definition-v20) - full field
  reference for Registry Definition v2.0 including all `authConfig` fields.
- [Artifact Definition v2.0 schema](/docs/envgene-objects.md#artifact-definition-v20) - full field
  reference for Artifact Definition v2.0.
- [Application Definition schema](/docs/envgene-objects.md#application-definition) - field reference
  for Application Definition v1.0 used for SD/DD artifact downloads.
- [Application and Registry Definition](/docs/features/app-reg-defs.md) - how AppDefs and RegDefs
  are rendered, resolved, and overridden in the pipeline.
- [Artifact resolution](/docs/features/artifact-resolution.md) - how EnvGene constructs Maven URLs
  and resolves SNAPSHOT versions for cloud registries.
- [Artifact downloading use cases](/docs/use-cases/artifact-downloading.md) - end-to-end use case
  scenarios for AWS CodeArtifact and GCP Artifact Registry.
- [Credential Encryption](/docs/how-to/credential-encryption.md) - how to encrypt credential values
  in `credentials.yml` before committing to the instance repository.
- [Using Docker Registries in EnvGene GitHub Workflow](/docs/how-to/docker-registry-configuration.md) -
  image registry configuration (Context B, separate from Maven artifact registries).
