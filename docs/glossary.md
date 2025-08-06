# Glossary

## Environment

A logical grouping representing parameters for deployment target, defined by a unique combination of cluster and environment name (e.g., `cluster-01/env-1`). See [Environment Instance Objects](/docs/envgene-objects.md#environment-instance-objects)

## Namespace

An EnvGene object that groups parameters specific to applications within a single namespace in a cluster. Defined in the Environment Instance. See [Namespace](/docs/envgene-objects.md#namespace)

## deployPostfix

A short identifier for a [Namespace](/docs/envgene-objects.md#namespace) role. Used in the Solution Descriptor. Typically matches the namespace folder name or template name.

## Effective Set

The complete set of parameters generated for a specific Environment, used by consumers (e.g., ArgoCD). See [Effective Set Structure](/docs/calculator-cli.md#version-20-effective-set-structure).

## Environment Inventory

The configuration file describing a specific Environment, including template reference and parameters. See [env_definition.yml](/docs/envgene-configs.md#env_definitionyml).

## Template Artifact

A versioned template used to generate Environment Instances. Maven artifact.

## Instance Repository

The git repository containing Environment Inventories, generated Environment Instances, and related configuration.
