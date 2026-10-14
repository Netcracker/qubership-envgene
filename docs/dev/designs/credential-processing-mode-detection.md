# Credential processing: mode detection and external credentials

- [Problem](#problem)
- [Example](#example)
- [Design](#design)
- [Module changes](#module-changes)
- [Rules](#rules)
- [Performance](#performance)
- [What changes for the user](#what-changes-for-the-user)
- [Verification](#verification)
- [Out of scope](#out-of-scope)
- [Open questions](#open-questions)
- [Constraints](#constraints)

Design for [issue 1847](https://github.com/Netcracker/qubership-envgene/issues/1847). Behavior is defined in
[Credential processing](/docs/features/credential-processing.md) and
[ADR-0009](/docs/adr/0009-share-one-environment-template-across-local-and-external-instance-repositories.md).

## Problem

EnvGene picks external mode from `external_credential_template` in the Template Descriptor. One shared template
cannot serve a local and an external Instance repository. Migrating one repository forks or migrates the whole
template chain.

Build also lacks four things the ADR needs:

- No auto-generation. A `credId` that no source provides fails the build.
- No `${creds.get(...)}` to `credRef` rewrite.
- No Jinja rendering of the Shared Credentials File.
- Rotation does not stop in external mode as a whole. It rejects Credentials one by one.

## Example

Instance repository has `configuration/secret-stores.yml`. The template declares `db` only.

```yaml
# Template: Credential Template
db:
  type: external
  remoteRefPath: "{{ current_env.cloud }}/shared/db"
  properties:
    - name: username
    - name: password
```

```yaml
# Namespace deployParameters, as the template writes them
DB_PASSWORD: ${creds.get('db').password}
API_TOKEN: ${creds.get('api').secret}
REPORT_USER: ${creds.get('report').username}
```

After env build:

```yaml
# Namespace deployParameters
DB_PASSWORD:
  $type: credRef
  credId: db
  property: password
API_TOKEN:
  $type: credRef
  credId: api
REPORT_USER:
  $type: credRef
  credId: report
  property: username
```

```yaml
# Credentials/credentials.yml, regenerated on every run
db:
  type: external
  remoteRefPath: cloud-01/shared/db
  properties:
    - name: username
    - name: password
api:
  type: external
  secretStore: default_store
  remoteRefPath: cloud-01/env-01
report:
  type: external
  secretStore: default_store
  remoteRefPath: cloud-01/env-01
  properties:
    - name: username
    - name: password
```

`api` and `report` are auto-generated. The first macro of a `credId` sets the shape, as in local mode. `.secret`
gives a single-value Credential. `.username` or `.password` gives a Credential with `properties`. The rewrite
reads only the macro. Without `secret-stores.yml` the macros stay, the template is skipped, and the file keeps its
user values.

## Design

Env build decides the mode once and builds the Credentials in memory. It writes the file once.

1. `EnvBuildStep` detects the mode from `/configuration/secret-stores.yml` and opens the store with it.
2. `EnvGenerator` validates `secret-stores.yml` in external mode. It renders the Credential Template in external
   mode and keeps the result. It writes no file.
3. `process_cloud_passport` updates `cloud.yml` as before and returns the Cloud Passport Credentials. It writes
   no file.
4. `create_credentials` makes one walk over the objects in the store. The walk collects each referenced `credId`
   with the shape of its first reference. In external mode it also rewrites each macro in place. The rewrite
   needs only the macro.
5. `create_credentials` loads the Shared Credentials Files and renders their Jinja. It merges them with the
   template and the Cloud Passport Credentials by precedence.
6. It adds the auto-generated entries for the `credId` values no source provides, shaped by the first reference.
7. It validates once and puts the result in the store. `flush()` writes it.

Merge by mode:

| Step                | Local mode                           | External mode                                  |
|---------------------|--------------------------------------|------------------------------------------------|
| Base                | Credentials File of the previous run | Empty                                          |
| Credential Template | Skipped, INFO log with the path      | Applied                                        |
| Cloud Passport      | Applied                              | Applied                                        |
| Shared Credentials  | Applied                              | Applied                                        |
| Gap filler          | Local entry with `envgeneNullValue`  | External entry for each `credId` no source has |
| Macros              | Unchanged                            | Rewritten to `credRef`                         |

Precedence, lowest to highest: Credential Template, Cloud Passport, Shared Credentials File. An entry replaces
the whole entry of the same `credId`. The gap filler never replaces an entry of a source.

## Module changes

| Module                                         | Change                                                                                         |
|------------------------------------------------|------------------------------------------------------------------------------------------------|
| `envgenehelper/external_credential_helper.py`  | `detect_credential_mode(base_dir)` stays here. It is the only reader of `secret-stores.yml`    |
| `envgenehelper/current_env_instance_store.py`  | Store holds `credential_mode`, given when it opens. Default is local                           |
| `envgenehelper/creds_helper.py`                | Macro guard, one compiled macro pattern, `validate_cred_types` takes the mode                  |
| `scripts/pipeline/orchestrator.py`             | `EnvBuildStep` detects the mode and opens the store with it                                    |
| `scripts/build_env/render_config_env.py`       | `generate_external_cred` reads the mode from the store. Returns the template                   |
| `scripts/build_env/main.py`                    | Passes the template and Cloud Passport Credentials to `create_credentials`                     |
| `scripts/build_env/build_env.py`               | Drops the flag. Returns the Cloud Passport Credentials                                         |
| `scripts/cloud_passport/cloud_passport.py`     | Drops the flag. Returns Credentials instead of writing them                                    |
| `scripts/build_env/create_credentials.py`      | `CredentialCollector`, macro rewrite, shared file lookup and rendering                         |
| `scripts/creds_rotation/*`                     | Gate at the top of `run_cred_rotation`, error message and code, per-Credential checks removed  |
| `scripts/CLAUDE.md`, `docs/envgene-objects.md` | Replace the description of mode detection                                                      |
| `docs/features/credential-processing.md`       | The auto-generated external entry carries `properties` when the first reference is multi-field |

New objects:

- `CredentialCollector` is a dataclass. It holds the referenced `credId` values with the type and provenance
  comment of the first reference. It replaces the `credsList`, `external_cred_ids`, and `comment` arguments that
  the functions pass along today.

## Rules

- **One reader of the signal.** `detect_credential_mode()` reads `secret-stores.yml`. Only `EnvBuildStep` and
  rotation call it.
- **The store never reads the disk.** The step gives the mode to the store, as the build gives it objects.
- **Mode is an enum, not a flag.** `is_external_cred_env` and its parameters are removed. `create_credentials`
  and `process_cloud_passport` read `current_env_instance_store().credential_mode` once. Helpers that branch on
  it take the mode as an argument.
- **Rotation reads the mode itself.** It runs outside the store.
- **Rotation fails first.** The gate runs before the payload is decoded and before any Credentials file is
  scanned. It raises `ValidationError` with the external-mode message and the invalid-state code. The
  per-Credential `external` checks are removed, because the gate makes them unreachable. The gate and these
  removals are done on this branch.
- **`secret-stores.yml` is validated when the mode is external.** Not only when a template exists.
- **Provenance comments stay in memory.** `flush()` already removes comments from Credentials files, in both
  modes.
- **Parameter blocks.** `deployParameters`, `e2eParameters`, and Tenant `globalE2EParameters` are rewritten.
  A macro in `technicalConfigurationParameters` fails in external mode, as before.
- **Restrictions fail the build in external mode.** The walk checks them: a macro that reads a `vaultAppRole`
  field, a value with more than one reference or with text around one reference, and a `#creds`, `#credscl`, or
  `#credsns` key. Each error names the parameter key and the `credId`.
- **`vaultAppRole` Credentials fail in external mode.** `validate_cred_types` rejects the declared ones.
- **The rewrite uses only the macro.** `.username` and `.password` give `property` with that name. `.secret`
  gives no `property`. No source is needed.
- **The first reference sets the auto-generated shape.** `.secret` or a single-value built-in reference gives no
  `properties`. `.username`, `.password`, or a built-in reference to a `usernamePassword` field gives
  `properties` for `username` and `password`. A `credRef` with `property` does the same. Later references to the
  same `credId` do not change it, as in local mode.
- **The auto-generated entry has no `create` key.** The schema default is `false`.
- **Shared Credentials Files are rendered with Jinja for any extension.** The file is parsed first, then
  `render_context.render_from_obj_to_obj` renders it, as for the Credential Template. A Jinja value must be
  quoted. Text without `{{`, `{%`, or `{#` skips Jinja. Discovery also finds `.yml.j2` and `.yaml.j2`.
- **A missing `credId` is no error.** `validate_external_creds` keeps only the warning for unused external
  Credentials.

## Performance

- Mode is detected once per run. One `stat`.
- Local mode does not open or render the Credential Template.
- The Credentials are merged in memory. One put, one schema check, one beautify. Today there are three schema
  checks.
- The walk is single. It collects and rewrites in the same visit. The rewrite needs no merged source, so no
  second pass and no list of positions.
- The merge of local Credentials uses a dict. The list scan with `any()` is gone.
- A cheap `in` check runs before the macro regexes. One compiled pattern replaces about ten searches per string.
- Shared files render through `render_context.render_from_obj_to_obj`, only when the text has a Jinja marker.
- The shared file lookup finds all names in one pass. It walks each existing directory at most once, in the old
  search order, and stops when every name is found. It also finds `.yml.j2` and `.yaml.j2`.
- Per-file `countAdded` logs become DEBUG.

Success: local mode is not slower than before. External mode costs about the same as local mode on the same
environment.

## What changes for the user

- A repository gets external mode by adding `configuration/secret-stores.yml`. Declaring the template no longer
  does it.
- On the first generation in external mode the Credentials File loses its local entries. Git history is the only
  way back.
- An undeclared `credId` no longer fails the build in external mode. It gets a default external entry.
- In local mode a declared Credential Template is ignored. The log shows its path.
- A Shared Credentials File renders its Jinja. A literal `{{` in a value needs `{% raw %}`.
- External mode fails on `vaultAppRole`, embedded or multiple references, and deprecated key macros.
- Rotation in external mode fails at once and points to the Secret Store.

## Verification

Tests run the real build. They mock nothing of EnvGene.

- One test per acceptance criterion of the issue, in `scripts/tests/env-build/`, next to
  `test_create_credentials_store.py`.
- The precedence test covers each pair: Credential Template and Cloud Passport, Cloud Passport and Shared file,
  Credential Template and Shared file.
- Local mode keeps `kept` and external mode drops `obsolete` on a second run.
- The macro table in `test_creds_helper.py` runs against the new pattern.
- Restriction tests cover each of the three failures and the `technicalConfigurationParameters` failure.
- The rotation test with `secret-stores.yml` asserts the error code and that no output file exists.
- BDD scenarios in `cucumber_tests/features/external-creds.feature`.
- Benchmark: profile `create_credentials` on a synthetic environment with many Namespaces, applications, and
  parameters. Compare before and after in both modes.

## Out of scope

- Several Credential Templates. Merge of Templates along the chain. Build gets one merged Template.
- VALS and ESO rendering, External Credential Context, the provisioning CLI.
- Migration of an existing external repository. The operator does it.
- Changes to local-mode placeholders and to the legacy key macros in local mode.

## Open questions

- Key order of the Credentials File is not set by the merge. `flush()` sorts it. Confirm with the golden files.

Settled during review:

- When the first reference is `.username` only, the auto-generated entry lists both properties, as the local
  `usernamePassword` does.
- A template Credential without `properties` that a macro reads with `.username` fails only in the Effective Set
  check. Build adds no check.
- Shared files and generated entries use `render_context`. `current_env.cloud` is set in `setup_base_context`,
  before any render.
- `copy_creds_to_env_creds_file` lost its callers and is removed. `EXTERNAL_CRED_COMMENT` stays, because the merge
  attaches provenance comments.
- An entry replaces the whole entry. `store_value_to_yaml` deletes the key and sets the new value.
- `credRef` objects in `technicalConfigurationParameters` stay unregistered, as today.

## Constraints

- Minimum code that solves the problem. No feature, flexibility, or configurability beyond the request.
- No abstraction for single-use code. No error handling for impossible cases.
- Touch only what the request needs. Do not improve adjacent code, comments, or formatting.
- Match the existing style. Remove only the imports and functions that this change leaves unused.
- Mention unrelated dead code. Do not delete it.
- Every changed line traces to the request.
- Never mock the component under test. Mock only the network, the clock, randomness, and services that the test
  environment lacks.
- Build a real component, such as the Calculator CLI JAR, in the test setup. A vacuous test is not acceptable.
- Name things by what they are. `namespace_paths`, not `items`.
- No comments, docstrings, or pragmas in new code. Tests included.
- No wrapper that only composes an existing function. Put the expression at the call sites.
- No extra enum members when a plain `==` gives the right default.
- No assertion on log text. A test checks that a warning fired, never its message.
