# Environment Configurations

Environment configurations define specific instances of environments deployed in clusters. Each environment has its own inventory, credentials, parameters, and resource profiles.

## Cluster Template Variables

Shared variables across all environments in a cluster:

```yaml title="sample-cloud-template-variables.yml"
--8<-- "samples/environments/cluster-01/sample-cloud-template-variables.yml"
```

## Global Template Variables

Template variables used across multiple environments:

```yaml title="prod-template-variables.yml"
--8<-- "samples/environments/prod-template-variables.yml"
```

## GAV Coordinates

Maven GAV (Group, Artifact, Version) coordinates for template artifacts:

```yaml title="GAV_coordinates.yaml"
--8<-- "samples/GAV_coordinates.yaml"
```

## Environment Structure

Each environment configuration typically includes:

### Directory Structure
```
environments/
├── cluster-01/              # Cluster grouping
│   ├── env-01/             # Specific environment
│   │   └── Inventory/      # Environment definition
│   ├── env-02/             # Another environment
│   ├── credentials/        # Shared credentials
│   ├── parameters/         # Shared parameters
│   └── resource_profiles/  # Shared resource profiles
├── credentials/            # Global credentials
└── parameters/             # Global parameters
```

### Key Components

- **Inventory**: Contains `env_definition.yml` with environment specifications
- **Credentials**: Encrypted credential files for authentication
- **Parameters**: Environment-specific parameter overrides
- **Resource Profiles**: Environment-specific resource configurations
- **Template Variables**: Jinja2 variables used during template processing

For detailed environment definition structure, see the [Environment Definition documentation](../env_definition.md). 
