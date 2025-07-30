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
  - [Credential Macro](#credential-macro)
  - [Deprecated Macros](#deprecated-macros)
    - [`environment.environmentName`](#environmentenvironmentname)
    - [`tenant`](#tenant)
    - [`cloud`](#cloud)
    - [`deployer`](#deployer)
    - [`${envgene.creds.get('<cred-id>').username|password|secret}`](#envgenecredsgetcred-idusernamepasswordsecret)

This documentation provides a list of macros that can be used during template generation

## Jinja Macros

These Jinja macros that can be used during template generation

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

## Credential Macro

---
**Description:** This macro marks parameters as sensitive, triggering special processing that differs from regular parameters.

```yaml
${creds.get('<cred-id>').username|password|secret}
```

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

### `environment.environmentName`

**Description:** Name of environment

**Replacement**: [`current_env.name`](#current_envname)

### `tenant`

**Description:** Name of tenant for environment

**Replacement**: [`current_env.tenant`](#current_envtenant)

### `cloud`

**Description:** Name of cloud for environment

**Replacement**: [`current_env.cloud`](#current_envcloud)

### `deployer`

**Description:** Name of deployer used for environment

**Replacement**: [`current_env.cmdb_name`](#current_envcmdb_name)

### `${envgene.creds.get('<cred-id>').username|password|secret}`

**Description:** This macro was used for processing system sensitive parameters—parameters that EnvGene uses to integrate itself with external systems, such as the login and password for a registry or a token for a GitLab instance.

**Replacement**: [`${creds.get('<cred-id>').username|password|secret}`](#credential-macro)
