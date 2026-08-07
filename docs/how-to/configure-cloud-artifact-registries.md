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
  - [GCP Artifact Registry configuration](#gcp-artifact-registry-configuration)
    - [GCP-side: required permissions](#gcp-side-required-permissions)
    - [Step 1: Create the credential entry](#step-1-create-the-credential-entry-1)
    - [Step 2: Create the registry definition](#step-2-create-the-registry-definition-1)
    - [Step 3: Reference the registry in an Artifact or Application Definition](#step-3-reference-the-registry-in-an-artifact-or-application-definition-1)
    - [GCP authentication flow](#gcp-authentication-flow)
  - [Placing configuration files](#placing-configuration-files)
  - [Supported auth methods reference](#supported-auth-methods-reference)
  - [Troubleshooting](#troubleshooting)

EnvGene downloads Maven artifacts (Solution Descriptors, Deployment Descriptors, and environment
templates) from AWS CodeArtifact and GCP Artifact Registry using Registry Definition v2.0 with an
`authConfig` block. This guide walks through each provider step by step.

## Two registry contexts in EnvGene

EnvGene uses the term "registry" in two distinct contexts. Keep them separate when you read
documentation or configure the system.

| Context                  | Purpose                                              | Configured via                                                              |
|--------------------------|------------------------------------------------------|-----------------------------------------------------------------------------|
| A. Artifact registries   | Download Maven artifacts (SD, DD, env templates)     | RegDef v2.0 or ArtDef v2.0 with `authConfig`                               |
| B. Image registries      | Pull EnvGene's own container images in CI            | GitHub repository variables (`DOCKER_REGISTRY`, `DOCKER_CLOUD_REGISTRY_PROVIDER`, `GCP_SA_KEY`) |

This guide covers Context A only. For image registry configuration (Context B), see
[Using Docker Registries in EnvGene GitHub Workflow](/docs/how-to/docker-registry-configuration.md).

## Prerequisites

- An instance repository with the EnvGene workflow installed.
- Write access to `configuration/registry_definitions/` and `configuration/credentials/` in the
  instance repository.
- AWS or GCP credentials ready (see the provider-specific sections below).

## AWS CodeArtifact configuration

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

```yaml
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

To encrypt the credential value, see
[Credential Encryption](/docs/how-to/credential-encryption.md).

### Step 2: Create the registry definition

Create a Registry Definition v2.0 file, for example
`configuration/registry_definitions/aws-codeartifact.yaml`:

```yaml
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
| `authConfig.<key>.awsRegion`       | AWS region where the CodeArtifact domain is hosted (for example, `us-east-1`)  |
| `authConfig.<key>.awsDomain`       | CodeArtifact domain name, without the account suffix                            |
| `mavenConfig.authConfig`           | Must match the auth config key defined above (for example, `aws-auth`)          |
| `mavenConfig.repositoryDomainName` | Full Maven endpoint URL from the AWS CodeArtifact console                       |

To find the `repositoryDomainName`, open the AWS CodeArtifact console, select your repository, and
copy the **Connection instructions - Maven** endpoint URL.

### Step 3: Reference the registry in an Artifact or Application Definition

**For SD/DD artifacts (Application Definition v1.0 + Registry Definition v2.0):**

```yaml
# configuration/app_definitions/my-app.yaml
name: "my-app"
registryName: "aws-codeartifact"
groupId: "com.example"
artifactId: "my-app"
```

**For environment templates (Artifact Definition v2.0):**

```yaml
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

### Step 1: Create the credential entry

Add an entry to `configuration/credentials/credentials.yml` in the instance repository:

```yaml
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

The `secret` field must contain the complete JSON content of the GCP service account key file.
Paste the full content of `sa-key.json` as the value.

To encrypt the credential value, see
[Credential Encryption](/docs/how-to/credential-encryption.md).

### Step 2: Create the registry definition

Create a Registry Definition v2.0 file, for example
`configuration/registry_definitions/gcp-artifact-registry.yaml`:

```yaml
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

| Field                              | Description                                                                       |
|------------------------------------|-----------------------------------------------------------------------------------|
| `authConfig.<key>.provider`        | Must be `gcp`                                                                     |
| `authConfig.<key>.authMethod`      | Must be `service_account` (the only implemented GCP auth method)                  |
| `authConfig.<key>.credentialsId`   | Must match the key in `credentials.yml`                                           |
| `authConfig.<key>.gcpRegion`       | GCP region where the repository is hosted (for example, `us-central1`)            |
| `mavenConfig.authConfig`           | Must match the auth config key defined above (for example, `gcp-auth`)            |
| `mavenConfig.repositoryDomainName` | Full Maven endpoint URL: `https://REGION-maven.pkg.dev/PROJECT_ID/REPOSITORY_NAME` |

To find the `repositoryDomainName`, open the GCP Artifact Registry console, select your Maven
repository, and copy the endpoint URL from the repository details panel.

### Step 3: Reference the registry in an Artifact or Application Definition

**For SD/DD artifacts (Application Definition v1.0 + Registry Definition v2.0):**

```yaml
# configuration/app_definitions/my-app.yaml
name: "my-app"
registryName: "gcp-artifact-registry"
groupId: "com.example"
artifactId: "my-app"
```

**For environment templates (Artifact Definition v2.0):**

```yaml
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

| Level           | Path                                                                      | Scope                        |
|-----------------|---------------------------------------------------------------------------|------------------------------|
| Root            | `configuration/registry_definitions/<name>.yaml`                          | All environments             |
| Per-environment | `environments/<cluster>/<env>/configuration/registry_definitions/<name>.yaml` | This environment only    |

Credentials follow the same pattern:

| Level           | Path                                                            |
|-----------------|-----------------------------------------------------------------|
| Root            | `configuration/credentials/credentials.yml`                     |
| Per-environment | `environments/<cluster>/<env>/configuration/credentials/credentials.yml` |

Use root-level placement for registries shared across environments. Use per-environment placement
when different environments use different registries or accounts.

## Supported auth methods reference

| Provider       | Auth method        | Implemented       | Credential type    | Credential fields                                  |
|----------------|--------------------|-------------------|--------------------|----------------------------------------------------|
| `aws`          | `secret`           | Yes               | `usernamePassword` | `username` = access key ID, `password` = secret key |
| `aws`          | `assume_role`      | No (raises error) | -                  | -                                                  |
| `gcp`          | `service_account`  | Yes               | `secret`           | `secret` = full JSON of GCP service account key    |
| `gcp`          | `federation`       | No (raises error) | -                  | -                                                  |
| `nexus`        | `user_pass`        | Yes               | `usernamePassword` | `username`, `password`                             |
| `artifactory`  | `user_pass`        | Yes               | `usernamePassword` | `username`, `password`                             |
| any            | `anonymous`        | Yes               | none               | -                                                  |

> [!WARNING]
> The `assume_role` (AWS) and `federation` (GCP) auth methods appear in the schema but are not
> implemented. Using them causes a runtime error. Use `secret` for AWS and `service_account` for
> GCP.

## Troubleshooting

**"AWS secret auth requires both username and password in credentials"**

The credential type is wrong. AWS requires `type: usernamePassword` - not `type: secret`. Check
that your `credentials.yml` entry matches the example in
[Step 1: Create the credential entry](#step-1-create-the-credential-entry).

**"GCP service_account requires credential with 'secret' field containing SA JSON key"**

The credential is missing the `secret` field, or the type is not `secret`. Check that your
`credentials.yml` entry uses `type: secret` with `data.secret` containing the full service account
JSON.

**"GCP service account key must be valid JSON"**

The value in `data.secret` is not valid JSON. Paste the raw content of the service account key
file. Do not base64-encode or otherwise transform it.

**"AuthConfig 'X' not found in registry 'Y'"**

The `mavenConfig.authConfig` value in your RegDef or ArtDef does not match any key under
`authConfig`. The value is case-sensitive - check for typos at both ends.

**Credential not found**

The `credentialsId` in your `authConfig` block does not match any top-level key in
`credentials.yml`. Check the spelling at both ends.

**AWS token request fails with "access denied"**

The IAM user does not have `codeartifact:GetAuthorizationToken` or `sts:GetServiceBearerToken`
permissions. Review the policy in
[AWS-side: required permissions](#aws-side-required-permissions).

**GCP returns 403 Forbidden on artifact download**

The service account does not have `roles/artifactregistry.reader` on the target repository. Run
the `gcloud artifacts repositories add-iam-policy-binding` command from
[GCP-side: required permissions](#gcp-side-required-permissions).
