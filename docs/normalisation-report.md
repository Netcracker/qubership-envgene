# Normalisation report — ObsSaaSCloud — 2026-08-05

## Summary

| Rule | Description | Findings | Applied |
|------|-------------|----------|---------|
| SEC-1 | No plaintext secrets | 12 secrets detected | 12 replaced with credential stubs |
| SEC-2 | No mixed plaintext/encrypted | No SOPS-encrypted files found | N/A |
| SEC-3 | No secrets in runtime params | No secret keys in `technicalConfigurationParameters` | N/A |
| SEC-4 | Credential shape matches secret | All new stubs use `type: secret` — single-field values | N/A |
| SEC-5 | Repository-wide encryption | No `.sops.yaml` found | Recommendation added (see below) |
| PLACE-1 | Highest correct layer | 3 ParameterSets identical across both environments | Promoted to cluster level |
| PLACE-2 | Override only the delta | No redundant env-level keys after PLACE-1 promotion | N/A |
| PLACE-3 | Place by system tier | Platform-indicator keys already in cloud-deploy ParameterSets | Retained in promoted cluster-level file |
| PLACE-4 | CLOUD_ keys in Cloud Passport | All CLOUD_ keys are already in `cloud-passport/ObsSaaSCloud.yml` | N/A |
| PLACE-5 | Right parameter category | All parameters are in `parameters:` (deploy) category; no misplaced e2e or technical keys detected | N/A |
| PLACE-6 | Pipeline parameters bound to Cloud | `envSpecificE2EParamsets` already keyed by `cloud` / `bss` — no namespace deploy-postfix keys | N/A |
| INT-1 | Schema-valid | All `*ParameterSets` fields are lists; all category bodies are maps | N/A |
| INT-2 | Every reference resolves | Dangling credential ID references noted (see below) | N/A — stubs written |
| INT-3 | One resolvable Cloud Passport | `cloud-passport/ObsSaaSCloud.yml` resolves for both environments | N/A |
| INT-4 | No shadowed same-name overrides | No duplicate names across scopes | N/A |
| INT-5 | No unreferenced entities | Original env-scoped cloud-deploy files superseded by cluster promotion; references updated in env_definition.yml | Applied |
| INT-6 | No dead parameters | No template repo or Helm schemas available — check skipped | Limitation recorded |
| NAME-2 | Filename equals `name` field | Promoted cluster files renamed; `name:` field updated to match | Applied to 2 files |
| NAME-5 | Resource Profile Override naming | No Resource Profile Override files found | N/A |
| NAME-7 | Shared Template Variable naming | No STV files found | N/A |
| VAL-1 | YAML type matches consumer | 15 boolean quoted-string values corrected | Applied |
| VAL-2 | Reserved-value semantics | `envgeneNullValue` used only in credential stubs (correct usage) | N/A |
| VAL-3 | URLs have no trailing slash | No trailing slashes found | N/A |
| VAL-4 | Complex values are native YAML | 2 corrections: GLOBAL_RESOURCE_PROFILE JSON→YAML; pg multiline→block scalar | Applied |
| VAL-5 | Resource quantities use unit form | No Resource Profile Override files | N/A |

---

## Changes applied

### SEC-1 — No plaintext secrets

**12 plaintext secrets detected and replaced with credential references.**

All cloud-deploy secrets are identical across both environments → placed at cluster level under
`environments/ObsSaaSCloud/Inventory/credentials/`.

BSS-deploy secrets are unique to `diagnostic-toolkit-qa` → placed at environment level under
`environments/ObsSaaSCloud/diagnostic-toolkit-qa/Inventory/credentials/`.

| Original key | File | Credential ID | Layer |
|---|---|---|---|
| `CLOUD_DEPLOY_TOKEN` | `cloud-passport/ObsSaaSCloud.yml` | `cloud-token-cred` | cluster |
| `KAFKA_SASL_PASSWORD` | `ObsSaaSCloud-cloud-deploy.yml` | `kafka-sasl-admin-cred` | cluster |
| `INFLUXDB_PASSWORD` | `ObsSaaSCloud-cloud-deploy.yml` | `influxdb-admin-cred` | cluster |
| `KAFKA_PASSWORD` | `ObsSaaSCloud-cloud-deploy.yml` | `kafka-admin-cred` | cluster |
| `CSE_GRAYLOG_PASSWORD` | `ObsSaaSCloud-cloud-deploy.yml` | `cse-admin-cred` | cluster |
| `STORAGE_PASSWORD` | `ObsSaaSCloud-cloud-deploy.yml` | `storage-admin-cred` | cluster |
| `GRAFANA_PASSWORD` | `ObsSaaSCloud-cloud-deploy.yml` | `grafana-admin-cred` | cluster |
| `BEOC_VM_QUERY_PASSWORD` | `ObsSaaSCloud-cloud-deploy.yml` | `beoc-admin-cred` | cluster |
| `ARGOCD_PASSWORD` | `dcl-mandatory-obs-rnd-01.yml` | `argocd-admin-cred` | cluster |
| `DCL_CONFIG_CMDB_PASSWORD` | `dcl-mandatory-obs-rnd-01.yml` | `dcl-admin-cred` | cluster |
| `CASSANDRA_PASSWORD` | `ObsSaaSCloud-diagnostic-toolkit-qa-bss-deploy.yml` | `cassandra-admin-cred` | environment |
| `INFRA_POSTGRES_ADMIN_PASSWORD` | `ObsSaaSCloud-diagnostic-toolkit-qa-bss-deploy.yml` | `infra-admin-cred` | environment |

> **Note:** `pg` block in `bss-deploy` contains a password inline in a YAML block scalar.
> This value (`paSSw0rd`) was not automatically replaced because the block scalar is a
> structured text blob passed to an application config; the owner should extract it into the
> `infra-admin-cred` or a dedicated credential and template the block. Flagged here for
> follow-up.

### PLACE-1 — Highest correct layer

**3 ParameterSets promoted from environment level to cluster level.**

The following ParameterSets had identical content across both `dev-jaeger` and
`diagnostic-toolkit-qa`:

| Original (env-scoped) | Promoted to (cluster-scoped) |
|---|---|
| `ObsSaaSCloud-dev-jaeger-cloud-deploy` | `ObsSaaSCloud-cloud-deploy` |
| `ObsSaaSCloud-dev-jaeger-cloud-app-deploy` | `ObsSaaSCloud-cloud-app-deploy` |
| `dcl-mandatory-obs-rnd-01` (both env copies identical) | `dcl-mandatory-obs-rnd-01` |

Both `env_definition.yml` files updated to reference the cluster-level names.

> **Template-promotion candidate:** `ObsSaaSCloud-cloud-deploy` and
> `dcl-mandatory-obs-rnd-01` contain cluster-specific URLs (e.g.
> `saas-rnd-obs-01.managed.netcracker.cloud`). They cannot be promoted to template level
> without knowing which templates consume them. Left at cluster level.

### VAL-1 — YAML type matches consumer

**15 boolean values unquoted.**

All occurrences of `'true'` and `'false'` in ParameterSet files converted to unquoted
`true` / `false`:

- `monitoring.install`, `monitoring.installDashboard`, `waitForPodsReady`,
  `PUSHGATEWAY_ENABLED`, `ESCAPE_SEQUENCE`, `MONITORING_ENABLED`, `CONSUL_ENABLED`
  in `ObsSaaSCloud-cloud-deploy.yml`
- `DCL_CONFIG_ARGOCD_PRUNE_SYNC`, `DCL_CONFIG_BUSINESS_ERRORS_CATALOG_ENABLED`,
  `DCL_DEBUG`, `DCL_SKIP_CHART_VALIDATION` in `dcl-mandatory-obs-rnd-01.yml`
- `DEPLOY_W_HELM`, `INTEGRATION_TESTS`, `MONITORING_ENABLED`, `ESCAPE_SEQUENCE`
  in `ObsSaaSCloud-diagnostic-toolkit-qa-bss-deploy.yml`
- `DCL_CONFIG_ARGOCD_PRUNE_SYNC` in `ObsSaaSCloud-diagnostic-toolkit-qa-bss-e2e.yml`

> **Note on `CREATE_DEFAULT_TENANT`:** value `'true'` in `ObsSaaSCloud-cloud-app-deploy.yml`
> also unquoted.

### VAL-4 — Complex values are native YAML

**`GLOBAL_RESOURCE_PROFILE`** in `ObsSaaSCloud-cloud-deploy.yml`:
- Original: a YAML-quoted multi-line JSON string with escaped `\n` characters.
- Converted to native YAML mapping structure.

**`pg`** in `ObsSaaSCloud-diagnostic-toolkit-qa-bss-deploy.yml`:
- Original: YAML scalar with embedded literal `\n` characters and surrounding quotes.
- Converted to a proper YAML block scalar (`|`).

### NAME-2 — Filename equals `name` field

Promoted cluster-level files were given new filenames (`ObsSaaSCloud-cloud-deploy.yml`,
`ObsSaaSCloud-cloud-app-deploy.yml`). The `name:` field in each was updated to match.

---

## Limitations

### Rules skipped due to missing data

| Rule | Reason |
|------|--------|
| INT-6 (dead parameters) | No Jinja2 template repo or Helm `values.yaml` / `values.schema.json` available in scope. Cannot determine which parameter keys are consumed by templates. All parameters retained as active. |
| PLACE-1 (template-promotion check) | Only one cluster (`ObsSaaSCloud`) in scope. Cannot determine whether cluster-level values are universal across all clusters. Conservative default: left at cluster level. |

---

## Items requiring follow-up

### SEC-1 — Inline password in `pg` block scalar (bss-deploy)

`environments/ObsSaaSCloud/diagnostic-toolkit-qa/Inventory/parameters/ObsSaaSCloud-diagnostic-toolkit-qa-bss-deploy.yml`
key: `pg`

The `pg` block scalar contains an inline `password: paSSw0rd` value. This could not be
automatically extracted without knowing the consuming application's config schema. The owner
should replace it with a credential reference once the appropriate credential object is
identified.

### SEC-5 — No SOPS configuration found

No `.sops.yaml` file exists in the repository. All credential stubs are written as plaintext
with `envgeneNullValue`. Recommend setting up SOPS encryption before populating real secret
values into the credential files.

### INT-2 — Dangling credential references (stubs written, not yet populated)

All credential stubs below were written with `envgeneNullValue`. The credential references in
ParameterSet files will not resolve until real values are supplied:

| Credential ID | File | Referenced from |
|---|---|---|
| `cloud-token-cred` | `ObsSaaSCloud/Inventory/credentials/cloud-token-cred.yml` | `cloud-passport/ObsSaaSCloud.yml` |
| `kafka-sasl-admin-cred` | `ObsSaaSCloud/Inventory/credentials/kafka-sasl-admin-cred.yml` | `ObsSaaSCloud-cloud-deploy.yml` |
| `influxdb-admin-cred` | `ObsSaaSCloud/Inventory/credentials/influxdb-admin-cred.yml` | `ObsSaaSCloud-cloud-deploy.yml` |
| `kafka-admin-cred` | `ObsSaaSCloud/Inventory/credentials/kafka-admin-cred.yml` | `ObsSaaSCloud-cloud-deploy.yml` |
| `cse-admin-cred` | `ObsSaaSCloud/Inventory/credentials/cse-admin-cred.yml` | `ObsSaaSCloud-cloud-deploy.yml` |
| `storage-admin-cred` | `ObsSaaSCloud/Inventory/credentials/storage-admin-cred.yml` | `ObsSaaSCloud-cloud-deploy.yml` |
| `grafana-admin-cred` | `ObsSaaSCloud/Inventory/credentials/grafana-admin-cred.yml` | `ObsSaaSCloud-cloud-deploy.yml` |
| `beoc-admin-cred` | `ObsSaaSCloud/Inventory/credentials/beoc-admin-cred.yml` | `ObsSaaSCloud-cloud-deploy.yml` |
| `argocd-admin-cred` | `ObsSaaSCloud/Inventory/credentials/argocd-admin-cred.yml` | `dcl-mandatory-obs-rnd-01.yml` |
| `dcl-admin-cred` | `ObsSaaSCloud/Inventory/credentials/dcl-admin-cred.yml` | `dcl-mandatory-obs-rnd-01.yml` |
| `cassandra-admin-cred` | `diagnostic-toolkit-qa/Inventory/credentials/cassandra-admin-cred.yml` | `ObsSaaSCloud-diagnostic-toolkit-qa-bss-deploy.yml` |
| `infra-admin-cred` | `diagnostic-toolkit-qa/Inventory/credentials/infra-admin-cred.yml` | `ObsSaaSCloud-diagnostic-toolkit-qa-bss-deploy.yml` |

### PLACE-1 — Template-promotion candidates

The following cluster-level ParameterSets contain only cluster-specific infrastructure values
(hostnames anchored to `saas-rnd-obs-01`). They are not candidates for template-level
promotion. No action required.

- `ObsSaaSCloud-cloud-deploy.yml`
- `dcl-mandatory-obs-rnd-01.yml`
