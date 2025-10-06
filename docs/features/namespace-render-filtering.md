# Namespace Render Filter

## Description

Namespace render filter feature lets select which Environment [Namespaces](/docs/envgene-objects.md#namespace) will be rendered. It does not affect rendering of other objects like cloud or tenant.

This feature uses the [`NS_BUILD_FILTER`](/docs/instance-pipeline-parameters.md#parameters) Instance pipeline parameter. This parameter is used during the Environment Instance generation in the `env_build` job.

It allows to generate or update only specific Namespaces without touching the others. This is useful, for example, in Blue-Green deployment scenarios.

## Syntax

You can set the value of `NS_BUILD_FILTER` in two ways:

### BG Domain role aliases

You can use BG Domain role aliases as namespace selectors:

- `@controller` - controller namespace
- `@origin` - origin namespace  
- `@peer` - peer namespace

EnvGene resolves these aliases using the [BG Domain](/docs/envgene-objects.md#bg-domain) object. To use aliases, the BG Domain object must exist in the Environment.

### Direct namespace names

You can specify the namespace name directly, as defined in the `name` attribute of the Namespace object:

- `env-name-api` - full namespace name

### Operators

The following operators are available:

- `!` - exclusion operator. When used at the beginning, it excludes the specified namespaces from processing. **Important**: The `!` operator applies to the entire expression, not to individual namespaces within a comma-separated list.
- `,` - multiple selection operator. Separates multiple namespace selectors

## Usage examples

### Update all except the peer NS

```yaml
NS_BUILD_FILTER: "! @peer"
# or
NS_BUILD_FILTER: "! env-name-peer"
```

### Update only the peer NS

```yaml
NS_BUILD_FILTER: "@peer"
# or
NS_BUILD_FILTER: "env-name-peer"
```

### Update all

```yaml
NS_BUILD_FILTER: ""
# or
NS_BUILD_FILTER is not provided
```

### Multiple selection

```yaml
# Update controller and origin
NS_BUILD_FILTER: "@peer,@origin"

# Update all except peer and controller
NS_BUILD_FILTER: "! @peer,@controller"

# Update specific namespaces by name
NS_BUILD_FILTER: "env-name-api,env-name-frontend"
```

Mixed use of aliases and names is not allowed

## Error Handling

- Invalid/non-existent namespace names: Pipeline fails
- Missing BG Domain: Pipeline fails when using aliases without BG Domain
- Mixed aliases and names: Pipeline fails with validation error