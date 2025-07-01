# Environment Templates

Environment templates define the structure and components of different environment types in EnvGene. They specify how tenant, cloud, and namespace configurations should be organized.

## Simple Template

A basic environment template with minimal configuration:

```yaml title="simple.yaml"
--8<-- "samples/templates/env_templates/simple.yaml"
```

## Composite Templates

More complex templates for different deployment scenarios:

### Development Environment
```yaml title="composite-dev.yaml"
--8<-- "samples/templates/env_templates/composite-dev.yaml"
```

### Production Environment
```yaml title="composite-prod.yaml"
--8<-- "samples/templates/env_templates/composite-prod.yaml"
```

## Template Structure

Environment templates typically include:

- **tenant**: Reference to tenant configuration template
- **cloud**: Reference to cloud infrastructure template  
- **namespaces**: Array of namespace templates to be deployed

Each template uses Jinja2 templating (`{{ templates_dir }}`) to reference other template files in the template artifact. 
