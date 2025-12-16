# EnvGene Sample Layouts

This document provides an overview of the recommended structures for Template and Instance repositories when using EnvGene.

---

## Template Repository Layout

For an example, refer to [this template repository](/docs/samples/template-repository/).

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

---

## Instance Repository Layout

For an example, refer to [this instance repository](/docs/samples/instance-repository/).

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

> **Note:**  
> The `env_definition.yml` should follow the [documented structure](/docs/envgene-configs.md#env_definitionyml).
