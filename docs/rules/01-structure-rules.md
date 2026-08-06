# Structure Rules — Placement and Naming

Rules that decide **where** values live and **how** everything is named.
Source: [configuration-standard.md](../configuration-standard.md)

Cross-document dependencies: NAME-6 → SEC-1 (Correctness Rules), SEC-3 → PLACE-5 (this doc).

---

## Terms

Instance override chain, lowest to highest:

1. **Repository** — parameters shared across all clusters.
2. **Cluster** — values shared by every environment on one cluster.
3. **Environment** — values that differ per environment.

Composition layer:

- **Template repository** — constants true for every environment of a type, brought in by composition, not by the instance override chain.

---

## Placement and grouping

### PLACE-1 - Highest correct layer (SHOULD)

Define a value at the highest layer where it holds — template, repository, cluster, environment.
Override lower only for a genuine difference. A credential follows the same rule: place it at the layer its consumers share, and no broader.

```yaml
# OK - shared cluster value defined once at cluster level
# environments/cluster-01/parameters/cluster-01-cloud-deploy.yml
MONITORING_URL: https://monitoring.cluster-01.example.com

# Not OK - the same value copied into every environment
# environments/cluster-01/env-1/Inventory/parameters/env-1-deploy.yml -> MONITORING_URL: ...
# environments/cluster-01/env-2/Inventory/parameters/env-2-deploy.yml -> MONITORING_URL: ...
```

### PLACE-2 - Override only the delta (SHOULD)

When you override at a higher layer, include only the keys whose value actually differs from the layer below.
Do not restate keys already correct there.

```yaml
# lower - environments/cluster-01/parameters/cluster-01-cloud-deploy.yml
LOG_LEVEL: info
REPLICA_COUNT: 2
MONITORING_URL: https://monitoring.cluster-01.example.com

# Not OK - the env override restates keys identical to the cluster layer
# .../env-1/Inventory/parameters/env-1-deploy.yml
LOG_LEVEL: info
REPLICA_COUNT: 3
MONITORING_URL: https://monitoring.cluster-01.example.com

# OK - only the key that differs
REPLICA_COUNT: 3
```

### PLACE-3 - Place by the system tier (SHOULD)

A parameter's placement follows what it configures. A value that configures the environment's own
applications is placed by PLACE-1, at the highest layer where it holds. A value that instead describes
the platform or the physical cluster the environment runs on is the same for every environment on that
cluster, so it lives at the cluster layer, and a Cloud Passport contract key lives in the passport (see
PLACE-4). A business environment runs on both a platform and a physical cluster, so its cluster-layer values
can describe either. A platform environment runs on the physical cluster alone.

```yaml
# OK - MONITORING_URL describes the platform this env runs on, shared by every env on the cluster
# environments/cluster-01/parameters/cluster-01-platform.yml
MONITORING_URL: https://monitoring.cluster-01.example.com

# OK - BSS_DEFAULT_TENANT configures the env's own application, specific to this env
# environments/cluster-01/env-1/Inventory/parameters/env-1-bss.yml
BSS_DEFAULT_TENANT: acme

# Not OK - both keys grouped at the env by application, ignoring that MONITORING_URL is a shared platform value
# environments/cluster-01/env-1/Inventory/parameters/env-1-bss.yml
MONITORING_URL: https://monitoring.cluster-01.example.com   # describes the platform -> belongs at the cluster
BSS_DEFAULT_TENANT: acme
```

### PLACE-4 - Contract keys in the Cloud Passport (SHOULD)

A key that belongs to the Cloud Passport contract is authored in the passport, not in any other EnvGene entity.
See [Cloud Passport processing](/docs/features/cloud-passport-processing.md).

```yaml
# OK - a contract key in the passport
# environments/cluster-01/cloud-passport/cluster-01.yml
dbaas:
  DBAAS_AGGREGATOR_ADDRESS: https://dbaas.cluster-01.example.com

# Not OK - a contract key sitting in a ParameterSet
# .../Inventory/parameters/env-1-deploy.yml
DBAAS_AGGREGATOR_ADDRESS: https://dbaas.cluster-01.example.com
```

### PLACE-5 - Right parameter category (MUST)

Put a parameter in the category whose Effective Set context matches when its consumer reads the value:
`deployParameters` at deployment, `e2eParameters` in the pipeline, and `technicalConfigurationParameters`
at runtime. The category decides which context receives the value, so the wrong category sends it to the
wrong consumer.

```yaml
# OK - each value in the category its consumer reads
technicalConfigurationParameters:   # runtime
  CACHE_TTL_SECONDS: 300
e2eParameters:                       # pipeline
  E2E_LOGIN_URL: https://bss.env-1.example.com/login

# Not OK - a pipeline URL and a runtime setting both placed in deployment
deployParameters:
  E2E_LOGIN_URL: https://bss.env-1.example.com/login
  CACHE_TTL_SECONDS: 300
```

### PLACE-6 - Pipeline parameters bind to the Cloud (MUST)

A pipeline parameter set, the pipeline context named `e2eParameters`, associates to the Cloud only.
The file may sit at the environment, cluster, or repository location. Only the binding is fixed to the Cloud.

```yaml
# OK - the reserved key cloud binds the paramset to the Cloud
envTemplate:
  envSpecificE2EParamsets:
    cloud:
      - env-1-pipeline

# Not OK - keyed by a namespace identifier
envTemplate:
  envSpecificE2EParamsets:
    bss:                          # a namespace deploy_postfix
      - env-1-pipeline
```

### PLACE-7 - One category per ParameterSet (SHOULD)

A ParameterSet is referenced from at most one of `deployParameterSets`, `e2eParameterSets`, or
`technicalConfigurationParameterSets`. A set carries no category of its own, the array that lists it
assigns one, so naming one set in two arrays copies its whole `parameters` block into two contexts. When
the same values are genuinely needed in two categories, author two sets.

```yaml
# Not OK - one set in two category arrays, its parameters land in both contexts
# deployParameterSets: [oss-config]
# technicalConfigurationParameterSets: [oss-config]
# OK - a set per category
# deployParameterSets: [oss-deploy]
# technicalConfigurationParameterSets: [oss-runtime]
```

### PLACE-8 - One concern per entity (SHOULD)

Give a ParameterSet, Resource Profile Override, or credentials file a single concern. Split entities by
subject and parameter category, the axes the referencing template selects on, not by team, environment,
changeset, ticket, or release train. Prefer many small single-concern files over one large one. Do not
author a catch-all file that collects unrelated concerns. A per-application value belongs in the entity's
`applications` section, not in a separate per-application file. Remove an entity committed empty, unless
it is a deliberately wired but empty slot.

```yaml
# OK - one concern per file, selected by name from the referencing template
# parameters/postgresql-deploy.yml    -> deployParameterSets: [postgresql-deploy]
# parameters/postgresql-runtime.yml   -> technicalConfigurationParameterSets: [postgresql-runtime]

# Not OK - one file collecting every application's parameters
# parameters/custom-apps-parameters.yml   (5000 lines, unrelated concerns)

# Not OK - an empty file committed as configuration
# parameters/bss-deploy.yml   ->   parameters: {}
```

---

## Naming

### NAME-1 - One name per concept (SHOULD)

Collapse true aliases to one canonical key and update its consumers. Equal values are not proof of an alias — confirm the keys mean the same concept for the same consumer before collapsing, because a wrong collapse drops a key some consumer reads.

```yaml
# Not OK - three names, one value
KAFKA_URL: kafka.internal:9092
BOOTSTRAP_SERVERS: kafka.internal:9092
STREAMING_BROKER_ADDRESS: kafka.internal:9092

# OK
KAFKA_BOOTSTRAP_SERVERS: kafka.internal:9092
```

### NAME-2 - Filename equals `name` (MUST)

The filename, without extension, equals the object's `name` for a ParameterSet, an Application Definition, a Registry Definition, and an Artifact Definition. EnvGene validates this and stops generation on a mismatch.

```yaml
# OK - file env-1-deploy.yml
name: env-1-deploy
# Not OK - file env-1-deploy.yml
name: deploy-params
```

### NAME-3 - Kebab-case files, directories, and namespaces (SHOULD)

Filenames, directory names, and namespace names use kebab-case. YAML field names and enum values follow the object's own convention.

Casing is part of a name's identity, so kebab-case governs a new name. A name that a reference resolves by exact string (a ParameterSet, Resource Profile Override, Shared Template Variable, or credential id) is not re-cased to fit this rule, because re-casing breaks the reference. A name an external producer dictates, such as a Cloud Passport discovery id or a legacy capitalised application or registry name, is exempt.

```yaml
# OK
# environments/cluster-01/env-01/parameters.yml
# Not OK
# environments/Cluster_01/Env01/Parameters.yml
```

### NAME-4 - Name a ParameterSet by subject and category (SHOULD)

Name a ParameterSet `<subject>-<category>`, with an optional `-<topology>` suffix, kebab-case and equal to the `name:` field.

| Part       | Required | Values | Rule |
|------------|----------|--------|------|
| `subject`  | yes      | what the set configures at its scope: a service or namespace (`postgresql`, `oss`), the cloud (`cloud`), or a cross-cutting area (`monitoring`, `registry`, `platform`) | one stable identity |
| `category` | yes      | `deploy`, `pipeline`, or `runtime` | matches the array that references the set: `deploy` from `deployParameterSets`, `pipeline` from `e2eParameterSets`, `runtime` from `technicalConfigurationParameterSets` |
| `topology` | no       | a repository's own topology flavor, for example `offsite`/`onsite`, `primary`/`dr`, `edge`/`core` | only where topology is a real axis of variation |

The scope (site, cluster, environment) and whether the set is a base or an environment override come from the file location, not from a name token. Never put an environment name, cluster name, release or version, ticket id, or date in the name.

```yaml
# OK - subject and category, scope comes from the file location
postgresql-deploy            # in the instance repo, the environment override of the template base
postgresql-runtime           # same subject, second category
oss-pipeline
integration-deploy-offsite   # topology suffix where it genuinely varies

# Not OK
cloud-env-specific           # scope in the name, the file location already says environment
qa01-bss-deploy              # environment name baked in
bss-deploy-r23-3             # release baked in
etbss-51477                  # ticket id, opaque
bss                          # category missing
```

### NAME-5 - Name a Resource Profile Override by baseline and subsystem (SHOULD)

Name a Resource Profile Override `<baseline>-<subsystem>-override`, with an optional `-<flavor>` suffix, matching the `name:` field.

| Part        | Required | Values | Rule |
|-------------|----------|--------|------|
| `baseline`  | yes      | `dev`, `prod`, `prod-nonha`, `dev-ha` | the base profile being overridden, and it must equal the `baseline:` field value |
| `subsystem` | yes      | the domain whose applications the file carries: `bss`, `core`, `oss`, `dm`, `portal` | one subsystem per file |
| `override`  | yes      | the literal `override` | entity-type marker, singular for a new name (an existing `overrides` is not renamed) |
| `flavor`    | no       | a workload variant: `hawk`, `single`, `new-perf` | an alternate profile for the same baseline and subsystem, not a second baseline and not an environment |

The `baseline:` field holds a base-profile name, never an environment name. Generation adds the environment prefix through `updateRPOverrideNameWithEnvName`, so do not bake it into the name. Scope comes from the file location.

```yaml
# OK
dev-core-override
prod-oss-override
dev-core-override-hawk
# Not OK
sit-dm-override                # baseline is dev, so the leading token contradicts the field
telus-dv2-multi-sql-override   # environment name baked in
```

### NAME-6 - Name a credential id by purpose (SHOULD)

Name a credential id, the key of a credentials entry, `<purpose>`, with an optional `-<role>` qualifier and an optional `-cred` or `-creds` suffix.

| Part      | Required | Values | Rule |
|-----------|----------|--------|------|
| `purpose` | yes      | what the secret unlocks: `registry`, `argocd`, `keycloak`, `cmdb`, `dbaas`, `postgresql` | the primary dimension, named for purpose, not environment, application, or account |
| `role`    | no       | `deployer`, `client`, `admin`, `ci` | disambiguates when one purpose has several |
| suffix    | no       | `-cred` or `-creds` | optional, kept consistent within a scope, and an existing id is not re-suffixed |

One logical credential is one credential id. Do not split a username and password pair into two `secret` entries. A credential id a Cloud Passport discovery process dictates is exempt.

See also: SEC-1 (Correctness Rules) — credential format.

```yaml
# OK
argocd-cred
app-deployer-cmdb-cred
keycloak-client-cred
# Not OK
id_toms_b2b_dev_credentials    # environment and account baked in
cloud-deployer-username        # a username and password pair split into two entries
```

### NAME-7 - Name a Shared Template Variable by purpose (SHOULD)

Name a Shared Template Variable file `<purpose>`, with an optional `-<qualifier>`. The bare filename is the name listed in the `sharedTemplateVariables` array, so the filename is the reference.

| Part        | Required | Values | Rule |
|-------------|----------|--------|------|
| `purpose`   | yes      | a stable keyword: `toggles`, `ci-global-vars`, `ns-overrides` | the reference is this bare name, so the filename equals the reference |
| `qualifier` | no       | `-vars` or `-overrides` where it adds meaning | do not append a generic `-template-variables` suffix |

Scope comes from the file location: a repository-wide file is authored once under `environments/configuration/variables/`, a per-environment file under the environment's `Inventory/configuration/variables/`. A file not listed in `sharedTemplateVariables` is ignored.

```yaml
# OK
toggles
ci-global-vars
ns-overrides
# Not OK
saas-nd-bss-dev-template-variables   # customer, environment, and a generic suffix
toggles-release-2024.4               # release baked in
```
