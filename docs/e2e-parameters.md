# EnvGene `e2eParameters`

- [EnvGene `e2eParameters`](#envgene-e2eparameters)
  - [`HELM_MAP_REPOSITORIES`](#helm_map_repositories)
  - [`MAVEN_PROVIDER`](#maven_provider)
  - [`PUB_REG_METHOD`](#pub_reg_method)
  - [`PUB_REG_KEY`](#pub_reg_key)
  - [`PUB_REG_SECRET`](#pub_reg_secret)
  - [`PUB_REG_REGION`](#pub_reg_region)
  - [`PUB_REG_DOMAIN`](#pub_reg_domain)
  - [`PUB_REG_REPOSITORY`](#pub_reg_repository)
  - [`PUB_REG_ROLE_ARN`](#pub_reg_role_arn)
  - [`PUB_REG_ROLE_SESSION_PREFIX`](#pub_reg_role_session_prefix)
  - [`PUB_REG_PROJECT`](#pub_reg_project)
  - [`PUB_REG_PROVIDER_ID`](#pub_reg_provider_id)
  - [`PUB_REG_POOL_ID`](#pub_reg_pool_id)
  - [`PUB_REG_SA_EMAIL`](#pub_reg_sa_email)
  - [`PUB_REG_OIDC_URL`](#pub_reg_oidc_url)
  - [`PUB_REG_OIDC_METHOD`](#pub_reg_oidc_method)
  - [`PUB_REG_OIDC_CUSTOM_PARAM`](#pub_reg_oidc_custom_param)
  - [`PUB_REG_OIDC_PROVIDER`](#pub_reg_oidc_provider)
  - [`PUB_REG_OIDC_CLIENT_ID`](#pub_reg_oidc_client_id)
  - [`PUB_REG_OIDC_CLIENT_SECRET`](#pub_reg_oidc_client_secret)
  - [`PUB_REG_TENANT_ID`](#pub_reg_tenant_id)
  - [`PUB_REG_ACR_RESOURCE`](#pub_reg_acr_resource)
  - [`PUB_REG_ACR_NAME`](#pub_reg_acr_name)
  - [`PUB_REG_AA_RESOURCE`](#pub_reg_aa_resource)
  - [`NON_PUB_REG_METHOD`](#non_pub_reg_method)
  - [`NON_PUB_REG_KEY`](#non_pub_reg_key)
  - [`NON_PUB_REG_SECRET`](#non_pub_reg_secret)
  - [`DCL_GIT_URL`](#dcl_git_url)
  - [`DCL_GIT_BRANCH`](#dcl_git_branch)
  - [`DCL_CONFIG_GITLAB_USER`](#dcl_config_gitlab_user)
  - [`DCL_CONFIG_GITLAB_TOKEN`](#dcl_config_gitlab_token)
  - [`DCL_CONFIG_SOPS_DCL2ARGO_AGE_PUBLIC_KEY`](#dcl_config_sops_dcl2argo_age_public_key)

These are the parameters EnvGene reads from a Cloud's `e2eParameters`/`pipeline` (the `e2eParameters` block of
`cloud.yml`). Each entry names the EnvGene component that consumes it. For the RegDef v2 adapter parameters, how each
value maps into the synthesized RegDef v2 `authConfig`, and which combinations are mandatory, is described in
[`regdefv2_adapter`](/docs/technical-design/instance-pipeline/steps/regdefv2-adapter.md).

## `HELM_MAP_REPOSITORIES`

**Description**: Overrides the reconstructed Helm chart registry base URL, keyed by the Helm group repository name
(`helmAppConfig.helmGroupRepoName`). Lets an environment point chart downloads at a different registry without editing
the RegDef. See
[`full_chart_name`](/docs/features/sbom-generation.md#full_chart_name).

**Consumer**: SBOM generation, artifact download from AWS and GCP. The pipeline fails when the value is not a map of
objects with a string `url`.

**Example**:

```yaml
nc.helm.charts:
  url: https://mirror.example.com/helm
```

## `MAVEN_PROVIDER`

**Description**: Registry type - `nexus`, `artifactory`, `aws`, `azure`, or `gcp`. When it is `aws` or `gcp`, EnvGene
authenticates to the registry with the `PUB_REG_*` parameters. When it is not set, EnvGene ignores the registry auth
parameters.

**Consumer**: RegDef v2 adapter

**Example**: `aws`

## `PUB_REG_METHOD`

**Description**: Public registry auth method - `secret`, `assume_role`, `federation`, `service_account`, `oauth2`,
`basic_auth`, or `anonymous`. Mandatory when `MAVEN_PROVIDER` is `aws` or `gcp`. For `aws`, EnvGene supports
`secret` and `anonymous`. For `gcp`, it supports `service_account` and `anonymous`. With any other value, the pipeline
fails.

**Consumer**: RegDef v2 adapter

**Example**: `secret`

## `PUB_REG_KEY`

**Description**: Public registry access key or client ID.

**Consumer**: RegDef v2 adapter

## `PUB_REG_SECRET`

**Description**: Public registry secret key, client secret, or service account JSON.

**Consumer**: RegDef v2 adapter

## `PUB_REG_REGION`

**Description**: AWS region.

**Consumer**: RegDef v2 adapter

## `PUB_REG_DOMAIN`

**Description**: AWS CodeArtifact domain.

**Consumer**: RegDef v2 adapter

## `PUB_REG_REPOSITORY`

**Description**: AWS CodeArtifact repository.

**Consumer**: RegDef v2 adapter

## `PUB_REG_ROLE_ARN`

**Description**: AWS role ARN. Used with the `assume_role` method only.

**Consumer**: RegDef v2 adapter

**Example**: `arn:aws:iam::123456789012:role/YourRole`

## `PUB_REG_ROLE_SESSION_PREFIX`

**Description**: AWS session name prefix. Used with the `assume_role` method only.

**Consumer**: RegDef v2 adapter

## `PUB_REG_PROJECT`

**Description**: GCP project number.

**Consumer**: RegDef v2 adapter

## `PUB_REG_PROVIDER_ID`

**Description**: GCP workload identity provider ID. Used with the `federation` method only.

**Consumer**: RegDef v2 adapter

## `PUB_REG_POOL_ID`

**Description**: GCP workload identity pool ID. Used with the `federation` method only.

**Consumer**: RegDef v2 adapter

## `PUB_REG_SA_EMAIL`

**Description**: GCP service account email.

**Consumer**: RegDef v2 adapter

## `PUB_REG_OIDC_URL`

**Description**: GCP external OIDC server URL. Used with the `federation` method only.

**Consumer**: RegDef v2 adapter

## `PUB_REG_OIDC_METHOD`

**Description**: GCP external OIDC auth method. Used with the `federation` method only.

**Consumer**: RegDef v2 adapter

## `PUB_REG_OIDC_CUSTOM_PARAM`

**Description**: GCP extra OIDC request parameters. Used with the `federation` method only.

**Consumer**: RegDef v2 adapter

## `PUB_REG_OIDC_PROVIDER`

**Description**: GCP OIDC provider. Used by the dpg reader only.

**Consumer**: RegDef v2 adapter

## `PUB_REG_OIDC_CLIENT_ID`

**Description**: GCP OIDC client ID. Used by the dpg reader only.

**Consumer**: RegDef v2 adapter

## `PUB_REG_OIDC_CLIENT_SECRET`

**Description**: GCP OIDC client secret. Used by the dpg reader only.

**Consumer**: RegDef v2 adapter

## `PUB_REG_TENANT_ID`

**Description**: Azure AD tenant ID.

**Consumer**: RegDef v2 adapter

## `PUB_REG_ACR_RESOURCE`

**Description**: Azure Container Registry target resource.

**Consumer**: RegDef v2 adapter

## `PUB_REG_ACR_NAME`

**Description**: Azure Container Registry name.

**Consumer**: RegDef v2 adapter

## `PUB_REG_AA_RESOURCE`

**Description**: Azure Artifacts resource.

**Consumer**: RegDef v2 adapter

## `NON_PUB_REG_METHOD`

**Description**: Non-public registry auth method - `none` or `basic_auth`.

**Consumer**: RegDef v2 adapter

## `NON_PUB_REG_KEY`

**Description**: Non-public registry user. Used with the `basic_auth` method only.

**Consumer**: RegDef v2 adapter

## `NON_PUB_REG_SECRET`

**Description**: Non-public registry password. Used with the `basic_auth` method only.

**Consumer**: RegDef v2 adapter

## `DCL_GIT_URL`

**Description**: URL of the external GitLab repository the Effective Set is published to in the GitLab-deploy flow. See
[Publishing in the GitLab-deploy flow](/docs/features/effective-set-generation.md#publishing-in-the-gitlab-deploy-flow).

**Consumer**: Effective Set external export (`argocd-dpg`)

## `DCL_GIT_BRANCH`

**Description**: Target branch in the external GitLab repository. Defaults to `master` when not set.

**Consumer**: Effective Set external export (`argocd-dpg`)

## `DCL_CONFIG_GITLAB_USER`

**Description**: Username for the external GitLab repository credentials.

**Consumer**: Effective Set external export (`argocd-dpg`)

## `DCL_CONFIG_GITLAB_TOKEN`

**Description**: Token or password for the external GitLab repository credentials.

**Consumer**: Effective Set external export (`argocd-dpg`)

## `DCL_CONFIG_SOPS_DCL2ARGO_AGE_PUBLIC_KEY`

**Description**: Public key of a key pair that Argo CD owns. When set, EnvGene adds it to the SOPS recipients so
the Effective Set is encrypted for Argo CD as well as for `PUBLIC_AGE_KEYS`. EnvGene reads it from
`effective-set/pipeline/parameters.yaml` after it generates the Effective Set. If the parameter is missing or
empty, EnvGene logs a warning and encrypts with `PUBLIC_AGE_KEYS` only. EnvGene skips this step when `crypt` is
`false`. Set it per Cloud. The private half, `DCL_CONFIG_SOPS_DCL2ARGO_AGE_PRIVATE_KEY`, is held on the Argo CD
side and is not an EnvGene parameter. For why EnvGene uses a separate key pair and the setup steps, see
[Letting Argo CD decrypt the Effective Set](/docs/features/credential-encryption.md#letting-argo-cd-decrypt-the-effective-set)
and the [how-to](/docs/how-to/credential-encryption.md#let-argo-cd-decrypt-the-effective-set).

**Consumer**: Effective Set encryption with SOPS

**Example**: `age1abc123...`
