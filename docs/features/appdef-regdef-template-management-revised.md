# AppDef/RegDef Template Management

- [AppDef/RegDef Template Management](#appdefregdef-template-management)
  - [Problem Statement](#problem-statement)
  - [Approach](#approach)
    - [Template-Based Generation](#template-based-generation)
    - [Configuration Overrides](#configuration-overrides)
    - [Flexible Source Control](#flexible-source-control)
  - [Template Structure](#template-structure)
  - [Configuration Files](#configuration-files)
  - [Use Cases](#use-cases)
    - [Environment-Specific Configuration](#environment-specific-configuration)
    - [Cluster-Specific Overrides](#cluster-specific-overrides)
    - [External Definition Sources](#external-definition-sources)
  - [Troubleshooting](#troubleshooting)
    - [Template Rendering Issues](#template-rendering-issues)
    - [Configuration Override Problems](#configuration-override-problems)
    - [External Source Issues](#external-source-issues)
  - [Related Documentation](#related-documentation)

## Problem Statement

Managing application and registry configurations across multiple environments presents several challenges:

1. **Manual Configuration**: Without templates, each environment requires manual creation and maintenance of AppDef and RegDef files.
2. **Configuration Consistency**: Ensuring consistent configuration across environments is difficult with manual processes.
3. **Environment-Specific Overrides**: Different environments often require specific configuration values.
4. **Reusability**: Common configuration patterns should be reusable across environments.

Goals:

1. Provide template-based generation of AppDef and RegDef files
2. Support environment-specific and cluster-specific configuration overrides
3. Enable flexible sourcing of definition files (local templates or external sources)
4. Ensure consistent configuration across environments

## Approach

EnvGene provides a comprehensive template management system for generating environment-specific AppDef and RegDef files.

### Template-Based Generation

- **Jinja2 Templates**: Uses Jinja2 templating engine for powerful and flexible template rendering
- **Environment Variables**: Supports environment variable substitution in templates
- **Default Values**: Templates can include default values for optional parameters
- **Validation**: Validates rendered output against JSON schemas

### Configuration Overrides

- **Global Overrides**: Apply configuration values across all templates
- **Cluster-Specific Overrides**: Override values for specific clusters
- **Override Precedence**: Cluster-specific overrides take precedence over global overrides

### Flexible Source Control

- **Local Templates**: Render templates from local repository
- **External Sources**: Use pre-rendered AppDef/RegDef files from external job artifacts
- **Pipeline Control**: Control source using pipeline parameters

## Template Structure

The template directory structure is organized as follows:

```
/templates/
├── appdefs/
│   ├── app1.yaml.j2
│   ├── app2.yml.j2
│   └── ...
├── regdefs/
│   ├── registry1.yaml.j2
│   ├── registry2.yml.j2
│   └── ...
└── configuration/
    └── appregdef_config.yaml
```

#### Instance Repository

```
/environments/
├── <cluster-name>/
│   ├── configuration/
│   │   └── appregdef_config.yaml (optional, cluster-specific overrides)
│   └── <env-name>/
│       ├── AppDefs/
│       │   ├── app1.yml
│       │   ├── app2.yml
│       │   └── ...
│       └── RegDefs/
│           ├── registry1.yml
│           ├── registry2.yml
│           └── ...
└── configuration/
    └── appregdef_config.yaml (optional, global overrides)
```

### Configuration

#### app_reg_def_mode

The `app_reg_def_mode` setting in `config.yml` controls how AppDef and RegDef data is handled:

```yaml
app_reg_def_mode: "auto"  # Can be "auto" or "local"
```

- **auto**: Automatically determine the source based on availability
- **local**: Use local template files only

#### appregdef_config.yaml

Configuration overrides can be specified in `appregdef_config.yaml`:

```yaml
appdefs:
  overrides:
    # Override by groupId:artifactId key
    "com.example:app1":
      version: "2.0.0"
      registry: "custom-registry"
    # Override by template name
    "app2":
      memory: "2048Mi"
      replicas: 3

regdefs:
  overrides:
    # Override by registry name
    "docker-registry":
      url: "https://custom-docker-registry.example.com"
    "maven-registry":
      credentials:
        username: "custom-user"
```

### Template Rendering Process

1. **Template Discovery**: The system searches for templates in `/templates/appdefs/` and `/templates/regdefs/` directories.
2. **Configuration Loading**: The system loads configuration from `appregdef_config.yaml` files, with the following precedence:
   - Cluster-specific configuration (`/environments/<cluster-name>/configuration/appregdef_config.yaml`)
   - Global configuration (`/environments/configuration/appregdef_config.yaml`)
3. **Template Rendering**: Each template is rendered using Jinja2 with the following context:
   - Environment variables
   - Configuration overrides
   - For AppDefs: `artifactId`, `groupId`, and `app_lookup_key` (derived from template content)
4. **Output Generation**: Rendered files are saved to the appropriate directories:
   - AppDefs: `/environments/<cluster-name>/<env-name>/AppDefs/`
   - RegDefs: `/environments/<cluster-name>/<env-name>/RegDefs/`

### External Definition Sources

The system can use AppDef and RegDef files from external job artifacts instead of rendering templates locally. This is controlled by the `APP_REG_DEFS_JOB` pipeline parameter:

1. When `APP_REG_DEFS_JOB` is set to a job name:
   - The system downloads and unpacks a `definitions.zip` file from the specified job
   - Files are copied from paths specified by `app_defs_path` and `reg_defs_path` parameters
   - No local template rendering occurs

2. When `APP_REG_DEFS_JOB` is not set:
   - The system discovers and renders templates from the local repository
   - The rendering process is controlled by the `app_reg_def_mode` setting

## Pipeline Parameters

### APP_REG_DEFS_JOB

**Description**: Controls the source of AppDef/RegDef files for environment generation.

**Values**:
- When set to a job name: Uses AppDef/RegDef files from the specified job's artifacts
- When not set (empty): Uses local template rendering from the template repository

**Default**: Empty (local template rendering)

## Use Cases

### Standard Environment Build

1. Set `app_reg_def_mode: "local"` in `config.yml`
2. Create templates in `/templates/appdefs/` and `/templates/regdefs/`
3. Create `appregdef_config.yaml` with environment-specific overrides
4. Run the environment build process
5. Templates are rendered and saved to the appropriate directories

### External Definition Source

1. Set `APP_REG_DEFS_JOB: "appdef-generation-job"`
2. Set `app_defs_path` and `reg_defs_path` to the appropriate paths within the job artifacts
3. Run the environment build process
4. AppDef and RegDef files are copied from the job artifacts instead of being rendered locally

## JSON Schemas

### AppDef Schema

AppDef files must conform to the following schema structure:

```json
{
  "type": "object",
  "required": ["name", "artifactId", "groupId", "version", "registry"],
  "properties": {
    "name": { "type": "string" },
    "artifactId": { "type": "string" },
    "groupId": { "type": "string" },
    "version": { "type": "string" },
    "registry": { "type": "string" },
    "deployment": {
      "type": "object",
      "properties": {
        "replicas": { "type": "integer" },
        "resources": {
          "type": "object",
          "properties": {
            "requests": {
              "type": "object",
              "properties": {
                "memory": { "type": "string" },
                "cpu": { "type": "string" }
              }
            },
            "limits": {
              "type": "object",
              "properties": {
                "memory": { "type": "string" },
                "cpu": { "type": "string" }
              }
            }
          }
        }
      }
    }
  }
}
```

### RegDef Schema

RegDef files must conform to the following schema structure:

```json
{
  "type": "object",
  "required": ["name", "type"],
  "properties": {
    "name": { "type": "string" },
    "type": { "type": "string", "enum": ["docker", "maven", "npm", "pypi"] },
    "url": { "type": "string", "format": "uri" },
    "credentials": {
      "type": "object",
      "properties": {
        "username": { "type": "string" },
        "password": { "type": "string" }
      }
    }
  }
}
```

## Troubleshooting

### Common Issues

1. **Missing Template Files**: Ensure templates exist in the correct directories (`/templates/appdefs/` and `/templates/regdefs/`).
2. **Configuration Not Applied**: Check the precedence of configuration files and ensure overrides are correctly formatted.
3. **Template Rendering Errors**: Verify that templates contain valid Jinja2 syntax and all required variables are defined.
4. **External Job Artifacts Not Found**: Verify that the specified job exists and contains a `definitions.zip` file with the expected structure.

### Debugging

1. Enable debug logging to see detailed information about the template rendering process.
2. Check the rendered files in the output directories to verify that templates are being processed correctly.
3. Review the template rendering logs for any errors during the process.

## Implementation Details in EnvGene

The AppDef/RegDef template management is implemented in the env-builder component of EnvGene. The main implementation is in the following files:

- `env-builder/main.yaml`: Contains the main logic for determining whether to use external definitions or render templates locally.
- `env-builder/roles/generate_appregdefs/tasks/main.yaml`: Implements the template discovery, configuration loading, and rendering process.
- `env-builder/roles/generate_appregdefs/tasks/render_single_appdef.yaml`: Handles the rendering of individual AppDef templates.
- `env-builder/roles/generate_appregdefs/tasks/render_single_regdef.yaml`: Handles the rendering of individual RegDef templates.

The implementation follows these steps:

1. Check if `APP_REG_DEFS_JOB` is defined and has a non-empty value:
   - If yes, download and unpack the external definitions from the specified job.
   - If no, proceed with local template rendering.

2. For local template rendering:
   - Find AppDef and RegDef templates in the templates directory.
   - Load configuration overrides from `appregdef_config.yaml`.
   - Render each template using Jinja2 with the appropriate context.
   - Save the rendered files to the environment's AppDefs and RegDefs directories.

3. The rendered AppDef and RegDef files are then available for use in the environment build process.
