# How to define environment specific parameters schema
## Use case
I as DevOps want to define the set of parameters that should be specified by customer/onsite DevOps during environment generation.

## Steps
1. In my template (e.g. [composite-prod-template](../samples/templates/env_templates/composite-prod.yaml)) I am adding section for environment specific parameters schema
```yaml
...
envSpecificSchema: "{{ templates_dir }}/env_templates/composite-prod/env-specific-schema.yml"
...
```
2. I'm creating schema for the path (e.g. [env-specific-schema](../samples/templates/env_templates/composite-prod/env-specific-schema.yml))
3. I'm building template

## Schema structure
```yaml
envSpecific:
  # list of white listed parameters, that can be present on environment specific level
  # during environment specific parameters generation we will go thorough parameters 
  # and check that all of them are present and no other parameters are present. 
  # If no env_builder job will fail
  whiteList:
    cloud:
      e2eParameters:
        key3: "boolean"
      applications:
        APP:
          deployParameters: 
            key5: "string"
    namespaces:
      oss:
        deployParameters: 
          key4: "string"
        applications:
          OSS:
            deployParameters: 
              key5: "string"
# list of mandatory listed parameters that may be present at the environment level
# during generation of environment parameters we will go through all the parameters
# and check that they are present if they are not then we will show an error 
# with the list of parameters that need to be filled in.
# If there is no env_builder task, it will end with an error
  mandatoryList:
    cloud:
      e2eParameters:
        key3: "boolean"
      applications:
        APP:
          deployParameters: 
            key5: "string"
    namespaces:
      oss:
        deployParameters: 
          key4: "string"
        applications:
          OSS:
            deployParameters: 
              key5: "string"
  # list of black listed parameters, that can be present on environment specific level
  # if they will be present in the result of generation on any level, than env_builder job will fail
  blackList:
    deployParameters:
      - "key8"
      - "key9"
    e2eParameters:
      - "key10"
    technicalConfigurationParameters: []
```
