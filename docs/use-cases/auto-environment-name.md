# Use Case: Automatic Environment Name Derivation

## Name
Simplified Environment Configuration

## Description
As an environment administrator, I want to avoid redundantly specifying the environment name in both the folder structure and the configuration file, so that I can reduce manual effort and minimize the risk of inconsistencies.

## Features Used
- [Environment Inventory Generation](../env-inventory-generation.md#automatic-environment-name-derivation)

## Benefits
- Reduces redundancy in environment configuration
- Minimizes the risk of human error from inconsistent naming
- Simplifies environment creation process
- Maintains backward compatibility with existing configurations

## Example Scenario
When creating a new environment in the path `/environments/cluster01/dev01/Inventory/`, the administrator can omit the `environmentName` field in the `env_definition.yml` file. The system will automatically derive the environment name as "dev01" from the folder structure.
