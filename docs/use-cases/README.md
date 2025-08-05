# EnvGene Use Cases

This catalog provides an overview of common use cases for EnvGene. Each use case describes a specific scenario where EnvGene provides value, without delving into technical implementation details.

## Environment Configuration

| Use Case | Description | Related Features |
|----------|-------------|-----------------|
| [Simplified Environment Configuration](auto-environment-name.md) | Automatically derive environment names from folder structure to reduce redundancy and prevent inconsistencies | [Environment Inventory Generation](../env-inventory-generation.md#automatic-environment-name-derivation) |

## Template Management

| Use Case | Description | Related Features |
|----------|-------------|-----------------|
| Template Overrides | Customize specific parts of templates without modifying the original template files | [Template Override](../features/template-override.md) |
| AppDef/RegDef Template Management | Manage application definitions and registry definitions using templates | [AppDef/RegDef Template Management](../features/appdef-regdef-template-management.md) |

## Deployment

| Use Case | Description | Related Features |
|----------|-------------|-----------------|
| Environment Instance Generation | Generate environment instances from templates | [Environment Inventory Generation](../env-inventory-generation.md) |

## How to Add New Use Cases

To add a new use case:

1. Create a markdown file in the `use-cases` directory with a descriptive name
2. Follow the simple format:
   - Name: Short, descriptive title
   - Description: User-focused description following "As a [role], I want to [action], so that [benefit]" format
   - Features Used: Links to relevant feature documentation
   - Benefits: Bullet points highlighting key benefits
   - Example Scenario: A simple example of the use case in action
3. Add the use case to this catalog under the appropriate category
