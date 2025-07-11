# Resource Profiles

Resource profiles define compute, memory, and other resource configurations for different environments and applications. They provide environment-specific resource overrides for optimal performance and cost management.

## Development Environment Profiles

### Core Development Override
```yaml title="dev_core_override.yml"
--8<-- "samples/templates/resource_profiles/dev_core_override.yml"
```

### BSS Development Override
```yaml title="dev_bss_override.yaml"
--8<-- "samples/templates/resource_profiles/dev_bss_override.yaml"
```

### OSS Development Override
```yaml title="dev_oss_override.yaml"
--8<-- "samples/templates/resource_profiles/dev_oss_override.yaml"
```

### Billing Development Override
```yaml title="dev_billing_override.yml"
--8<-- "samples/templates/resource_profiles/dev_billing_override.yml"
```

## Production Environment Profiles

### Core Production Override
```yaml title="prod_core_override.yml"
--8<-- "samples/templates/resource_profiles/prod_core_override.yml"
```

### BSS Production Override
```yaml title="prod_bss_override.yaml"
--8<-- "samples/templates/resource_profiles/prod_bss_override.yaml"
```

### OSS Production Override
```yaml title="prod_oss_override.yaml"
--8<-- "samples/templates/resource_profiles/prod_oss_override.yaml"
```

### Billing Production Override
```yaml title="prod_billing_override.yml"
--8<-- "samples/templates/resource_profiles/prod_billing_override.yml"
```

## Resource Profile Structure

Resource profiles typically define:

- **CPU and Memory**: Resource requests and limits
- **Scaling**: Horizontal and vertical scaling parameters
- **Storage**: Persistent volume configurations
- **Network**: Service and ingress configurations
- **Environment-specific**: Overrides for different deployment environments (dev, prod) 
