# Spec Delta

## Purpose

Defines how the four `current_env.cluster` connection macros (`cloud_api_protocol`, `cloud_api_url`, `cloud_api_port`,
`cloud_public_url`) obtain their values when the environment configuration is generated, from the Environment
Inventory's `clusterUrl` and, when `clusterUrl` is absent, from the Cloud Passport.

## ADDED Requirements

### Requirement: Resolve cluster connection macros from the Environment Inventory when clusterUrl is set

When the Environment Inventory sets `clusterUrl`, the generator SHALL derive each of the four `current_env.cluster`
connection macros from `clusterUrl` and SHALL NOT consult the Cloud Passport for them.

#### Scenario: clusterUrl is set and no Cloud Passport is used

- **WHEN** an environment whose Environment Inventory sets `clusterUrl` is generated without a Cloud Passport
- **THEN** in the generated environment configuration `current_env.cluster.cloud_public_url` is the host parsed from
  `clusterUrl`, and `cloud_api_protocol`, `cloud_api_url`, and `cloud_api_port` are the protocol, host, and port
  parsed from `clusterUrl`

#### Scenario: clusterUrl is set and a Cloud Passport is also present

- **WHEN** an environment whose Environment Inventory sets `clusterUrl` is generated with a Cloud Passport that also
  carries cluster values
- **THEN** in the generated environment configuration the four `current_env.cluster` connection macros are derived
  from `clusterUrl`, and the Cloud Passport cluster values are not used for them

### Requirement: Fall back to the Cloud Passport when clusterUrl is not set

When the Environment Inventory does not set `clusterUrl`, the generator SHALL resolve each `current_env.cluster`
connection macro from the corresponding Cloud Passport cluster value, and SHALL leave a macro empty when the Cloud
Passport does not provide its value.

#### Scenario: clusterUrl is not set and the Cloud Passport provides the cluster values

- **WHEN** an environment whose Environment Inventory does not set `clusterUrl` is generated with a Cloud Passport that
  carries the cluster public host, API host, API port, and protocol
- **THEN** in the generated environment configuration `current_env.cluster.cloud_public_url` is the Cloud Passport
  public host, and the three API macros are the Cloud Passport API host, API port, and protocol, so a template host
  `<prefix>.{{ current_env.cluster.cloud_public_url }}` renders with its domain

#### Scenario: clusterUrl is not set and no Cloud Passport is used

- **WHEN** an environment whose Environment Inventory does not set `clusterUrl` is generated without a Cloud Passport
- **THEN** in the generated environment configuration the four `current_env.cluster` connection macros are empty
  strings

#### Scenario: clusterUrl is not set and the Cloud Passport omits a cluster value

- **WHEN** an environment whose Environment Inventory does not set `clusterUrl` is generated with a Cloud Passport that
  carries the public host but omits the API port
- **THEN** in the generated environment configuration `current_env.cluster.cloud_public_url` is the Cloud Passport
  public host and `current_env.cluster.cloud_api_port` is an empty string
