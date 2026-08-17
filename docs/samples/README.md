# EnvGene samples

- [EnvGene samples](#envgene-samples)
  - [Template repository layout](#template-repository-layout)
  - [Instance repository layout](#instance-repository-layout)
  - [Feature samples](#feature-samples)
    - [Blue-Green Deployment](#blue-green-deployment)
    - [Cloud artifact registries](#cloud-artifact-registries)
    - [External credentials](#external-credentials)

EnvGene samples are copyable file sets of two kinds: the generic repository layouts below and
feature-scoped sample sets under `docs/samples/<feature>/`.

## Template repository layout

For an example, see the [template repository sample](/docs/samples/template-repository/).

```yaml
templates/
  ├── env_templates/
  │   ├── <template-group>/
  │   │   ├── <tenant-template>.yml.j2
  │   │   ├── <cloud-template>.yml.j2
  │   │   └── <namespace-template>.yml.j2
  │   └── <template-descriptor>.yml
  ├── parameters/
  │   └── <parameter-set>.yml
  └── resource_profiles/
      └── <resource-profile>.yml
```

## Instance repository layout

For an example, see the [instance repository sample](/docs/samples/instance-repository/).

```yaml
configuration/
  ├── credentials/
  │   └── credentials.yml
  ├── registry.yml
  ├── integration.yml
  └── config.yml
environments/
  ├── <cluster-name>/
  │   ├── <environment-name>/
  │   │   └── Inventory/
  │   │       ├── env_definition.yml
  │   │       └── parameters/
  │   │           └── <paramset>.yml
  │   ├── credentials/
  │   │   └── <shared-cred>.yml
  │   └── parameters/
  │       └── <paramset>.yml
  ├── credentials/
  │   └── <shared-cred>.yml
  ├── parameters/
  │   └── <paramset>.yml
  └── <shared-template-variables>.yml
```

> [!NOTE]
> The `env_definition.yml` should follow the [documented structure](/docs/envgene-configs.md#env_definitionyml).

## Feature samples

### Blue-Green Deployment

Migration of a non-BG template and environment to BGD: the before and after Environment Templates and
per-variant sample environments. See [BGD samples](/docs/samples/blue-green-deployment/), the
[migration how-to](/docs/how-to/blue-green-deployment-migration.md), and the
[deploy operations how-to](/docs/how-to/blue-green-deployment-deploy-operations.md).

### Cloud artifact registries

Registry Definition v2.0 and Artifact Definition v2.0 sample files for AWS CodeArtifact and GCP
Artifact Registry, plus a credentials file with placeholder values for both providers. See the
[cloud artifact registries samples](/docs/samples/cloud-artifact-registries/) and
[Configuring cloud artifact registries for AWS and GCP](/docs/how-to/configure-cloud-artifact-registries.md).

### External credentials

A minimal external credentials setup: the Template Descriptor, Credential Template, Application and
Registry Definition templates, the instance, the Effective Set, and the system credentials EnvGene
consumes (integration, deployer, registry, and definition credentials). See the
[external credentials samples](/docs/samples/external-credentials/) and
[External Credentials Management](/docs/features/external-creds.md).
