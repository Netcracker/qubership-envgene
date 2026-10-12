# Current env instance store

- [Problem](#problem)
- [Example](#example)
- [Rules](#rules)
- [What passes between steps](#what-passes-between-steps)
- [Changes by file](#changes-by-file)
- [What changes for the user](#what-changes-for-the-user)
- [What stays the same](#what-stays-the-same)
- [Tests](#tests)
- [Out of scope](#out-of-scope)
- [Open questions](#open-questions)
- [Constraints](#constraints)

## Problem

Env build is slow. It works with files in `tmp/render/<env>`. Each part of the build opens a file, changes
it, and saves it again. So one object is read and written many times.

On a real environment with 5 Namespaces and 190 AppDefs, `env_build` takes 11.5 s.

## Example

One Namespace, before:

```text
render the template          -> write file
open file, apply override    -> write file
open file, add ParameterSets -> write file
open file, sort by schema    -> write file
open file, add header        -> write file
open file, fix comments      -> write file
copy tmp/render/<env> to the env directory
```

After:

```text
render the template          -> put the object into the store
apply override, add ParameterSets (in memory)
end of the step: sort by schema, add header, fix comments, write file once
```

On the same environment `env_build` takes 5.0 s.

## Rules

- **The store lives only in `EnvBuildStep`.** Other steps do not see it. Only this step writes the env
  instance.
- **Code gets the store with `current_env_instance_store()`.** No parameter is needed. Outside the step
  this call fails.
- **The store never reads the disk.** It gives back only what was put into it. The build reads an input
  file itself and puts the object into the store.
- **The disk is the previous run. The store is the current run.** `get_namespaces(env_dir)` and
  `get_bgd_object(env_dir)` read the disk. `namespaces()` and `bg_domain()` of the store read the current
  run.
- **The store writes once, at the end of the step.** `flush()` sorts each object by schema, adds quotes and
  the header, fixes the space before comments, and writes the file.
- **The store never writes into `Inventory`.** Files there are input, for example an env-specific Resource
  Profile.
- **A failed build writes nothing.** The build removes the generated objects of the env directory at its
  start. After a failed build the env directory has no generated objects, and the job artifact has no
  objects of the failed build.
- **Early steps do not use the store.** `AppregdefRenderStep`, `RegdefV2AdapterStep`, and the Namespace map
  step render an object, take the value they need, and drop the object. They write no drafts into the env
  directory.
- **`env_definition` is not in the store.** The build reads it once and passes it as a parameter. It is
  input and the build does not write it.
- **The build has one directory.** It reads input from the env directory and writes the result there.
  `tmp/render` and `tmp/resource_profiles` are gone.
- **Schema checks stay where they were.** Each check is a separate call in the build code. `flush()` does
  not check.

## What passes between steps

| Value                           | From                  | To                    | How                               |
|---------------------------------|-----------------------|-----------------------|-----------------------------------|
| Names of the rendered RegDefs   | `AppregdefRenderStep` | `RegdefV2AdapterStep` | `ctx.rendered_regdef_names`       |
| Deploy postfix to Namespace map | Namespace map step    | Deployment plan steps | `ctx.namespace_by_deploy_postfix` |
| RegDefs of version 2            | `RegdefV2AdapterStep` | `ProcessSdStep`       | `ctx.transient_regdefs_dir`       |
| Rendered ParameterSets          | `RegdefV2AdapterStep` | `EnvBuildStep`        | `tmp/render-workspace/parameters` |

AppDefs and RegDefs are not in the store. They go to their directories at once.

## Changes by file

| File                                            | Change                                                           |
|-------------------------------------------------|------------------------------------------------------------------|
| `envgenehelper/current_env_instance_store.py`   | New. The store                                                   |
| `envgenehelper/yaml_helper.py`                  | `sortYaml` does not check by schema. Comments are fixed in the object, not in the file |
| `envgenehelper/business_helper.py`              | Cloud Passport lookup takes `env_definition` as a parameter      |
| `envgene_shared/utils/yaml_utils.py`            | A schema file is read once, not on each check                    |
| `scripts/pipeline/orchestrator.py`              | `EnvBuildStep` opens the store, runs the build, calls `flush()`  |
| `scripts/build_env/main.py`                     | No `tmp/render`. The build cleans the env directory and fills the store |
| `scripts/build_env/render_config_env.py`        | Render methods return objects. `EnvBuildStep` puts them into the store |
| `build_env.py`, `create_credentials.py`, `resource_profiles.py`, `env_specific_overrides.py`, `cloud_passport.py`, `creds_helper.py` | Read and change objects in the store, not files |

## What changes for the user

One-time changes in the files of the Instance Repository:

- One space before a comment at the end of a line. Some lines had two.
- `cleaned` is the last field of a Namespace.
- `profile.name` stands where the schema puts it.
- New Credentials have no `# FillMe` comment.

Changes in behavior:

- Only the ParameterSets that the environment uses are checked and rendered. A broken ParameterSet that
  nobody uses does not fail the build.
- `validate_bgd` checks the BG Domain and the Namespaces of the current run. Before, it read an empty
  directory and always passed.
- Definition overrides in `configuration/appdefs` and `configuration/regdefs` are checked by schema.
- A schema error is a `ValueError`. The log lists what is wrong.
- When two Resource Profiles of the template have the same name, the first one found is used. Before, it
  was the last one.

## What stays the same

- The objects in the store: Tenant, Cloud, Namespace, Application, BG Domain, Composite Structure, Resource
  Profiles, and Credentials.
- The list of steps and their order.
- The files in the Instance Repository, except the one-time changes above.
- The job artifact.

## Tests

- The old test suites pass.
- `scripts/tests/env-build/test_render_envs.py` compares the build result with the expected files.
- New tests check that:
  - `current_env_instance_store()` fails outside the step
  - a second store for the same step fails
  - the store does not read the disk
  - `get_namespaces(env_dir)` does not see an object that is only in the store
  - the Namespace map step leaves only `Inventory/namespace-map.yml` in the env directory
  - a build over the result of a previous build passes

## Out of scope

- One store for the whole pipeline.
- Reuse of the early renders in `EnvBuildStep`. Cloud is rendered twice per run. BG Domain and Namespace
  are rendered two or three times.
- AppDefs, RegDefs, and ParameterSets in the store.
- Faster sorting by schema.
- Sorting of BG Domain and Composite Structure by schema.

## Open questions

- Memory is measured only on test data. There it did not grow. It is not measured on a large environment
  or on a run with several `ENV_NAMES` values.
- `validate_bgd` is not tried on a real BG environment yet.
- The log prints `env_definition` two times.

## Constraints

- Minimum code that solves the problem. No features, abstractions, or options that nobody asked for.
- Touch only what the change needs. Do not improve adjacent code. Remove only the code that this change
  makes unused.
- Do not mock the component that a test verifies.
- Name things by what they are.
- No comments, no docstrings, and no `# noqa` or other pragmas in new code. Tests included.
- No function that only calls an existing function.
- No extra enum members.
- A test checks that a warning fired. It never checks the message text.
