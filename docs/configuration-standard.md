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
    - [PLACE-9 - One Cloud Passport per cluster (SHOULD)](#place-9---one-cloud-passport-per-cluster-should)
    - [PLACE-10 - Each entity in its type's directory (MUST)](#place-10---each-entity-in-its-types-directory-must)
  - [Secrets](#secrets)
    - [SEC-1 - No plaintext secrets (MUST)](#sec-1---no-plaintext-secrets-must)
    - [SEC-2 - No mixed plaintext and encrypted secrets (MUST)](#sec-2---no-mixed-plaintext-and-encrypted-secrets-must)
    - [SEC-3 - No secrets in runtime parameters (MUST)](#sec-3---no-secrets-in-runtime-parameters-must)
    - [SEC-4 - Credential shape matches the secret (SHOULD)](#sec-4---credential-shape-matches-the-secret-should)
    - [SEC-5 - Repository-wide encryption (MAY)](#sec-5---repository-wide-encryption-may)
  - [Integrity](#integrity)
    - [INT-1 - Schema-valid (MUST)](#int-1---schema-valid-must)
    - [INT-2 - Every reference resolves (MUST)](#int-2---every-reference-resolves-must)
    - [INT-3 - No shadowed same-name overrides (SHOULD)](#int-3---no-shadowed-same-name-overrides-should)
    - [INT-4 - No unreferenced entities (SHOULD)](#int-4---no-unreferenced-entities-should)
    - [INT-5 - No dead parameters (SHOULD)](#int-5---no-dead-parameters-should)
  - [Naming](#naming)
    - [NAME-1 - One name per concept (SHOULD)](#name-1---one-name-per-concept-should)
    - [NAME-2 - Filename equals `name` (MUST)](#name-2---filename-equals-name-must)
    - [NAME-3 - Kebab-case files, directories, and namespaces (SHOULD)](#name-3---kebab-case-files-directories-and-namespaces-should)
    - [NAME-4 - Name a ParameterSet by subject and category (SHOULD)](#name-4---name-a-parameterset-by-subject-and-category-should)
    - [NAME-5 - Name a Resource Profile Override by baseline and subsystem (SHOULD)](#name-5---name-a-resource-profile-override-by-baseline-and-subsystem-should)
    - [NAME-6 - Name a credential ID by purpose (SHOULD)](#name-6---name-a-credential-id-by-purpose-should)
    - [NAME-7 - Name a Shared Template Variable by purpose (SHOULD)](#name-7---name-a-shared-template-variable-by-purpose-should)
    - [NAME-8 - Name the Cloud Passport `passport` (SHOULD)](#name-8---name-the-cloud-passport-passport-should)
    - [NAME-9 - Name an infra Cloud Passport `passport-infra` (SHOULD)](#name-9---name-an-infra-cloud-passport-passport-infra-should)
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

## Scope

This standard describes how a well-formed EnvGene configuration is structured. It applies to the
parameters, credentials, Cloud Passport, and layer placement authored in EnvGene template and instance
repositories, whether written by hand or produced by tooling. It complements the descriptive references
such as [EnvGene Objects](/docs/envgene-objects.md) and [EnvGene Configuration](/docs/envgene-configs.md),
which define what these objects are, by stating how to author them well.

## How to read this standard

- **Normative keywords.** MUST and MUST NOT mark a requirement. SHOULD and SHOULD NOT mark a strong
  default - deviate only with a documented reason. MAY marks an optional practice. The keywords follow
  their RFC 2119 meaning.
- **Rule IDs.** Each rule has a stable ID in the form `AREA-N`, for example `SEC-1`. A new rule takes
  the next free ID in its area and does not renumber the rest.
- **Rule shape.** Each rule states what it requires and how to tell you comply, then shows a `# OK` and
  a `# Not OK` example. It adds a reason only where the reason guides a judgement call. Background and
  analysis live elsewhere, not in the rule.
- **Repository.** A rule applies in whichever repository the config it governs lives, usually both the
  template and the instance repository. A one-sided rule is clear from its subject - a Jinja rule applies
  where `.j2` templates live.
- **Deviations.** Record any deviation as described in [Exceptions](#exceptions).

## Terms

A value resolves through two distinct mechanisms, not one uniform chain. The instance override chain has
three layers, ordered from lowest to highest precedence. A higher layer overrides a lower one per key,
and a value that is a nested map is deep-merged, so a key the higher layer does not restate is kept. The
template repository is a separate composition layer.

Instance override chain, lowest to highest:

1. **Repository** - parameters shared across all clusters.
2. **Cluster** - values shared by every environment on one cluster.
3. **Environment** - values that differ per environment.

Composition layer:

- **Template repository** - constants true for every environment of a type, brought in by composition,
  not by the instance override chain.

Objects the rules refer to:

- **Cloud Passport** - a key-contract set of parameters describing a cluster and the infrastructure and
  platform applications installed on it. It is part of the override chain, merged in at the cluster
  level.
- **Association target** - a ParameterSet or a Resource Profile binds to a Cloud or a Namespace, set by
  the key it is listed under in `env_definition.yml`. This is independent of the file's layer. Shared
  Template Variables and shared credentials carry no such target and apply to the whole environment.
- **Application scope** - per-application values live inside a ParameterSet under `applications`, keyed by
  application name, and reach only that application. There is no separate per-application file.
- **Site** - EnvGene has no site object. The word means either the Repository layer, the widest file
  location, written `site` in file paths, or an `onsite`/`offsite` template variable that only Jinja
  reads. A value shared by a network-isolated site goes to the Repository layer or is branched in a
  template.

## Placement and grouping

Which layer a value sits at, which category and association carry it, and which entity holds it. Add a
rule here when it decides where a value belongs or how values are grouped into entities.

### PLACE-1 - Highest correct layer (SHOULD)

Define a value at the highest layer where it holds - template, repository, cluster, environment.
Override lower only for a genuine difference. A credential follows the same rule: place it at the layer
its consumers share, and no broader.

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
# environments/cluster-01/cloud-passport/passport.yml
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
The file may sit at the environment, cluster, or repository location. Only the binding is
fixed to the Cloud.

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

### PLACE-9 - One Cloud Passport per cluster (SHOULD)

Keep a cluster's Cloud Passport in `cloud-passport/` at the cluster directory, with its credentials file
beside it, and nowhere else. A cluster has one default passport (NAME-8) and, for a business/infra
split, at most one infra passport (NAME-9). Do not place a passport below the cluster level, and do not
leave more than one passport on an environment's resolution path. A second resolvable passport fails
generation, because the passport is pointed at by name and never merged, unlike a ParameterSet or
Resource Profile override. See [Cloud Passport processing](/docs/features/cloud-passport-processing.md)
for how EnvGene resolves it.

```yaml
# OK - one default passport at the cluster level (a split adds passport-infra.yml)
# environments/cluster-01/cloud-passport/passport.yml
# environments/cluster-01/cloud-passport/passport-creds.yml

# Not OK - a passport below the cluster level
# environments/cluster-01/env-1/Inventory/cloud-passport/passport.yml

# Not OK - the same passport duplicated on the resolution path
# environments/cluster-01/cloud-passport/passport.yml
# environments/cloud-passport/passport.yml
```

### PLACE-10 - Each entity in its type's directory (MUST)

An authored entity lives only in the directory its type defines: a ParameterSet in `parameters/`, a
Resource Profile Override in `resource_profiles/`, a Shared Template Variable in
`shared-template-variables/`, a shared credentials file in `credentials/`, and the Cloud Passport in
`cloud-passport/` (PLACE-9). The directory name is fixed by the entity type. Which layer it sits at
follows PLACE-1, and the exact per-layer path, such as an environment-level entity nested under
`Inventory/`, is the object's Location in [EnvGene Objects](/docs/envgene-objects.md). EnvGene loads an
entity only from its type's directory, so a file placed elsewhere is silently ignored and ships
nothing. Generated output directories such as `Credentials/`, `Profiles/`, and the effective set are
not authored, see TPL-16.

```yaml
# OK - a ParameterSet in the cluster parameters directory
# environments/cluster-01/parameters/cluster-bss.yml

# OK - an environment-level ParameterSet nested under Inventory
# environments/cluster-01/env-1/Inventory/parameters/env-1-bss.yml

# Not OK - a ParameterSet outside its type's directory -> silently ignored, ships nothing
# environments/cluster-01/env-1/Inventory/env-1-bss.yml
```

## Secrets

How secrets are handled so none reaches plaintext, Git, or a context that would expose it. Add a rule
here when it concerns a credential value or where secrets may appear.

### SEC-1 - No plaintext secrets (MUST)

A secret never appears as a literal parameter value in any object that defines parameters, such as a
ParameterSet, a Cloud, or Namespace. Create a Credential object named
`<product>-<purpose>-cred` and reference it with `${creds.get("<id>").<field>}`.

```yaml
# Not OK
DB_PASSWORD: s3cr3t

# OK - Inventory/credentials/db-cred.yml
db-cred:
  type: usernamePassword
  data:
    username: "<value>"
    password: "<value>"
# ParameterSet
DB_PASSWORD: ${creds.get("db-cred").password}
```

### SEC-2 - No mixed plaintext and encrypted secrets (MUST)

A repository never keeps a live secret in plaintext alongside encrypted ones. Once any credential material
is encrypted, no real secret remains in plaintext, because a single plaintext secret defeats the
encryption of the rest.

```yaml
# Not OK - one repository, mixed:
#   configuration/credentials.yml         SOPS-encrypted
#   Inventory/credentials/db-cred.yml     a real plaintext password
# OK - no live secret is left in plaintext alongside encrypted ones
```

### SEC-3 - No secrets in runtime parameters (MUST)

A secret is never placed in a runtime parameter (`technicalConfigurationParameters`). Runtime parameters
are applied live through Consul, which holds them in plaintext, so a secret there is exposed even though
the Effective Set encrypts it at rest. Keep the secret in a deployment parameter (`deployParameters`),
referenced through a Credential, where it reaches the application as a secret rather than Consul.

```yaml
# Not OK - a secret referenced in a runtime parameter, exposed in Consul
technicalConfigurationParameters:
  DB_PASSWORD: ${creds.get("db-cred").password}
# OK - the secret stays in a deployment parameter
deployParameters:
  DB_PASSWORD: ${creds.get("db-cred").password}
```

### SEC-4 - Credential shape matches the secret (SHOULD)

Declare a credential with the shape the secret actually has. A username and password pair is declared as
a pair, a single token or value as a single value. Do not pad a single value into a pair or collapse a
pair into a single field. This holds whether the secret is held locally or resolved from an external
store.

```yaml
# OK - a single value, local credential
registry-pull-cred:
  type: secret
  data:
    secret: "<value>"

# OK - a single value, resolved from an external store
app-token-cred:
  type: external
  remoteRefPath: cluster-01/env-1/app-token

# OK - a username and password pair, resolved from an external store
db-app-cred:
  type: external
  remoteRefPath: cluster-01/env-1/db-app
  properties:
    - name: username
    - name: password

# Not OK - a single value padded into a pair
registry-pull-cred:
  type: usernamePassword
  data:
    username: "<value>"
    password: "<value>"
```

### SEC-5 - Repository-wide encryption (MAY)

A repository may encrypt every credential file that holds secret material with SOPS, applying one backend
across the whole repository. This is optional: a repository whose secrets are resolved from an external
store, or that holds no local secret material, needs no repository-wide encryption.

```yaml
# OK - every credential file with secret material in the repository is encrypted with SOPS
# OK - no repository-wide encryption, because secrets are resolved from an external store
```

## Integrity

The configuration validates and resolves without ambiguity, and carries nothing dead. Add a rule here
when it decides whether the configuration is well-formed, resolves, or stays consistent.

### INT-1 - Schema-valid (MUST)

Every EnvGene object validates against its schema (see [EnvGene objects](/docs/envgene-objects.md)).

```yaml
# OK     - the object matches its schema: a *ParameterSets field is a list, a category body is a map
# Not OK - a *ParameterSets field given a map, or a required key missing -> generation fails
```

### INT-2 - Every reference resolves (MUST)

A `${creds.get("<id>")}`, a `$type: credRef`, and a
ParameterSet or Resource Profile reference each resolve to exactly one existing object. A dangling or
ambiguous reference fails generation.

```yaml
# Not OK - references a credential id no Credential defines -> generation fails
DB_PASSWORD: ${creds.get("bss-db-cred").password}
# OK - bss-db-cred exists in a credentials file on the resolution path
DB_PASSWORD: ${creds.get("bss-db-cred").password}
```

### INT-3 - No shadowed same-name overrides (SHOULD)

An env-specific ParameterSet, Credential, Shared
Template Variable, or Resource Profile resolves by reference name across environment, cluster, and
repository, first-match-wins. The highest-scope match is used, and same-named files at lower scopes are
ignored, not merged. Do not keep the same reference name at two scopes expecting a merge. Give each a
distinct name, or keep the override at one scope.

```yaml
# Not OK - same name at two scopes: the env file wins, the cluster file is silently ignored
# environments/cluster-01/env-1/Inventory/parameters/env-specific-bss.yml   (used)
# environments/cluster-01/parameters/env-specific-bss.yml                   (shadowed, edits do nothing)
# OK - distinct names, or a single scope
# environments/cluster-01/parameters/cluster-bss.yml
# environments/cluster-01/env-1/Inventory/parameters/env-1-bss.yml
```

### INT-4 - No unreferenced entities (SHOULD)

Remove an authored entity that no reference names: a ParameterSet in no `*ParameterSets` or
`envSpecific*` list, a Shared Template Variable in no `sharedTemplateVariables` array, a credential no
`creds.get` or `credRef` reads, a Resource Profile Override no `profile` or `override_name` selects.
EnvGene ignores an unreferenced entity, so it ships nothing and only misleads a reader. This is the
complement of INT-2. Count every reference site first: a system credential read by `deployer.yml`,
`registry.yml`, or the Cloud Passport, and a template entity an instance selects, are referenced outside
the current file or repository, not dead.

```yaml
# Not OK - a ParameterSet file named by no reference list
# parameters/legacy-oss-deploy.yml   (in no *ParameterSets or envSpecific* list)
# OK - remove it, or add the reference where it is genuinely needed
```

### INT-5 - No dead parameters (SHOULD)

Delete a parameter no consumer reads. A key is dead by who reads it, not by its value, so a dead key with
a real value is removed too, and an empty value a consumer reads stays.

```yaml
# Not OK - parameters for a decommissioned integration, read by no consumer
LEGACY_SERVICE_HOST: legacy.internal
LEGACY_SERVICE_PORT: 8080
# OK - the dead keys are removed
```

## Naming

How an entity and its keys are named so a consumer resolves them and a reader finds them. Add a rule
here when it constrains a name.

### NAME-1 - One name per concept (SHOULD)

Collapse true aliases to one canonical key and update its
consumers. Equal values are not proof of an alias - confirm the keys mean the same concept for the
same consumer before collapsing, because a wrong collapse drops a key some consumer reads.

```yaml
# Not OK - three names, one value
KAFKA_URL: kafka.internal:9092
BOOTSTRAP_SERVERS: kafka.internal:9092
STREAMING_BROKER_ADDRESS: kafka.internal:9092

# OK
KAFKA_BOOTSTRAP_SERVERS: kafka.internal:9092
```

### NAME-2 - Filename equals `name` (MUST)

The filename, without extension, equals the object's
`name` for a ParameterSet, an Application Definition, a Registry Definition, and an Artifact
Definition. EnvGene validates this and stops generation on a mismatch.

```yaml
# OK - file env-1-deploy.yml
name: env-1-deploy
# Not OK - file env-1-deploy.yml
name: deploy-params
```

### NAME-3 - Kebab-case files, directories, and namespaces (SHOULD)

Filenames, directory names, and
namespace names use kebab-case. YAML field names and enum values follow the object's own convention.

Casing is part of a name's identity, so kebab-case governs a new name. A name that a reference resolves
by exact string (a ParameterSet, Resource Profile Override, Shared Template Variable, or credential ID)
is not re-cased to fit this rule, because re-casing breaks the reference. A name an external producer
dictates, such as a Cloud Passport discovery ID or a legacy capitalised application or registry name, is
exempt.

```yaml
# OK
# environments/cluster-01/env-01/parameters.yml
# Not OK
# environments/Cluster_01/Env01/Parameters.yml
```

### NAME-4 - Name a ParameterSet by subject and category (SHOULD)

Name a ParameterSet `<subject>-<category>`, with an optional `-<topology>` suffix, kebab-case and equal
to the `name:` field.

| Part       | Required | Values                                                                                                                                                                  | Rule                                                                                                                                                                     |
| ---------- | -------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `subject`  | yes      | what the set configures at its scope: a service or namespace (`postgresql`, `oss`), the cloud (`cloud`), or a cross-cutting area (`monitoring`, `registry`, `platform`) | one stable identity                                                                                                                                                      |
| `category` | yes      | `deploy`, `pipeline`, or `runtime`                                                                                                                                      | matches the array that references the set: `deploy` from `deployParameterSets`, `pipeline` from `e2eParameterSets`, `runtime` from `technicalConfigurationParameterSets` |
| `topology` | no       | a repository's own topology flavor, for example `offsite`/`onsite`, `primary`/`dr`, `edge`/`core`                                                                       | only where topology is a real axis of variation                                                                                                                          |

The scope (site, cluster, environment) and whether the set is a base or an environment override come from
the file location, not from a name token. Never put an environment name, cluster name, release or version,
ticket ID, or date in the name.

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

Name a Resource Profile Override `<baseline>-<subsystem>-override`, with an optional `-<flavor>` suffix,
matching the `name:` field.

| Part        | Required | Values                                                                               | Rule                                                                                                   |
| ----------- | -------- | ------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------ |
| `baseline`  | yes      | `dev`, `prod`, `prod-nonha`, `dev-ha`                                                | the base profile being overridden, and it must equal the `baseline:` field value                       |
| `subsystem` | yes      | the domain whose applications the file carries: `bss`, `core`, `oss`, `dm`, `portal` | one subsystem per file                                                                                 |
| `override`  | yes      | the literal `override`                                                               | entity-type marker, singular for a new name (an existing `overrides` is not renamed)                   |
| `flavor`    | no       | a workload variant: `hawk`, `single`, `new-perf`                                     | an alternate profile for the same baseline and subsystem, not a second baseline and not an environment |

The `baseline:` field holds a base-profile name, never an environment name. Generation adds the
environment prefix through `updateRPOverrideNameWithEnvName`, so do not bake it into the name. Scope comes
from the file location.

```yaml
# OK
dev-core-override
prod-oss-override
dev-core-override-hawk
# Not OK
sit-dm-override                # baseline is dev, so the leading token contradicts the field
telus-dv2-multi-sql-override   # environment name baked in
```

### NAME-6 - Name a credential ID by purpose (SHOULD)

Name a credential ID, the key of a credentials entry, `<purpose>`, with an optional `-<role>` qualifier
and an optional `-cred` or `-creds` suffix.

| Part      | Required | Values                                                                                   | Rule                                                                                                      |
| --------- | -------- | ---------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------- |
| `purpose` | yes      | what the secret unlocks: `registry`, `argocd`, `keycloak`, `cmdb`, `dbaas`, `postgresql` | the primary dimension, named for purpose, not environment, application, or account                        |
| `role`    | no       | `deployer`, `client`, `admin`, `ci`                                                      | disambiguates when one purpose has several, with provenance normally from the source file, not this token |
| suffix    | no       | `-cred` or `-creds`                                                                      | optional, kept consistent within a scope, and an existing ID is not re-suffixed                           |

One logical credential is one credential ID (a `usernamePassword` or a `secret`). Do not split a username
and password pair into two `secret` entries. The generated Effective Set form (upper-snake `_USERNAME`
and `_PASSWORD`, SOPS-encrypted) is output, not an authoring convention. A credential ID a Cloud Passport
discovery process dictates is exempt.

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

Name a Shared Template Variable file `<purpose>`, with an optional `-<qualifier>`. The bare filename is
the name listed in the `sharedTemplateVariables` array, so the filename is the reference.

| Part        | Required | Values                                                        | Rule                                                                  |
| ----------- | -------- | ------------------------------------------------------------- | --------------------------------------------------------------------- |
| `purpose`   | yes      | a stable keyword: `toggles`, `ci-global-vars`, `ns-overrides` | the reference is this bare name, so the filename equals the reference |
| `qualifier` | no       | `-vars` or `-overrides` where it adds meaning                 | do not append a generic `-template-variables` suffix                  |

Scope comes from the file location: a repository-wide file is authored once under
`environments/configuration/variables/`, a per-environment file under the environment's
`Inventory/configuration/variables/`. A file not listed in `sharedTemplateVariables` is ignored.

```yaml
# OK
toggles
ci-global-vars
ns-overrides
# Not OK
saas-nd-bss-dev-template-variables   # customer, environment, and a generic suffix
toggles-release-2024.4               # release baked in
```

### NAME-8 - Name the Cloud Passport `passport` (SHOULD)

Name a cluster's Cloud Passport `passport.yml`, with its credentials in `passport-creds.yml`. Naming it
`passport` lets every environment in the cluster auto-associate it with no `inventory.cloudPassport`
field. `.yaml` is equally valid as `.yml`. A passport under any other name still resolves, but only by
matching the cluster directory name or an explicit reference, which is easier to get wrong.

```yaml
# OK - cloud-passport/passport.yml (default, auto-associated)
# Not OK - cloud-passport/cluster-01.yml (relies on the directory name)
```

### NAME-9 - Name an infra Cloud Passport `passport-infra` (SHOULD)

When a cluster runs a business/infra split (see
[Split a Cloud Passport for business and infra environments](/docs/how-to/split-cloud-passport-for-business-and-infra.md)),
name the infra passport `passport-infra.yml`, with credentials in `passport-infra-creds.yml`, alongside
the default `passport.yml` (NAME-8). Business environments keep auto-associating `passport.yml`. Each
infra environment references `passport-infra` explicitly with `inventory.cloudPassport: passport-infra`.

```yaml
# OK - cloud-passport/passport-infra.yml, infra env_definition.yml: inventory.cloudPassport: passport-infra
# Not OK - cloud-passport/cluster-01-infra.yml (old cluster-based name)
```

## Values

What a single value is: its YAML type, its format, and its reserved meanings. Add a rule here when it
constrains the content of one value.

### VAL-1 - A value's YAML type matches its consumer (MUST)

A parameter's type is fixed by the consumer that reads it, and YAML sets a value's type from its syntax,
so write the value so its parsed type is the one the consumer expects. Leave it bare when the consumer
reads a boolean, a number, or a list. Quote it when the consumer reads a string, including a string YAML
would otherwise coerce (a country code, a version, a leading-zero number). When the consumer expects a
type a general style would not, the consumer wins. In the deployment context the type contract is the
application Helm chart's `values.schema.json`.

```yaml
# OK - parsed type matches the consumer
REPLICA_COUNT: 3               # consumer reads a number
COUNTRY_CODE: "NO"             # consumer reads a string, quoted so it is not false
LEGACY_COUNT: "3"              # consumer reads a string, quoted even though it looks like a number
# Not OK - parsed type fights the consumer
MONITORING_ENABLED: "true"     # consumer reads a boolean, this is a string
CHART_VERSION: 1.20            # consumer reads a string, YAML coerced it to 1.2
```

### VAL-2 - Reserved-value semantics (MUST)

`envgeneNullValue` means "a value must be supplied here", not "empty" and not "delete". Use it for a
mandatory parameter whose value is not known at the current layer, for example a template that defers the
concrete value to the instance, so a lower layer fills it. Do not stand in an empty string for a
mandatory value, and do not repurpose reserved control markers or invent placeholders.

```yaml
# OK - a template marks a mandatory value the instance must fill
# template:
DB_HOST: envgeneNullValue
# instance:
DB_HOST: db.env-1.example.com
# Not OK - an empty string for a mandatory value, or the marker used to mean "off"
DB_HOST: ""
FEATURE_X: envgeneNullValue
```

### VAL-3 - URLs have no trailing slash (SHOULD)

No trailing `/` on a URL, so joining it with a path never yields a double slash.

```yaml
# OK
MY_SERVICE_URL: https://my-service.cluster-01.example.com
# Not OK - trailing slash
MY_SERVICE_URL: https://my-service.example.com/
```

### VAL-4 - Complex values are native YAML (SHOULD)

Author a structured value (a map or a list) as native YAML, never as a JSON string packed into one
value. Native YAML validates against the schema, reads in a diff, and merges per key across layers. A
packed string does none of these.

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

In a Resource Profile Override, write a memory or CPU value in its Kubernetes unit form - `512Mi`, `1Gi`,
`500m` - not as raw bytes. Kubernetes accepts both forms, so this is for readability and comparable diffs,
in the one place the consumer is fixed (the Kubernetes resource field).

```yaml
# OK
GATEWAY_MEMORY_LIMIT: 512Mi
GATEWAY_CPU_REQUEST: 500m
# Not OK - raw bytes, valid but unreadable
GATEWAY_MEMORY_LIMIT: 536870912
```

## Templating

How templates and macros derive values, and how to write Jinja that renders safely. Add a rule here
when it concerns a `.j2` template or a macro.

### TPL-1 - Jinja lives only in `.j2` templates (MUST)

A `.j2` template may use Jinja. An instance
ParameterSet, a Cloud Passport, and a Credential file are plain YAML with no Jinja.

```yaml
# OK - templates/.../parameters.yml.j2
MY_NAMESPACE: "{{ current_env.name }}-core"
# Not OK - the same Jinja in an instance file (environments/.../parameters.yml)
MY_NAMESPACE: "{{ current_env.name }}-core"
```

### TPL-2 - Override at a layer, not through Jinja plumbing (MUST)

To change a value at a layer,
place the value at that layer. Do not add Jinja plus `additionalTemplateVariables` plus interpolation
to push a value down. Interpolation composes a string, it does not pass a key through unchanged.

```yaml
# Not OK - the template re-emits a key just to pass it through
# parameters.yml.j2:  LOG_LEVEL: "{{ LOG_LEVEL }}"   with additionalTemplateVariables LOG_LEVEL: info
# OK - set the value at the layer, no template logic
# environments/<cluster>/<env>/parameters.yml:  LOG_LEVEL: info
```

### TPL-3 - Default at a layer, not a Jinja default (MUST)

Put a default value in a shallower layer
and override the delta deeper. Use a Jinja conditional only for genuine branching, not to supply a
missing default.

```yaml
# Not OK - default hidden in template logic
TIMEOUT: "{{ TIMEOUT | default('30s') }}"
# OK - default at the template layer, optional override at env
# template parameters.yml.j2:  TIMEOUT: 30s
# env parameters.yml (optional):  TIMEOUT: 60s
```

### TPL-4 - A reference never fails on a missing value (SHOULD)

A value that can be absent is wrapped
with `| default(...)`, so a missing input renders empty instead of failing generation.

```yaml
# Not OK - fails when FEATURE_A is absent
ENABLED: "{% if FEATURE_A == 'on' %}true{% else %}false{% endif %}"
# OK - safe on absence
ENABLED: "{% if FEATURE_A | default('') == 'on' %}true{% else %}false{% endif %}"
```

### TPL-5 - No per-level presence guards (SHOULD)

Do not guard a nested access with an `is defined` check at each level. EnvGene resolves a missing key at
any depth of a path, whether an attribute or a dictionary key, to empty rather than an error, so a
per-level guard wall defends against a failure that cannot happen. Read the value with one trailing
`| default(...)` (see TPL-4), which covers the whole path, and use a single `is defined` on the full path
only to branch on whether an optional block is present.

```yaml
# Not OK - a guard at each level, standing in for a failure that cannot occur
DR_MODE: "{% if current_env.additionalTemplateVariables is defined and current_env.additionalTemplateVariables.drParameters is defined %}{{ current_env.additionalTemplateVariables.drParameters.mode }}{% endif %}"
# OK - one trailing default covers every missing level of the path
DR_MODE: "{{ current_env.additionalTemplateVariables.drParameters.mode | default('') }}"
# OK - a single presence test to branch on an optional block
{% if current_env.additionalTemplateVariables.drParameters is defined %}
DR_ENABLED: true
{% endif %}
```

### TPL-6 - Keep template logic small (SHOULD)

Use `if`, `elif`, `else`, and the filters `default`,
`join`, `upper`, and `lower`. Use a `for` loop only to iterate a genuinely dynamic list. Never use
`macro`, `include`, `import`, `extends`, `block`, `raw`, or a custom filter - reuse comes from template
composition. Deeply nested logic is a signal the value should be set by placement, not by rendering.

```yaml
# Not OK - macro and include
# {% macro url(h) %}...{% endmacro %}   {% include "shared.j2" %}
# OK - a single conditional
FEATURE: "{% if SITE | default('') == 'onsite' %}on{% else %}off{% endif %}"
```

### TPL-7 - Build URLs from the Cloud Passport host (MUST)

Compose a service URL from the passport
host value (`CLOUD_PUBLIC_HOST`), not from a hardcoded cluster hostname. The template appends the path
to the host.

```yaml
# Not OK - hardcoded cluster hostname
MY_SERVICE_URL: https://my-service.cluster-01.example.com
# OK - built from the passport host
MY_SERVICE_URL: "https://my-service.{{ CLOUD_PUBLIC_HOST }}"
```

### TPL-8 - Protect Helm passthrough (MUST)

A token meant for Helm, not EnvGene, is wrapped in
`{% raw %}` so EnvGene does not evaluate it. EnvGene renders its own `{{ }}` and leaves Helm's for the
chart.

```yaml
# Not OK - EnvGene evaluates a Helm token and breaks it
RELEASE: "{{ .Release.Name }}"
# OK - protected for Helm
RELEASE: "{% raw %}{{ .Release.Name }}{% endraw %}"
```

### TPL-9 - Every branch renders valid YAML (SHOULD)

Each branch of a conditional emits well-formed
YAML of the target shape. No branch leaves a half-written key or a broken document.

```yaml
# Not OK - the empty branch leaves a dangling key
TIMEOUT:{% if HAS_TIMEOUT %} 30s{% endif %}
# OK - each branch emits a complete value
TIMEOUT: "{% if HAS_TIMEOUT | default('') %}30s{% else %}10s{% endif %}"
```

### TPL-10 - No secret in a template (SHOULD)

A template holds no secret literal and no secret in a
comment. Secrets live in Credential objects and are referenced (see SEC-1).

```yaml
# Not OK - a secret baked into a template value
DB_PASSWORD: "s3cr3t-{{ current_env.name }}"
# OK - reference a credential
DB_PASSWORD: ${creds.get("db-cred").password}
```

### TPL-11 - No hardcoded derivable values (MUST)

Do not author a literal for a value EnvGene derives - the environment name, cloud and cluster names,
cluster hosts and ports. Read it from the context variable or macro instead (see
[template macros](/docs/template-macros.md)).
Build a URL from the Cloud Passport host per TPL-7. TPL-12 to TPL-14 unpack the common namespace and
solution cases.

```yaml
# Not OK - literals for derived values
DEPLOYMENT_ENV: env-1
CLOUD_NAME: cluster-01
# OK - read from the context
DEPLOYMENT_ENV: "{{ current_env.name }}"
CLOUD_NAME: "{{ current_env.cloud }}"
```

### TPL-12 - Reference the current namespace with a macro (SHOULD)

Under TPL-11, when a value must contain the current namespace's name, read it from `${NAMESPACE}`, which
EnvGene resolves from the rendered Namespace object. Do not rebuild the name by concatenation such as
`current_env.name` plus a postfix literal, which re-implements the naming convention and drifts when the
scheme changes.

```yaml
# OK
PG_HOST: "pg-patroni.${NAMESPACE}"
# Not OK - the same name rebuilt by hand
PG_HOST: "pg-patroni.{{ current_env.name }}-oss"
```

### TPL-13 - Gate on app presence, not on a toggle (SHOULD)

Under TPL-11, emit a parameter block only when an application is really in the solution by testing
`current_env.solution_structure`, so presence follows the resolved composition. Do not gate the same
decision on a hand-maintained `additionalTemplateVariables` toggle, which an operator must keep in sync
with the Solution Descriptor and which drifts. Combining presence with a real feature toggle is fine.

```yaml
# OK - presence derived from the solution
{% if 'billing-app' in current_env.solution_structure %}
BILLING_ENABLED: true
{% endif %}
# Not OK - a hand-kept flag standing in for presence
{% if current_env.additionalTemplateVariables.billing_enabled %}
BILLING_ENABLED: true
{% endif %}
```

### TPL-14 - Resolve a namespace by deploy-postfix, do not rebuild it (SHOULD)

Under TPL-11, when a value must contain the current namespace's name or a neighbor's, look it up by its
deploy-postfix rather than rebuilding it by concatenation or carrying it in an
`additionalTemplateVariables` key. The target is a late-resolving calculator macro keyed by
deploy-postfix (see TPL-15), which resolves after every namespace is rendered and so never sees a
neighbor as Null. That macro is not yet available, so until it ships resolve a neighbor through the
documented Jinja path `current_env.solution_structure['<app>']['<deploy-postfix>'].namespace`, which
returns Null when the neighbor is not yet rendered. The host suffix stays under TPL-7.

```yaml
# Not OK - a neighbor namespace name rebuilt by hand
OSS_NAMESPACE: "{{ current_env.name }}-oss"
# OK (target) - a late-resolving macro keyed by deploy-postfix, exact syntax to be finalized
OSS_NAMESPACE: "${namespace_map('oss')}"
# OK (today) - documented Jinja interim, keyed by application then deploy-postfix
OSS_NAMESPACE: "{{ current_env.solution_structure['oss-app']['oss'].namespace }}"
```

### TPL-15 - Prefer a macro over a Jinja expression (SHOULD)

When the same value is available as a calculator macro (`${...}`) and as a Jinja expression (`{{ ... }}`),
prefer the macro. A macro needs no `.j2` template, resolves late so a cross-reference reflects the
deployed state instead of a generation-time snapshot, and is a stable contract. Reach for Jinja when the
value must be fixed at generation, or when no macro exposes it. TPL-12 and TPL-14 are the namespace cases
of this preference.

```yaml
# OK - a macro, resolved late in a plain ParameterSet
PG_HOST: "pg-patroni.${NAMESPACE}"
# Not OK - Jinja recomputes the same name at generation and needs a .j2
PG_HOST: "pg-patroni.{{ current_env.name }}-oss"
```

### TPL-16 - Edit inputs, not generated output (SHOULD)

A generated object - the Effective Set, a
generated `cloud.yml` or namespace file, anything marked auto-generated - is overwritten on the next
generation. To change it, edit the template or the inventory that produces it, not the generated file.

```yaml
# Not OK - hand-editing a generated file (overwritten next run)
# environments/<cluster>/<env>/effective-set/...   or a generated cloud.yml
# OK - edit the input that produces it
# templates/.../parameters.yml.j2   or   environments/.../Inventory/parameters/...
```

## Exceptions

A rule cannot always be followed, because a downstream consumer requires a specific format or a legacy
consumer cannot be changed in the current window. "It was like this before" and "fix it later" are not
valid reasons.

Mark a deviation with an inline comment above the parameter. The comment names the rule ID, the
consumer that forces it, and what removes it.

```yaml
# [EXCEPTION VAL-3] trailing slash required by the legacy gateway.
# Remove when the gateway accepts the slash-free URL.
API_BASE_URL: https://gw.internal/
```
