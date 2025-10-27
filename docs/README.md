# EnvGene Documentation

- [EnvGene Documentation](#envgene-documentation)
  - [Getting Started](#getting-started)
  - [Core Concepts](#core-concepts)
  - [Advanced Features](#advanced-features)
    - [Examples \& Samples](#examples--samples)
    - [Development](#development)

## Getting Started

- [**Quick Start Guide**](/README.md#getting-started) - Create your first Environment

## Core Concepts

- [**EnvGene Objects**](/docs/envgene-objects.md) - What are EnvGene objects and how they work
- [**Configuration Files**](/docs/envgene-configs.md) - File formats and config options
- [**Pipeline Configuration**](/docs/envgene-pipelines.md) - How EnvGene pipelines work
- [**Repository Variables**](/docs/envgene-repository-variables.md) - CI/CD variables used in EnvGene repositories
- [**Template Macros**](/docs/template-macros.md) - How to use EnvGene macros in templates

## Advanced Features

- [**Solution Descriptor Processing**](/docs/features/sd-processing.md) - Manage [Solution Descriptor](/docs/envgene-objects.md#solution-descriptor) for your Environments
- [**Effective Set Calculation**](/docs/features/effective-set-calculation.md) - Calculate the [Effective Set](/docs/features/calculator-cli.md#effective-set-v20)
- [**Application and Registry Definition**](/docs/features/app-registry-definition.md) - Describe how applications and registries are defined and referenced
- [**Environment Inventory Generation**](/docs/features/environment-inventory-generation.md) - Auto-generate [Environment Inventory](/docs/envgene-configs.md#env_definitionyml)
- [**Credential Rotation**](/docs/features/credential-rotation.md) - Automate [Credential](/docs/envgene-objects.md#credential) rotation
- [**Namespace Render Filter**](/docs/features/namespace-render-filtering.md) - Render only selected [Namespaces](/docs/envgene-objects.md#namespace)
- [**System Certificate Configuration**](/docs/features/system-certificate.md) - Auto-config system certs for internal registries or TLS services
- [**Template Override**](/docs/features/template-override.md) - Use a base Environment template and override parts as needed
- [**Automatic Environment Name Derivation**](/docs/features/auto-env-name-derivation.md) - Auto-detect Environment name from folder structure
- [**Template Inheritance**](/docs/features/template-inheritance.md) - Advanced Environment template patterns
- [**Credential Encryption**](/docs/how-to/credential-encryption.md) - Secure [Credential](/docs/envgene-objects.md#credential) rotation

### Examples & Samples

- [**Sample Configurations**](/docs/samples/README.md) - Complete example configurations
- [**Template Examples**](/docs/samples/template-repository/) - Ready-to-use template examples
- [**Environment Examples**](/docs/samples/instance-repository/) - Sample environment configurations

### Development

- [**Development Guides**](/docs/dev/) - Development setup and guidelines
