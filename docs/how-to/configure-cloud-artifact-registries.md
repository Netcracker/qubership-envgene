# Configuring cloud artifact registries for AWS and GCP

- [Configuring cloud artifact registries for AWS and GCP](#configuring-cloud-artifact-registries-for-aws-and-gcp)
  - [Two registry contexts in EnvGene](#two-registry-contexts-in-envgene)
  - [Prerequisites](#prerequisites)
  - [AWS CodeArtifact configuration](#aws-codeartifact-configuration)
    - [AWS-configuration: required permissions](#aws-configuration-required-permissions)
    - [AWS Step 1: Create the credential entry](#aws-step-1-create-the-credential-entry)
    - [AWS Step 2: Create the registry definition](#aws-step-2-create-the-registry-definition)
    - [AWS Step 3: Set the registry auth parameters](#aws-step-3-set-the-registry-auth-parameters)
    - [AWS Step 4: Reference the registry in an Artifact or Application Definition](#aws-step-4-reference-the-registry-in-an-artifact-or-application-definition)
    - [GitLab CI: pulling images from AWS ECR](#gitlab-ci-pulling-images-from-aws-ecr)
      - [Set CI/CD variables](#set-cicd-variables)
  - [GCP Artifact Registry configuration](#gcp-artifact-registry-configuration)
    - [GCP-side: required permissions](#gcp-side-required-permissions)
    - [GCP Step 1: Create the credential entry](#gcp-step-1-create-the-credential-entry)
    - [GCP Step 2: Create the registry definition](#gcp-step-2-create-the-registry-definition)
    - [GCP Step 3: Set the registry auth parameters](#gcp-step-3-set-the-registry-auth-parameters)
    - [GCP Step 4: Reference the registry in an Artifact or Application Definition](#gcp-step-4-reference-the-registry-in-an-artifact-or-application-definition)
  - [Placing configuration files](#placing-configuration-files)
  - [Supported auth methods reference](#supported-auth-methods-reference)
  - [See also](#see-also)

EnvGene downloads Maven artifacts ([Solution Descriptors](/docs/envgene-objects.md#solution-descriptor),
Deployment Descriptors, and environment templates) from external cloud registries like AWS CodeArtifact and
GCP Artifact Registry.

You describe the registry with a [Registry Definition v1.0](/docs/envgene-objects.md#registry-definition-v10) and set
the registry auth parameters in [Cloud](/docs/envgene-objects.md#cloud) `e2eParameters`. EnvGene builds the
authentication for the pipeline run from these two sources.

> [!IMPORTANT]
> **Pulling EnvGene Docker images from cloud registries (GAR) during pipeline execution is supported only
> in the GitHub workflow** via the `DOCKER_REGISTRY` and `DOCKER_CLOUD_REGISTRY_PROVIDER` variables.
> For GitLab CI pipelines, set `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` as masked CI/CD
> variables and configure the runner with the Amazon ECR credential helper -
> see [GitLab CI: pulling images from AWS ECR](#gitlab-ci-pulling-images-from-aws-ecr).
>
> **Publishing environment template build artifacts to external cloud registries (GAR, ECR) is not currently supported.**

## Two registry contexts in EnvGene

EnvGene uses the term "registry" in two distinct contexts. Keep them separate when you read
documentation or configure the system.

| Context                    | Purpose                                                        | Configured via                                                                                     |
|----------------------------|----------------------------------------------------------------|----------------------------------------------------------------------------------------------------|
| **A. Artifact registries** | Download Maven artifacts (SDs, DDs, and environment templates) | SDs and DDs: RegDef v1.0 and registry auth parameters. Environment templates: ArtDef v2.0          |
| **B. Image registries**    | Pull EnvGene container images during CI                        | GitHub repository variables: `DOCKER_REGISTRY`, `DOCKER_CLOUD_REGISTRY_PROVIDER`, and `GCP_SA_KEY` |

This guide covers Context A only. For image registry configuration (Context B), see
[Using Docker Registries in EnvGene GitHub Workflow](/docs/how-to/docker-registry-configuration.md).

## Prerequisites

- An instance repository with the EnvGene workflow installed.
- Write access to `configuration/regdefs/`, `configuration/credentials/`, and
  `environments/<cluster-name>/<env-name>/` in the instance repository.
- AWS or GCP credentials ready (see the provider-specific sections below).

## AWS CodeArtifact configuration

> [!WARNING]
> AWS CodeArtifact support is not tested end-to-end. The `authMethod: secret` implementation is
> present in code but has not been validated against a live CodeArtifact repository. Use with
> caution and report issues if encountered.

### AWS-configuration: required permissions

The IAM user or role whose access key you use must have the following CodeArtifact permissions on
the target domain and repository:

| Permission                              | Purpose                                         |
|-----------------------------------------|-------------------------------------------------|
| `codeartifact:GetAuthorizationToken`    | Obtain a temporary download token               |
| `codeartifact:GetRepositoryEndpoint`    | Resolve the Maven repository URL                |
| `codeartifact:ReadFromRepository`       | Download artifacts from the repository          |
| `sts:GetServiceBearerToken`             | Exchange credentials for an Authorization token |

To create an IAM user or role with these permissions and Create an access key pair, follow the official
AWS guides:

- [Create an IAM user](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_users_create.html)
- [CodeArtifact permissions reference](https://docs.aws.amazon.com/codeartifact/latest/ug/auth-and-access-control-permissions-reference.html)
- [Create an IAM access key](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_credentials_access-keys.html)

### AWS Step 1: Create the credential entry

Add an entry to the [Environment Credentials File](/docs/envgene-objects.md#environment-credentials-file)
`environments/<cluster-name>/<env-name>/Credentials/credentials.yml` in the instance repository:

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
>
> Add the credential entry before the first pipeline run. Otherwise the pipeline fails with
> `Credential for env aws-codeartifact-creds is not found in environment credentials.`

When you also download the environment template from this registry, add the same entry to
`configuration/credentials/credentials.yml`. The Artifact Definition in
[AWS Step 4](#aws-step-4-reference-the-registry-in-an-artifact-or-application-definition) reads it from there.

To encrypt the credential value, see
[Credential Encryption](/docs/how-to/credential-encryption.md).

### AWS Step 2: Create the registry definition

Create a Registry Definition v1.0 file, for example `configuration/regdefs/aws-codeartifact.yml`:

```yaml
name: "aws-codeartifact"
credentialsId: "aws-codeartifact-creds"
mavenConfig:
  repositoryDomainName: "https://my-domain-123456789012.d.codeartifact.us-east-1.amazonaws.com/maven/my-repo"
  targetSnapshot: "my-repo"
  targetStaging: "my-repo"
  targetRelease: "my-repo"
  snapshotGroup: "my-repo"
  releaseGroup: "my-repo"
dockerConfig:
  snapshotUri: "123456789012.dkr.ecr.us-east-1.amazonaws.com"
  stagingUri: "123456789012.dkr.ecr.us-east-1.amazonaws.com"
  releaseUri: "123456789012.dkr.ecr.us-east-1.amazonaws.com"
  groupUri: "123456789012.dkr.ecr.us-east-1.amazonaws.com"
  snapshotRepoName: "my-images"
  stagingRepoName: "my-images"
  releaseRepoName: "my-images"
  groupName: "my-images"
```

The Registry Definition gives the registry coordinates only. Authentication comes from the parameters in
[AWS Step 3](#aws-step-3-set-the-registry-auth-parameters). Do not add `authConfig` to this file. Otherwise EnvGene
ignores the registry auth parameters.

`credentialsId` is required, but EnvGene does not use it for AWS. The credential comes from `PUB_REG_KEY` and
`PUB_REG_SECRET`.

To find the `repositoryDomainName`, open the AWS CodeArtifact console, select your repository, and
copy the **Connection instructions - Maven** endpoint URL.

To add the file without a template, see
[Add an Application or Registry Definition without a template](/docs/how-to/app-reg-defs-add-without-template.md).

### AWS Step 3: Set the registry auth parameters

Create an [Environment Specific ParameterSet](/docs/envgene-objects.md#environment-specific-parameterset), for example
`environments/<cluster-name>/<env-name>/Inventory/parameters/registry-auth.yml`:

```yaml
name: "registry-auth"
parameters:
  MAVEN_PROVIDER: "aws"
  PUB_REG_METHOD: "secret"
  PUB_REG_KEY: "${creds.get('aws-codeartifact-creds').username}"
  PUB_REG_SECRET: "${creds.get('aws-codeartifact-creds').password}"
  PUB_REG_REGION: "us-east-1"
  PUB_REG_DOMAIN: "my-domain"
  PUB_REG_REPOSITORY: "my-repo"
```

All parameters above are mandatory for `aws` with `secret`. Write every value in quotes. A number without quotes is
ignored. For the description
of each parameter, see [EnvGene `e2eParameters`](/docs/e2e-parameters.md).

Reference the ParameterSet for the Cloud in the [Environment Inventory](/docs/envgene-configs.md#env_definitionyml):

```yaml
envTemplate:
  envSpecificE2EParamsets:
    cloud:
      - "registry-auth"
```

For a complete set of files, see the
[AWS environment sample](/docs/samples/cloud-artifact-registries/instance-repository/environments/cluster-01/aws-env/).

When the Registry Definition has `helmConfig` or `helmAppConfig`, also set
[`HELM_MAP_REPOSITORIES`](/docs/e2e-parameters.md#helm_map_repositories) for its `helmAppConfig.helmGroupRepoName`.
Without it, the pipeline fails with `'repositoryDomainName' is a required property`.

> [!NOTE]
> In a `LEGACY` pipeline, set [`ENV_BUILDER`](/docs/instance-pipeline-parameters.md#env_builder) to `true`. Otherwise
> the download from AWS or GCP fails.

### AWS Step 4: Reference the registry in an Artifact or Application Definition

**For SD/DD artifacts ([Application Definition v1.0](/docs/envgene-objects.md#application-definition) +
[Registry Definition v1.0](/docs/envgene-objects.md#registry-definition-v10)):**

```yaml
# configuration/appdefs/my-app.yml
name: "my-app"
registryName: "aws-codeartifact"
groupId: "com.example"
artifactId: "my-app"
```

**For environment templates ([Artifact Definition v2.0](/docs/envgene-objects.md#artifact-definition-v20)):**

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
> For SD and DD downloads, the authentication comes from the registry auth parameters and the AppDef references the
> registry by name. The environment template download is separate: it uses the `authConfig` inside the Artifact
> Definition's `registry` block and the credential from `configuration/credentials/credentials.yml`. The registry
> auth parameters do not apply to it.

### GitLab CI: pulling images from AWS ECR

To pull Docker images from AWS ECR in a GitLab CI pipeline, provide AWS credentials as masked
CI/CD variables. The GitLab Runner uses these variables together with the
[Amazon ECR credential helper](https://github.com/awslabs/amazon-ecr-credential-helper) to
authenticate automatically on each pipeline run.

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
> [GitLab Runner advanced configuration](https://docs.gitlab.com/runner/configuration/advanced-configuration/).

#### Set CI/CD variables

In **Settings → CI/CD → Variables**, add the following masked variables:

| Variable                | Description                |
|-------------------------|----------------------------|
| `AWS_ACCESS_KEY_ID`     | IAM user access key ID     |
| `AWS_SECRET_ACCESS_KEY` | IAM user secret access key |

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

- [Create and manage service accounts](https://docs.cloud.google.com/iam/docs/service-accounts-create)
- [Grant an IAM role on an Artifact Registry repository](https://cloud.google.com/artifact-registry/docs/access-control#grant-repo)
- [Create and manage service account keys](https://docs.cloud.google.com/iam/docs/keys-create-delete)

### GCP Step 1: Create the credential entry

Add an entry to the [Environment Credentials File](/docs/envgene-objects.md#environment-credentials-file)
`environments/<cluster-name>/<env-name>/Credentials/credentials.yml` in the instance repository:

```yaml
gcp-artifact-registry-key:
  type: secret
  data:
    secret: |
      {
        "type": "service_account",
        "project_id": "my-project",
        "private_key_id": "key-id-placeholder",
        "private_key": "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n",
        "client_email": "envgene-artifact-reader@my-project.iam.gserviceaccount.com",
        "client_id": "123456789",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token"
      }
```

The `secret` field must contain the complete JSON content of the GCP service account key file.
Paste the full content of `sa-key.json` as the value.

> [!IMPORTANT]
> Add the credential entry before the first pipeline run. Otherwise the pipeline fails with
> `Credential for env gcp-artifact-registry-key is not found in environment credentials.`

When you also download the environment template from this registry, add the same entry to
`configuration/credentials/credentials.yml`.

To encrypt the credential value, see
[Credential Encryption](/docs/how-to/credential-encryption.md).

### GCP Step 2: Create the registry definition

Create a Registry Definition v1.0 file, for example `configuration/regdefs/gcp-artifact-registry.yml`:

```yaml
name: "gcp-artifact-registry"
credentialsId: "gcp-artifact-registry-key"
mavenConfig:
  repositoryDomainName: "https://us-central1-maven.pkg.dev/my-project/my-maven-repo"
  targetSnapshot: "my-maven-repo"
  targetStaging: "my-maven-repo"
  targetRelease: "my-maven-repo"
  snapshotGroup: "my-maven-repo"
  releaseGroup: "my-maven-repo"
dockerConfig:
  snapshotUri: "us-central1-docker.pkg.dev/my-project"
  stagingUri: "us-central1-docker.pkg.dev/my-project"
  releaseUri: "us-central1-docker.pkg.dev/my-project"
  groupUri: "us-central1-docker.pkg.dev/my-project"
  snapshotRepoName: "my-images"
  stagingRepoName: "my-images"
  releaseRepoName: "my-images"
  groupName: "my-images"
```

The Registry Definition gives the registry coordinates only. Authentication comes from the parameters in
[GCP Step 3](#gcp-step-3-set-the-registry-auth-parameters). Do not add `authConfig` to this file. Otherwise EnvGene
ignores the registry auth parameters.
`credentialsId` is required, but EnvGene does not use it for GCP. The credential comes from `PUB_REG_SECRET`.

To find the `repositoryDomainName`, open the GCP Artifact Registry console, select your Maven
repository, and copy the endpoint URL from the repository details panel.

### GCP Step 3: Set the registry auth parameters

Create an [Environment Specific ParameterSet](/docs/envgene-objects.md#environment-specific-parameterset), for example
`environments/<cluster-name>/<env-name>/Inventory/parameters/registry-auth.yml`:

```yaml
name: "registry-auth"
parameters:
  MAVEN_PROVIDER: "gcp"
  PUB_REG_METHOD: "service_account"
  PUB_REG_SECRET: "${creds.get('gcp-artifact-registry-key').secret}"
  PUB_REG_PROJECT: "123456789012"
  PUB_REG_SA_EMAIL: "envgene-artifact-reader@my-project.iam.gserviceaccount.com"
```

`MAVEN_PROVIDER`, `PUB_REG_METHOD`, and `PUB_REG_SECRET` are mandatory for `gcp` with `service_account`.
`PUB_REG_PROJECT` and `PUB_REG_SA_EMAIL` are optional. Write every value in quotes. A number without quotes is ignored.
For the description of each parameter, see
[EnvGene `e2eParameters`](/docs/e2e-parameters.md).

Reference the ParameterSet in `envTemplate.envSpecificE2EParamsets.cloud` of the Environment Inventory, as in
[AWS Step 3](#aws-step-3-set-the-registry-auth-parameters). The Helm and `ENV_BUILDER` rules from AWS Step 3 apply
to GCP too.

### GCP Step 4: Reference the registry in an Artifact or Application Definition

**For SD/DD artifacts ([Application Definition v1.0](/docs/envgene-objects.md#application-definition) +
[Registry Definition v1.0](/docs/envgene-objects.md#registry-definition-v10)):**

```yaml
# configuration/appdefs/my-app.yml
name: "my-app"
registryName: "gcp-artifact-registry"
groupId: "com.example"
artifactId: "my-app"
```

**For environment templates ([Artifact Definition v2.0](/docs/envgene-objects.md#artifact-definition-v20)):**

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
  mavenConfig:
    authConfig: "gcp-auth"
    repositoryDomainName: "https://us-central1-maven.pkg.dev/my-project/my-maven-repo"
```

The note in [AWS Step 4](#aws-step-4-reference-the-registry-in-an-artifact-or-application-definition) applies to GCP
too.

## Placing configuration files

| File                                       | Path                                                           | Scope            |
|--------------------------------------------|----------------------------------------------------------------|------------------|
| Registry Definition                        | `configuration/regdefs/<name>.yml`                             | All environments |
| ParameterSet with registry auth parameters | `environments/<cluster>/<env>/Inventory/parameters/<name>.yml` | One environment  |
| Credential for registry auth parameters    | `environments/<cluster>/<env>/Credentials/credentials.yml`     | One environment  |
| Credential for the Artifact Definition     | `configuration/credentials/credentials.yml`                    | All environments |

Use the `.yml` extension. A `.yaml` file does not override a Registry Definition from the template.

EnvGene reads Registry Definitions from the root `configuration/regdefs/` only. To use a different registry account
per environment, keep one Registry Definition and set different registry auth parameters in each environment.

## Supported auth methods reference

For SD and DD downloads, set the provider in `MAVEN_PROVIDER` and the method in `PUB_REG_METHOD`:

| `MAVEN_PROVIDER` | `PUB_REG_METHOD`  | Mandatory parameters                                                                      |
|------------------|-------------------|-------------------------------------------------------------------------------------------|
| `aws`            | `secret`          | `PUB_REG_KEY`, `PUB_REG_SECRET`, `PUB_REG_REGION`, `PUB_REG_DOMAIN`, `PUB_REG_REPOSITORY` |
| `gcp`            | `service_account` | `PUB_REG_SECRET`                                                                          |
| `aws`, `gcp`     | `anonymous`       | none                                                                                      |

## See also

- [EnvGene `e2eParameters`](/docs/e2e-parameters.md) - description of every registry auth parameter.
- [Cloud artifact registries samples](/docs/samples/cloud-artifact-registries/) - the files from this guide for AWS
  and GCP.
- [Registry Definition v1.0 schema](/docs/envgene-objects.md#registry-definition-v10) - full field reference for
  Registry Definition v1.0.
- [Artifact Definition v2.0 schema](/docs/envgene-objects.md#artifact-definition-v20) - full field reference for Artifact Definition v2.0.
- [Application Definition schema](/docs/envgene-objects.md#application-definition) - field reference for Application Definition v1.0 used for SD/DD artifact downloads.
- [Application and Registry Definition](/docs/features/app-reg-defs.md) - how AppDefs and RegDefs are rendered, resolved, and overridden in the pipeline.
- [Artifact resolution](/docs/features/artifact-resolution.md) - how EnvGene constructs Maven URLs and resolves SNAPSHOT versions for cloud registries.
- [Artifact downloading use cases](/docs/use-cases/artifact-downloading.md) - end-to-end use case scenarios for AWS CodeArtifact and GCP Artifact Registry.
- [Credential Encryption](/docs/how-to/credential-encryption.md) - how to encrypt credential values in `credentials.yml` before committing to the instance repository.
- [Using Docker Registries in EnvGene GitHub Workflow](/docs/how-to/docker-registry-configuration.md) - image registry configuration (Context B, separate from Maven artifact registries).
