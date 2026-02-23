# Glossary

- [Glossary](#glossary)
  - [Custom Params](#custom-params)
  - [Deploy Postfix](#deploy-postfix)
  - [Environment](#environment)
  - [Environment Inventory](#environment-inventory)
  - [Environment Template](#environment-template)
  - [Effective Set](#effective-set)
  - [Instance Repository](#instance-repository)
  - [Namespace](#namespace)
  - [Environment Template Artifact](#environment-template-artifact)

This glossary provides definitions of key terms used in the EnvGene documentation.

## Custom Params

Session-scoped parameters passed via the Instance pipeline parameter [`CUSTOM_PARAMS`](/docs/instance-pipeline-parameters.md#custom_params) and applied to the [Effective Set](/docs/features/calculator-cli.md#version-20-effective-set-structure) with the highest priority. Custom Params are not persisted between parameter calculation sessions and are treated as sensitive. See [Calculator CLI](/docs/features/calculator-cli.md) for details.

## Deploy Postfix

A short identifier for a [Namespace](/docs/envgene-objects.md#namespace) role. Used in the Solution Descriptor. Typically matches the namespace folder name or template name.

## Environment

A logical grouping representing parameters for deployment target, defined by a unique combination of cluster and environment name (e.g., `cluster-01/env-1`). See [Environment Instance Objects](/docs/envgene-objects.md#environment-instance-objects)

## Environment Inventory

The configuration file describing a specific Environment, including template reference and parameters. See [env_definition.yml](/docs/envgene-configs.md#env_definitionyml).

## Environment Template

A file structure within the Template Repository describing the structure and parameters of a solution type. Consists of a Template Descriptor and component templates (Tenant, Cloud, Namespaces). Template Descriptors can be Jinja templates (`.yml.j2`, `.yaml.j2`) or static YAML files (`.yml`, `.yaml`). 

A single Environment Template can be used for multiple projects or environment types (commonly referred to as a "unified Environment Template"), with namespace filtering used to include only relevant components for each specific deployment. See [Environment Template Objects](/docs/envgene-objects.md#environment-template-objects) and [Namespace Filtering in Template Descriptor](/docs/features/namespace-filtering-in-template-descriptor.md).

## Effective Set

The complete set of parameters generated for a specific Environment, used by consumers (e.g., ArgoCD). See [Effective Set Structure](/docs/features/calculator-cli.md#version-20-effective-set-structure).

## Instance Repository

The Git repository containing Environment Inventories, generated Environment Instances, and related configuration.

## Namespace

An EnvGene object that groups parameters specific to applications within a single namespace in a cluster. Defined in the Environment Instance. See [Namespace](/docs/envgene-objects.md#namespace)

## Environment Template Artifact

A versioned Maven artifact containing one or more [Environment Templates](#environment-template) from the Template Repository. Published during Template Repository build process and referenced in the [Environment Inventory](/docs/envgene-configs.md#env_definitionyml) using `application:version` notation (e.g., `project-env-template:v1.2.3`). Used by EnvGene to generate Environment Instances. Also referred to as "Environment Template Artifact". See [Environment Template Objects](/docs/envgene-objects.md#environment-template-objects).
