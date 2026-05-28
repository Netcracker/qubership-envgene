# Add Application or Registry Definitions to the template repository

This guide shows a template repository maintainer how to add new AppDef/RegDef templates to a shared template
repository, parameterized for different deployment sites.

For background, see [Application and Registry Definition](/docs/features/app-reg-defs.md). For use case examples,
see [UC-ARD-TR-3 / TR-4](/docs/use-cases/app-reg-defs.md#uc-ard-tr-3-shared-template-repository-off-site-instance-rendering).

## Prerequisites

- Write access to the template repository.
- Knowledge of which applications are configured in the template (defines the AppDef scope).
- Read access to the centralized definitions repository where pre-made AppDef/RegDef YAML files are maintained.

## Steps

### 1. Identify applications and registries in scope

You need to add a template for each AppDef and RegDef the template repository depends on:

- An **AppDef** template is required for every application whose configuration is maintained in this template
  repository.
- A **RegDef** template is required only for off-site registries that those AppDefs reference. The on-site RegDef is
  added as a user-provided file in the instance repository (see
  [Add an Application or Registry Definition without a template](/docs/how-to/app-reg-defs-add-without-template.md)).

### 2. Get base definitions from the centralized storage

For each application and registry in scope, fetch the corresponding base YAML file from the centralized definitions
repository. There is no automated tool. Copy files manually.

Place them in a working directory for editing.

### 3. Place in the template repository

Move the copied files under the template directories:

- AppDef: `/templates/appdefs/<application-name>.yml`
- RegDef: `/templates/regdefs/<registry-name>.yml`

If you plan to parameterize them (next step), rename to `.yml.j2` to mark them as Jinja templates:

- `/templates/appdefs/<application-name>.yml.j2`
- `/templates/regdefs/<registry-name>.yml.j2`

### 4. Parameterize for environment-specific values

The value that typically differs between instance repositories is the registry an AppDef references (the
`registryName` field), since different deployment sites use different registries (off-site source registries vs an
on-site customer registry).

Replace the hardcoded `registryName` with the `appdefs.overrides.registryName` Jinja macro and provide a `default()`
matching the value from the downloaded base. The default applies in instances where no override is configured
(typical off-site case). The override takes effect in instances where `appregdef_config.yaml` sets it (typical
on-site case).

**AppDef example.**

Downloaded base file (`app-1.yml` from centralized storage):

```yaml
name: app-1
artifactId: app-1
groupId: org.example
registryName: off-site-registry-A
supportParallelDeploy: true
```

Parameterized template (`/templates/appdefs/app-1.yml.j2`) - redirect registry by override:

```jinja
name: app-1
artifactId: app-1
groupId: org.example
registryName: "{{ appdefs.overrides.registryName | default('off-site-registry-A') }}"
supportParallelDeploy: true
```

The `default('off-site-registry-A')` preserves the value from the downloaded base when no override is configured.

> [!NOTE]
> The on-site RegDef itself is **not** added to the template repository. It is created in the instance repository as a
> user-provided file - see
> [Add an Application or Registry Definition without a template](/docs/how-to/app-reg-defs-add-without-template.md).
> The template repository holds only off-site RegDef templates.

### 5. Configure override values in the instance repository

In each instance repository that consumes these templates, configure override values in
`/configuration/appregdef_config.yaml`.

**Off-site instance** - no overrides. Defaults from templates apply (file can be absent or empty).

**On-site instance** - redirect AppDefs to the on-site registry:

```yaml
appdefs:
  overrides:
    registryName: customer-onsite-registry
```

Then create the on-site RegDef as a user-provided file at `/configuration/regdefs/customer-onsite-registry.yml` -
see [Add an Application or Registry Definition without a template](/docs/how-to/app-reg-defs-add-without-template.md)
for the procedure.

### 6. Verify

After committing the templates and the instance config:

1. Trigger the `app_reg_def_process` job in the instance pipeline.
2. Inspect `/appdefs/` and `/regdefs/` in the instance repository.
3. Confirm AppDef `registryName` resolves as expected per instance overrides.
4. Confirm RegDef fields use override values where configured.

## Notes

- All RegDef templates in `/templates/regdefs/` render unconditionally on each pipeline run. Templates not referenced
  by AppDefs in a particular instance are still generated as effective definitions and persist in `/regdefs/` -
  harmless but unused.
- For instance-only customizations (no template repository changes), see
  [Add an Application or Registry Definition without a template](/docs/how-to/app-reg-defs-add-without-template.md).
- For the full set of fields, see [Application Definition](/docs/envgene-objects.md#application-definition) and
  [Registry Definition](/docs/envgene-objects.md#registry-definition).
