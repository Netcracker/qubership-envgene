# EnvGene Configuration Standard

- [EnvGene Configuration Standard](#envgene-configuration-standard)
  - [Scope](#scope)
  - [How to read this standard](#how-to-read-this-standard)
  - [Terms](#terms)
  - [Placement and grouping](#placement-and-grouping)
    - [PLACE-1 - Highest correct layer (SHOULD)](#place-1---highest-correct-layer-should)
    - [PLACE-2 - Override only the delta (SHOULD)](#place-2---override-only-the-delta-should)
    - [PLACE-3 - Place by the system tier (SHOULD)](#place-3---place-by-the-system-tier-should)
    - [PLACE-4 - Contract keys in the Cloud Passport (SHOULD)](#place-4---contract-keys-in-the-cloud-passport-should)
    - [PLACE-5 - Right parameter category (MUST)](#place-5---right-parameter-category-must)
    - [PLACE-6 - Pipeline parameters bind to the Cloud (MUST)](#place-6---pipeline-parameters-bind-to-the-cloud-must)
    - [PLACE-7 - One category per ParameterSet (SHOULD)](#place-7---one-category-per-parameterset-should)
    - [PLACE-8 - One concern per entity (SHOULD)](#place-8---one-concern-per-entity-should)
  - [Secrets](#secrets)
    - [SEC-1 - No plaintext secrets (MUST)](#sec-1---no-plaintext-secrets-must)
    - [SEC-2 - No mixed plaintext and encrypted secrets (MUST)](#sec-2---no-mixed-plaintext-and-encrypted-secrets-must)
    - [SEC-3 - No secrets in runtime parameters (MUST)](#sec-3---no-secrets-in-runtime-parameters-must)
    - [SEC-4 - Credential shape matches the secret (SHOULD)](#sec-4---credential-shape-matches-the-secret-should)
    - [SEC-5 - Repository-wide encryption (MAY)](#sec-5---repository-wide-encryption-may)
  - [Integrity](#integrity)
    - [INT-1 - Schema-valid (MUST)](#int-1---schema-valid-must)
    - [INT-2 - Every reference resolves (MUST)](#int-2---every-reference-resolves-must)
    - [INT-3 - One resolvable Cloud Passport (MUST)](#int-3---one-resolvable-cloud-passport-must)
    - [INT-4 - No shadowed same-name overrides (SHOULD)](#int-4---no-shadowed-same-name-overrides-should)
    - [INT-5 - No unreferenced entities (SHOULD)](#int-5---no-unreferenced-entities-should)
    - [INT-6 - No dead parameters (SHOULD)](#int-6---no-dead-parameters-should)
  - [Naming](#naming)
    - [NAME-1 - One name per concept (SHOULD)](#name-1---one-name-per-concept-should)
    - [NAME-2 - Filename equals `name` (MUST)](#name-2---filename-equals-name-must)
    - [NAME-3 - Kebab-case files, directories, and namespaces (SHOULD)](#name-3---kebab-case-files-directories-and-namespaces-should)
    - [NAME-4 - Name a ParameterSet by subject and category (SHOULD)](#name-4---name-a-parameterset-by-subject-and-category-should)
    - [NAME-5 - Name a Resource Profile Override by baseline and subsystem (SHOULD)](#name-5---name-a-resource-profile-override-by-baseline-and-subsystem-should)
    - [NAME-6 - Name a credential id by purpose (SHOULD)](#name-6---name-a-credential-id-by-purpose-should)
    - [NAME-7 - Name a Shared Template Variable by purpose (SHOULD)](#name-7---name-a-shared-template-variable-by-purpose-should)
  - [Values](#values)
    - [VAL-1 - A value's YAML type matches its consumer (MUST)](#val-1---a-values-yaml-type-matches-its-consumer-must)
    - [VAL-2 - Reserved-value semantics (MUST)](#val-2---reserved-value-semantics-must)
    - [VAL-3 - URLs have no trailing slash (SHOULD)](#val-3---urls-have-no-trailing-slash-should)
    - [VAL-4 - Complex values are native YAML (SHOULD)](#val-4---complex-values-are-native-yaml-should)
    - [VAL-5 - Resource quantities use unit form (SHOULD)](#val-5---resource-quantities-use-unit-form-should)
  - [Templating](#templating)
    - [TPL-1 - Jinja lives only in `.j2` templates (MUST)](#tpl-1---jinja-lives-only-in-j2-templates-must)
    - [TPL-2 - Override at a layer, not through Jinja plumbing (MUST)](#tpl-2---override-at-a-layer-not-through-jinja-plumbing-must)
    - [TPL-3 - Default at a layer, not a Jinja default (MUST)](#tpl-3---default-at-a-layer-not-a-jinja-default-must)
    - [TPL-4 - A reference never fails on a missing value (SHOULD)](#tpl-4---a-reference-never-fails-on-a-missing-value-should)
    - [TPL-5 - No per-level presence guards (SHOULD)](#tpl-5---no-per-level-presence-guards-should)
    - [TPL-6 - Keep template logic small (SHOULD)](#tpl-6---keep-template-logic-small-should)
    - [TPL-7 - Build URLs from the Cloud Passport host (MUST)](#tpl-7---build-urls-from-the-cloud-passport-host-must)
    - [TPL-8 - Protect Helm passthrough (MUST)](#tpl-8---protect-helm-passthrough-must)
    - [TPL-9 - Every branch renders valid YAML (SHOULD)](#tpl-9---every-branch-renders-valid-yaml-should)
    - [TPL-10 - No secret in a template (SHOULD)](#tpl-10---no-secret-in-a-template-should)
    - [TPL-11 - No hardcoded derivable values (MUST)](#tpl-11---no-hardcoded-derivable-values-must)
    - [TPL-12 - Reference the current namespace with a macro (SHOULD)](#tpl-12---reference-the-current-namespace-with-a-macro-should)
    - [TPL-13 - Gate on app presence, not on a toggle (SHOULD)](#tpl-13---gate-on-app-presence-not-on-a-toggle-should)
    - [TPL-14 - Resolve a namespace by deploy-postfix, do not rebuild it (SHOULD)](#tpl-14---resolve-a-namespace-by-deploy-postfix-do-not-rebuild-it-should)
    - [TPL-15 - Prefer a macro over a Jinja expression (SHOULD)](#tpl-15---prefer-a-macro-over-a-jinja-expression-should)
    - [TPL-16 - Edit inputs, not generated output (SHOULD)](#tpl-16---edit-inputs-not-generated-output-should)
  - [Exceptions](#exceptions)

---

## Scope

This standard describes how to author a well-formed EnvGene configuration. It covers parameters,
credentials, Cloud Passports, and layer placement — whether you write files by hand or produce them
with a migration tool.

It complements the descriptive references [EnvGene Objects](/docs/envgene-objects.md) and
[EnvGene Configuration](/docs/envgene-configs.md), which explain *what* these objects are. This
document explains *how to author them well*.

---

## How to read this standard

**Keywords** tell you how strictly to follow a rule:

| Keyword | Meaning |
|---------|---------|
| **MUST** / **MUST NOT** | Non-negotiable. Breaking this causes generation failures or security issues. |
| **SHOULD** / **SHOULD NOT** | Strong default. Deviate only when you have a documented reason. |
| **MAY** | Optional good practice. Use it when it fits. |

**Rule IDs** are stable — for example `SEC-1`. New rules get the next free number in their area and
never renumber existing ones, so you can safely reference a rule ID in comments or tickets.

**Rule shape** — each rule states what is required and how to check compliance, then shows a
`# OK` and `# Not OK` example. A reason is added only when it helps you make a judgement call.

**Where a rule applies** — most rules apply to both the template and the instance repository. Rules
that are one-sided (for example Jinja rules that only apply where `.j2` templates live) make that
clear from their subject.

**Deviations** — when you genuinely cannot follow a rule, record it as described in
[Exceptions](#exceptions).

---

## Terms

EnvGene resolves values through two distinct mechanisms:

**Instance override chain** — three layers, lowest to highest precedence. A higher layer wins per
key. Nested maps are deep-merged, so a key the higher layer does not mention is kept from the
lower layer.

1. **Repository** — parameters shared across all clusters.
2. **Cluster** — values shared by every environment on one cluster.
3. **Environment** — values that differ per environment.

**Composition layer** — a separate mechanism, not part of the override chain:

- **Template repository** — constants that are true for every environment of a type, brought in
  by composition.

**Other objects referenced by the rules:**

- **Cloud Passport** — the key-contract set of parameters that describes a cluster and the
  infrastructure and platform applications on it. It merges in at the cluster level.
- **Association target** — a ParameterSet or Resource Profile binds to a Cloud or Namespace by
  which key it is listed under in `env_definition.yml`. This is independent of the file's layer.
  Shared Template Variables and shared credentials carry no target and apply to the whole
  environment.
- **Application scope** — per-application values live inside a ParameterSet under `applications`,
  keyed by application name. There is no separate per-application file.
- **Site** — EnvGene has no site object. The word means either the Repository layer (the widest
  file location, written `site` in file paths) or the `onsite`/`offsite` template variable that
  only Jinja reads. A value shared across a network-isolated site goes to the Repository layer,
  or is branched in a template.

---

## Placement and grouping

These rules decide *where* a value belongs — which layer, which category, and which entity holds it.

### PLACE-1 - Highest correct layer (SHOULD)

**Put each value as high up as it can correctly go.**

If a value is the same for every environment on a cluster, it belongs at the cluster layer — not
copied into every individual environment. Override lower only when a genuine difference exists at
that level. The same applies to credentials: place them at the layer their consumers share.

```yaml
# OK - shared cluster value defined once at cluster level
# environments/cluster-01/parameters/cluster-01-cloud-deploy.yml
MONITORING_URL: https://monitoring.cluster-01.example.com

# Not OK - the same value copied into every environment
# environments/cluster-01/env-1/Inventory/parameters/env-1-deploy.yml -> MONITORING_URL: ...
# environments/cluster-01/env-2/Inventory/parameters/env-2-deploy.yml -> MONITORING_URL: ...
```

### PLACE-2 - Override only the delta (SHOULD)

**When overriding at a deeper layer, include only the keys that actually differ.**

Do not restate keys that are already correct at the layer below. Restating them creates hidden
duplicates — a change at the lower layer no longer takes effect because the upper layer silently
wins.

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

# OK - only the key that actually differs
REPLICA_COUNT: 3
```

### PLACE-3 - Place by the system tier (SHOULD)

**Ask: does this value describe the environment's own apps, or the platform/cluster it runs on?**

- Values that configure the environment's own applications follow PLACE-1 (highest layer where
  they hold).
- Values that describe the platform or physical cluster are the same for every environment on
  that cluster, so they live at the cluster layer. Cloud Passport contract keys go in the
  passport (see PLACE-4).

```yaml
# OK - MONITORING_URL describes the platform, shared by every env on the cluster
# environments/cluster-01/parameters/cluster-01-platform.yml
MONITORING_URL: https://monitoring.cluster-01.example.com

# OK - BSS_DEFAULT_TENANT configures this env's own application
# environments/cluster-01/env-1/Inventory/parameters/env-1-bss.yml
BSS_DEFAULT_TENANT: acme

# Not OK - both keys in the same env file, ignoring that MONITORING_URL is a platform value
# environments/cluster-01/env-1/Inventory/parameters/env-1-bss.yml
MONITORING_URL: https://monitoring.cluster-01.example.com   # belongs at the cluster layer
BSS_DEFAULT_TENANT: acme
```

### PLACE-4 - Contract keys in the Cloud Passport (SHOULD)

**If a key is part of the Cloud Passport contract, author it in the passport — nowhere else.**

Duplicating a contract key in a ParameterSet creates two sources of truth that will drift.
See [Cloud Passport processing](/docs/features/cloud-passport-processing.md) for the full key list.

```yaml
# OK - a contract key in the passport
# environments/cluster-01/cloud-passport/cluster-01.yml
dbaas:
  DBAAS_AGGREGATOR_ADDRESS: https://dbaas.cluster-01.example.com

# Not OK - the same contract key sitting in a ParameterSet
# .../Inventory/parameters/env-1-deploy.yml
DBAAS_AGGREGATOR_ADDRESS: https://dbaas.cluster-01.example.com
```

### PLACE-5 - Right parameter category (MUST)

**Use the category that matches when the consumer reads the value.**

| Category | When it is read | Use for |
|----------|-----------------|---------|
| `deployParameters` | At deployment | App config, secrets, Helm values |
| `e2eParameters` | In the CI pipeline | Test URLs, pipeline config |
| `technicalConfigurationParameters` | At runtime (via Consul) | Live config, feature toggles |

The wrong category sends the value to the wrong consumer — it either arrives at the wrong time or
not at all.

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

**A pipeline ParameterSet (`e2eParameters`) must be associated to the Cloud, not to a namespace.**

The file itself can live at the environment, cluster, or repository layer — but the binding in
`env_definition.yml` must use the reserved key `cloud`.

```yaml
# OK - the reserved key 'cloud' binds the paramset to the Cloud
envTemplate:
  envSpecificE2EParamsets:
    cloud:
      - env-1-pipeline

# Not OK - keyed by a namespace deploy_postfix
envTemplate:
  envSpecificE2EParamsets:
    bss:                          # a namespace deploy_postfix, not valid here
      - env-1-pipeline
```

### PLACE-7 - One category per ParameterSet (SHOULD)

**List a ParameterSet in only one category array.**

A ParameterSet has no category of its own — the array that lists it assigns one. If you list the
same set in two arrays (e.g. `deployParameterSets` and `technicalConfigurationParameterSets`),
its entire `parameters` block lands in both contexts. When you genuinely need the same values in
two categories, create two separate sets.

```yaml
# Not OK - one set listed in two category arrays
# deployParameterSets: [oss-config]
# technicalConfigurationParameterSets: [oss-config]

# OK - a dedicated set per category
# deployParameterSets: [oss-deploy]
# technicalConfigurationParameterSets: [oss-runtime]
```

### PLACE-8 - One concern per entity (SHOULD)

**Give each ParameterSet, Resource Profile Override, or credentials file a single concern.**

Split by subject and parameter category — the two axes the referencing template selects on. Do
not split by team, environment, ticket, or release train. Prefer many small focused files over one
large catch-all.

Per-application values belong in the entity's `applications` section, not in a separate
per-application file. Remove any entity committed empty, unless it is a deliberately wired but
intentionally empty slot.

```yaml
# OK - one concern per file
# parameters/postgresql-deploy.yml    -> deployParameterSets: [postgresql-deploy]
# parameters/postgresql-runtime.yml   -> technicalConfigurationParameterSets: [postgresql-runtime]

# Not OK - one file collecting every application's parameters
# parameters/custom-apps-parameters.yml   (5000 lines, unrelated concerns)

# Not OK - an empty file committed as configuration
# parameters/bss-deploy.yml   ->   parameters: {}
```

---

## Secrets

These rules ensure no secret ever reaches plaintext storage, Git, or a context that would expose it.

### SEC-1 - No plaintext secrets (MUST)

**Never write a secret as a literal value in any parameter file.**

A raw password or token in a ParameterSet, Cloud, or Namespace file is committed to Git and
visible to anyone with repository access. Instead, create a Credential object and reference it.

Name the credential `<product>-<purpose>-cred` and reference it with
`${creds.get("<id>").<field>}`.

```yaml
# Not OK - a real secret as a literal value
DB_PASSWORD: s3cr3t

# OK - a Credential object in Inventory/credentials/db-cred.yml
db-cred:
  type: usernamePassword
  data:
    username: "<value>"
    password: "<value>"

# OK - the ParameterSet references it
DB_PASSWORD: ${creds.get("db-cred").password}
```

### SEC-2 - No mixed plaintext and encrypted secrets (MUST)

**Once any secret in the repository is encrypted, no real secret may remain in plaintext.**

A single plaintext secret in the same repository defeats the protection of all encrypted ones — an
attacker only needs to find the one unencrypted file.

```yaml
# Not OK - one repository with both:
#   configuration/credentials.yml         SOPS-encrypted
#   Inventory/credentials/db-cred.yml     a real plaintext password

# OK - no live secret is left in plaintext alongside encrypted ones
```

### SEC-3 - No secrets in runtime parameters (MUST)

**Never put a secret inside `technicalConfigurationParameters`.**

Runtime parameters are applied live through Consul, which stores them in plaintext. Even though
the Effective Set encrypts them at rest, the value is exposed the moment it reaches Consul. Keep
secrets in `deployParameters`, where they reach the application as a Kubernetes secret rather than
a Consul key.

```yaml
# Not OK - a secret in a runtime parameter, exposed in Consul
technicalConfigurationParameters:
  DB_PASSWORD: ${creds.get("db-cred").password}

# OK - the secret stays in a deployment parameter
deployParameters:
  DB_PASSWORD: ${creds.get("db-cred").password}
```

### SEC-4 - Credential shape matches the secret (SHOULD)

**Declare a credential with the shape that matches the real secret.**

- A username + password pair → `usernamePassword` type.
- A single token or value → `secret` type (or `external` with a single field).

Do not pad a single value into a pair, and do not collapse a pair into a single field. This
applies whether the secret is stored locally or resolved from an external store.

```yaml
# OK - a single value, stored locally
registry-pull-cred:
  type: secret
  data:
    secret: "<value>"

# OK - a single value, from an external store
app-token-cred:
  type: external
  remoteRefPath: cluster-01/env-1/app-token

# OK - a username + password pair, from an external store
db-app-cred:
  type: external
  remoteRefPath: cluster-01/env-1/db-app
  properties:
    - name: username
    - name: password

# Not OK - a single value padded into a username+password pair
registry-pull-cred:
  type: usernamePassword
  data:
    username: "<value>"
    password: "<value>"
```

### SEC-5 - Repository-wide encryption (MAY)

**You may encrypt every credential file with SOPS if the repository holds local secret material.**

This is optional. If all secrets are resolved from an external store, or the repository holds no
local secret material, no repository-wide encryption is needed.

```yaml
# OK - every credential file with secret material is SOPS-encrypted
# OK - no encryption, because all secrets come from an external store
```

---

## Integrity

These rules ensure the configuration is well-formed, all references resolve, and nothing is left
dead or ambiguous.

### INT-1 - Schema-valid (MUST)

**Every EnvGene object must pass schema validation.**

An object that does not match its schema fails generation immediately. Check the schemas in
[EnvGene objects](/docs/envgene-objects.md).

```yaml
# OK     - a *ParameterSets field is a list; a category body is a map
# Not OK - a *ParameterSets field given a map, or a required key missing -> generation fails
```

### INT-2 - Every reference resolves (MUST)

**Every `${creds.get(...)}`, `$type: credRef`, ParameterSet reference, and Resource Profile
reference must point to exactly one existing object.**

A dangling reference (pointing to something that does not exist) or an ambiguous reference
(pointing to two things) fails generation.

```yaml
# Not OK - references a credential that does not exist -> generation fails
DB_PASSWORD: ${creds.get("bss-db-cred").password}

# OK - bss-db-cred exists in a credentials file on the resolution path
DB_PASSWORD: ${creds.get("bss-db-cred").password}
```

### INT-3 - One resolvable Cloud Passport (MUST)

**An environment must resolve to exactly one Cloud Passport — no more, no less.**

- If `env_definition.yml` sets `inventory.cloudPassport: <name>`, exactly one `<name>.yml` must
  exist on the search path from the environment directory up to the repository root.
- With no `cloudPassport` field, EnvGene looks for `cloud-passport/<cluster>.yml` then
  `cloud-passport/passport.yml`.

Zero matches or two matches both fail generation. Unlike ParameterSets (which use first-match),
the Cloud Passport is pointed at by name and must be unique.

```yaml
# OK - the reference resolves to exactly one file
# env_definition.yml: inventory.cloudPassport: cluster-01
# environments/cluster-01/cloud-passport/cluster-01.yml   (the one match)

# Not OK - no file named cluster-01 in the path      -> generation fails
# Not OK - two files named cluster-01 in the path    -> generation fails
```

### INT-4 - No shadowed same-name overrides (SHOULD)

**Do not author two files with the same reference name at different scopes expecting a merge —
only the highest-scope match is used; the lower one is silently ignored.**

ParameterSets, Credentials, Shared Template Variables, and Resource Profiles all resolve by
first-match across environment → cluster → repository. If two scopes have the same name, edits
to the lower-scope file have no effect.

```yaml
# Not OK - same name at two scopes; the env file wins, the cluster file is silently ignored
# environments/cluster-01/env-1/Inventory/parameters/env-specific-bss.yml   (used)
# environments/cluster-01/parameters/env-specific-bss.yml                   (shadowed, edits do nothing)

# OK - give each a distinct name, or keep it at one scope
# environments/cluster-01/parameters/cluster-bss.yml
# environments/cluster-01/env-1/Inventory/parameters/env-1-bss.yml
```

### INT-5 - No unreferenced entities (SHOULD)

**Remove any entity that nothing references.**

EnvGene silently ignores an unreferenced entity — it ships nothing and only misleads a reader
into thinking it has an effect. This is the flip side of INT-2.

Before removing, count all reference sites: a system credential read by `deployer.yml`,
`registry.yml`, or the Cloud Passport, and a template entity selected by an instance, are
referenced outside the current file and are not dead.

```yaml
# Not OK - a ParameterSet file listed by no reference array
# parameters/legacy-oss-deploy.yml   (in no *ParameterSets or envSpecific* list)

# OK - remove it, or add the reference where it is genuinely needed
```

### INT-6 - No dead parameters (SHOULD)

**Delete a parameter that no consumer reads.**

A key is dead based on who reads it, not on its value. A dead key with a real-looking value is
still dead and should be removed. An empty value that a consumer actually reads is not dead and
must stay.

```yaml
# Not OK - parameters for a decommissioned integration, read by nothing
LEGACY_SERVICE_HOST: legacy.internal
LEGACY_SERVICE_PORT: 8080

# OK - the dead keys are removed
```

---

## Naming

These rules ensure entities and their keys are named so a consumer can resolve them and a reader
can find them.

### NAME-1 - One name per concept (SHOULD)

**If two keys mean the same thing for the same consumer, collapse them to one canonical key.**

Equal values alone are not proof of an alias — confirm the keys genuinely mean the same concept
for the same consumer before collapsing. A wrong collapse silently drops a key some consumer
depends on.

```yaml
# Not OK - three names, one concept
KAFKA_URL: kafka.internal:9092
BOOTSTRAP_SERVERS: kafka.internal:9092
STREAMING_BROKER_ADDRESS: kafka.internal:9092

# OK - one canonical name
KAFKA_BOOTSTRAP_SERVERS: kafka.internal:9092
```

### NAME-2 - Filename equals `name` (MUST)

**The filename (without extension) must equal the `name:` field inside the file.**

This applies to ParameterSets, Application Definitions, Registry Definitions, and Artifact
Definitions. EnvGene validates this on every run and stops generation on a mismatch.

```yaml
# OK - file env-1-deploy.yml
name: env-1-deploy

# Not OK - file env-1-deploy.yml but name field does not match
name: deploy-params
```

### NAME-3 - Kebab-case files, directories, and namespaces (SHOULD)

**Use kebab-case for filenames, directory names, and namespace names.**

YAML field names and enum values follow the object's own convention, not this rule.

Important: casing is part of a name's identity. Do not re-case an existing name that references
resolve by exact string (ParameterSets, Resource Profile Overrides, Shared Template Variables,
credential ids) — re-casing breaks the reference. Names dictated by an external producer (Cloud
Passport discovery ids, legacy capitalised application or registry names) are exempt.

```yaml
# OK
# environments/cluster-01/env-01/parameters.yml

# Not OK
# environments/Cluster_01/Env01/Parameters.yml
```

### NAME-4 - Name a ParameterSet by subject and category (SHOULD)

**Follow the pattern `<subject>-<category>` with an optional `-<topology>` suffix.**

| Part | Required | Values | Rule |
|------|----------|--------|------|
| `subject` | yes | what the set configures at its scope: a service or namespace (`postgresql`, `oss`), the cloud (`cloud`), or a cross-cutting area (`monitoring`, `registry`, `platform`) | one stable identity |
| `category` | yes | `deploy`, `pipeline`, or `runtime` | must match the array that lists it: `deploy` → `deployParameterSets`, `pipeline` → `e2eParameterSets`, `runtime` → `technicalConfigurationParameterSets` |
| `topology` | no | a repository's own topology flavor, e.g. `offsite`/`onsite`, `primary`/`dr` | only where topology is a real axis of variation |

The file's location tells you the scope (site, cluster, environment). Never encode the environment
name, cluster name, release, version, ticket id, or date in the name.

```yaml
# OK
postgresql-deploy            # subject + category, scope from file location
postgresql-runtime           # same subject, second category
oss-pipeline
integration-deploy-offsite   # topology suffix where variation is real

# Not OK
cloud-env-specific           # 'env-specific' is scope — the file location already says that
qa01-bss-deploy              # environment name baked in
bss-deploy-r23-3             # release baked in
etbss-51477                  # opaque ticket id
bss                          # category missing
```

### NAME-5 - Name a Resource Profile Override by baseline and subsystem (SHOULD)

**Follow the pattern `<baseline>-<subsystem>-override` with an optional `-<flavor>` suffix.**

| Part | Required | Values | Rule |
|------|----------|--------|------|
| `baseline` | yes | `dev`, `prod`, `prod-nonha`, `dev-ha` | must equal the `baseline:` field value |
| `subsystem` | yes | `bss`, `core`, `oss`, `dm`, `portal` | one subsystem per file |
| `override` | yes | the literal `override` | entity-type marker; an existing `overrides` plural is not renamed |
| `flavor` | no | `hawk`, `single`, `new-perf` | an alternate profile for the same baseline and subsystem, not a second baseline |

The `baseline:` field holds a base-profile name, never an environment name. Generation adds the
environment prefix automatically through `updateRPOverrideNameWithEnvName` — do not bake it into
the name. Scope comes from the file location.

```yaml
# OK
dev-core-override
prod-oss-override
dev-core-override-hawk

# Not OK
sit-dm-override                # 'sit' is an env name; baseline is 'dev', so this contradicts the field
telus-dv2-multi-sql-override   # environment name baked in
```

### NAME-6 - Name a credential id by purpose (SHOULD)

**Follow the pattern `<purpose>` with an optional `-<role>` qualifier and an optional `-cred` suffix.**

| Part | Required | Values | Rule |
|------|----------|--------|------|
| `purpose` | yes | what the secret unlocks: `registry`, `argocd`, `keycloak`, `cmdb`, `dbaas`, `postgresql` | named for purpose, not environment, application, or account |
| `role` | no | `deployer`, `client`, `admin`, `ci` | disambiguates when one purpose has several credentials |
| suffix | no | `-cred` or `-creds` | optional; keep it consistent within a scope; do not re-suffix an existing id |

One logical secret = one credential id. Do not split a username + password pair into two `secret`
entries. A credential id dictated by a Cloud Passport discovery process is exempt.

```yaml
# OK
argocd-cred
app-deployer-cmdb-cred
keycloak-client-cred

# Not OK
id_toms_b2b_dev_credentials    # environment and personal account baked in
cloud-deployer-username        # a username/password pair split into two entries
```

### NAME-7 - Name a Shared Template Variable by purpose (SHOULD)

**Use `<purpose>` with an optional `-<qualifier>`. The filename is the reference, so keep it stable.**

| Part | Required | Values | Rule |
|------|----------|--------|------|
| `purpose` | yes | a stable keyword: `toggles`, `ci-global-vars`, `ns-overrides` | the bare filename is listed in `sharedTemplateVariables`, so it is the reference |
| `qualifier` | no | `-vars` or `-overrides` where it adds meaning | do not append a generic `-template-variables` suffix |

Scope comes from the file location:
- Repository-wide → `environments/configuration/variables/`
- Per-environment → `Inventory/configuration/variables/`

A file not listed in `sharedTemplateVariables` is ignored by EnvGene.

```yaml
# OK
toggles
ci-global-vars
ns-overrides

# Not OK
saas-nd-bss-dev-template-variables   # customer, environment, and a generic suffix all baked in
toggles-release-2024.4               # release version baked in
```

---

## Values

These rules constrain the content of individual values — their YAML type, format, and reserved
meanings.

### VAL-1 - A value's YAML type matches its consumer (MUST)

**Write each value so its parsed YAML type is the type the consumer expects.**

YAML infers types from syntax: `true` is a boolean, `3` is an integer, `"3"` is a string. The
consumer's contract (such as a Helm chart's `values.schema.json`) determines the expected type —
write to match it, not to match a general style preference.

- Leave values bare when the consumer reads a boolean, number, or list.
- Quote values when the consumer reads a string, especially strings YAML would otherwise coerce
  (country codes like `NO`, versions like `1.20`, leading-zero numbers).

```yaml
# OK - parsed type matches the consumer
REPLICA_COUNT: 3               # consumer reads a number
COUNTRY_CODE: "NO"             # consumer reads a string; quoted so YAML does not parse it as false
LEGACY_COUNT: "3"              # consumer reads a string; quoted even though it looks like a number

# Not OK - parsed type conflicts with the consumer
MONITORING_ENABLED: "true"     # consumer reads a boolean; this value is a string
CHART_VERSION: 1.20            # consumer reads a string; YAML coerced this to the number 1.2
```

### VAL-2 - Reserved-value semantics (MUST)

**Use `envgeneNullValue` only to mark a mandatory value that a lower layer must supply.**

It does not mean "empty" and it does not mean "delete this key". Use it in a template to signal
that the instance is required to provide a concrete value. Do not use an empty string as a
substitute, and do not repurpose this marker or invent your own placeholders.

```yaml
# OK - a template marks a mandatory value the instance must fill in
# template:
DB_HOST: envgeneNullValue
# instance:
DB_HOST: db.env-1.example.com

# Not OK - an empty string standing in for a mandatory value
DB_HOST: ""

# Not OK - the marker used to mean "this feature is off"
FEATURE_X: envgeneNullValue
```

### VAL-3 - URLs have no trailing slash (SHOULD)

**Strip the trailing `/` from every URL value.**

Code that joins a base URL with a path often does simple string concatenation. A trailing slash
produces double slashes (`https://host//path`), which some services reject.

```yaml
# OK
MY_SERVICE_URL: https://my-service.cluster-01.example.com

# Not OK
MY_SERVICE_URL: https://my-service.example.com/
```

### VAL-4 - Complex values are native YAML (SHOULD)

**Write structured values (maps, lists) as native YAML, never as a JSON string or a block scalar.**

A JSON string packed into a single value cannot be schema-validated, does not diff cleanly, and
cannot be deep-merged across layers. Native YAML can do all three.

```yaml
# Not OK - a complex object packed into a JSON string
FEATURE_CONFIG: '{"retries": 3, "targets": ["a", "b"], "tls": {"enabled": true}}'

# Not OK - a block scalar is still a string, not a native structure
FEATURE_CONFIG: |
  retries: 3
  targets:
    - a
    - b

# OK - native YAML
FEATURE_CONFIG:
  retries: 3
  targets:
    - a
    - b
  tls:
    enabled: true
```

### VAL-5 - Resource quantities use unit form (SHOULD)

**In a Resource Profile Override, write memory and CPU values in Kubernetes unit form.**

Use `512Mi`, `1Gi`, `500m` — not raw bytes. Kubernetes accepts both, but unit form is readable
in a diff and immediately comparable at a glance.

```yaml
# OK
GATEWAY_MEMORY_LIMIT: 512Mi
GATEWAY_CPU_REQUEST: 500m

# Not OK - raw bytes, technically valid but unreadable
GATEWAY_MEMORY_LIMIT: 536870912
```

---

## Templating

These rules govern `.j2` templates and macros — how they derive values and how to write Jinja
that renders safely and predictably.

### TPL-1 - Jinja lives only in `.j2` templates (MUST)

**Only `.j2` template files may contain Jinja expressions. Plain YAML files must not.**

Instance ParameterSets, Cloud Passports, and Credential files are plain YAML. Jinja in these
files is not evaluated by EnvGene and produces unexpected literal output.

```yaml
# OK - templates/.../parameters.yml.j2
MY_NAMESPACE: "{{ current_env.name }}-core"

# Not OK - Jinja expression in an instance file (environments/.../parameters.yml)
MY_NAMESPACE: "{{ current_env.name }}-core"
```

### TPL-2 - Override at a layer, not through Jinja plumbing (MUST)

**To change a value at a layer, place the override directly at that layer.**

Do not create a chain of `additionalTemplateVariables` + Jinja interpolation just to pass a value
down. Interpolation composes a string — it does not pass a typed key through unchanged, and it
adds indirection with no benefit.

```yaml
# Not OK - the template re-emits a key just to pass it through unchanged
# parameters.yml.j2:  LOG_LEVEL: "{{ LOG_LEVEL }}"   with additionalTemplateVariables LOG_LEVEL: info

# OK - set the value directly at the layer where it belongs, no template logic needed
# environments/<cluster>/<env>/parameters.yml:  LOG_LEVEL: info
```

### TPL-3 - Default at a layer, not a Jinja default (MUST)

**Put default values in a shallower layer and override only the delta deeper.**

Use a Jinja `| default(...)` filter only for genuine branching (a value that is absent in some
environments). Using it to supply a missing default hides the value inside template logic, where
it is invisible to the instance author.

```yaml
# Not OK - default hidden inside the template
TIMEOUT: "{{ TIMEOUT | default('30s') }}"

# OK - default set openly at the template layer; the instance overrides only when needed
# template parameters.yml.j2:  TIMEOUT: 30s
# env parameters.yml (optional override):  TIMEOUT: 60s
```

### TPL-4 - A reference never fails on a missing value (SHOULD)

**Wrap any value that may be absent with `| default(...)` so a missing input renders empty
instead of crashing generation.**

```yaml
# Not OK - fails when FEATURE_A is absent
ENABLED: "{% if FEATURE_A == 'on' %}true{% else %}false{% endif %}"

# OK - safe when FEATURE_A is absent
ENABLED: "{% if FEATURE_A | default('') == 'on' %}true{% else %}false{% endif %}"
```

### TPL-5 - No per-level presence guards (SHOULD)

**Do not guard every level of a nested path with `is defined`. One trailing `| default(...)` covers
the whole path.**

EnvGene resolves a missing key at any depth to empty rather than an error, so layer-by-layer
guards defend against a failure that cannot happen. They also bloat the template and hide intent.

Use a single `is defined` test only when you need to branch on whether an entire optional block
is present.

```yaml
# Not OK - a guard at every level, standing in for a failure that cannot occur
DR_MODE: "{% if current_env.additionalTemplateVariables is defined and current_env.additionalTemplateVariables.drParameters is defined %}{{ current_env.additionalTemplateVariables.drParameters.mode }}{% endif %}"

# OK - one trailing default covers every missing level of the path
DR_MODE: "{{ current_env.additionalTemplateVariables.drParameters.mode | default('') }}"

# OK - a single presence test to branch on an optional block
{% if current_env.additionalTemplateVariables.drParameters is defined %}
DR_ENABLED: true
{% endif %}
```

### TPL-6 - Keep template logic small (SHOULD)

**Use only the basic Jinja constructs: `if`, `elif`, `else`, `for` (over genuinely dynamic lists),
and the filters `default`, `join`, `upper`, and `lower`.**

Never use `macro`, `include`, `import`, `extends`, `block`, `raw`, or a custom filter — reuse
comes from template composition, not from Jinja abstractions. If the logic is growing deeply
nested, that is usually a sign the value should be set by placement rather than computed in a
template.

```yaml
# Not OK - macros and includes
# {% macro url(h) %}...{% endmacro %}   {% include "shared.j2" %}

# OK - a simple conditional
FEATURE: "{% if SITE | default('') == 'onsite' %}on{% else %}off{% endif %}"
```

### TPL-7 - Build URLs from the Cloud Passport host (MUST)

**Compose service URLs from `CLOUD_PUBLIC_HOST` (the Cloud Passport host value), not from a
hardcoded cluster hostname.**

Hardcoded hostnames break when the environment moves to a different cluster or the domain changes.
Building from the passport host makes the URL correct automatically.

```yaml
# Not OK - hardcoded cluster hostname
MY_SERVICE_URL: https://my-service.cluster-01.example.com

# OK - built from the Cloud Passport host
MY_SERVICE_URL: "https://my-service.{{ CLOUD_PUBLIC_HOST }}"
```

### TPL-8 - Protect Helm passthrough (MUST)

**Wrap any token meant for Helm (not EnvGene) in `{% raw %}...{% endraw %}`.**

EnvGene evaluates all `{{ }}` it sees. A Helm expression like `{{ .Release.Name }}` without `raw`
protection is evaluated by EnvGene and broken before Helm ever sees it.

```yaml
# Not OK - EnvGene evaluates a Helm token and corrupts it
RELEASE: "{{ .Release.Name }}"

# OK - protected so EnvGene leaves it for Helm
RELEASE: "{% raw %}{{ .Release.Name }}{% endraw %}"
```

### TPL-9 - Every branch renders valid YAML (SHOULD)

**Each branch of a conditional must produce well-formed YAML of the target shape.**

No branch should leave a dangling key, a half-written value, or a broken document.

```yaml
# Not OK - the empty branch leaves a dangling key with no value
TIMEOUT:{% if HAS_TIMEOUT %} 30s{% endif %}

# OK - each branch emits a complete, valid YAML value
TIMEOUT: "{% if HAS_TIMEOUT | default('') %}30s{% else %}10s{% endif %}"
```

### TPL-10 - No secret in a template (SHOULD)

**A template must not contain a secret literal, not even in a comment.**

Secrets in template files are committed to the template repository and visible to everyone with
read access. Store secrets in Credential objects and reference them (see SEC-1).

```yaml
# Not OK - a secret literal baked into a template value
DB_PASSWORD: "s3cr3t-{{ current_env.name }}"

# OK - reference a Credential object
DB_PASSWORD: ${creds.get("db-cred").password}
```

### TPL-11 - No hardcoded derivable values (MUST)

**Do not write a literal for any value EnvGene can derive — environment name, cloud and cluster
names, cluster hosts and ports.**

Read these from the context variable or macro instead. See
[template macros](/docs/template-macros.md). TPL-12 to TPL-14 unpack the most common namespace
and solution cases.

```yaml
# Not OK - literals for values EnvGene already knows
DEPLOYMENT_ENV: env-1
CLOUD_NAME: cluster-01

# OK - read from the context
DEPLOYMENT_ENV: "{{ current_env.name }}"
CLOUD_NAME: "{{ current_env.cloud }}"
```

### TPL-12 - Reference the current namespace with a macro (SHOULD)

**Under TPL-11, use `${NAMESPACE}` to get the current namespace's name — do not rebuild it by
concatenation.**

Rebuilding the namespace name by hand (e.g. `current_env.name` + a postfix literal) re-implements
the naming convention and silently breaks if the scheme changes.

```yaml
# OK
PG_HOST: "pg-patroni.${NAMESPACE}"

# Not OK - the namespace name rebuilt by hand
PG_HOST: "pg-patroni.{{ current_env.name }}-oss"
```

### TPL-13 - Gate on app presence, not on a toggle (SHOULD)

**Under TPL-11, emit a parameter block based on whether an application is in the solution, not on
a hand-maintained toggle variable.**

Test `current_env.solution_structure` to check real presence. A hand-maintained
`additionalTemplateVariables` toggle must be kept in sync with the Solution Descriptor manually
and will drift. Combining a presence check with a real feature toggle is fine.

```yaml
# OK - presence derived from the solution structure
{% if 'billing-app' in current_env.solution_structure %}
BILLING_ENABLED: true
{% endif %}

# Not OK - a hand-kept flag standing in for presence
{% if current_env.additionalTemplateVariables.billing_enabled %}
BILLING_ENABLED: true
{% endif %}
```

### TPL-14 - Resolve a namespace by deploy-postfix, do not rebuild it (SHOULD)

**Under TPL-11, look up a namespace by its deploy-postfix rather than rebuilding its name by
string concatenation or carrying it in an `additionalTemplateVariables` key.**

The long-term target is a late-resolving calculator macro keyed by deploy-postfix (see TPL-15),
which resolves after all namespaces are rendered. Until that macro ships, use the documented Jinja
interim path `current_env.solution_structure['<app>']['<deploy-postfix>'].namespace`, which
returns Null when the neighbor is not yet rendered. The host suffix always follows TPL-7.

```yaml
# Not OK - a neighbor namespace name rebuilt by hand
OSS_NAMESPACE: "{{ current_env.name }}-oss"

# OK (target) - a late-resolving macro keyed by deploy-postfix (exact syntax to be finalised)
OSS_NAMESPACE: "${namespace_map('oss')}"

# OK (today) - documented Jinja interim, keyed by application then deploy-postfix
OSS_NAMESPACE: "{{ current_env.solution_structure['oss-app']['oss'].namespace }}"
```

### TPL-15 - Prefer a macro over a Jinja expression (SHOULD)

**When a value is available as both a calculator macro (`${...}`) and a Jinja expression
(`{{ ... }}`), prefer the macro.**

A macro does not require a `.j2` template, resolves late (so cross-references reflect deployed
state rather than a generation-time snapshot), and is a stable contract. Use Jinja when the value
must be fixed at generation time, or when no macro exposes it. TPL-12 and TPL-14 are the most
common namespace applications of this preference.

```yaml
# OK - a macro, resolved late, usable in a plain ParameterSet
PG_HOST: "pg-patroni.${NAMESPACE}"

# Not OK - Jinja recomputes the same name at generation time and requires a .j2 file
PG_HOST: "pg-patroni.{{ current_env.name }}-oss"
```

### TPL-16 - Edit inputs, not generated output (SHOULD)

**Never hand-edit a generated file — it will be overwritten on the next generation run.**

Generated files include the Effective Set, generated `cloud.yml` or namespace files, and anything
marked auto-generated. To change the output, edit the template or the inventory that produces it.

```yaml
# Not OK - hand-editing a file that is overwritten on the next generation run
# environments/<cluster>/<env>/effective-set/...   or a generated cloud.yml

# OK - edit the input that produces the output
# templates/.../parameters.yml.j2   or   environments/.../Inventory/parameters/...
```

---

## Exceptions

A rule cannot always be followed — for example, a downstream consumer requires a specific format
that the rule forbids, or a legacy consumer cannot be changed in the current window.

**"It was like this before"** and **"fix it later"** are not valid reasons for an exception.

When you genuinely cannot follow a rule, mark the deviation with an inline comment directly above
the parameter. The comment must state:

1. The rule ID being deviated from.
2. The consumer that forces the deviation.
3. What removes the exception (the condition under which the comment can be deleted).

```yaml
# [EXCEPTION VAL-3] trailing slash required by the legacy gateway.
# Remove when the gateway accepts the slash-free URL.
API_BASE_URL: https://gw.internal/
```
