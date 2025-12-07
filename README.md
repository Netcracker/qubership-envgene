# EnvGene

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Build Status](https://img.shields.io/badge/Build-Passing-brightgreen.svg)](https://github.com/Netcracker/qubership-envgene/actions)

![Environment generator logo](/docs/images/envgene-logo.png "Environment generator")

- [EnvGene](#envgene)
  - [Overview](#overview)
  - [🎯 Goals](#-goals)
  - [✨ Key Features](#-key-features)
    - [Version Control \& History](#version-control--history)
    - [Automation \& CI/CD](#automation--cicd)
    - [Security \& Credentials](#security--credentials)
  - [🚀 Quick Start](#-quick-start)
    - [System Requirements](#system-requirements)
    - [Basic Usage](#basic-usage)
  - [📚 Documentation](#-documentation)
    - [Getting Started](#getting-started)
    - [Core Concepts](#core-concepts)
    - [Advanced Features](#advanced-features)
    - [Examples \& Samples](#examples--samples)
    - [Development](#development)
  - [🤝 Contributing](#-contributing)
  - [📄 License](#-license)

## Overview

**EnvGene** (Environment Generator) is git-based tool for generating and versioning Environment configs using templates. Helps manage parameters for many similar cloud Environments.

## 🎯 Goals

EnvGene simplifies Environment management by providing:

- **Template-based Environment Creation**: Define reusable templates for your Environment types
- **Environment Inventory Management**: Define and manage inventories of your Environments
- **Automated Environment Provisioning**: Create Environments from inventory and versioned templates with automated pipelines
- **Configuration as Code**: Store all Environment configurations in Git with full history and diff capabilities

## ✨ Key Features

### Version Control & History

- **Git-native Versioning**: Full history of Environment/parameter changes using native Git functionality
- **Configuration Comparison**: Compare Environments configuration using native Git diff
- **Template Versioning**: Version-controlled templates with Maven artifact management
- **Change Tracking**: Track all modifications with detailed commit history

### Automation & CI/CD

- **Automated Environment Creation/Update**: Automation for Environment generation
- **Pipeline Integration**: Integration with GitLab CI and GitHub Actions
- **Build Automation**: Automated template building and artifact publishing

### Security & Credentials

- **Encrypted Credentials Management**: Secure credential storage in Git using encryption
- **Credential Rotation**: Automated credential rotation capabilities

## 🚀 Quick Start

### System Requirements

1. GitHub account with permission to create repositories
2. Git client installed locally

### Basic Usage

1. **Init Template Repository**

2. **Create Environment Template**

   See the guide: [Create Simple Template](/docs/how-to/create-simple-template.md)

3. **Init Instance Repository**

   Copy [the workflow files](/github_workflows/instance-repo-pipeline/.github) to your Instance repository on GitHub.

4. **Create Cluster**

   See: [Create Cluster guide](/docs/how-to/create-cluster.md)

5. **Create Inventory for Environment**

   See: [Create Inventory guide](/docs/how-to/create-environment-inventory.md)

6. **Generate Environment**

   Run the pipeline with [these parameters](/docs/instance-pipeline-parameters.md):

   ```text
   ENV_NAMES: <cluster-name>/<environment-name>
   ENV_BUILDER: true
   GENERATE_EFFECTIVE_SET: true
   GH_ADDITIONAL_PARAMS:
      SD_SOURCE_TYPE: json
      SD_DATA: <your-Solution-Descriptor-content>
   ```

   > [!NOTE] For special instructions on the GitHub pipeline, see [GH_ADDITIONAL_PARAMS docs](/docs/instance-pipeline-parameters.md)
   > and the [pipeline description](/github_workflows/instance-repo-pipeline/.github/docs/README.md)

After the pipeline finishes, the Environment configuration will be generated and committed to your instance repository:

- [Environment Instance Object](/docs/envgene-objects.md#environment-instance-objects)
- [Effective Set](/docs/features/calculator-cli.md)

## 📚 Documentation

### Getting Started

- [**Quick Start Guide**](#-quick-start) - Create your first Environment

### Core Concepts

- [**EnvGene Objects**](/docs/envgene-objects.md) - What are EnvGene objects and how they work
- [**Configuration Files**](/docs/envgene-configs.md) - File formats and config options
- [**Pipeline Configuration**](/docs/envgene-pipelines.md) - How EnvGene pipelines work
- [**Repository Variables**](/docs/envgene-repository-variables.md) - CI/CD variables used in EnvGene repositories
- [**Template Macros**](/docs/template-macros.md) - How to use EnvGene macros in templates

### Advanced Features

- [**Solution Descriptor Processing**](/docs/features/sd-processing.md) - Manage [Solution Descriptor](/docs/envgene-objects.md#solution-descriptor) for your Environments
- [**Effective Set Calculation**](/docs/features/calculator-cli.md) - Calculate the [Effective Set](/docs/features/calculator-cli.md#effective-set-v20)
- [**Application and Registry Definition**](/docs/features/app-reg-defs.md) - Describe how applications and registries are defined and referenced
- [**Environment Inventory Generation**](/docs/features/env-inventory-generation.md) - Auto-generate [Environment Inventory](/docs/envgene-configs.md#env_definitionyml)
- [**Credential Rotation**](/docs/features/cred-rotation.md) - Automate [Credential](/docs/envgene-objects.md#credential) rotation
- [**Namespace Render Filter**](/docs/features/namespace-render-filtering.md) - Render only selected [Namespaces](/docs/envgene-objects.md#namespace)
- [**System Certificate Configuration**](/docs/features/system-certificate.md) - Auto-config system certs for internal registries or TLS services
- [**Template Override**](/docs/features/template-override.md) - Use a base Environment template and override parts as needed
- [**Automatic Environment Name Derivation**](/docs/features/auto-env-name-derivation.md) - Auto-detect Environment name from folder structure
- [**Template Inheritance**](/docs/features/template-inheritance.md) - Advanced Environment template patterns
- [**Credential Encryption**](/docs/how-to/credential-encryption.md) - Secure [Credential](/docs/envgene-objects.md#credential) rotation

### Examples & Samples

- [**Sample Configurations**](/docs/samples/README.md)
- [**Environment Template Examples**](/docs/samples/template-repository/)
- [**Environment Inventory Examples**](/docs/samples/instance-repository/)

### Development

- [**Development Guides**](/docs/dev/) - Development setup and guidelines

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details on:

- Code of Conduct
- Development setup
- Pull request process
- Issue reporting

## 📄 License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.
