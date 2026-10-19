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
  - [`HELM_REPO_BASE_URL`](#helm_repo_base_url)

These are the parameters EnvGene reads from a Cloud's `e2eParameters`/`pipeline` (the `e2eParameters` block of
`cloud.yml`). Each entry names the EnvGene component that consumes it. For the RegDef v2 adapter parameters, how each
value maps into the synthesized RegDef v2 `authConfig`, and which combinations are mandatory, is described in
[`regdefv2_adapter`](/docs/technical-design/instance-pipeline/steps/regdefv2-adapter.md).

## `HELM_MAP_REPOSITORIES`

**Description**: Overrides the reconstructed Helm chart registry base URL, keyed by the Helm group repository name
(`helmAppConfig.helmGroupRepoName`). Lets an environment point chart downloads at a different registry without editing
the RegDef. See the
[`helm-map-repositories` input attribute](/docs/features/sbom-generation.md#sbom-generation-library-input-attributes).

**Consumer**: SBOM generation

**Example**:

```yaml
nc.helm.charts:
  url: https://mirror.example.com/helm
```

## `MAVEN_PROVIDER`

**Description**: Registry type - `nexus`, `artifactory`, `aws`, `azure`, or `gcp`. When it is `aws`, `azure`, or `gcp`,
the RegDef v2 adapter synthesizes a RegDef v2 with public cloud registry authentication.

**Consumer**: RegDef v2 adapter

**Example**: `aws`

## `PUB_REG_METHOD`

**Description**: Public registry auth method - `secret`, `assume_role`, `federation`, `service_account`, `oauth2`, or
`basic_auth`.

**Consumer**: RegDef v2 adapter

**Example**: `assume_role`

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

## `HELM_REPO_BASE_URL`

**Description**: Helm repository base URL. The RegDef v2 adapter writes it into the `helmConfig` and `helmAppConfig`
`repositoryDomainName` of the synthesized RegDef v2.

**Consumer**: RegDef v2 adapter

**Example**: `https://ops-portal.example.com/nexus/repository/nc.helm.charts`
