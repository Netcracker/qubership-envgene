# EnvGene Documentation

- [EnvGene Documentation](#envgene-documentation)
  - [Getting Started](#getting-started)
  - [Tutorials](#tutorials)
  - [Core Concepts](#core-concepts)
  - [How-To Guides](#how-to-guides)
  - [Advanced Features](#advanced-features)
  - [Examples \& Samples](#examples--samples)
  - [Development](#development)

## Getting Started

- [**Quick Start Guide**](/README.md#getting-started) - Create your first Environment

## Tutorials

- [**Understanding the Effective Set**](/docs/tutorials/effective-set.md) - Trace how parameters from Tenant, Cloud, Namespace, Application, and SBOM sources are merged into the final Effective Set; learn to read traceability comments and debug wrong values
- [**Managing Resource Profiles**](/docs/tutorials/resource-profiles.md) - End-to-end walkthrough: from Baseline to Template Override to Environment-Specific Override, including `template_override`, `overrides-parent`, and result verification

## Core Concepts

- [**EnvGene Objects**](/docs/envgene-objects.md) - What are EnvGene objects and how they work
- [**Configuration Files**](/docs/envgene-configs.md) - File formats and config options
- [**Pipeline Configuration**](/docs/envgene-pipelines.md) - How EnvGene pipelines work
- [**Repository Variables**](/docs/envgene-repository-variables.md) - CI/CD variables used in EnvGene repositories
- [**Template Macros**](/docs/template-macros.md) - How to use EnvGene macros in templates
- [**Instance Pipeline Parameters**](/docs/instance-pipeline-parameters.md) - Reference for Instance pipeline inputs

## How-To Guides

**Repository Setup:**

- [**Create Simple Template**](/docs/how-to/create-simple-template.md) - Create your first environment template
- [**Create Cluster**](/docs/how-to/create-cluster.md) - Set up a new cluster
- [**Create Environment Inventory**](/docs/how-to/create-environment-inventory.md) - Define environment inventory
- [**Initialize and Upgrade Instance Repository**](/docs/how-to/envgene-maitanance.md) - Set up or upgrade Instance Repository using GSF

**Configuration Management:**

- [**Update Template Version**](/docs/how-to/update-template-version.md) - Update environment template version
- [**Override Template Parameters**](/docs/how-to/environment-specific-parameters.md) - Override template parameters for specific environments
- [**Configure Resource Profiles**](/docs/how-to/configure-resource-profiles.md) - Configure performance parameters for different environment types

**Effective Set:**

- [**Generate an Effective Set**](/docs/how-to/generate-effective-set.md) - Trigger Effective Set generation from a Solution Descriptor artifact and template version

**Advanced Configuration:**

- [**Configure Namespace Names for Sites**](/docs/how-to/configure-ns-names-for-sites.md) - Site-specific namespace naming
- [**Credential Encryption**](/docs/how-to/credential-encryption.md) - Secure credential storage and rotation
- [**Migrate to Dot-Notated Parameters**](/docs/how-to/dot-notated-parameter-migration.md) - Parameter format migration

## Advanced Features

- [**Solution Descriptor Processing**](/docs/features/sd-processing.md) - Manage [Solution Descriptor](/docs/envgene-objects.md#solution-descriptor) for your Environments
- [**Effective Set Calculation**](/docs/features/calculator-cli.md) - Calculate the [Effective Set](/docs/features/calculator-cli.md#effective-set-v20)
- [**Custom Params**](/docs/instance-pipeline-parameters.md#custom_params) for session-scoped overrides
- [**Application and Registry Definition**](/docs/features/app-reg-defs.md) - Describe how applications and registries are defined and referenced
- [**Environment Inventory Generation**](/docs/features/env-inventory-generation.md) - Auto-generate [Environment Inventory](/docs/envgene-configs.md#env_definitionyml)
- [**Environment Instance Generation**](/docs/features/environment-instance-generation.md) - Generate Environment Instances from templates and inventories (including BG support)
- [**Credential Rotation**](/docs/features/cred-rotation.md) - Automate [Credential](/docs/envgene-objects.md#credential) rotation
- [**Namespace Render Filter**](/docs/features/namespace-render-filtering.md) - Render only selected [Namespaces](/docs/envgene-objects.md#namespace)
- [**System Certificate Configuration**](/docs/features/system-certificate.md) - Auto-config system certs for internal registries or TLS services
- [**Template Override**](/docs/features/template-override.md) - Use a base Environment template and override parts as needed
- [**Automatic Environment Name Derivation**](/docs/features/auto-env-name-derivation.md) - Auto-detect Environment name from folder structure
- [**Template Composition**](/docs/features/template-composition.md) - Advanced Environment template patterns
- [**Blue-Green Deployment**](/docs/features/blue-green-deployment.md) - BG domains, state management, and `bg_manage` pipeline job
- [**Resource Profiles**](/docs/features/resource-profile.md) - Baselines and overrides for performance parameters
- [**SBOM**](/docs/features/sbom.md) - CycloneDX-based artifact and parameter exchange for EnvGene
- [**SBOM Retention**](/docs/features/sbom-retention.md) - Automatic cleanup of cached SBOM files to manage repository size

## Examples & Samples

- [**Sample Configurations**](/docs/samples/README.md) - Complete example configurations
- [**Template Examples**](/docs/samples/template-repository/) - Ready-to-use template examples
- [**Environment Examples**](/docs/samples/instance-repository/) - Sample environment configurations

## Development

- [**Development Guides**](/docs/dev/) - Development setup and guidelines
