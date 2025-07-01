# Environment Generator (EnvGene)

Environment Generator allows you to easily create environments from predefined templates with version control, automation, and Git-based configuration management.

## What is Environment Generator?

Environment Generator (EnvGene) is a comprehensive solution for managing infrastructure and application environments through a template-based approach. It enables teams to:

- **Define Templates**: Create reusable environment templates including Tenant, Cloud, Namespaces, and Parameters
- **Manage Inventory**: Define and maintain your environment inventory with version control
- **Generate Environments**: Create consistent environments from inventory and versioned templates
- **Track Changes**: Leverage native Git functionality for environment and parameter change history

## Key Features

### Version Control Integration

- Get complete history of environment and parameter changes using native Git functionality
- Compare environment configurations using standard diff tools
- Track template evolution through Git versioning
- Manage merge requests with clear configuration diffs

### Automation Capabilities

- Automated environment creation and updates
- Effective parameter set generation with dependency resolution
- Template-driven deployment processes
- Integration with CI/CD pipelines

### Security and Compliance

- Built-in credentials management with encryption
- Secure storage of sensitive configuration data in Git repositories
- Support for multiple encryption backends
- Compliance-ready audit trails

### Template Management

- Hierarchical template structure with inheritance
- Parameterized templates with macro support
- Template versioning and rollback capabilities
- Environment-specific customizations

## Core Concepts

### Templates
Predefined configurations that serve as blueprints for environments. Templates include:

- **Environment Templates**: Define the overall structure and components
- **Parameter Templates**: Specify configuration parameters and their relationships  
- **Resource Profiles**: Define resource allocation and scaling policies

### Inventory
The specification of your actual environments, including:

- Environment definitions and metadata
- Parameter values and overrides
- Resource profile assignments
- Deployment targets and credentials

### Effective Set
The final computed configuration that results from merging templates, parameters, and environment-specific overrides.

## Architecture

Environment Generator consists of several components:

- **Template Engine**: Processes templates and generates effective configurations
- **Parameter Calculator**: Resolves parameter dependencies and inheritance
- **Credential Manager**: Handles encrypted credential storage and retrieval
- **Environment Builder**: Creates and manages environment deployments

## Getting Started

Ready to start using Environment Generator? Check out our [Basic How-To Guide](basic-how-to.md) for step-by-step instructions.

For detailed configuration options, explore our [Configuration](envgene-configs.md) documentation.

## Documentation Structure

This documentation is organized into the following sections:

- **Installation**: Get started with Environment Generator
- **Architecture & Components**: Understand how the system works
- **Configuration**: Learn how to configure and customize the system
- **Integrations**: Connect with external systems and tools
- **Operations**: Maintain and troubleshoot running environments

## Support and Contribution

Environment Generator is an open source project. For questions, issues, or contributions, please visit our [GitHub repository](https://github.com/netcracker/qubership-envgene). 
