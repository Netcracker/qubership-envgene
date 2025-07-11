# Environment Generator (EnvGene) Samples

This section contains comprehensive examples and samples for working with EnvGene. The samples are organized into logical categories to help you understand different aspects of environment configuration and template management.

## Sample Categories

### 🏗️ [Environment Templates](environment-templates.md)
Templates that define the structure and components of different environment types. Includes simple and composite templates for various deployment scenarios.

### ⚙️ [Parameter Sets](parameter-sets.md)  
Configuration parameter sets that can be applied to applications within environments. Includes examples for core, BSS, billing, and technical components.

### 📊 [Resource Profiles](resource-profiles.md)
Resource configuration profiles for different environments and applications. Contains development and production overrides for optimal resource management.

### 🌐 [Environment Configurations](environment-configurations.md)
Specific environment instances deployed in clusters. Shows how to configure inventories, credentials, parameters, and resource profiles for actual environments.

### 🔧 [Configuration Files](configuration-files.md)
System-wide configuration files for registry connections, integrations, and external system management.

## Getting Started

If you're new to EnvGene, we recommend exploring the samples in this order:

1. **Environment Templates** - Understand the basic structure
2. **Parameter Sets** - Learn how to configure applications  
3. **Resource Profiles** - See how to manage resources
4. **Environment Configurations** - Put it all together
5. **Configuration Files** - Configure system integrations

## Structure

Instance git should have following structure

```yaml
├── configuration
│   ├── credentials # Credentials, that can be used in configuration
│   │   └── credentials.yml
│   └── registry.yml # Definition of the list of registries for templates
│   └── integration.yml # Configuration of integrations with discovery repository. Also here a token is set for committing to itself (to the instance repository) 
│   └── config.yml # Repository wide configuration.
└── environments
    ├── <cloud_name> #Grouping level of the environments, only 1 grouping level is supported
    │   ├── env_name3
    │   │   └── ...
    │   ├── env_name4
    │   │   └── ...
    │   ├── credentials # Optional, folder for shared credentials
    │   │   └── credentials.yml # File with shared credentials.
    │   ├── parameters # Optional, folder for shared parameter sets
    │   │   └── shared-paramset.yml # File with shared parameter sets.
    │   └── shared-template-variables # Optional, folder for shared template variables file
    │       └── shared-template-variables.yml # File with shared template variables, key: value
    ├── credentials # Optional, folder for shared credentials
    │   └── credentials.yml # File with shared credentials.
    ├── parameters # Optional, folder for shared parameter sets
    │   └── shared-paramset.yml # File with shared parameter sets.
    └── shared-template-variables # Optional, folder for shared template variables file
        └── shared-template-variables.yml # File with shared template variables, key: value
```

## Description of env_definition.yml

env_definition.yml should have following structure

```yaml
# mandatory | Structure that defines inventory of your environment
inventory:                    
    # mandatory 
    # name of the environment, e.g. dev01
    environmentName: string
    # mandatory 
    # name of the tenant for your environment
    tenantName: string
    # optional
    # name of the cloud for your environment
    cloudName: string
    # optional 
    # URL of the cluster from kube_config
    clusterUrl: string         
    # optional 
    # Environment description
    description: string        
    # optional
    # Environment owners
    owners: string                   
    config:
        # optional, default false
        # if true, during CMDB import credentials IDs, 
        # except defined with #"credscl" or "credsns" 
        # will be update using pattern:
        # <tenant-name>-<cloud-name>-<env-name>-<cred-id>
        updateCredIdsWithEnvName: boolean
        # optional, default false
        # if true, during CMDB import resource profile
        # override (RPO) names will be update with env 
        # name will be update using pattern:
        # <tenant-name>-<cloud-name>-<env-name>-<RPO-name>
        updateRPOverrideNameWithEnvName: boolean
# mandatory
# definition of template that will be used
envTemplate:
    # mandatory
    # name of the template, name should correspond to 
    # the name of namespace in your template artifact
    name: "multidb"
    # optional
    # array of file names in 'credentials' folders that will override generated and defined for instance credentials
    sharedMasterCredentialFiles: array
    # optional
    # array of file names in 'shared-template-variables' folders that will be merged with additionalTemplateVariables
    sharedTemplateVariables: array
    # optional
    # additional variables that will be available
    # during template processing
    additionalTemplateVariables: hashmap
    # optional
    # envronment specific resource profiles override, 
    # array items should contain file name (w/o extension)
    # to the file located in "resource_profiles" dir
    envSpecificResourceProfiles: hashmap
        cloud: [ "env-specific-cloud-RP-override" ]
        bss: [ "env-specific-bss-RP-overrde" ]
    # optional
    # envronment specific deployment parameters set, 
    # array items should contain file name (w/o extension)
    # to the file located in "parameters" dir
    envSpecificParamsets: hashmap
        cloud: [ "env-specific-cloud" ]
        bss: [ "env-specific-bss" ]
    # optional
    # envronment specific e2e parameters set, 
    # array items should contain file name (w/o extension)
    # to the file located in "parameters" dir
    envSpecificE2EParamsets: hashmap
        cloud: [ "env-specific-tech-cloud" ]
        bss: [ "env-specific-e2e-bss" ]
    # optional
    # envronment specific technical parameters set, 
    # array items should contain file name (w/o extension)
    # to the file located in "parameters" dir
    envSpecificTechnicalParamsets: hashmap
        cloud: [ "env-specific-tech-cloud" ]
        bss: [ "env-specific-tech-bss" ]
    # mandatory
    # structure to define template artifact
    templateArtifact:
        # mandatory
        # registry name
        # should be listed in configuration/registry.yml
        registry: "default"
        # mandatory
        # repository name for zip artifact of template
        # should be listed in configuration/registry.yml
        repository: "snapshotRepository"
        # mandatory
        # repository name for storing Deployment Descriptor artifact of template
        # should be listed in configuration/registry.yml
        templateRepository: "stagingTemplateRepository"
        # mandatory
        # definition of template artifact that will be 
        # used for environment generation
        artifact:
            group_id: "deployment-configuration"
            artifact_id: "deployment-configuration-env-templates"
            version: "master-20240209.153935-69"
    # following parameters are automatically generated during job and display that version of Deployment Descriptor artifact of template was used for last environment generation
    generatedVersions:
        generateEnvironmentLatestVersion: "master-20240209.153935-69"
```

Sample is [here](/docs/samples/environments/cluster-01/env-01/Inventory/env_definition.yml)
