# Template Macros

- [Template Macros](#template-macros)
  - [Jinja Macros](#jinja-macros)
    - [`templates_dir`](#templates_dir)
    - [`current_env.name`](#current_envname)
    - [`current_env.tenant`](#current_envtenant)
    - [`current_env.cloud`](#current_envcloud)
    - [`current_env.cloudNameWithCluster`](#current_envcloudnamewithcluster)
    - [`current_env.cmdb_name`](#current_envcmdb_name)
    - [`current_env.cmdb_url`](#current_envcmdb_url)
    - [`current_env.description`](#current_envdescription)
    - [`current_env.owners`](#current_envowners)
    - [`current_env.env_template`](#current_envenv_template)
    - [`current_env.additionalTemplateVariables`](#current_envadditionaltemplatevariables)
    - [`current_env.cloud_passport`](#current_envcloud_passport)
    - [`current_env.solution_structure`](#current_envsolution_structure)
    - [`current_env.cluster.cloud_api_protocol`](#current_envclustercloud_api_protocol)
    - [`current_env.cluster.cloud_api_url`](#current_envclustercloud_api_url)
    - [`current_env.cluster.cloud_api_port`](#current_envclustercloud_api_port)
    - [`current_env.cluster.cloud_public_url`](#current_envclustercloud_public_url)
  - [AppDef/RegDef macros](#appdefregdef-macros)
    - [`appdefs.overrides`](#appdefsoverrides)
    - [`regdefs.overrides`](#regdefsoverrides)
    - [`app_lookup_key`](#app_lookup_key)
    - [`env`](#env)
  - [Calculator CLI macros](#calculator-cli-macros)
    - [`APPLICATION_NAME`](#application_name)
    - [`NAMESPACE`](#namespace)
    - [`CLOUDNAME`](#cloudname)
    - [`TENANTNAME`](#tenantname)
    - [`CLOUD_API_HOST`](#cloud_api_host)
    - [`CLOUD_PRIVATE_HOST`](#cloud_private_host)
    - [`CLOUD_PUBLIC_HOST`](#cloud_public_host)
    - [`CLOUD_PROTOCOL`](#cloud_protocol)
    - [`CLOUD_API_PORT`](#cloud_api_port)
    - [`PRIVATE_GATEWAY_URL`](#private_gateway_url)
    - [`PUBLIC_GATEWAY_URL`](#public_gateway_url)
    - [`API_DBAAS_ADDRESS`](#api_dbaas_address)
    - [`DBAAS_AGGREGATOR_ADDRESS`](#dbaas_aggregator_address)
    - [`DBAAS_AGGREGATOR_USERNAME`](#dbaas_aggregator_username)
    - [`DBAAS_AGGREGATOR_PASSWORD`](#dbaas_aggregator_password)
    - [`DBAAS_ENABLED`](#dbaas_enabled)
    - [`MAAS_INTERNAL_ADDRESS`](#maas_internal_address)
    - [`MAAS_EXTERNAL_ROUTE`](#maas_external_route)
    - [`MAAS_CREDENTIALS_USERNAME`](#maas_credentials_username)
    - [`MAAS_CREDENTIALS_PASSWORD`](#maas_credentials_password)
    - [`MAAS_ENABLED`](#maas_enabled)
    - [`VAULT_ADDR`](#vault_addr)
    - [`PUBLIC_VAULT_URL`](#public_vault_url)
    - [`VAULT_TOKEN`](#vault_token)
    - [`VAULT_ENABLED`](#vault_enabled)
    - [`CONSUL_URL`](#consul_url)
    - [`CONSUL_PUBLIC_URL`](#consul_public_url)
    - [`CONSUL_ADMIN_TOKEN`](#consul_admin_token)
    - [`CONSUL_ENABLED`](#consul_enabled)
  - [Credential Macro](#credential-macro)
  - [Deprecated Macros](#deprecated-macros)
    - [Deprecated Jinja Macros](#deprecated-jinja-macros)
      - [`environment.environmentName`](#environmentenvironmentname)
      - [`tenant`](#tenant)
      - [`cloud`](#cloud)
      - [`deployer`](#deployer)
    - [Deprecated Credential Macros](#deprecated-credential-macros)
      - [`${envgene.creds.get('<cred-id>').username|password|secret}`](#envgenecredsgetcred-idusernamepasswordsecret)

This documentation provides a list of macros that can be used in environment templates and environment-specific parameter sets.

## Jinja Macros

These Jinja macros are rendered at the stage of [Environment Instance](/docs/envgene-objects.md#environment-instance-objects) generation and are present in it as rendered values.

The usage rules for these macros are limited by the Jinja engine.

### `templates_dir`

---
**Description:** Absolute path to the templates directory. Automatically generated as either:

- `${CI_PROJECT_DIR}/templates/` (for GitLab)
- `${GITHUB_WORKSPACE}/templates/` (for GitHub)

using the respective platform's CI variables. This macro is used in [Template Descriptor](/docs/envgene-objects.md#template-descriptor) to include solution component templates, such as [Tenant](/docs/envgene-objects.md#tenant-template), [Cloud](/docs/envgene-objects.md#cloud-template) and [Namespace](/docs/envgene-objects.md#namespace-template) templates

**Type:** string

**Default Value:**

- `${CI_PROJECT_DIR}/templates/` (for GitLab)
- `${GITHUB_WORKSPACE}/templates/` (for GitHub)

**Basic usage:**

```yaml
tenant: "{{ templates_dir }}/env_templates/composite/tenant.yml.j2"
```

**Usage in sample:** [Sample](/docs/samples/templates/env_templates/simple.yaml)

### `current_env.name`

---
**Description:** The name of the Environment being generated. Primarily sourced from `inventory.environmentName` in the [Environment Inventory](/docs/envgene-configs.md#env_definitionyml). Falls back to `<environmentName>` folder name in the path `/environments/<clusterName>/<environmentName>/` of the Environment for which the generation is being executed.

**Type:** string

**Default Value:** `<environmentName>` from the Environment path structure

**Basic usage:**

```yaml
name: "{{current_env.name }}-oss" 
```

**Usage in sample:** [Sample](/docs/samples/templates/env_templates/composite/namespaces/oss.yml.j2)

### `current_env.tenant`

---
**Description:** Name of Tenant for environment. The value is obtained from `inventory.tenantName` in the [Environment Inventory](/docs/envgene-configs.md#env_definitionyml).

**Type:** string

**Default Value:** `""`

**Basic usage:**

```yaml
name: "{{ current_env.tenant }}"
```

**Usage in sample:** [Sample](/docs/samples/templates/env_templates/composite/tenant.yml.j2)

### `current_env.cloud`

---
**Description:** Name of the Environment's Cloud. Primarily sourced from `inventory.cloudName` in [Environment Inventory](/docs/envgene-configs.md#env_definitionyml). Falls back to [`current_env.name`](#current_envname) with hyphens converted to underscores (`-` → `_`).

**Type:** string

**Default Value:** `current_env.name.replace("-","_")`

**Basic usage:**

```yaml
name: "{{ current_env.cloud }}"
```

**Usage in sample:** [Sample](/docs/samples/templates/env_templates/simple/cloud.yml.j2)

### `current_env.cloudNameWithCluster`

---
**Description:** Name of the Environment's Cloud incorporating cluster and environment names. Used to generate environment-specific Cloud names. Generated using these rules:

1. Uses `inventory.cloudName` value from [Environment Inventory](/docs/envgene-configs.md#env_definitionyml) if defined
2. When `inventory.cloudPassport` in [Environment Inventory](/docs/envgene-configs.md#env_definitionyml) if defined:  
   `(<inventory.cloudPassport> + '_' + <current_env.name>).replace("-", "_")`  
3. Otherwise combines:  
   `(<clusterName> + '_' + <current_env.name>).replace("-", "_")`

Notes:

- `current_env.name` refers to the [macro](#current_envname)
- `clusterName` is folder name in the path `/environments/<clusterName>/<environmentName>/` of the Environment for which the generation is being executed.

**Type:** string

**Default Value:** `(<clusterName> + '_' + <current_env.name>).replace("-", "_")`

**Basic usage:**

```yaml
name: "{{ current_env.cloudNameWithCluster }}"
```

**Usage in sample:** [Sample](/docs/samples/templates/env_templates/composite/cloud.yml.j2)

### `current_env.cmdb_name`

---
**Description:** Name of external CMDB system where the Environment Instance can be imported. Used by EnvGene extensions (not part of EnvGene Core) that implement integration with various CMDB systems. Value is obtained from `inventory.deployer` in the [Environment Inventory](/docs/envgene-configs.md#env_definitionyml).

**Type:** string

**Default Value:** None

**Basic usage:**

```yaml
CMDB-NAME: "{{ current_env.cmdb_name }}"
```

**Usage in sample:** TBD

### `current_env.cmdb_url`

---
**Description:** Name of external CMDB system where the Environment Instance can be imported. Used by EnvGene extensions (not part of EnvGene Core) that implement integration with various CMDB systems. Value is **calculated** from `inventory.deployer` in the [Environment Inventory](/docs/envgene-configs.md#env_definitionyml).

**Type:** string

**Default Value:** None

**Basic usage:**

```yaml
CMDB-URL: "{{ current_env.current_env.cmdb_url }}"
```

**Usage in sample:** TBD

### `current_env.description`

---
**Description:** Description of Environment. Value is obtained from `inventory.description` in the [Environment Inventory](/docs/envgene-configs.md#env_definitionyml).

**Type:** string

**Default Value:** `""`

**Basic usage:**

```yaml
description: "{{ current_env.description }}"
```

**Usage in sample:** [Sample](/docs/samples/templates/env_templates/simple/tenant.yml.j2)

### `current_env.owners`

---
**Description:** Owners of Environment. Value is obtained from `inventory.owners` in the [Environment Inventory](/docs/envgene-configs.md#env_definitionyml).

**Type:** string

**Default Value:** `""`

**Basic usage:**

```yaml
owners: "{{ current_env.owners }}"
```

**Usage in sample:** [Sample](/docs/samples/templates/env_templates/simple/tenant.yml.j2)

### `current_env.env_template`

---
**Description:** Name Template in Template artifact used for generation. Value is obtained from `envTemplate.name` in the [Environment Inventory](/docs/envgene-configs.md#env_definitionyml).

**Type:** string

**Default Value:** None

**Basic usage:**

```yaml
TEMPLATE_NAME: "{{ current_env.env_template }}"
```

**Usage in sample:** TBD

### `current_env.additionalTemplateVariables`

---
**Description:** Hashable to pass additional parameters for template rendering. Values is obtained from `envTemplate.additionalTemplateVariables` in the [Environment Inventory](/docs/envgene-configs.md#env_definitionyml).

**Type:** HashMap

**Default Value:** `{}`

**Basic usage:**

```yaml
deployParameters:
  INSTANCES_LEVEL_VAR_GLOBAL: "{{ current_env.additionalTemplateVariables.GLOBAL_LEVEL_PARAM1 }}"
  INSTANCES_LEVEL_VAR_CLOUD: "{{ current_env.additionalTemplateVariables.CLOUD_LEVEL_PARAM1 }}"
```

**Usage in sample:** [Sample](/docs/samples/templates/env_templates/composite/namespaces/billing.yaml.j2)

### `current_env.cloud_passport`

---
**Description:** Hashable with values from [Cloud Passport](/docs/envgene-objects.md#cloud-passport) defined in `inventory.cloudPassport` in the [Environment Inventory](/docs/envgene-configs.md#env_definitionyml).

**Type:** HashMap

**Default Value:** `{}`

**Basic usage:**

```yaml
{% if current_env.cloud_passport.cloud.CLOUD_PUBLIC_HOST is defined %}
  e2eParameters:
    CLOUD_PUBLIC_HOST_E2E: "{{ current_env.cloud_passport.cloud.CLOUD_PUBLIC_HOST}}"
{% else %}
  e2eParameters: {}
{% endif %}
```

**Usage in sample:** TBD

### `current_env.solution_structure`

---
**Description:** A hashable with values describing the structure of the solution - its composition by applications and the mapping of these applications to namespaces. The variable has the following structure:

```yaml
<application-name-A>:
  <deploy-postfix-A>:
    version: <application-version-A>
    namespace: <namespace-A>
<application-name-B>:
  <deploy-postfix-B>:
    version: <application-version-B>
    namespace: <namespace-B>
  <deploy-postfix-C>:
    version: <application-version-C>
    namespace: <namespace-C>
```

The variable is obtained by transforming the file defined in the path `/configuration/environments/<CLUSTER-NAME>/<ENV-NAME>/solution-descriptor/sd.yml`.

The value of the `namespace` attribute in this variable is obtained from the `name` attribute of the **already rendered** `Namespace` object. The definition of the object is located at `/configuration/environments/<CLUSTER-NAME>/<ENV-NAME>/Namespaces/<deployPostfix>/namespace.yml`. If the corresponding `Namespace` object is not found, the `namespace` value is set to `Null`.

**Type:** HashMap

**Default Value:** `{}`

**Basic usage:**

```yaml
  deployParameters:
{% if 'billing-app' in current_env.solution_structure %}
    param: value-1
{% else %}
    param: value-2
{% endif %}
```

```yaml
  deployParameters:
    oss_ns: "{{ current_env.solution_structure['oss-app]['oss'].namespace }}"
```

**Usage in sample:**

- [Sample template](/docs/samples/templates/env_templates/composite/namespaces/bss.yml.j2)

### `current_env.cluster.cloud_api_protocol`

---
**Description:** HTTP/HTTPS protocol for cluster connection URL

Value is parsed from `inventory.clusterUrl` in the [Environment Inventory](/docs/envgene-configs.md#env_definitionyml). If [Cloud Passport](/docs/envgene-objects.md#cloud-passport) is used for Environment generation, the value will be overwritten from Cloud Passport file

**Type:** String

**Default Value:** `""`

**Basic usage:**

```yaml
protocol: "{{current_env.cluster.cloud_api_protocol}}"
```

**Usage in sample:**

- [Sample](/docs/samples/templates/env_templates/composite/cloud.yml.j2)

### `current_env.cluster.cloud_api_url`

---
**Description:** API URL of a cluster

Value is parsed from `inventory.clusterUrl` in the [Environment Inventory](/docs/envgene-configs.md#env_definitionyml). If [Cloud Passport](/docs/envgene-objects.md#cloud-passport) is used for Environment generation, the value will be overwritten from Cloud Passport file

**Type:** String

**Default Value:** `""`

**Basic usage:**

```yaml
apiUrl: "{{current_env.cluster.cloud_api_url}}"
```

**Usage in sample:**

- [Sample](/docs/samples/templates/env_templates/composite/cloud.yml.j2)

### `current_env.cluster.cloud_api_port`

---
**Description:** Port of a cluster API server

Value is parsed from `inventory.clusterUrl` in in the [Environment Inventory](/docs/envgene-configs.md#env_definitionyml). If [Cloud Passport](/docs/envgene-objects.md#cloud-passport) is used for Environment generation, the value will be overwritten from Cloud Passport file

**Type:** String

**Default Value:** `""`

**Basic usage:**

```yaml
apiPort: "{{current_env.cluster.cloud_api_port}}"
```

**Usage in sample:**

- [Sample](/docs/samples/templates/env_templates/composite/cloud.yml.j2)

### `current_env.cluster.cloud_public_url`

---
**Description:** Public URL of a cluster.

Value is parsed from `env_definition.inventory.clusterUrl` in the [Environment Inventory](/docs/envgene-configs.md#env_definitionyml). If [Cloud Passport](/docs/envgene-objects.md#cloud-passport) is used for Environment generation, the value will be overwritten from Cloud Passport file

**Type:** String

**Default Value:** `""`

**Basic usage:**

`apiPort: "{{current_env.cluster.cloud_api_port}}"`

**Usage in sample:**

- [Sample](/docs/samples/templates/env_templates/composite/cloud.yml.j2)

## AppDef/RegDef macros

These macros are specifically used in AppDef and RegDef templates for rendering environment-specific configurations.

### `appdefs.overrides`

---
**Description:** Provides access to AppDef override values defined in the `appregdef_config.yaml` file. Used to customize application definitions for specific environments or clusters.

**Type:** HashMap

**Basic usage:**

```yaml
name: "{{ artifactId }}"
registryName: "{{ appdefs.overrides[app_lookup_key].registry | default('default-registry') }}"
supportParallelDeploy: {{ appdefs.overrides[app_lookup_key].supportParallelDeploy | default('true') }}
deployParameters:
  replicas: "{{ appdefs.overrides[artifactId].replicas | default('1') }}"
```

**Usage in sample:** [Sample](test_data/test_templates/appdefs/app1.yaml.j2)

### `regdefs.overrides`

---
**Description:** Provides access to RegDef override values defined in the `appregdef_config.yaml` file. Used to customize registry definitions for specific environments or clusters.

**Type:** HashMap

**Basic usage:**

```yaml
name: "{{ registry_name }}"
credentialsId: "{{ regdefs.overrides[registry_name].credentialsId | default('default-creds') }}"
mavenConfig:
  repositoryDomainName: "{{ regdefs.overrides[registry_name].mavenConfig.repositoryDomainName | default('maven.example.com') }}"
```

**Usage in sample:** [Sample](test_data/test_templates/regdefs/registry1.yaml.j2)

### `app_lookup_key`

---
**Description:** A special variable used to look up application-specific overrides in the configuration. Typically set to the artifactId or application name.

**Type:** string

**Basic usage:**

```yaml
# app_lookup_key is typically set during template rendering
registryName: "{{ appdefs.overrides[app_lookup_key].registry | default('default-registry') }}"
```

### `env`

---
**Description:** Provides access to environment variables during template rendering. Useful for passing external parameters to templates.

**Type:** HashMap

**Basic usage:**

```yaml
name: {{ env['APP_NAME'] | default('default-app-name') }}
registryName: {{ env['REGISTRY_NAME'] | default('default-registry') }}
artifactId: {{ env['ARTIFACT_ID'] | default('com.example.default') }}
```

**Usage in sample:** [Sample](test_data/test_templates/appdefs/app_with_env_vars.yaml.j2)

## Calculator CLI macros

These macros are rendered at the stage of calculating the [Effective Set](/docs/calculator-cli.md#effective-set-structure) and are present in it as rendered values.

### `APPLICATION_NAME`

---
**Description:** Application name.

Value is get from `name` of the [Application](/docs/envgene-objects.md#application) object

Application-level macro, can not be used on [Tenant](/docs/envgene-objects.md#tenant), [Cloud](/docs/envgene-objects.md#cloud) and [Namespace](/docs/envgene-objects.md#namespace) objects

**Type:** String

**Default Value:** `None`

**Basic usage:**

`app_name: "${APPLICATION_NAME}"`

**Usage in sample:** TBD

### `NAMESPACE`

---
**Description:** Namespace name.

Value is get from `name` of the [Namespace](/docs/envgene-objects.md#namespace) object

Namespace-level macro, can not be used on [Tenant](/docs/envgene-objects.md#tenant) or [Cloud](/docs/envgene-objects.md#cloud) objects

**Type:** String

**Default Value:** `None`

**Basic usage:**

`ns: "${NAMESPACE}"`

**Usage in sample:** TBD

### `CLOUDNAME`

---
**Description:** Cloud name.

Value is get from `name` of the [Cloud](/docs/envgene-objects.md#cloud)

**Type:** String

**Default Value:** `None`

**Basic usage:**

`cloud: "${CLOUDNAME}"`

**Usage in sample:** TBD

### `TENANTNAME`

---
**Description:** Tenant name.

Value is get from `name` of the [Tenant](/docs/envgene-objects.md#tenant) object

**Type:** String

**Default Value:** `None`

**Basic usage:**

`tenant: "${TENANTNAME}"`

**Usage in sample:** TBD

### `CLOUD_API_HOST`

---
**Description:** URL of the cluster API.

Value is get from `apiUrl` of the Environment's [Cloud](/docs/envgene-objects.md#cloud) object

**Type:** String

**Default Value:** `None`

**Basic usage:**

`cluster_api: "${CLOUD_API_HOST}"`

**Usage in sample:** TBD

### `CLOUD_PRIVATE_HOST`

---
**Description:** Internal host of the cluster. For example - `qubership.org`

Value is get from `privateUrl` of the Environment's [Cloud](/docs/envgene-objects.md#cloud) object

**Type:** String

**Default Value:** `None`

**Basic usage:**

`public_cluster_host: "${CLOUD_PRIVATE_HOST}"`

**Usage in sample:** TBD

### `CLOUD_PUBLIC_HOST`

---
**Description:** External URL of the cluster API. For example - `qubership.org`

Value is get from `publicUrl` of the Environment's [Cloud](/docs/envgene-objects.md#cloud) object

**Type:** String

**Default Value:** `None`

**Basic usage:**

`public_cluster_host: "${CLOUD_PUBLIC_HOST}"`

**Usage in sample:** TBD

### `CLOUD_PROTOCOL`

---
**Description:** Protocol/Schema (http or https) of the cluster API.

Value is get from `protocol` of the Environment's [Cloud](/docs/envgene-objects.md#cloud) object

**Type:** String

**Default Value:** `None`

**Basic usage:**

`schema: "${CLOUD_PROTOCOL}"`

**Usage in sample:** TBD

### `CLOUD_API_PORT`

---
**Description:** Port of the cluster API.

Value is get from `dbaasConfigs[0].apiPort` of the Environment's [Cloud](/docs/envgene-objects.md#cloud) object

**Type:** String

**Default Value:** `None`

**Basic usage:**

`port: "${CLOUD_API_PORT}"`

**Usage in sample:** TBD

### `PRIVATE_GATEWAY_URL`

---
**Description:** Defines URL of private gateway in the namespace.

The value is calculated as `${CLOUD_PROTOCOL}://${PRIVATE_GATEWAY_ROUTE_HOST}` if `${PRIVATE_GATEWAY_ROUTE_HOST}` is set, otherwise as `${CLOUD_PROTOCOL}://private-gateway-${ORIGIN_NAMESPACE}.${CLOUD_PUBLIC_HOST}`.

Namespace-level macro, can not be used on [Tenant](/docs/envgene-objects.md#tenant) or [Cloud](/docs/envgene-objects.md#cloud) objects

**Type:** String

**Default Value:** `None`

**Basic usage:**

`private_gw: "${PRIVATE_GATEWAY_URL}"`

**Usage in sample:** TBD

### `PUBLIC_GATEWAY_URL`

---
**Description:** Defines URL of public gateway in the namespace.

The value is calculated as `${CLOUD_PROTOCOL}://${PUBLIC_GATEWAY_ROUTE_HOST}` if `${PUBLIC_GATEWAY_ROUTE_HOST}` is set, otherwise as `${CLOUD_PROTOCOL}://public-gateway-${NAMESPACE}.${CLOUD_PUBLIC_HOST}`.

Namespace-level macro, can not be used on [Tenant](/docs/envgene-objects.md#tenant) or [Cloud](/docs/envgene-objects.md#cloud) objects

**Type:** String

**Default Value:** `None`

**Basic usage:**

`public_gw: "${PRIVATE_GATEWAY_URL}"`

**Usage in sample:** TBD

---
**Description:** Defines URL of private gateway in the namespace.

The value is calculated as `${CLOUD_PROTOCOL}://${PRIVATE_GATEWAY_ROUTE_HOST}` if `${PRIVATE_GATEWAY_ROUTE_HOST}` is set, otherwise as `${CLOUD_PROTOCOL}://private-gateway-${NAMESPACE}.${CLOUD_PUBLIC_HOST}`.

Namespace-level macro, can not be used on [Tenant](/docs/envgene-objects.md#tenant) or [Cloud](/docs/envgene-objects.md#cloud) objects

**Type:** String

**Default Value:** `None`

**Basic usage:**

`private_gw: "${PRIVATE_GATEWAY_URL}"`

**Usage in sample:** TBD

### `API_DBAAS_ADDRESS`

---
**Description:** Internal URL of the DBaaS.

Value is get from `dbaasConfigs[0].apiUrl` of the Environment's [Cloud](/docs/envgene-objects.md#cloud) object

**Type:** String

**Default Value:** `""`

**Basic usage:**

`private_dbaas_address: "${API_DBAAS_ADDRESS}"`

**Usage in sample:** TBD

### `DBAAS_AGGREGATOR_ADDRESS`

---
**Description:** External URL of the DBaaS.

Value is get from `dbaasConfigs[0].aggregatorUrl` of the Environment's [Cloud](/docs/envgene-objects.md#cloud) object

**Type:** String

**Default Value:** `""`

**Basic usage:**

`public_dbaas_address: "${DBAAS_AGGREGATOR_ADDRESS}"`

**Usage in sample:** TBD

### `DBAAS_AGGREGATOR_USERNAME`

---
**Description:** Username for access to the DBaaS.

Value is get from `dbaasConfigs[0].credentialsId.username` of the Environment's [Cloud](/docs/envgene-objects.md#cloud) object

**Type:** String

**Default Value:** `None`

**Basic usage:**

`dbaas_username: "${DBAAS_AGGREGATOR_USERNAME}"`

**Usage in sample:** TBD

### `DBAAS_AGGREGATOR_PASSWORD`

---
**Description:** Password for access to the DBaaS.

Value is get from `dbaasConfigs[0].credentialsId.password` of the Environment's [Cloud](/docs/envgene-objects.md#cloud) object

**Type:** String

**Default Value:** `None`

**Basic usage:**

`dbaas_password: "${DBAAS_AGGREGATOR_PASSWORD}"`

**Usage in sample:** TBD

### `DBAAS_ENABLED`

---
**Description:** Determines whether DBaaS is used

Value is get from `dbaasConfigs[0].enable` of the Environment's [Cloud](/docs/envgene-objects.md#cloud) object

**Type:** Boolean

**Default Value:** `None`

**Basic usage:**

`dbaas_is_used: "${DBAAS_ENABLED}"`

**Usage in sample:** TBD

### `MAAS_INTERNAL_ADDRESS`

---
**Description:** Internal URL of the MaaS.

Value is get from `maasConfig.maasInternalAddress` of the Environment's [Cloud](/docs/envgene-objects.md#cloud) object

**Type:** String

**Default Value:** `None`

**Basic usage:**

`private_maas_address: "${MAAS_INTERNAL_ADDRESS}"`

**Usage in sample:** TBD

### `MAAS_EXTERNAL_ROUTE`

---
**Description:** External URL of the MaaS.

Value is get from `maasConfig.maasUrl` of the Environment's [Cloud](/docs/envgene-objects.md#cloud) object

**Type:** String

**Default Value:** `None`

**Basic usage:**

`public_maas_address: "${MAAS_EXTERNAL_ROUTE}"`

**Usage in sample:** TBD

### `MAAS_CREDENTIALS_USERNAME`

---
**Description:** Username for access to the MaaS.

Value is get from `maasConfig.credentialsId.username` of the Environment's [Cloud](/docs/envgene-objects.md#cloud) object

**Type:** String

**Default Value:** `None`

**Basic usage:**

`maas_username: "${MAAS_CREDENTIALS_USERNAME}"`

**Usage in sample:** TBD

### `MAAS_CREDENTIALS_PASSWORD`

---
**Description:** Password for access to the MaaS.

Value is get from `maasConfig.credentialsId.password` of the Environment's [Cloud](/docs/envgene-objects.md#cloud) object

**Type:** String

**Default Value:** `None`

**Basic usage:**

`maas_password: "${MAAS_CREDENTIALS_PASSWORD}"`

**Usage in sample:** TBD

### `MAAS_ENABLED`

---
**Description:** Determines whether MaaS is used

Value is get from `maasConfig.enable` of the Environment's [Cloud](/docs/envgene-objects.md#cloud) object

**Type:** Boolean

**Default Value:** `None`

**Basic usage:**

`maas_is_used: "${MAAS_ENABLED}"`

**Usage in sample:** TBD

### `VAULT_ADDR`

---
**Description:** Internal URL of the Vault.

Value is get from `vaultConfig.url` of the Environment's [Cloud](/docs/envgene-objects.md#cloud) object

**Type:** String

**Default Value:** `None`

**Basic usage:**

`private_vault_address: "${VAULT_ADDR}"`

**Usage in sample:** TBD

### `PUBLIC_VAULT_URL`

---
**Description:** External URL of the Vault.

Value is get from `vaultConfig.url` of the Environment's [Cloud](/docs/envgene-objects.md#cloud) object

**Type:** String

**Default Value:** `None`

**Basic usage:**

`public_vault_address: "${PUBLIC_VAULT_URL}"`

**Usage in sample:** TBD

### `VAULT_TOKEN`

---
**Description:** Token for access to the Vault.

Value is get from `vaultConfig.credentialsId.secret` of the Environment's [Cloud](/docs/envgene-objects.md#cloud) object

**Type:** String

**Default Value:** `""`

**Basic usage:**

`vault_token: "${VAULT_TOKEN}"`

**Usage in sample:** TBD

### `VAULT_ENABLED`

---
**Description:** Determines whether Vault is used

Value is get from `vaultConfig.enable` of the Environment's [Cloud](/docs/envgene-objects.md#cloud) object

**Type:** Boolean

**Default Value:** `None`

**Basic usage:**

`vault_is_used: "${PUBLIC_VAULT_URL}"`

**Usage in sample:** TBD

### `CONSUL_URL`

---
**Description:** Internal URL of the Consul.

Value is get from `consulConfig.internalUrl` of the Environment's [Cloud](/docs/envgene-objects.md#cloud) object

**Type:** String

**Default Value:** `None`

**Basic usage:**

`private_consul_address: "${CONSUL_URL}"`

**Usage in sample:** TBD

### `CONSUL_PUBLIC_URL`

---
**Description:** External URL of the Consul.

Value is get from `consulConfig.publicUrl` of the Environment's [Cloud](/docs/envgene-objects.md#cloud) object

**Type:** String

**Default Value:** `None`

**Basic usage:**

`public_consul_address: "${CONSUL_PUBLIC_URL}"`

**Usage in sample:** TBD

### `CONSUL_ADMIN_TOKEN`

---
**Description:** Token for access to the Consul.

Value is get from `consulConfig.tokenSecret` of the Environment's [Cloud](/docs/envgene-objects.md#cloud) object

**Type:** String

**Default Value:** `""`

**Basic usage:**

`consul_token: "${CONSUL_ADMIN_TOKEN}"`

**Usage in sample:** TBD

### `CONSUL_ENABLED`

---
**Description:** Determines whether Consul is used

Value is get from `vaultConfig.enable` of the Environment's [Cloud](/docs/envgene-objects.md#cloud) object

**Type:** Boolean

**Default Value:** `None`

**Basic usage:**

`consul_is_used: "${CONSUL_ENABLED}"`

**Usage in sample:** TBD

## Credential Macro

---
**Description:** This macro marks parameters as sensitive, triggering special processing that differs from regular parameters.

```text
${creds.get('<cred-id>').username|password|secret}
```

Where `username`, `password`, and `secret` are **credential fields** that define the type of sensitive data being referenced.

For each `<cred-id>` during Environment Instance generation a [Credential](/docs/envgene-objects.md#credential) object is created in the [Environment Credential File](/docs/envgene-objects.md#environment-credential-file)

Type assignment:

- `usernamePassword` for `username` and `password` attributes
- `secret` for `secret` attribute

**Basic usage:**

```yaml
kafka_username: ${creds.get('kafka-cred').username}
kafka_password: ${creds.get('kafka-cred').password}
k8s_token: ${creds.get('k8s-cred').secret}
```

**Usage in sample:** [Sample](/docs/samples/templates/parameters/migration/test-deploy-creds.yml)

## Deprecated Macros

### Deprecated Jinja Macros

#### `environment.environmentName`

**Description:** Name of environment

**Replacement**: [`current_env.name`](#current_envname)

#### `tenant`

**Description:** Name of tenant for environment

**Replacement**: [`current_env.tenant`](#current_envtenant)

#### `cloud`

**Description:** Name of cloud for environment

**Replacement**: [`current_env.cloud`](#current_envcloud)

#### `deployer`

**Description:** Name of deployer used for environment

**Replacement**: [`current_env.cmdb_name`](#current_envcmdb_name)

### Deprecated Credential Macros

#### `${envgene.creds.get('<cred-id>').username|password|secret}`

**Description:** This macro was used for processing system sensitive parameters—parameters that EnvGene uses to integrate itself with external systems, such as the login and password for a registry or a token for a GitLab instance.

**Replacement**: [`${creds.get('<cred-id>').username|password|secret}`](#credential-macro)
