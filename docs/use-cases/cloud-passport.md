# Cloud Passport Association — Use Cases

- [Cloud Passport Association — Use Cases](#cloud-passport-association--use-cases)
  - [UC-01: Environment Inherits Cluster Cloud Passport Automatically](#uc-01-environment-inherits-cluster-cloud-passport-automatically)
  - [UC-02: Environment Uses Explicitly Named Cloud Passport](#uc-02-environment-uses-explicitly-named-cloud-passport)
  - [UC-03: Environment Builds Without Cloud Passport](#uc-03-environment-builds-without-cloud-passport)
  - [UC-04: Environment Uses Passport from Custom Location](#uc-04-environment-uses-passport-from-custom-location)
  - [UC-05: Parameter Source Traceability](#uc-05-parameter-source-traceability)
    - [Example](#example)
  - [UC-06: Business Environments Auto-Associate the Business Passport in a Mixed Cluster](#uc-06-business-environments-auto-associate-the-business-passport-in-a-mixed-cluster)
  - [UC-07: Infra Environments Use an Explicit Infra Passport in a Mixed Cluster](#uc-07-infra-environments-use-an-explicit-infra-passport-in-a-mixed-cluster)
  - [UC-08: Mixed Cluster Failure When Infra Relies on Auto-Association](#uc-08-mixed-cluster-failure-when-infra-relies-on-auto-association)
  - [UC-09: Backward Compatibility for Existing Business Environments](#uc-09-backward-compatibility-for-existing-business-environments)

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
3. Each parameter includes an inline comment with: passport name, passport version

4. The user identifies the parameter source

### Example

```text
ZOOKEEPER_ADDRESS: zookeeper.zookeeper:2181  # cloud passport: cluster-01 version: 1.5
```

**Results:**

- Parameter origin is fully traceable from the file itself

## UC-06: Business Environments Auto-Associate the Business Passport in a Mixed Cluster

**Pre-requisites:**

- Mixed cluster exists under `/environments/<cluster-name>/`
- The cluster contains at least two passport files under:
  `/environments/<cluster-name>/cloud-passport/`
- The business default passport exists at:
  `cloud-passport/<cluster-name>.yml`
- The infra passport exists at:
  `cloud-passport/<cluster-name>-infra.yml`
- The business environment `env_definition.yml` does not include `inventory.cloudPassport`

**Trigger:**

- Build the business environment

**Steps:**

1. The system reads the business environment `env_definition.yml`
2. The system detects that `inventory.cloudPassport` is absent
3. The system resolves the passport via auto-association:
   `cloud-passport/<cluster-name>.yml`
4. The system merges all passport sections into the generated environment `cloud.yml`
5. The system generates traceability comments for passport-derived parameters

**Results:**

- Business environment `cloud.yml` contains business workload keys (for example sections/keys like `bss`, `core`, `storage`, `maas`, `dbaas`, `zookeeper`) if those keys exist in `cloud-passport/<cluster-name>.yml`
- For passport-derived values, inline comments reference:
  - `cloud passport: <cluster-name> version: <passport-version>`

## UC-07: Infra Environments Use an Explicit Infra Passport in a Mixed Cluster

**Pre-requisites:**

- Mixed cluster exists under `/environments/<cluster-name>/`
- The cluster contains:
  - business passport: `cloud-passport/<cluster-name>.yml`
  - infra passport: `cloud-passport/<cluster-name>-infra.yml`
- The infra environment `env_definition.yml` includes:

  ```yaml
  inventory:
    cloudPassport: <cluster-name>-infra
  ```

- The infra environment `env_definition.yml` does not rely on auto-association.

**Trigger:**

- Build the infra environment

**Steps:**

1. The system reads the infra environment `env_definition.yml`
2. The system detects `inventory.cloudPassport: <cluster-name>-infra`
3. The system resolves `cloud-passport/<cluster-name>-infra.yml` (search hierarchy resolution)
4. The system merges all passport sections into the infra environment generated `cloud.yml`
5. The system generates traceability comments for passport-derived parameters

**Results:**

- Infra environment cloud.yml contains only the keys present in `cloud-passport/<cluster-name>-infra.yml`
- Infra environment does not receive business-only keys from `cloud-passport/<cluster-name>.yml`
- For passport-derived values present in cloud.yml, traceability comments reference:
  - `cloud passport: <cluster-name>-infra version: <passport-version>`

## UC-08: Mixed Cluster Failure When Infra Relies on Auto-Association

**Pre-requisites:**

- Mixed cluster exists under `/environments/<cluster-name>/`
- Only the business default passport exists at:
  - `cloud-passport/<cluster-name>.yml` (contains business-only keys)
- The infra environment `env_definition.yml` does not include `inventory.cloudPassport`

**Trigger:**

- Build the infra environment and proceed to deployment

**Steps:**

1. The system reads the infra environment env_definition.yml
2. The system detects inventory.cloudPassport is absent
3. The system auto-associates the passport via cluster default: `cloud-passport/<cluster-name>.yml`
4. The system merges passport sections into the infra environment generated cloud.yml
5. The infra deployment context includes business-only parameters
6. Infra deployer validates or consumes these parameters and fails

**Results:**

- Infra deployment fails because the infra environment inherits business-only parameters via the cluster default passport
- Traceability comments in the generated cloud.yml confirm that problematic values came from:
  - `cloud passport: <cluster-name> version: <passport-version>`

## UC-09: Backward Compatibility for Existing Business Environments

**Pre-requisites:**

- Existing business environments already deploy successfully using auto-association
- For those business environments: `env_definition.yml` has no `inventory.cloudPassport`
- A new infra passport is introduced: `cloud-passport/<cluster-name>-infra.yml`
- Only infra environments are updated to explicitly reference: `inventory.cloudPassport: <cluster-name>-infra`

**Trigger:**

- Rebuild/generate Effective Set for existing business environments after infra passport changes

**Steps:**

1. Build/generate Effective Set for each existing business environment before the infra passport change (baseline)
2. Add the infra passport file
3. Update infra environments to explicitly reference the infra passport
4. Rebuild/generate Effective Set for the business environments without changing their env_definition.yml
5. Compare:

- business effective values (deployment context and/or generated `cloud.yml`)
- traceability comments

**Results:**

- Business environments keep their Effective Set behaviour:
  - same effective values for business workload keys
  - traceability indicates the business passport origin (`cloud passport: <cluster-name> ...`)
- Infra environments are isolated to the infra passport after explicit configuration
