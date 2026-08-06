# Correctness Rules — Secrets, Integrity, and Values

Rules that decide **whether the configuration is valid**: secrets handled safely, references resolve, values have the right shape.
Source: [configuration-standard.md](../configuration-standard.md)

Cross-document dependencies: SEC-1 ← NAME-6 (Structure Rules), PLACE-5 ← SEC-3 (this doc), TPL-7 → VAL-3 (this doc), TPL-10 → SEC-1 (this doc).

---

## Secrets

### SEC-1 - No plaintext secrets (MUST)

A secret never appears as a literal parameter value in any object that defines parameters, such as a ParameterSet, a Cloud, or Namespace. Create a Credential object named `<product>-<purpose>-cred` and reference it with `${creds.get("<id>").<field>}`.

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

A repository never keeps a live secret in plaintext alongside encrypted ones. Once any credential material is encrypted, no real secret remains in plaintext, because a single plaintext secret defeats the encryption of the rest.

```yaml
# Not OK - one repository, mixed:
#   configuration/credentials.yml         SOPS-encrypted
#   Inventory/credentials/db-cred.yml     a real plaintext password
# OK - no live secret is left in plaintext alongside encrypted ones
```

### SEC-3 - No secrets in runtime parameters (MUST)

A secret is never placed in a runtime parameter (`technicalConfigurationParameters`). Runtime parameters are applied live through Consul, which holds them in plaintext, so a secret there is exposed even though the Effective Set encrypts it at rest. Keep the secret in a deployment parameter (`deployParameters`), referenced through a Credential, where it reaches the application as a secret rather than Consul.

See also: PLACE-5 (Structure Rules) — parameter category assignment.

```yaml
# Not OK - a secret referenced in a runtime parameter, exposed in Consul
technicalConfigurationParameters:
  DB_PASSWORD: ${creds.get("db-cred").password}
# OK - the secret stays in a deployment parameter
deployParameters:
  DB_PASSWORD: ${creds.get("db-cred").password}
```

### SEC-4 - Credential shape matches the secret (SHOULD)

Declare a credential with the shape the secret actually has. A username and password pair is declared as a pair, a single token or value as a single value. Do not pad a single value into a pair or collapse a pair into a single field. This holds whether the secret is held locally or resolved from an external store.

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

A repository may encrypt every credential file that holds secret material with SOPS, applying one backend across the whole repository. This is optional: a repository whose secrets are resolved from an external store, or that holds no local secret material, needs no repository-wide encryption.

```yaml
# OK - every credential file with secret material in the repository is encrypted with SOPS
# OK - no repository-wide encryption, because secrets are resolved from an external store
```

---

## Integrity

### INT-1 - Schema-valid (MUST)

Every EnvGene object validates against its schema (see [EnvGene objects](/docs/envgene-objects.md)).

```yaml
# OK     - the object matches its schema: a *ParameterSets field is a list, a category body is a map
# Not OK - a *ParameterSets field given a map, or a required key missing -> generation fails
```

### INT-2 - Every reference resolves (MUST)

A `${creds.get("<id>")}`, a `$type: credRef`, and a ParameterSet or Resource Profile reference each resolve to exactly one existing object. A dangling or ambiguous reference fails generation.

```yaml
# Not OK - references a credential id no Credential defines -> generation fails
DB_PASSWORD: ${creds.get("bss-db-cred").password}
# OK - bss-db-cred exists in a credentials file on the resolution path
DB_PASSWORD: ${creds.get("bss-db-cred").password}
```

### INT-3 - One resolvable Cloud Passport (MUST)

An environment that uses a Cloud Passport resolves to exactly one passport file. When `env_definition.yml` sets `inventory.cloudPassport: <name>`, exactly one `<name>.{yml,yaml}` exists in the search path from the environment directory up to the repository root. With no `cloudPassport` field, auto-association takes `cloud-passport/<cluster>.{yml,yaml}` then `cloud-passport/passport.{yml,yaml}`. Zero matches or duplicate matches fail generation. Unlike a ParameterSet or Resource Profile, which resolves by first-match across scopes (see INT-4, INT-2), the Cloud Passport is pointed at by name and never merged, so a duplicate in the path is an error rather than an override.

```yaml
# OK - the reference resolves to exactly one file
# env_definition.yml: inventory.cloudPassport: cluster-01
# environments/cluster-01/cloud-passport/cluster-01.yml   (the one match)

# Not OK - no file named cluster-01 in the path      -> not-found, generation fails
# Not OK - two files named cluster-01 in the path    -> duplicate, generation fails
```

### INT-4 - No shadowed same-name overrides (SHOULD)

An env-specific ParameterSet, Credential, Shared Template Variable, or Resource Profile resolves by reference name across environment, cluster, and repository, first-match-wins. The highest-scope match is used, and same-named files at lower scopes are ignored, not merged. Do not keep the same reference name at two scopes expecting a merge. Give each a distinct name, or keep the override at one scope.

```yaml
# Not OK - same name at two scopes: the env file wins, the cluster file is silently ignored
# environments/cluster-01/env-1/Inventory/parameters/env-specific-bss.yml   (used)
# environments/cluster-01/parameters/env-specific-bss.yml                   (shadowed, edits do nothing)
# OK - distinct names, or a single scope
# environments/cluster-01/parameters/cluster-bss.yml
# environments/cluster-01/env-1/Inventory/parameters/env-1-bss.yml
```

### INT-5 - No unreferenced entities (SHOULD)

Remove an authored entity that no reference names: a ParameterSet in no `*ParameterSets` or `envSpecific*` list, a Shared Template Variable in no `sharedTemplateVariables` array, a credential no `creds.get` or `credRef` reads, a Resource Profile Override no `profile` or `override_name` selects. EnvGene ignores an unreferenced entity, so it ships nothing and only misleads a reader. This is the complement of INT-2. Count every reference site first: a system credential read by `deployer.yml`, `registry.yml`, or the Cloud Passport, and a template entity an instance selects, are referenced outside the current file or repository, not dead.

```yaml
# Not OK - a ParameterSet file named by no reference list
# parameters/legacy-oss-deploy.yml   (in no *ParameterSets or envSpecific* list)
# OK - remove it, or add the reference where it is genuinely needed
```

### INT-6 - No dead parameters (SHOULD)

Delete a parameter no consumer reads. A key is dead by who reads it, not by its value, so a dead key with a real value is removed too, and an empty value a consumer reads stays.

```yaml
# Not OK - parameters for a decommissioned integration, read by no consumer
LEGACY_SERVICE_HOST: legacy.internal
LEGACY_SERVICE_PORT: 8080
# OK - the dead keys are removed
```

---

## Values

### VAL-1 - A value's YAML type matches its consumer (MUST)

A parameter's type is fixed by the consumer that reads it, and YAML sets a value's type from its syntax, so write the value so its parsed type is the one the consumer expects. Leave it bare when the consumer reads a boolean, a number, or a list. Quote it when the consumer reads a string, including a string YAML would otherwise coerce (a country code, a version, a leading-zero number). When the consumer expects a type a general style would not, the consumer wins. In the deployment context the type contract is the application Helm chart's `values.schema.json`.

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

`envgeneNullValue` means "a value must be supplied here", not "empty" and not "delete". Use it for a mandatory parameter whose value is not known at the current layer, for example a template that defers the concrete value to the instance, so a lower layer fills it. Do not stand in an empty string for a mandatory value, and do not repurpose reserved control markers or invent placeholders.

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

Author a structured value (a map or a list) as native YAML, never as a JSON string packed into one value. Native YAML validates against the schema, reads in a diff, and merges per key across layers. A packed string does none of these.

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

In a Resource Profile Override, write a memory or CPU value in its Kubernetes unit form — `512Mi`, `1Gi`, `500m` — not as raw bytes. Kubernetes accepts both forms, so this is for readability and comparable diffs, in the one place the consumer is fixed (the Kubernetes resource field).

```yaml
# OK
GATEWAY_MEMORY_LIMIT: 512Mi
GATEWAY_CPU_REQUEST: 500m
# Not OK - raw bytes, valid but unreadable
GATEWAY_MEMORY_LIMIT: 536870912
```
