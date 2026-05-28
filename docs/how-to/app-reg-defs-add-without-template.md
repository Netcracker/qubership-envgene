# Add an Application or Registry Definition without a template

This guide shows how to add a new Application Definition (AppDef) or Registry Definition (RegDef) to an instance
repository without modifying the template repository. The new definition is provided as a YAML file under
`/configuration/` and is added to the effective definitions during the next pipeline run.

For background on the user-provided file mechanism, see
[Application and Registry Definition - User-provided files](/docs/features/app-reg-defs.md#user-provided-files).

## Steps

1. **Create the YAML file in the instance repository.**

   For a new AppDef, create `/configuration/appdefs/<application-name>.yml`:

   ```yaml
   name: my-new-app
   artifactId: my-new-app
   groupId: org.example
   registryName: my-registry
   ```

   For a new RegDef, create `/configuration/regdefs/<registry-name>.yml`:

   ```yaml
   name: my-registry
   credentialsId: my-creds
   mavenConfig:
     fullRepositoryUrl: https://maven.example.com/repository
   ```

   Use a filename that does **not** match any existing template-rendered definition in `/appdefs/` or `/regdefs/`. If
   the filename matches, the user-provided file will **replace** the template-rendered one instead of adding a new one.

   For the full set of required and optional fields, see
   [Application Definition](/docs/envgene-objects.md#application-definition) and
   [Registry Definition](/docs/envgene-objects.md#registry-definition).

2. **Commit and push** the new file to the instance repository.

3. **Trigger the instance pipeline.** The `app_reg_def_process` job picks up the user-provided file and adds it as a
   new effective definition.

4. **Verify** the new effective definition appears at:
   - `/appdefs/<filename>.yml` (for AppDef), or
   - `/regdefs/<filename>.yml` (for RegDef)

   with the contents of your user-provided file.

## Notes

- User-provided files are plain YAML used as-is. They are **not** rendered as Jinja templates.
- User-provided files apply repository-wide, not per-environment.
- The new definition is available to downstream pipeline processing (CMDB export, Generate Effective Set) in the same
  way as template-rendered definitions.

## Related

- [Application and Registry Definition (feature)](/docs/features/app-reg-defs.md) - full specification
- [UC-ARD-UD-3](/docs/use-cases/app-reg-defs.md#uc-ard-ud-3-add-new-definition-via-user-provided-file-with-no-matching-template) - use case scenario
