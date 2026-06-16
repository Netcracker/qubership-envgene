# Refactor migrated parameters

- [Refactor migrated parameters](#refactor-migrated-parameters)
  - [Description](#description)
  - [Prerequisites](#prerequisites)
  - [1. Replace multi-line strings with YAML objects](#1-replace-multi-line-strings-with-yaml-objects)
  - [2. Move Cloud Passport parameters into the Cloud Passport](#2-move-cloud-passport-parameters-into-the-cloud-passport)
  - [3. Split the parameters by reuse](#3-split-the-parameters-by-reuse)
  - [4. Replace plaintext secrets with credential macros](#4-replace-plaintext-secrets-with-credential-macros)

## Description

A CMDB migration first copies parameters as they are, so a freshly migrated environment holds the CMDB values
verbatim. This guide cleans them up. Each section is independent, so do them in any order. Do them only after the
environment generates.

## Prerequisites

- An environment migrated with
  [Migrate CMDB environments to EnvGene](/docs/cmdb-migration/migrate-cmdb-to-envgene.md) that already generates.

## 1. Replace multi-line strings with YAML objects

Find parameters whose value is a multi-line YAML-in-string blob. Replace each one with a real YAML object, so the
structure is parsed rather than carried as text.

## 2. Move Cloud Passport parameters into the Cloud Passport

Find connection parameters that sit in the ParameterSets. Move them into the Cloud Passport, where every
environment on the cluster reads them from one place. For which cloud fields belong in the passport, see
[Create the Cloud Passport](/docs/cmdb-migration/migrate-cmdb-to-envgene.md#32-create-the-cloud-passport).

## 3. Split the parameters by reuse

Sort the remaining parameters into two groups and move each group to its scope.

- Common to every environment, on-site and off-site, goes into a Template ParameterSet in the template
  repository.
- Environment-specific goes into an instance ParameterSet at the repository, cluster, or environment scope.

## 4. Replace plaintext secrets with credential macros

Find plaintext secrets in the parameters. Replace each one with a credential macro, for example
`${creds.get("id").field}`, and add a matching Credential object. Copy the
[Credentials blank](/docs/cmdb-migration/blanks/credentials.yml) as a starting point.
