# Spec Delta

## Purpose

Defines where the instance pipeline publishes rendered Application and Registry Definitions for each value of
`app_reg_defs_placement`, and which of those published locations the pipeline reads back when it resolves a
definition. The capability covers the write side of `app_reg_def_process`, the placement validation rule, and the
resolution order that consumers of the definitions follow.

## ADDED Requirements

### Requirement: Placement mode selects the definition output locations

The `app_reg_defs_placement` attribute of `configuration/config.yml` SHALL select where `app_reg_def_process` writes
the rendered definitions and the definition overrides. Allowed values SHALL be `root`, `env`, and `dual`, and the
default, used when the attribute is absent, SHALL be `root`.

#### Scenario: attribute is absent and the default applies

- **WHEN** `configuration/config.yml` does not set `app_reg_defs_placement` and `app_reg_def_process` runs
- **THEN** the effective definitions are written to `appdefs/` and `regdefs/` at the repository root, and the
  per-environment `environments/<cluster>/<env>/AppDefs/` and `RegDefs/` directories are not created

#### Scenario: root placement

- **WHEN** `app_reg_defs_placement` is `root` and `app_reg_def_process` runs
- **THEN** the effective definitions, including the definition overrides from `configuration/appdefs/` and
  `configuration/regdefs/`, are written to `appdefs/` and `regdefs/` at the repository root, and no per-environment
  definition directory is written

#### Scenario: env placement

- **WHEN** `app_reg_defs_placement` is `env` and `app_reg_def_process` runs
- **THEN** the effective definitions, including the definition overrides, are written to
  `environments/<cluster>/<env>/AppDefs/` and `environments/<cluster>/<env>/RegDefs/`, and `appdefs/` and `regdefs/`
  at the repository root keep the content committed before the run

#### Scenario: dual placement writes both locations

- **WHEN** `app_reg_defs_placement` is `dual` and `app_reg_def_process` runs
- **THEN** the effective definitions are written to `appdefs/` and `regdefs/` at the repository root and to
  `environments/<cluster>/<env>/AppDefs/` and `environments/<cluster>/<env>/RegDefs/`

#### Scenario: a repeated run is idempotent in every mode

- **WHEN** `app_reg_def_process` runs twice in a row for the same environment in the same placement mode
- **THEN** the definition directories and files after the second run are the same as after the first run

### Requirement: Placement value is validated against the allowed set

`app_reg_defs_placement` SHALL be declared in the configuration schema with the `root`, `env` and `dual` enum and a
`root` default. The value SHALL be matched exactly, so an upper-case or otherwise unknown value is rejected when the
pipeline reads `configuration/config.yml`, before any definition directory is created or removed.

#### Scenario: unknown value is rejected before any folder change

- **WHEN** `configuration/config.yml` sets `app_reg_defs_placement` to a value other than `root`, `env` or `dual` and
  the pipeline reads the configuration
- **THEN** the configuration validation fails and `app_reg_def_process` does not create, overwrite or remove any
  definition directory

#### Scenario: value is matched case-sensitively

- **WHEN** `configuration/config.yml` sets `app_reg_defs_placement` to `ROOT`
- **THEN** the configuration validation fails with the same rejection as an unknown value

### Requirement: Root placement removes the per-environment definition directories

Under `root` placement the step SHALL remove `environments/<cluster>/<env>/AppDefs/` and
`environments/<cluster>/<env>/RegDefs/`, so a repository that switches to the default layout is left without stale
compatibility copies. Under `env` and `dual` placement the step SHALL rebuild both directories from the current run,
so a file no definition produces is not left behind.

#### Scenario: legacy per-environment directories are removed under root placement

- **WHEN** an instance repository holds `environments/<cluster>/<env>/AppDefs/` and `RegDefs/` from an earlier run and
  `app_reg_def_process` runs with `root` placement
- **THEN** both per-environment directories are absent after the run and `appdefs/` and `regdefs/` at the repository
  root hold the effective definitions

#### Scenario: files no definition produces are removed from the rebuilt pair

- **WHEN** `environments/<cluster>/<env>/AppDefs/` holds a file that no current template or definition override
  produces and `app_reg_def_process` runs with `env` or `dual` placement
- **THEN** that file is absent after the run

#### Scenario: root files are not cleaned

- **WHEN** `appdefs/` at the repository root holds a file that no current template or definition override produces and
  `app_reg_def_process` runs in any placement mode
- **THEN** that file is still present after the run

### Requirement: Definition resolution follows the placement mode

A pipeline consumer that resolves an Application Definition or a Registry Definition by name SHALL search the
locations the placement mode selects, in this order: `appdefs/` and `regdefs/` at the repository root only under
`root`, `environments/<cluster>/<env>/AppDefs/` and `RegDefs/` only under `env`, and the repository root location
first with the per-environment location as a fallback under `dual`.

#### Scenario: root placement reads the root location only

- **WHEN** a definition is resolved for an environment under `root` placement and the definition exists in `appdefs/`
  or `regdefs/` at the repository root
- **THEN** the root file is used and the per-environment directories are not read

#### Scenario: env placement reads the per-environment location only

- **WHEN** a definition is resolved for an environment under `env` placement and the definition exists in
  `environments/<cluster>/<env>/AppDefs/` or `RegDefs/`
- **THEN** the per-environment file is used, and a file of the same name in the repository root location is not read
  for that environment

#### Scenario: dual placement prefers the root location

- **WHEN** a definition is resolved under `dual` placement and files of the same name exist in both the repository root
  location and `environments/<cluster>/<env>/AppDefs/` or `RegDefs/`
- **THEN** the root file is used, and the per-environment file is used only when the root location does not hold that
  name

#### Scenario: a definition missing from every selected location fails the run

- **WHEN** a definition is resolved and none of the locations the placement mode selects holds it
- **THEN** the pipeline job fails and the error message names the missing definition and every location that was
  searched

### Requirement: Local definition path variables point at the primary location

The `LOCAL_APPDEFS_PATH` and `LOCAL_REGDEFS_PATH` values a pipeline job exports for a consumer that reads definitions
from the file system SHALL point at the primary location of the placement mode: the repository root directories under
`root` and `dual`, and `environments/<cluster>/<env>/AppDefs/` and `RegDefs/` under `env`.

#### Scenario: env placement exports the per-environment paths

- **WHEN** a pipeline job exports `LOCAL_APPDEFS_PATH` and `LOCAL_REGDEFS_PATH` for an environment under `env`
  placement
- **THEN** both values point into `environments/<cluster>/<env>/`, and a consumer reading them finds the effective
  definitions of the current run

#### Scenario: root placement exports the root paths

- **WHEN** a pipeline job exports `LOCAL_APPDEFS_PATH` and `LOCAL_REGDEFS_PATH` for an environment under `root` or
  `dual` placement
- **THEN** both values point at `appdefs/` and `regdefs/` at the repository root

### Requirement: Dual placement is retained for existing consumers

`dual` SHALL stay an accepted value so a repository whose consumers read the per-environment layout keeps working
after the default changes to `root`. Such a repository SHALL pin the value explicitly, because the absent attribute
resolves to `root` and removes the per-environment directories.

#### Scenario: pinning dual preserves the legacy layout across the default change

- **WHEN** an instance repository sets `app_reg_defs_placement: dual` and `app_reg_def_process` runs after the default
  becomes `root`
- **THEN** both the repository root directories and the per-environment directories hold the effective definitions, and
  a consumer reading either layout resolves the current definitions
