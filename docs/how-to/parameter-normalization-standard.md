# EnvGene Parameter Normalization Standard

## Table of Contents

1. [What Is Normalization and Why Do It?](#what-is-normalization-and-why-do-it)
2. [Step 1 — Understand the Layers](#step-1--understand-the-layers)
   - [Parameter Layers (Override Chain)](#step-1--understand-the-layers)
   - [Credentials, Shared Template Variables, and Resource Profiles](#step-1--understand-the-layers)
   - [Cloud Passport — A Separate Entity](#cloud-passport--a-separate-entity)
3. [Step 2 — Classify Every Parameter](#step-2--classify-every-parameter)
4. [Step 3 — Apply the Normalization Rules](#step-3--apply-the-normalization-rules)
   - [Rule 1 — SCREAMING_SNAKE_CASE keys](#rule-1--all-parameter-keys-must-be-screaming_snake_case)
   - [Rule 2 — One name per concept, no aliases](#rule-2--one-name-per-concept-no-aliases)
   - [Rule 3 — Secrets never go in parameter files](#rule-3--secrets-never-go-in-parameter-files)
   - [Rule 4 — Connectivity parameters belong in the Cloud Passport](#rule-4--connectivity-parameters-belong-in-the-cloud-passport)
   - [Rule 5 — Promote parameters to the highest correct layer](#rule-5--promote-parameters-to-the-highest-correct-layer)
   - [Rule 6 — Name ParameterSet files consistently](#rule-6--name-parameterset-files-consistently)
   - [Rule 7 — URLs: DNS names only, no trailing slash](#rule-7--urls-dns-names-only-no-trailing-slash)
   - [Rule 8 — Feature flags are native YAML booleans](#rule-8--feature-flags-are-native-yaml-booleans)
   - [Rule 9 — Debug and bypass flags default to false](#rule-9--debug-and-bypass-flags-default-to-false)
   - [Rule 10 — Remove empty and unused parameters](#rule-10--remove-empty-and-unused-parameters)
   - [Rule 11 — Use scoped names when two subsystems share a concept](#rule-11--use-scoped-names-when-two-subsystems-share-a-concept)
   - [Rule 12 — Never hardcode environment names inside parameter values](#rule-12--never-hardcode-environment-names-inside-parameter-values)
   - [Rule 13 — Multi-line values must use YAML multi-line format](#rule-13--multi-line-values-must-use-yaml-multi-line-format)
5. [Normalization Audit Checklist](#normalization-audit-checklist)
6. [Exceptions](#exceptions)

---

## What Is Normalization and Why Do It?

The migration tool does a straight copy from CMDB — it puts every parameter into your environment's `Inventory/parameters/` folder exactly as-is. That gives you a working environment but not a clean one.

Normalization is the step where you:
- Place every parameter at the right layer (so one change doesn't need to be made in ten files)
- Move secrets out of plain YAML files into Credential objects
- Establish consistent naming so every team follows the same convention
- Remove noise — empty values, duplicates, and parameters that belong somewhere else

---

## Step 1 — Understand the Layers

Parameters live in four layers. Higher layers override lower ones. Place each parameter at the **highest layer where it is correct**.

```
┌──────────────────────────────────────────────────────────┐
│  TEMPLATE REPO                          lowest priority  │
│  templates/parameters/<name>.yml                        │
│  Constants true for ALL environments of this type       │
│  e.g. platform type, ingress class, default flags       │
├──────────────────────────┬───────────────────────────────┤
│  SITE LEVEL              │ overrides template            │
│  environments/parameters/                               │
│  Defaults shared across all clusters in the org         │
├──────────────────────────┼───────────────────────────────┤
│  CLUSTER LEVEL           │ overrides site               │
│  environments/<cluster>/parameters/                     │
│  Same for every env on one cluster:                     │
│  cluster service URLs, registry, monitoring endpoints   │
├──────────────────────────┼───────────────────────────────┤
│  ENVIRONMENT LEVEL       │ overrides cluster  (highest) │
│  environments/<cluster>/<env>/Inventory/parameters/     │
│  Only what truly differs per environment:               │
│  env label, replica counts, env-specific overrides      │
└──────────────────────────────────────────────────────────┘
```

Credentials, Shared Template Variables, and Resource Profiles follow the same layered structure in their own folders:

| Type | Site (Global) | Cluster | Env |
|---|---|---|---|
| Credentials | `environments/credentials/` | `environments/<cluster>/credentials/` | `environments/<cluster>/<env>/Inventory/credentials/` |
| Shared Template Variables | `environments/shared-template-variables/` | `environments/<cluster>/shared-template-variables/` | `environments/<cluster>/<env>/shared-template-variables/` |
| Resource Profiles | `environments/resource_profiles/` | `environments/<cluster>/resource_profiles/` | `environments/<cluster>/<env>/Inventory/resource_profiles/` |

**Resource Profiles** group performance-related parameters (CPU limits, memory requests, replica counts) separately from all other deployment parameters. This keeps sizing concerns out of your general ParameterSet files and lets you tune resources independently per scope.

EnvGene resolves Resource Profiles at three levels — baseline (ships inside the application SBOM), template override (in the Template Repository at `templates/resource_profiles/`), and environment-specific override (in the Instance Repository paths above). Each level overrides the previous. Apply the same "promote to highest correct layer" logic as regular parameters: if a resource sizing is identical across all environments on a cluster, place the override at the cluster level rather than duplicating it per environment.

Reference your Resource Profile overrides in `env_definition.yml` via `envTemplate.envSpecificResourceProfiles`.

---

### Cloud Passport — A Separate Entity

The Cloud Passport is **not part of the parameter layer hierarchy**. It has no override chain and no precedence order — it is a standalone object with its own JSON schema that describes how EnvGene connects to a specific cluster.

```
┌──────────────────────────────────────────────────────────┐
│  CLOUD PASSPORT                                          │
│  Location: environments/<cluster>/cloud-passport/        │
│  Schema:   validated against cloud.schema.json           │
│                                                          │
│  Sections: cloud · dbaas · maas · vault · consul         │
│  + any free-form sections (all keys flow into            │
│    deployParameters)                                     │
└──────────────────────────────────────────────────────────┘
```

One Cloud Passport file per cluster. It covers:
- Kubernetes API host, port, and protocol
- Cluster public hostname and dashboard URL
- Deploy token reference
- `PRODUCTION_MODE`
- Internal service integration configs (MaaS, DBaaS, Consul, Vault)

**Cloud Passport Credentials** (`<name>-creds.yml`) sit alongside the main passport file in the same `cloud-passport/` folder. Sensitive values — deploy tokens, cluster passwords, private keys — must go in the credentials file, never in the main passport YAML. EnvGene merges both files at build time.

| File | Path | Contains |
|---|---|---|
| Main passport | `environments/<cluster>/cloud-passport/<name>.yml` | Non-sensitive connectivity config |
| Credentials | `environments/<cluster>/cloud-passport/<name>-creds.yml` | Secrets: tokens, passwords, keys |

> **Rule of thumb:** If a value would appear in the parameter layers, it does not belong in the Cloud Passport. If it describes how to reach or authenticate to the cluster itself, it belongs in the Cloud Passport.

---

## Step 2 — Classify Every Parameter

For each parameter in your migrated files, follow this flowchart. Note that Cloud Passport is a separate entity — not a layer — so connectivity parameters route to it as a distinct destination rather than fitting into the override chain:

```
┌─────────────────────────────────────────────────────────────┐
│  START: You have a parameter. Where does it belong?         │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
         Is it a cluster connectivity value?
         (API URL, port, protocol, hostname,
          deploy token, MaaS/DBaaS/Consul/Vault config)
                │               │
               YES              NO
                │               │
                ▼               ▼
         Is it a secret?    Is it a secret?
         (token, password,  (password, token, API key,
          private key)       certificate, private key)
                │    │               │               │
               YES   NO             YES              NO
                │    │               │               │
                ▼    ▼               ▼               ▼
         Cloud    Cloud        Credentials      Is it used in Jinja
         Passport Passport        file          template rendering?
         Creds    (main)                        (controls template
         file        │                           logic, not deployment)
                     │                               │               │
                     ▼                              YES              NO
         Does env-specific-schema.yml                │               │
         define validation rules for                 ▼               ▼
         this Cloud Passport?                Shared Template    Is the value the same
                │               │           Variable file      for ALL environments
               YES              NO                             of this topology type?
                │               │                                   │               │
                ▼               ▼                                  YES              NO
           Validate          Accepted                               │               │
           (whiteList /      as-is                                  ▼               ▼
           mandatoryList)                                    Template repo     Is the value the same
                │                                           ParameterSet      for ALL environments
                ▼                                                             on this one cluster?
           Passes?                                                                 │               │
                │       │                                                         YES              NO
               YES      NO                                                         │               │
                │       │                                                          ▼               ▼
                ▼       ▼                                                   Cluster-level    Environment-level
           Accepted   Fix value                                             ParameterSet     ParameterSet
                      before
                      continuing
```

---

## Step 3 — Apply the Normalization Rules

---

### Rule 1 — All parameter keys must be SCREAMING_SNAKE_CASE

All uppercase, words separated by underscores. No dots, no hyphens, no camelCase.

```yaml
# Correct
KAFKA_BOOTSTRAP_SERVERS: kafka.internal:9092
MONITORING_ENABLED: true

# Incorrect
kafkaBootstrapServers: kafka.internal:9092   ← camelCase
kafka.bootstrap.servers: kafka.internal:9092 ← dot-notation
kafka-bootstrap-servers: kafka.internal:9092 ← hyphens
```

> **Exception:** A Helm chart may require a specific key format (e.g. dot-notation). In that case keep the chart's format and add a comment explaining why — see the [Exceptions](#exceptions) section.

---

### Rule 2 — One name per concept, no aliases

If two keys hold the same value, they are aliases. Choose one canonical name and remove the others.

```yaml
# Before — three names for the same Kafka broker
KAFKA_URL: kafka.internal:9092
BOOTSTRAP_SERVERS: kafka.internal:9092
STREAMING_BROKER_ADDRESS: kafka.internal:9092

# After — one canonical name
KAFKA_BOOTSTRAP_SERVERS: kafka.internal:9092
```

Before removing an alias, search all consumers (Helm charts, app configs, pipeline scripts) for the old name and update them first.

---

### Rule 3 — Secrets never go in parameter files

Passwords, tokens, API keys, and private keys must not appear as plaintext values in any ParameterSet YAML.

**What to do:**

1. Create a Credential object in `Inventory/credentials/`:

```yaml
# Inventory/credentials/my-product-creds.yml

my-db-cred:
  type: usernamePassword
  data:
    username: "envgeneNullValue"   ← placeholder, never the real value
    password: "envgeneNullValue"

my-api-token-cred:
  type: secret
  data:
    secret: "envgeneNullValue"
```

2. Reference it in the ParameterSet instead of the plaintext value:

```yaml
# Before (wrong)
DB_USER: admin
DB_PASSWORD: s3cr3t

# After (correct)
DB_USER: ${creds.get("my-db-cred").username}
DB_PASSWORD: ${creds.get("my-db-cred").password}
```

Use `usernamePassword` type when you have a username and password pair.  
Use `secret` type when you have a single token.

**Credential ID naming:** `<product>-<purpose>-cred`  
Examples: `payment-service-admin-cred`, `registry-pull-cred`, `pipeline-deploy-cred`

---

### Rule 4 — Connectivity parameters belong in the Cloud Passport

These always go in the Cloud Passport — remove them from ParameterSets if the migration tool copied them there:

- Kubernetes API host, port, and protocol
- Cluster public and private hostname
- Dashboard URL
- Deploy token / credentials reference
- `PRODUCTION_MODE`
- Internal service integration configs (MaaS, DBaaS, Consul, Vault internal URLs and enabled flags)

The `CLOUD_` prefix is reserved for Cloud Passport keys only. Never use `CLOUD_` in a ParameterSet.

---

### Rule 5 — Promote parameters to the highest correct layer

After migration, most parameters land at the environment level. Ask for each one:

> "If I created a second environment on this cluster, would this value be the same?"

If yes → move it to the **cluster level**.

> "If another product team used this same template, would this value be the same for them too?"

If yes → move it to the **template repo**.

**Practical tip:** Open two environment-level parameter files side by side. Any key with the same value in both is a candidate to move up.

---

### Rule 6 — Name ParameterSet files consistently

Format: `<scope-identifier>-<product>-<type>.yml`

```
cluster-01-cloud-deploy.yml     ← cluster-scoped
cluster-01-cloud-e2e.yml
env-dev-bss-deploy.yml          ← env-scoped
env-dev-bss-app-deploy.yml
```

The `name:` field inside the file **must exactly match the filename without `.yml`**.  
A mismatch causes a fatal build error.

Template repo ParameterSets can use short descriptive names without a scope prefix:
```
platform-constants.yml
deployment-defaults.yml
```

---

### Rule 7 — URLs: DNS names only, no trailing slash

- Use a DNS hostname — never a raw IP address.
- Remove trailing slashes — consumers append paths and a trailing slash produces double-slashes.

```yaml
# Correct
MY_SERVICE_URL: https://my-service.cluster-01.example.com

# Wrong — raw IP (fragile, not human-readable)
MY_SERVICE_URL: https://10.42.0.15

# Wrong — trailing slash
MY_SERVICE_URL: https://my-service.cluster-01.example.com/
```

---

### Rule 8 — Feature flags are native YAML booleans

Use `true` / `false`, never `"true"` / `"false"`. YAML parsers treat the string `"false"` as truthy.

```yaml
# Correct
MONITORING_ENABLED: true

# Wrong
MONITORING_ENABLED: "true"
```

Name your flags consistently:

| Suffix | Meaning |
|---|---|
| `_ENABLED` | Component is installed; this flag turns it on or off at runtime |
| `_INSTALL` | Controls whether the component is installed at all |

Do not use them interchangeably — `CACHE_ENABLED: false` and `CACHE_INSTALL: false` mean different things.

---

### Rule 9 — Debug and bypass flags default to false

Flags for developer convenience (verbose logging, skipping validation, bypassing security) must default to `false` at the cluster level. Override to `true` only in the specific environment that needs it.

```yaml
# Cluster-level ParameterSet — safe default for everyone
DEBUG_MODE: false
SKIP_VALIDATION: false
```

```yaml
# Dev environment-level ParameterSet — explicit override
DEBUG_MODE: true
```

This way, if you create a new environment and forget to set the flag, it defaults to safe.

---

### Rule 10 — Remove empty and unused parameters

If a parameter has an empty string value and no consumer is using it, delete it.

```yaml
# Delete these if the integration is not active
LEGACY_SERVICE_HOST: ""
LEGACY_SERVICE_USER: ""
```

If the value is intentionally not yet configured but must exist, use `envgeneNullValue` instead of `""`.

---

### Rule 11 — Use scoped names when two subsystems share a concept

If two products or subsystems each need, say, a "storage URL" but use different backends with different values, give each one a prefixed name.

```yaml
# Wrong — same generic name, two different backends, will conflict
STORAGE_URL: https://storage-a.example.com    # subsystem A
STORAGE_URL: https://storage-b.example.com    # subsystem B

# Correct — scoped names, no ambiguity
SUBSYSTEM_A_STORAGE_URL: https://storage-a.example.com
SUBSYSTEM_B_STORAGE_URL: https://storage-b.example.com
```

---

### Rule 12 — Never hardcode environment names inside parameter values

A parameter value like `my-env-01-core` (where `my-env-01` is the environment name) will break when you reuse the ParameterSet or promote it to a higher layer.

```yaml
# Wrong — value contains the environment name
MY_NAMESPACE: my-env-01-core

# Correct — derived at render time in the template file
MY_NAMESPACE: "{{ current_env.name }}-core"
```

Jinja expressions work inside `.j2` template files, not inside ParameterSet YAML files. The expression must be placed in the namespace or cloud template, not the ParameterSet.

Fixed infrastructure namespaces that don't embed an environment name (e.g., `platform-monitoring`) are fine to hardcode.

---

### Rule 13 — Multi-line values must use YAML multi-line format

Any parameter whose value spans multiple lines must be written using a YAML block scalar, not a single-line string with escaped newlines. This applies to certificates, scripts, JSON blobs, SQL snippets, and any other multi-line content.

Use the literal block scalar (`|`) to preserve newlines exactly, or the folded block scalar (`>`) when line breaks in the source are for readability only and the consumer expects one continuous string.

```yaml
# Wrong — escaped newlines, unreadable and error-prone
TLS_CERT: "-----BEGIN CERTIFICATE-----\nMIIBIjANBgkq...\n-----END CERTIFICATE-----"

# Correct — literal block scalar, preserves every newline
TLS_CERT: |
  -----BEGIN CERTIFICATE-----
  MIIBIjANBgkq...
  -----END CERTIFICATE-----

# Wrong — long SQL crammed onto one line
INIT_QUERY: "CREATE TABLE foo (id INT, name VARCHAR(255)); INSERT INTO foo VALUES (1, 'bar');"

# Correct — folded block scalar, readable, consumer gets a single string
INIT_QUERY: >
  CREATE TABLE foo (id INT, name VARCHAR(255));
  INSERT INTO foo VALUES (1, 'bar');
```

Choose between `|` and `>`:

| Scalar | Newlines in output | Use when |
|---|---|---|
| `|` (literal) | Preserved exactly | Certificates, private keys, shell scripts, structured text |
| `>` (folded) | Replaced by spaces | Long prose strings, SQL, config lines where newlines are cosmetic |

---

## Normalization Audit Checklist

Run through this list after migration for every environment:

- [ ] **Secrets** — no plaintext passwords, tokens, or keys in any ParameterSet YAML (Rule 3)
- [ ] **Cloud Passport credentials** — sensitive connectivity secrets (deploy tokens, cluster passwords) are in the `-creds.yml` file, not the main Cloud Passport YAML
- [ ] **Cloud Passport schema** — if `env-specific-schema.yml` defines `cloudPassport` rules, the passport passes `whiteList` / `mandatoryList` validation
- [ ] **Connectivity** — no Cloud Passport values duplicated in ParameterSets (Rule 4)
- [ ] **Aliases** — no two keys holding the same value (Rule 2)
- [ ] **Layer** — every parameter is at the highest layer where it is correct (Rule 5)
- [ ] **Naming** — all keys are `SCREAMING_SNAKE_CASE` (Rule 1)
- [ ] **File names** — all ParameterSet filenames follow the format, `name:` field matches (Rule 6)
- [ ] **URLs** — all URL values use DNS names and have no trailing slash (Rule 7)
- [ ] **Flags** — boolean values use native YAML `true`/`false` (Rule 8)
- [ ] **Debug flags** — debug/bypass flags default to `false` at cluster level (Rule 9)
- [ ] **Empty params** — no empty-string values for inactive integrations (Rule 10)
- [ ] **Subsystem conflicts** — shared concept names are scoped per product (Rule 11)
- [ ] **Hardcoded env names** — no environment names embedded in parameter values (Rule 12)
- [ ] **Multi-line values** — all multi-line parameter values use YAML block scalar format (`|` or `>`) (Rule 13)
- [ ] **Pipeline passes** — `ENV_BUILD: true` and `GENERATE_EFFECTIVE_SET: true` run cleanly

---

## Exceptions

Sometimes a rule cannot be followed because a downstream consumer requires a specific format.

**Valid reasons for an exception:**
- A Helm chart's `values.yaml` maps a dot-notation path directly to an internal config key
- A legacy consumer cannot be updated in the current migration window
- CMDB round-trip requires an exact field name

**Not valid reasons:**
- "It was like this in CMDB" — migration is the right time to fix it
- "We will fix it later" — document a tracked item, or it will never happen

**How to mark an exception** — add an inline comment above the parameter:

```yaml
# [EXCEPTION Rule 1] dot-notation required by <chart-name> v<version>
# Chart maps this path to its internal config. Fix when chart is updated.
app.config.brokerUrl: kafka.internal:9092
```

Every exception comment must state: which rule, which consumer requires it, and what needs to change to remove it.
