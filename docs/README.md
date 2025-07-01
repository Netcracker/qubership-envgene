# Environment Generator (EnvGene)

Environment Generator allows you to easily create Environments from predefined templates with version control, automation, and Git-based configuration management.

## What is Environment Generator?

Environment Generator (EnvGene) is a comprehensive solution for managing infrastructure and application Environments through a template-based approach. It enables teams to:

- **Define Templates**: Create reusable Environment templates including Tenant, Cloud, Namespaces, and others
- **Manage Inventory**: Define and maintain your Environment Inventory with version control
- **Generate Environments**: Create consistent Environments from inventory and versioned templates
- **Track Changes**: Leverage native Git functionality for Environment and parameter change history
- **Generate Effective Set**: Create parameters fit for particular consumer

## Key Features

### Version Control Integration

- Get complete history of Environment and parameter changes using native Git functionality
- Compare Environment configurations using standard diff tools
- Track template evolution through Git versioning
- Manage merge requests with clear configuration diffs

### Automation Capabilities

- Automated Environment creation and updates
- Effective Parameter Set generation
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
Predefined configurations that serve as blueprints for Environments. Templates include:

- **Template Descriptor**: Define the overall structure and components
- **Cloud Templates**: Defines parameters describing the underlying infrastructure
- **Namespace Templates**: defines parameters common to applications of particular namespace
- **ParamSet Templates**: Define containers of configuration parameters  
- **Resource Profiles**: Define performance parameters

### Inventory
The specification of your actual Environments, including:

- Environment definitions and metadata
- Parameter values and overrides
- Resource profile assignments
- Deployment targets and credentials

### Effective Set
The final computed consumer (Helm/ArgoCD/Orchestration pipelines) specific configuration that results from merging templates, parameters, and Environment-specific overrides.

## Getting Started

Ready to start using Environment Generator? Check out our [Basic How-To Guide](basic-how-to.md) for step-by-step instructions.

For detailed configuration options, explore our [Configuration](envgene-configs.md) documentation.

## Documentation Structure

This documentation is organized into the following sections:

- **Installation**: Get started with Environment Generator
- **Architecture & Components**: Understand how the system works
- **Configuration**: Learn how to configure and customize the system
- **Integrations**: Connect with external systems and tools
- **Operations**: Maintain and troubleshoot running Environments

## Support and Contribution

Environment Generator is an open source project. For questions, issues, or contributions, please visit our [GitHub repository](https://github.com/netcracker/qubership-envgene). 
