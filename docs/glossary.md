# Glossary

- [Glossary](#glossary)
  - [Custom Params](#custom-params)
  - [Deploy Postfix](#deploy-postfix)
  - [Environment](#environment)
  - [Environment Inventory](#environment-inventory)
  - [Environment Template](#environment-template)
  - [Template-rendered Definition](#template-rendered-definition)
  - [Definition Override](#definition-override)
  - [Effective Definition](#effective-definition)
  - [Effective Set](#effective-set)
  - [Instance Repository](#instance-repository)
  - [Namespace](#namespace)
  - [Environment Template Artifact](#environment-template-artifact)
  - [Solution Descriptor](#solution-descriptor)
  - [Deployment Descriptor](#deployment-descriptor)
  - [SBOM](#sbom)
  - [SBOM Cache](#sbom-cache)

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

## Template-rendered Definition

An Application or Registry Definition produced by rendering a template from the template repository. The filename comes from the definition's `name` field. See [Templates](/docs/features/app-reg-defs.md#templates).

## Definition Override

A plain YAML file in the instance repository that replaces a Template-rendered Definition with the same filename, or adds a new definition. Applied as-is, never rendered. See [Definition overrides](/docs/features/app-reg-defs.md#definition-overrides).

## Effective Definition

An Application or Registry Definition after template rendering and Definition Overrides are applied. Lives in the root-level `/appdefs/` and `/regdefs/` folders. See [Output layout](/docs/features/app-reg-defs.md#output-layout).

## Effective Set

The complete set of parameters generated for a specific Environment, used by consumers (e.g., ArgoCD). See [Effective Set Structure](/docs/features/calculator-cli.md#version-20-effective-set-structure).

## Instance Repository

The Git repository containing Environment Inventories, generated Environment Instances, and related configuration.

## Namespace

An EnvGene object that groups parameters specific to applications within a single namespace in a cluster. Defined in the Environment Instance. See [Namespace](/docs/envgene-objects.md#namespace)

## Environment Template Artifact

A versioned Maven artifact containing one or more [Environment Templates](#environment-template) from the Template Repository. Published during Template Repository build process and referenced in the [Environment Inventory](/docs/envgene-configs.md#env_definitionyml) using `application:version` notation (e.g., `project-env-template:v1.2.3`). Used by EnvGene to generate Environment Instances. Also referred to as "Environment Template Artifact". See [Environment Template Objects](/docs/envgene-objects.md#environment-template-objects).

## Solution Descriptor

A list of `application:version` entries with their [Deploy Postfixes](#deploy-postfix) that declares which applications are deployed to an [Environment](#environment) and at which versions. Drives [Effective Set](#effective-set) generation. See [Solution Descriptor Processing](/docs/features/sd-processing.md).

## Deployment Descriptor

An artifact describing an application's deployable components (services, configurations, and images) together with their registry coordinates. EnvGene resolves and downloads one per application and derives the Application [SBOM](#sbom) from it. See [SBOM Generation](/docs/features/sbom-generation.md) and [Artifact resolution](/docs/features/artifact-resolution.md).

## SBOM

A Software Bill of Materials: the CycloneDX list of an application's components, derived from its [Deployment Descriptor](#deployment-descriptor) and consumed by [Effective Set](#effective-set) generation. EnvGene produces an Application SBOM per `application:version` and an Environment Template SBOM per template. See [SBOM](/docs/features/sbom.md).

## SBOM Cache

The `/sboms/` directory of the [Instance Repository](#instance-repository) where generated [SBOMs](#sbom) are stored and committed, keyed by application name, so an SBOM is regenerated only when its file is absent. Whether SBOMs are cached is set by the `sbom_cache.enabled` configuration, and the cache is cleaned by SBOM retention. See [SBOM Storage and Retention](/docs/features/sbom.md#sbom-storage-and-retention) and [SBOM Retention](/docs/features/sbom-retention.md).
