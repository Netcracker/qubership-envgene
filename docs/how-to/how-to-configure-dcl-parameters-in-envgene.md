# How to configure DCL parameters in EnvGene

- [Template repository - reference the parameter set](#template-repository---reference-the-parameter-set)
- [Instance repository - configure the cloud passport](#instance-repository---configure-the-cloud-passport)
  - [Required `devops:` attributes](#required-devops-attributes)
  - [Architecture and parameter groups](#architecture-and-parameter-groups)
  - [Reference example](#reference-example)
- [Result - generated effective set](#result---generated-effective-set)

DCL (Deployment Configuration Lifecycle) is a GitLab pipeline that deploys Kubernetes applications
through ArgoCD.

EnvGene provides the DCL parameter values to the deployment tooling but does not own or define them.
This document covers the delivery mechanism - how to configure the cloud-passport so EnvGene can read
and distribute the values at generation time. For the meaning and constraints of individual DCL
parameters, see the DCL documentation.

The recommended approach is to provide DCL parameters through the EnvGene effective set as E2E
parameters. To configure this, complete the steps in each section below.

## Template repository - reference the parameter set

The `dcl-deploy-configuration` parameter set template is available in the
[starter set](/docs/cmdb-migration/templates/parameters) template repository. Copy
`dcl-deploy-configuration.yml.j2` from the starter template repository and place it at the following
location in the template repository:

```text
envgene-templates/templates/parameters/dcl-deploy-configuration.yml.j2
```

The template reads its values from the environment's cloud-passport at generation time. It does not
contain hardcoded environment-specific values.

To include the parameter set in the environment configuration, add `dcl-deploy-configuration` to the
`e2eParameterSets` list in `cloud.yml.j2`:

```yaml
# envgene-templates/templates/env_templates/apihub/cloud.yml.j2

e2eParameterSets:
  - "dcl-deploy-configuration"
```

If `dcl-deploy-configuration` is not listed in `e2eParameterSets`, EnvGene does not resolve it and the
DCL parameters do not appear in the generated effective set.

## Instance repository - configure the cloud passport

The `dcl-deploy-configuration` template reads most DCL connection parameters from the `devops:` section
of the environment's cloud-passport. Some parameters use template defaults (for example,
`DCL_CONFIG_ARGOCD_MAX_RETRY` and `DCL_CONFIG_ARGOCD_PROJECT`) or are derived from environment macros.
Add the `devops:` section to the environment's cloud-passport YAML file.

### Required `devops:` attributes

```yaml
# cloud-passport/<env-name>.yml

devops:
  ARGOCD_URL:      https://argocd-server.<cluster-host>
  ARGOCD_USER:     ${creds.get("<argocd-cred-key>").username}
  ARGOCD_PASSWORD: ${creds.get("<argocd-cred-key>").password}

  ARGOCD_GITLAB_URL:      https://<gitlab-host>/.../<dcl-repo>
  ARGOCD_GITLAB_USER:     ${creds.get("<git-cred-key>").username}
  ARGOCD_GITLAB_PASSWORD: ${creds.get("<git-cred-key>").password}

  CA_BUNDLE_CERTIFICATE: "<base64-encoded-ca-bundle>"
```

`ARGOCD_GITLAB_BRANCH` is optional and defaults to `master` if not set.

### Architecture and parameter groups

The `dcl-deploy-configuration` template is designed to split DCL parameters into groups that match the
environment's [deployment architecture](/docs/deployment-architecture.md) - CMDB, No-CMDB v1, No-CMDB
v2, and a common group shared by all three.

The current template version conditions on `cloud_passport.cloud.cmdb_url` to separate CMDB parameters
from non-CMDB parameters. This condition does not read `inventory.noCmdbVersion`, so the template cannot
distinguish No-CMDB v1 from No-CMDB v2, and does not implement the precedence rule (`noCmdbVersion`
takes precedence over `deployer`). When `inventory.deployer` is set and `inventory.noCmdbVersion` is
`v2`, the template classifies the environment as CMDB even though it is No-CMDB v2. A macro that
exposes `noCmdbVersion` inside the parameter set template is needed to implement the full four-group
split; no such macro is currently documented.

For the CMDB architecture, set `cmdb_url` in the `cloud:` section of the cloud-passport:

```yaml
# cloud-passport/<env-name>.yml

cloud:
  cmdb_url: https://<cmdb-host>
```

For No-CMDB architectures, leave `cloud.cmdb_url` unset.

> [!NOTE]
> The effective set carries `DCL_GIT_*` keys for non-sensitive GitLab connection parameters and
> `DCL_CONFIG_GITLAB_*` keys for the corresponding credentials. The naming prefix diverges between
> the two files even though both describe the same GitLab connection. Confirm with the DCL team
> whether a unified prefix is intended.

For more details on `inventory.noCmdbVersion` and `inventory.deployer`, see
[EnvGene configuration](/docs/envgene-configs.md#deployeryml).

### Reference example

```yaml
# cloud-passport/<env-name>.yml

cloud:
  CLOUD_API_HOST:    <cluster-api-host>
  CLOUD_PUBLIC_HOST: <cluster-public-host>
  CLOUD_PROTOCOL:    https

devops:
  ARGOCD_URL:      https://argocd-server.<cluster-public-host>
  ARGOCD_USER:     ${creds.get("<argocd-cred-key>").username}
  ARGOCD_PASSWORD: ${creds.get("<argocd-cred-key>").password}

  ARGOCD_GITLAB_URL:      https://<gitlab-host>/.../<dcl-repo>
  ARGOCD_GITLAB_USER:     ${creds.get("<git-cred-key>").username}
  ARGOCD_GITLAB_PASSWORD: ${creds.get("<git-cred-key>").password}

  CA_BUNDLE_CERTIFICATE: "<base64-encoded-ca-bundle>"
```

The credential entries referenced above must be defined in the environment's credentials file (for
example, `<env-name>-creds.yml`).

## Result - generated effective set

For No-CMDB environments, EnvGene writes the DCL parameters into two files under
`effective-set/pipeline/`.

`effective-set/pipeline/parameters.yaml` - non-sensitive DCL parameters as flat key-value pairs:

```yaml
DCL_CONFIG_ARGOCD_URL: https://argocd-server.<cluster-public-host>
DCL_CONFIG_ARGOCD_FAST_FAIL: false
DCL_CONFIG_ARGOCD_MAX_RETRY: '180'
DCL_CONFIG_ARGOCD_PROJECT: project
DCL_CONFIG_CMDB_URL: ''
DCL_CONFIG_CMDB_USER: ''
DCL_CONFIG_CMDB_PASSWORD: ''
DCL_CONFIG_SSL_CERTIFICATES_BUNDLE: <base64-encoded-ca-bundle>
DCL_GIT_BRANCH: master
DCL_GIT_URL: https://<gitlab-host>/.../<dcl-repo>
DCL_GIT_CREDENTIALS_ID: <env-name>-argocd-gitlab-cred
```

`effective-set/pipeline/credentials.yaml` - resolved credential values:

```yaml
DCL_CONFIG_ARGOCD_USER:     <resolved-username>
DCL_CONFIG_ARGOCD_PASSWORD: <resolved-password>
DCL_CONFIG_GITLAB_USER:     <resolved-username>
DCL_CONFIG_GITLAB_TOKEN:    <resolved-token>
```

> [!NOTE]
> All files under `effective-set/` are overwritten on each EnvGene generation run. Do not edit them
> directly. Make changes in the cloud-passport or the parameter set template.
