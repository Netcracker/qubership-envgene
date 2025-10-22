# Glossary

- [Glossary](#glossary)
  - [Deploy Postfix](#deploy-postfix)
  - [Environment](#environment)
  - [Environment Inventory](#environment-inventory)
  - [Effective Set](#effective-set)
  - [Instance Repository](#instance-repository)
  - [Namespace](#namespace)
  - [Template Artifact](#template-artifact)

This glossary provides definitions of key terms used in the EnvGene documentation.

## Deploy Postfix

A short identifier for a [Namespace](/docs/envgene-objects.md#namespace) role. Used in the Solution Descriptor. Typically matches the namespace folder name or template name.

## Environment

A logical grouping representing parameters for deployment target, defined by a unique combination of cluster and environment name (e.g., `cluster-01/env-1`). See [Environment Instance Objects](/docs/envgene-objects.md#environment-instance-objects)

## Environment Inventory

The configuration file describing a specific Environment, including template reference and parameters. See [env_definition.yml](/docs/envgene-configs.md#env_definitionyml).

## Effective Set

The complete set of parameters generated for a specific Environment, used by consumers (e.g., ArgoCD). See [Effective Set Structure](/docs/calculator-cli.md#version-20-effective-set-structure).

## Instance Repository

The Git repository containing Environment Inventories, generated Environment Instances, and related configuration.

## Namespace

An EnvGene object that groups parameters specific to applications within a single namespace in a cluster. Defined in the Environment Instance. See [Namespace](/docs/envgene-objects.md#namespace)

## Template Artifact

A versioned template used to generate Environment Instances. Maven artifact.
