# EnvGene configuration standard

- [EnvGene configuration standard](#envgene-configuration-standard)
  - [Scope](#scope)
  - [How to read this standard](#how-to-read-this-standard)
  - [Terms](#terms)
  - [Placement and layering](#placement-and-layering)
    - [PLACE-1 - Highest correct layer (SHOULD)](#place-1---highest-correct-layer-should)
    - [PLACE-2 - Override only the delta (SHOULD)](#place-2---override-only-the-delta-should)
    - [PLACE-3 - Place by the system tier (SHOULD)](#place-3---place-by-the-system-tier-should)
    - [PLACE-4 - Contract keys in the Cloud Passport (SHOULD)](#place-4---contract-keys-in-the-cloud-passport-should)
    - [PLACE-5 - Right parameter category (SHOULD)](#place-5---right-parameter-category-should)
    - [PLACE-6 - One resolvable Cloud Passport (MUST)](#place-6---one-resolvable-cloud-passport-must)
    - [PLACE-7 - Pipeline parameters bind to the Cloud (SHOULD)](#place-7---pipeline-parameters-bind-to-the-cloud-should)
  - [Secrets and credentials](#secrets-and-credentials)
    - [SEC-1 - No plaintext secrets (MUST)](#sec-1---no-plaintext-secrets-must)
    - [SEC-2 - Credential shape matches the secret (SHOULD)](#sec-2---credential-shape-matches-the-secret-should)
    - [SEC-3 - Repository-wide encryption (MAY)](#sec-3---repository-wide-encryption-may)
    - [SEC-4 - No mixed plaintext and encrypted secrets (MUST)](#sec-4---no-mixed-plaintext-and-encrypted-secrets-must)
    - [SEC-5 - No secrets in runtime parameters (MUST)](#sec-5---no-secrets-in-runtime-parameters-must)
  - [Naming](#naming)
    - [NAME-1 - One name per concept (SHOULD)](#name-1---one-name-per-concept-should)
    - [NAME-2 - Filename equals `name` (MUST)](#name-2---filename-equals-name-must)
    - [NAME-3 - Kebab-case files, directories, and namespaces (SHOULD)](#name-3---kebab-case-files-directories-and-namespaces-should)
    - [NAME-4 - Name a ParameterSet by subject and category (SHOULD)](#name-4---name-a-parameterset-by-subject-and-category-should)
    - [NAME-5 - Name a Resource Profile Override by baseline and subsystem (SHOULD)](#name-5---name-a-resource-profile-override-by-baseline-and-subsystem-should)
    - [NAME-6 - Name a credential id by purpose (SHOULD)](#name-6---name-a-credential-id-by-purpose-should)
    - [NAME-7 - Name a Shared Template Variable by purpose (SHOULD)](#name-7---name-a-shared-template-variable-by-purpose-should)
  - [Values: type and format](#values-type-and-format)
    - [VAL-1 - Native YAML types (MUST)](#val-1---native-yaml-types-must)
    - [VAL-2 - URLs use DNS names, no trailing slash (SHOULD)](#val-2---urls-use-dns-names-no-trailing-slash-should)
    - [VAL-3 - Multi-line values use block scalars (SHOULD)](#val-3---multi-line-values-use-block-scalars-should)
    - [VAL-4 - No hardcoded environment names (MUST)](#val-4---no-hardcoded-environment-names-must)
    - [VAL-5 - Consistent units and formats (SHOULD)](#val-5---consistent-units-and-formats-should)
    - [VAL-6 - Pin immutable versions (SHOULD)](#val-6---pin-immutable-versions-should)
    - [VAL-7 - Quote coercion-prone scalars (SHOULD)](#val-7---quote-coercion-prone-scalars-should)
    - [VAL-8 - No volatile values (SHOULD)](#val-8---no-volatile-values-should)
  - [Flags and safe defaults](#flags-and-safe-defaults)
    - [FLAG-1 - Debug and bypass flags default to false (SHOULD)](#flag-1---debug-and-bypass-flags-default-to-false-should)
  - [Hygiene and safety](#hygiene-and-safety)
    - [HYG-1 - No empty or dead parameters (SHOULD)](#hyg-1---no-empty-or-dead-parameters-should)
    - [HYG-2 - Reserved-value semantics (MUST)](#hyg-2---reserved-value-semantics-must)
    - [HYG-3 - Schema-valid (MUST)](#hyg-3---schema-valid-must)
    - [HYG-4 - Flat parameters over deep nesting (SHOULD)](#hyg-4---flat-parameters-over-deep-nesting-should)
    - [HYG-5 - No shadowed same-name overrides (SHOULD)](#hyg-5---no-shadowed-same-name-overrides-should)
    - [HYG-6 - Every reference resolves (MUST)](#hyg-6---every-reference-resolves-must)
    - [HYG-7 - Edit inputs, not generated output (SHOULD)](#hyg-7---edit-inputs-not-generated-output-should)
  - [Templating and Jinja](#templating-and-jinja)
    - [TPL-1 - Jinja lives only in `.j2` templates (MUST)](#tpl-1---jinja-lives-only-in-j2-templates-must)
    - [TPL-2 - Override at a layer, not through Jinja plumbing (SHOULD)](#tpl-2---override-at-a-layer-not-through-jinja-plumbing-should)
    - [TPL-3 - Default at a layer, not a Jinja default (SHOULD)](#tpl-3---default-at-a-layer-not-a-jinja-default-should)
    - [TPL-4 - A reference never fails on a missing value (SHOULD)](#tpl-4---a-reference-never-fails-on-a-missing-value-should)
    - [TPL-5 - No defensive-guard walls (SHOULD)](#tpl-5---no-defensive-guard-walls-should)
    - [TPL-6 - Keep template logic small (SHOULD)](#tpl-6---keep-template-logic-small-should)
    - [TPL-7 - Build URLs from the Cloud Passport host (SHOULD)](#tpl-7---build-urls-from-the-cloud-passport-host-should)
    - [TPL-8 - Protect Helm passthrough (MUST)](#tpl-8---protect-helm-passthrough-must)
    - [TPL-9 - Every branch renders valid YAML (SHOULD)](#tpl-9---every-branch-renders-valid-yaml-should)
    - [TPL-10 - No secret in a template (SHOULD)](#tpl-10---no-secret-in-a-template-should)
  - [Exceptions](#exceptions)

## Scope

This standard describes how a well-formed EnvGene configuration is structured. It applies to the
parameters, credentials, Cloud Passport, and layer placement authored in EnvGene template and instance
repositories, whether written by hand or produced by tooling.

## How to read this standard

- **Normative keywords.** MUST and MUST NOT mark a requirement. SHOULD and SHOULD NOT mark a strong
  default - deviate only with a documented reason. MAY marks an optional practice. The keywords follow
  their RFC 2119 meaning.
- **Rule IDs.** Each rule has a stable ID in the form `AREA-N`, for example `SEC-1`. A new rule takes
  the next free ID in its area and does not renumber the rest.
- **Rule shape.** Each rule states what it requires and how to tell you comply, then shows a `# OK` and
  a `# Not OK` example. It adds a reason only where the reason guides a judgement call. Background and
  analysis live elsewhere, not in the rule.
- **Deviations.** Record any deviation as described in [Exceptions](#exceptions).

## Terms

A value resolves through two distinct mechanisms, not one uniform chain. The instance override chain has
three layers, ordered from lowest to highest precedence, and a higher layer overrides a lower one
(first-match-wins per key). The template repository is a separate composition layer.

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

## Placement and layering

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
the platform or the Kubernetes cluster the environment runs on is the same for every environment on that
cluster, so it lives at the cluster layer, and a Cloud Passport contract key lives in the passport (see
PLACE-4). A business environment runs on both a platform and Kubernetes, so its cluster-layer values can
describe either. A platform environment runs on Kubernetes alone.

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
See [Cloud Passport](TBD).

```yaml
# OK - a contract key in the passport
# environments/cluster-01/cloud-passport/cluster-01.yml
dbaas:
  DBAAS_AGGREGATOR_ADDRESS: https://dbaas.cluster-01.example.com

# Not OK - a contract key sitting in a ParameterSet
# .../Inventory/parameters/env-1-deploy.yml
DBAAS_AGGREGATOR_ADDRESS: https://dbaas.cluster-01.example.com
```

### PLACE-5 - Right parameter category (SHOULD)

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

### PLACE-6 - One resolvable Cloud Passport (MUST)

An environment that uses a Cloud Passport resolves to exactly one passport file. When
`env_definition.yml` sets `inventory.cloudPassport: <name>`, exactly one `<name>.{yml,yaml}` exists in
the search path from the environment directory up to the repository root. With no `cloudPassport` field,
auto-association takes `cloud-passport/<cluster>.{yml,yaml}` then `cloud-passport/passport.{yml,yaml}`.
Zero matches or duplicate matches fail generation. Unlike a ParameterSet or Resource Profile, which
resolves by first-match across scopes (see HYG-5, HYG-6), the Cloud Passport is pointed at by name and
never merged, so a duplicate in the path is an error rather than an override.

```yaml
# OK - the reference resolves to exactly one file
# env_definition.yml: inventory.cloudPassport: cluster-01
# environments/cluster-01/cloud-passport/cluster-01.yml   (the one match)

# Not OK - no file named cluster-01 in the path      -> not-found, generation fails
# Not OK - two files named cluster-01 in the path    -> duplicate, generation fails
```

### PLACE-7 - Pipeline parameters bind to the Cloud (SHOULD)

A pipeline parameter set, the pipeline context named `e2eParameters` in v2, associates to the Cloud,
never to a Namespace. Under `envTemplate.envSpecificE2EParamsets` the reserved key `cloud` selects the
Cloud. A namespace identifier (its `deploy_postfix`) is also accepted there, but do not use one for
pipeline parameters. The file may sit at the env, cluster, or repository location. Only the binding is
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

## Secrets and credentials

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

### SEC-2 - Credential shape matches the secret (SHOULD)

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

### SEC-3 - Repository-wide encryption (MAY)

A repository may encrypt every credential file that holds secret material with SOPS, applying one backend
across the whole repository. This is optional: a repository whose secrets are resolved from an external
store, or that holds no local secret material, needs no repository-wide encryption.

```yaml
# OK - every credential file with secret material in the repository is encrypted with SOPS
# OK - no repository-wide encryption, because secrets are resolved from an external store
```

### SEC-4 - No mixed plaintext and encrypted secrets (MUST)

A repository never keeps a live secret in plaintext alongside encrypted ones. Once any credential material
is encrypted, no real secret remains in plaintext, because a single plaintext secret defeats the
encryption of the rest.

```yaml
# Not OK - one repository, mixed:
#   configuration/credentials.yml         SOPS-encrypted
#   Inventory/credentials/db-cred.yml     a real plaintext password
# OK - no live secret is left in plaintext alongside encrypted ones
```

### SEC-5 - No secrets in runtime parameters (MUST)

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

## Naming

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
by exact string (a ParameterSet, Resource Profile Override, Shared Template Variable, or credential id)
is not re-cased to fit this rule, because re-casing breaks the reference. A name an external producer
dictates, such as a Cloud Passport discovery id or a legacy capitalised application or registry name, is
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

| Part | Required | Values | Rule |
|---|---|---|---|
| `subject` | yes | what the set configures at its scope: a service or namespace (`postgresql`, `oss`), the cloud (`cloud`), or a cross-cutting area (`monitoring`, `registry`, `platform`) | one stable identity |
| `category` | yes | `deploy`, `pipeline`, or `runtime` | matches the array that references the set: `deploy` from `deployParameterSets`, `pipeline` from `e2eParameterSets`, `runtime` from `technicalConfigurationParameterSets` |
| `topology` | no | a repository's own topology flavor, for example `offsite`/`onsite`, `primary`/`dr`, `edge`/`core` | only where topology is a real axis of variation |

The scope (site, cluster, environment) and whether the set is a base or an environment override come from
the file location, not from a name token. Never put an environment name, cluster name, release or version,
ticket id, or date in the name.

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

| Part | Required | Values | Rule |
|---|---|---|---|
| `baseline` | yes | `dev`, `prod`, `prod-nonha`, `dev-ha` | the base profile being overridden, and it must equal the `baseline:` field value |
| `subsystem` | yes | the domain whose applications the file carries: `bss`, `core`, `oss`, `dm`, `portal` | one subsystem per file |
| `override` | yes | the literal `override` | entity-type marker, singular for a new name (an existing `overrides` is not renamed) |
| `flavor` | no | a workload variant: `hawk`, `single`, `new-perf` | an alternate profile for the same baseline and subsystem, not a second baseline and not an environment |

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

### NAME-6 - Name a credential id by purpose (SHOULD)

Name a credential id, the key of a credentials entry, `<purpose>`, with an optional `-<role>` qualifier
and an optional `-cred` or `-creds` suffix.

| Part | Required | Values | Rule |
|---|---|---|---|
| `purpose` | yes | what the secret unlocks: `registry`, `argocd`, `keycloak`, `cmdb`, `dbaas`, `postgresql` | the primary dimension, named for purpose, not environment, application, or account |
| `role` | no | `deployer`, `client`, `admin`, `ci` | disambiguates when one purpose has several, with provenance normally from the source file, not this token |
| suffix | no | `-cred` or `-creds` | optional, kept consistent within a scope, and an existing id is not re-suffixed |

One logical credential is one credential id (a `usernamePassword` or a `secret`). Do not split a username
and password pair into two `secret` entries. The generated Effective Set form (upper-snake `_USERNAME`
and `_PASSWORD`, SOPS-encrypted) is output, not an authoring convention. A credential id a Cloud Passport
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

| Part | Required | Values | Rule |
|---|---|---|---|
| `purpose` | yes | a stable keyword: `toggles`, `ci-global-vars`, `ns-overrides` | the reference is this bare name, so the filename equals the reference |
| `qualifier` | no | `-vars` or `-overrides` where it adds meaning | do not append a generic `-template-variables` suffix |

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

## Values: type and format

### VAL-1 - Native YAML types (MUST)

Booleans, numbers, and lists are unquoted native types, not
strings. Name flags by intent - `_ENABLED` (runtime on or off) differs from `_INSTALL` (installed or
not).

```yaml
# OK
MONITORING_ENABLED: true
REPLICA_COUNT: 3
# Not OK - a quoted "false" is still truthy
MONITORING_ENABLED: "true"
REPLICA_COUNT: "3"
```

### VAL-2 - URLs use DNS names, no trailing slash (SHOULD)

No raw IP addresses, and no trailing `/`.

```yaml
# OK
MY_SERVICE_URL: https://my-service.cluster-01.example.com
# Not OK
MY_SERVICE_URL: https://10.42.0.15                  # raw IP
MY_SERVICE_URL: https://my-service.example.com/     # trailing slash
```

### VAL-3 - Multi-line values use block scalars (SHOULD)

`|` preserves newlines and `>` folds them.
No escaped `\n`.

```yaml
# Not OK
TLS_CERT: "-----BEGIN CERTIFICATE-----\nMIIB...\n-----END CERTIFICATE-----"
# OK
TLS_CERT: |
  -----BEGIN CERTIFICATE-----
  MIIB...
  -----END CERTIFICATE-----
```

### VAL-4 - No hardcoded environment names (MUST)

A value that embeds the environment's own name is
derived with `{{ current_env.name }}` in a `.j2` template, not written literally in a ParameterSet. A
fixed infrastructure namespace that does not embed the environment name, such as `platform-monitoring`,
is fine.

```yaml
# Not OK - environment name baked into a ParameterSet value
MY_NAMESPACE: env-1-core
# OK - derived in the .j2 template
MY_NAMESPACE: "{{ current_env.name }}-core"
```

### VAL-5 - Consistent units and formats (SHOULD)

Memory as Kubernetes quantities such as `512Mi`,
durations with a unit, and one date-time format across the repository.

```yaml
# OK
MEMORY_LIMIT: 512Mi
REQUEST_TIMEOUT: 30s
# Not OK - raw bytes and a bare number
MEMORY_LIMIT: 536870912
REQUEST_TIMEOUT: 30
```

### VAL-6 - Pin immutable versions (SHOULD)

A parameter value that selects an artifact or an image
pins an immutable version, not a floating tag such as `latest`, so the same input resolves the same
artifact.

```yaml
# OK
IMAGE_TAG: 1.42.0
# Not OK - floats, so it can resolve a different artifact later
IMAGE_TAG: latest
```

### VAL-7 - Quote coercion-prone scalars (SHOULD)

Quote a string value that YAML would coerce to
another type, so it keeps its meaning. This is the complement of VAL-1, which keeps real booleans and
numbers unquoted.

```yaml
# Not OK - YAML coerces the value
COUNTRY_CODE: NO       # becomes false
FEATURE_STATE: on      # becomes true
BUILD_NUMBER: 0123     # becomes octal 83
CHART_VERSION: 1.20    # trailing zero lost, becomes 1.2
# OK - quoted, stays a string
COUNTRY_CODE: "NO"
FEATURE_STATE: "on"
BUILD_NUMBER: "0123"
CHART_VERSION: "1.20"
```

### VAL-8 - No volatile values (SHOULD)

Do not put a timestamp, a random value, or anything that
changes between renders into a parameter. The same inputs must render the same value.

```yaml
# Not OK - changes on every render
BUILD_TIMESTAMP: 2026-07-28T10:15:00Z
CACHE_BUSTER: 8f3a9c1
# OK - a stable, meaningful value
RELEASE_VERSION: 1.42.0
```

## Flags and safe defaults

### FLAG-1 - Debug and bypass flags default to false (SHOULD)

`DEBUG_*`, `SKIP_*`, `BYPASS_*`, and
`DISABLE_*` default to `false` at cluster level. Override up only where a specific environment needs
it.

```yaml
# OK - cluster level safe default, env override only where needed
# cluster-01-cloud-deploy.yml -> SKIP_VALIDATION: false
# dev-env deploy              -> SKIP_VALIDATION: true
# Not OK - a bypass defaulted on at cluster level
SKIP_VALIDATION: true
```

## Hygiene and safety

### HYG-1 - No empty or dead parameters (SHOULD)

Delete an unused key. A value that must exist but is
unset uses `envgeneNullValue`.

```yaml
# Not OK - empty inactive integration left behind
LEGACY_SERVICE_HOST: ""
# OK - deleted, or if it must exist but is unset
LEGACY_SERVICE_HOST: envgeneNullValue
```

### HYG-2 - Reserved-value semantics (MUST)

`envgeneNullValue` means "a value must be supplied here",
not "empty" and not "delete". Do not repurpose reserved control markers or invent placeholders.

```yaml
# OK - operator must supply this
DB_PASSWORD: envgeneNullValue
# Not OK - used to mean "off" or "empty"
FEATURE_X: envgeneNullValue
```

### HYG-3 - Schema-valid (MUST)

Every object validates against its schema. Schema does not enforce
`name` equals filename or name uniqueness - those are convention rules (`NAME-2`, `NAME-1`), not schema
claims.

```yaml
# OK     - object matches its schema; *ParameterSets fields are lists, category bodies are maps
# Not OK - a *ParameterSets field given a map, or a required key missing -> generation fails
```

### HYG-4 - Flat parameters over deep nesting (SHOULD)

Keep parameter keys flat where the consumer
allows it. A nested map is not a violation when a chart's `values.yaml` requires that shape. The hazard
is that a higher layer replaces a whole map rather than merging into it, so a partial override at the
higher layer drops the sibling keys it did not restate.

```yaml
# Not OK - deep nesting, cross-layer merge is hard to predict
service:
  cache:
    ttl: 300
    enabled: true
# OK - flat, predictable override
SERVICE_CACHE_TTL: 300
SERVICE_CACHE_ENABLED: true
```

### HYG-5 - No shadowed same-name overrides (SHOULD)

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

### HYG-6 - Every reference resolves (MUST)

A `${creds.get("<id>")}`, a `$type: credRef`, and a
ParameterSet or Resource Profile reference each resolve to exactly one existing object. A dangling or
ambiguous reference fails generation.

```yaml
# Not OK - references a credential id no Credential defines -> generation fails
DB_PASSWORD: ${creds.get("bss-db-cred").password}
# OK - bss-db-cred exists in a credentials file on the resolution path
DB_PASSWORD: ${creds.get("bss-db-cred").password}
```

### HYG-7 - Edit inputs, not generated output (SHOULD)

A generated object - the Effective Set, a
generated `cloud.yml` or namespace file, anything marked auto-generated - is overwritten on the next
generation. To change it, edit the template or the inventory that produces it, not the generated file.

```yaml
# Not OK - hand-editing a generated file (overwritten next run)
# environments/<cluster>/<env>/effective-set/...   or a generated cloud.yml
# OK - edit the input that produces it
# templates/.../parameters.yml.j2   or   environments/.../Inventory/parameters/...
```

## Templating and Jinja

Jinja renders a template to configuration. Keep it small: most values belong at a layer, not in template
logic.

### TPL-1 - Jinja lives only in `.j2` templates (MUST)

A `.j2` template may use Jinja. An instance
ParameterSet, a Cloud Passport, and a Credential file are plain YAML with no Jinja.

```yaml
# OK - templates/.../parameters.yml.j2
MY_NAMESPACE: "{{ current_env.name }}-core"
# Not OK - the same Jinja in an instance file (environments/.../parameters.yml)
MY_NAMESPACE: "{{ current_env.name }}-core"
```

### TPL-2 - Override at a layer, not through Jinja plumbing (SHOULD)

To change a value at a layer,
place the value at that layer. Do not add Jinja plus `additionalTemplateVariables` plus interpolation
to push a value down. Interpolation composes a string, it does not pass a key through unchanged.

```yaml
# Not OK - the template re-emits a key just to pass it through
# parameters.yml.j2:  LOG_LEVEL: "{{ LOG_LEVEL }}"   with additionalTemplateVariables LOG_LEVEL: info
# OK - set the value at the layer, no template logic
# environments/<cluster>/<env>/parameters.yml:  LOG_LEVEL: info
```

### TPL-3 - Default at a layer, not a Jinja default (SHOULD)

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

### TPL-5 - No defensive-guard walls (SHOULD)

Do not stack presence checks (`is defined`, nested-key
walks) to cover a value the layers should provide. If a template needs a guard everywhere, the value
belongs at a layer (see TPL-3).

```yaml
# Not OK - a guard wall standing in for a missing default
DB_HOST: "{% if cfg is defined and cfg.db is defined and 'host' in cfg.db %}{{ cfg.db.host }}{% endif %}"
# OK - the value has a layered default, referenced plainly
DB_HOST: "{{ DB_HOST }}"
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

### TPL-7 - Build URLs from the Cloud Passport host (SHOULD)

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

## Exceptions

A rule cannot always be followed, because a downstream consumer requires a specific format or a legacy
consumer cannot be changed in the current window. "It was like this before" and "fix it later" are not
valid reasons.

Mark a deviation with an inline comment above the parameter. The comment names the rule ID, the
consumer that forces it, and what removes it.

```yaml
# [EXCEPTION VAL-2] trailing slash required by the legacy gateway.
# Remove when the gateway accepts the slash-free URL.
API_BASE_URL: https://gw.internal/
```
