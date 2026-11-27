# Spec Delta

## Purpose

Defines how the Effective Set generator routes each deployment-context parameter to the credentials file
or to the deployment parameters file by its sensitivity, keeping list values atomic so the deployer's
Helm value-file merge cannot drop data.

These requirements govern the version 2 Effective Set path. The version 1 path routes whole top-level keys
atomically and does not exhibit the list-split defect, so it is out of scope and no requirement or scenario
below covers it.

## ADDED Requirements

### Requirement: List values are atomic during separation

The Effective Set generator SHALL treat a list parameter value as an atomic unit when separating secured
from non-secured parameters, writing the whole list to the credentials file when the list holds a secured
value at any depth and leaving the whole list in the deployment parameters file otherwise.

#### Scenario: List of maps with a secured field

- **WHEN** an environment defines a list of maps where one element field holds a secured value
- **THEN** the deployment context writes the whole list to the credentials file, the deployment
  parameters file holds no entry for that key, and no element or value is dropped

#### Scenario: List of maps with no secured value

- **WHEN** an environment defines a list of maps where no field holds a secured value
- **THEN** the deployment context writes the whole list to the deployment parameters file, and the
  credentials file holds no entry for that key

#### Scenario: List of scalars with a secured element

- **WHEN** an environment defines a list of scalar values where at least one element is a secured value
- **THEN** the deployment context writes the whole list to the credentials file, and the deployment
  parameters file holds no entry for that key

### Requirement: Map values separate per key

The Effective Set generator SHALL separate a map parameter value per key, routing each secured key to the
credentials file and each non-secured key to the deployment parameters file, so a secured list nested in
a map does not pull the map's non-secured keys with it.

#### Scenario: Secured list nested in a map with non-secured siblings

- **WHEN** an environment defines a map whose keys include a list that holds a secured value and also
  non-secured scalar keys
- **THEN** the deployment context writes the whole nested list to the credentials file while the map's
  non-secured scalar keys stay in the deployment parameters file

#### Scenario: Map with mixed sensitivity and no list

- **WHEN** an environment defines a map that mixes secured and non-secured keys and holds no list value
- **THEN** the deployment context writes the secured keys to the credentials file and the non-secured
  keys to the deployment parameters file, and both are present after the value-file merge

### Requirement: External credential references inside a list

When separating parameters for an external-only environment, the Effective Set generator SHALL write a
list that holds an external credential reference whole to the credentials file, with every reference
resolved and no element dropped.

#### Scenario: List carrying an external credential reference

- **WHEN** an external-only environment defines a list where one element is an external credential
  reference
- **THEN** the deployment context writes the whole list to the credentials file, every external
  credential reference in the list is resolved to its reference value, and no element is dropped
