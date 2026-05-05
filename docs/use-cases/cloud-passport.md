# Cloud Passport Association — Use Cases

- [Cloud Passport Association — Use Cases](#cloud-passport-association--use-cases)
  - [UC-01: Environment Inherits Cluster Cloud Passport Automatically](#uc-01-environment-inherits-cluster-cloud-passport-automatically)
  - [UC-02: Environment Uses Explicitly Named Cloud Passport](#uc-02-environment-uses-explicitly-named-cloud-passport)
  - [UC-03: Environment Builds Without Cloud Passport](#uc-03-environment-builds-without-cloud-passport)
  - [UC-04: Environment Uses Passport from Custom Location](#uc-04-environment-uses-passport-from-custom-location)
  - [UC-05: Parameter Source Traceability](#uc-05-parameter-source-traceability)
    - [Example](#example)

## UC-01: Environment Inherits Cluster Cloud Passport Automatically

**Pre-requisites:**

- A Cloud Passport file `<cluster-name>.yml` exists under `cloud-passport/` at cluster level
- `env_definition.yml` does not contain a `cloudPassport` field

**Trigger:**

- Environment build is started

**Steps:**

1. The system reads `env_definition.yml`
2. The system detects that the `cloudPassport` field is not defined
3. The system walks up the directory structure to the cluster level
4. The system locates `cloud-passport/<cluster-name>.yml`
5. The passport is resolved
6. All passport sections are merged into `cloud.yml`

**Results:**

- `cloud.yml` contains cluster-level deployment parameters
- Build completes successfully

**Notes:**

- Each parameter includes traceability metadata (passport name and version)

## UC-02: Environment Uses Explicitly Named Cloud Passport

**Pre-requisites:**

- `env_definition.yml` contains `inventory.cloudPassport: <name>`
- A matching `<name>.yml` exists in the repository hierarchy

**Trigger:**

- Environment build is started

**Steps:**

1. The system reads the `cloudPassport` field
2. The system searches for `<name>.yml` starting from the environment directory
3. The system walks upward to the repository root
4. The closest matching file is selected
5. The passport is resolved
6. The passport is merged into `cloud.yml`

**Alternate Flow:**

- If no matching passport is found:
  - The build fails with an error
- If multiple matches exist:
  - The closest file in the hierarchy is used

**Results:**

- `cloud.yml` is populated using the explicitly selected passport

## UC-03: Environment Builds Without Cloud Passport

**Pre-requisites:**

- No `cloud-passport/` directory exists in the cluster
- `env_definition.yml` does not define `cloudPassport`

**Trigger:**

- Environment build is started

**Steps:**

1. The system reads `env_definition.yml`
2. No `cloudPassport` field is found
3. The system searches for a passport at cluster level
4. No passport is found
5. Passport processing is skipped
6. A log message is recorded:

  - "No cloud passport definition found. Cloud passport processing skipped."

**Results:**

- `cloud.yml` is not modified by passport logic
- Build continues successfully

## UC-04: Environment Uses Passport from Custom Location

**Pre-requisites:**

- `env_definition.yml` contains `inventory.cloudPassport: <custom-name>`
- `<custom-name>.yml` exists somewhere in the repository

**Trigger:**

- Environment build is started

**Steps:**

1. The system reads the `cloudPassport` field
2. The system searches for `<custom-name>.yml`
3. The system resolves the first matching file found
4. The passport is merged into `cloud.yml`

**Results:**

- `cloud.yml` contains parameters from the custom passport only

## UC-05: Parameter Source Traceability

**Pre-requisites:**

- `cloud.yml` has been generated

**Trigger:**

- A user inspects a parameter in `cloud.yml`

**Steps:**

1. The user opens `cloud.yml`
2. The user inspects parameter entries
3. Each parameter includes an inline comment with:

   - passport name
   - passport version

4. The user identifies the parameter source

### Example

```text
ZOOKEEPER_ADDRESS: zookeeper.zookeeper:2181  # cloud passport: cluster-01 version: 1.5
```

**Results:**

- Parameter origin is fully traceable from the file itself