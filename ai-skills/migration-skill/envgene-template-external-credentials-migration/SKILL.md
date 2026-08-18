---
name: envgene-template-external-credentials-migration
description: Update one EnvGene Environment Template for External Credentials: find Credential references, create a correct Credential Template, add external_credential_template, replace supported local references, and prepare a concrete version for the Instance Repository.
---

# EnvGene Template External Credentials Migration

Work with one Environment Template. On each run, update `external-credentials-migration-report.md` and show one next action.

## Constraints

- Work only with the local repository and user data.
- Do not use the web, GitHub, remote documentation, or helper scripts.
- Do not open Instance Credential files.
- Do not migrate System Credentials in the Template Repository: they remain local-only.
- Never run the template build pipeline, publish, commit, push, or merge.
- Do not create a Credential until its structure and source are defined.
- Do not determine structure from the `credId` name.

## 1. Select Environment Template

If no Template is specified, show Template Descriptors and ask the user to select one.

Analyse only Cloud, Namespace, Tenant, BG Domain, and ParameterSet templates connected to it. Do not change Template composition or BG deployment automatically.

## 2. Find references

Find:

```text
${creds.get(...)}
${envgen.creds.get(...)}
${cmdb.creds.get(...)}
#creds
#credscl
#credsns
$type: credRef
```

Also find built-in references: `defaultCredentialsId`, `credentialsId`, `tokenSecret`, `credential`, `controllerNamespace.credentials`.

For each `credId`, collect all usage locations.

## 3. Determine structure

Use only references:

- `.username`, `.password`, or `credRef.property` → `properties: username, password`;
- `.secret` or `credRef` without `property` → without `properties`.

Built-in cases with unambiguous structure:

- `Cloud.maasConfig.credentialsId`, `Cloud.dbaasConfigs[].credentialsId`, `BGDomain.controllerNamespace.credentials` → username/password;
- `Cloud.vaultConfig.credentialsId`, `Cloud.consulConfig.tokenSecret` → single-value.

For `Cloud.defaultCredentialsId`, `Namespace.credentialsId`, `Tenant.credential`, and other ambiguous cases, use the Instance migration report or ask one grouped question.

Do not assign `properties` to all Credentials the same way. If one `credId` is used both as single-value and username/password, do not create it until the user decides.

## 4. Determine source

For each `credId`, choose one source from the Instance migration report:

- Credential Template;
- Cloud Passport Credentials;
- Shared Credentials.

A reference in the Template alone does not determine the source.

- Add only Template Credentials to the Credential Template.
- Do not duplicate Cloud Passport and Shared Credentials.
- If the source is unknown, ask one grouped question.

## 5. Secret Store and credId

Use `secretStore` and its type from the Instance migration report. If data is missing, ask one question for all Template Credentials.

Before creating the file, validate `credId`:

- Vault: final `<remoteRefPath>/<credId>` - only `a-zA-Z0-9-/_`;
- Azure: `credId` - `a-zA-Z0-9-`, no more than 32 characters;
- AWS: final name - `a-zA-Z0-9-/_+=.@!`, `credId` no more than 32 characters;
- GCP: `credId` - `a-zA-Z0-9_-`, no more than 32 characters.

If no explicit `remoteRefPath` exists, use for validation:

```text
{{ current_env.cloud }}/{{ current_env.name }}
```

Do not rename `credId` automatically. On error, suggest an allowed name and after confirmation update all references in the selected Template. For Cloud Passport or Shared, note that the name must also be changed in the Instance Repository.

## 6. Create Credential Template

Create one Credential Template. Add only Credentials with confirmed structure, source, and Secret Store.

Username/password:

```yaml
<credId>:
  type: external
  secretStore: <secretStore>
  properties:
    - name: username
    - name: password
```

Single-value:

```yaml
<credId>:
  type: external
  secretStore: <secretStore>
```

Rules:

- no `data` or values;
- no `create` for existing Credentials;
- no `properties` for single-value;
- do not create the same structure for all `credId` values;
- do not add unconfirmed Credentials.

Do not specify `remoteRefPath` by default. EnvGene uses `{{ current_env.cloud }}/{{ current_env.name }}`. Add an explicit path only per a confirmed project scheme and without `credId` at the end.

## 7. Update Template Descriptor

Add:

```yaml
external_credential_template: "{{ templates_dir }}/<path-to-credential-template>"
```

After this, every `credId` used via built-in reference, `$type: credRef`, or `${creds.get(...)}` must be declared in the Credential Template, Cloud Passport, or Shared Credentials.

Confirm coverage from the Instance migration report. Do not open Instance Credential files.

## 8. Replace local references

Replace only in `deployParameters` and `e2eParameters`.

Username/password:

```yaml
<parameter>:
  $type: credRef
  credId: <credId>
  property: username|password
```

Single-value:

```yaml
<parameter>:
  $type: credRef
  credId: <credId>
```

Do not add `credRef` to `technicalConfigurationParameters`, do not move the parameter automatically. Leave built-in references as a string `credId`. Change hash macros only when mapping is unambiguous.

## 9. Validate changes

Check:

- one Credential Template for the selected Environment Template;
- Descriptor contains a correct `external_credential_template`;
- all entries have `type: external`, with no `data`, values, or `create`;
- username/password have `properties`, single-value do not;
- structure of each Credential is confirmed by references;
- `credId` suits the selected Secret Store;
- `remoteRefPath` does not contain a repeatedly appended `credId`;
- `credRef.property` matches `properties`;
- local references replaced only in supported blocks;
- built-in references remain strings;
- no `credRef` in `technicalConfigurationParameters`;
- every used `credId` has a source;
- Cloud Passport and Shared Credentials are not duplicated unnecessarily.

Check matching `credId` values with priority:

```text
Credential Template
Cloud Passport Credentials
Shared Credentials
```

Shared Credentials have the highest priority. Show a question only if definitions differ or the source is not confirmed.

If validation is incomplete, do not suggest publication.

## 10. Prepare publication

Never run the template build pipeline.

After successful validation, write:

```text
Run the template build pipeline manually.
After publication, report the concrete version in the format <artifactId>:<version>.
```

Do not use `SNAPSHOT` for Instance migration. After receiving the version, record:

```text
Template migration status: VERIFIED
```

## Report

```markdown
# External Credentials Migration

## Template
- Environment Template:
- Template Descriptor:
- Secret Store:
- Template migration status: NOT_VERIFIED | VERIFIED
- Concrete version:

## Progress
- [ ] References found
- [ ] Credential structure determined
- [ ] Source of each credId determined
- [ ] credId values validated for Secret Store
- [ ] Credential Template created
- [ ] Template Descriptor updated
- [ ] Local references replaced
- [ ] Matching credId values and coverage checked
- [ ] Changes validated
- [ ] Concrete version published by user

## Decision needed
...

## Next action
...
```

Add `Decision needed` only when a question exists. In the response, show changed files, Credential count, replacement count, real issues, and one next action.
