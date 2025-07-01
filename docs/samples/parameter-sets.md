# Parameter Sets

Parameter sets define configuration values that can be applied to applications within environments. They provide a way to manage application-specific settings separately from environment templates.

## Core Parameters

Basic parameter set for core system components:

```yaml title="core.yaml"
--8<-- "samples/templates/parameters/core.yaml"
```

## Business Support System (BSS) Parameters

Configuration for BSS applications:

```yaml title="bss.yaml"
--8<-- "samples/templates/parameters/bss.yaml"
```

## Billing Parameters

Specific parameters for billing applications:

```yaml title="billing.yaml"
--8<-- "samples/templates/parameters/billing.yaml"
```

## Technical BSS Parameters

Technical configuration for BSS components:

```yaml title="bss-tech.yml"
--8<-- "samples/templates/parameters/bss-tech.yml"
```

## Parameter Set Structure

Each parameter set contains:

- **name**: Unique identifier for the parameter set
- **version**: Version number for tracking changes
- **parameters**: Global parameters applied to all applications
- **applications**: Array of application-specific parameter overrides 
