# Current env instance store in the env build step

- [Problem](#problem)
- [Example](#example)
- [Decisions](#decisions)
- [What passes between steps](#what-passes-between-steps)
- [Changes by module](#changes-by-module)
- [What stays the same](#what-stays-the-same)
- [Verification](#verification)
- [Out of scope](#out-of-scope)
- [Open questions](#open-questions)
- [Constraints](#constraints)

## Problem

`EnvBuildStep` keeps the objects of the env instance in memory in one store and writes them once at the end.
Three things around that store are unclear in the code:

- The store is one per step, but it travels as the `object_store` parameter through 18 functions in 12 files.
- `get_namespaces` and `get_bgd_object` read the store when they get it and read the disk when they do not.
  The disk holds the result of the previous run. The store holds the current run. The call site does not
  show which run it reads.
- `AppregdefRenderStep`, `RegdefV2AdapterStep`, and the Namespace map step create a store of their own. They
  render BG Domain, Namespace, and Cloud into it, take one value, and drop the rest. Nothing from these
  stores reaches the disk or the next step.

The root cause is the removal of `tmp/render/<env>`. That directory was the place for the current run, and
the directory path told the two runs apart. The store took over the role, but the code kept the optional
argument that used to be a path.

## Example

Before:

```python
def update_profile_name(file_path, profile_name, object_store):
    data = object_store.get(file_path)

namespaces = get_namespaces(env_dir, object_store)
```

After:

```python
def update_profile_name(file_path, profile_name):
    data = current_env_instance_store().get(file_path)

namespaces = current_env_instance_store().namespaces()
previous_namespaces = get_namespaces(env_dir)
```

The first call reads the current run. The second call reads the previous run from the disk.

## Decisions

- **The store exists only in `EnvBuildStep`.** No other step creates or sees it. Reason: only this step
  writes the env instance.
- **The class is `CurrentEnvInstanceStore`.** Reason: the name says what it holds and which run it belongs to.
- **Code inside the step gets the store without a parameter.** `EnvBuildStep` in the orchestrator opens the
  store around the whole step, and `current_env_instance_store()` returns it. Reason: one store per step
  needs no argument.
- **The store returns only what was put into it.** `get`, `exists`, and `find_yaml` never read the disk.
  The build code reads an input file from the disk itself and puts the object into the store. Reason: the
  temporary render directory held only what was copied or rendered into it, and the store replaces that
  directory. A lookup that falls back to the disk mixes the two runs.
- **A call outside the step fails.** `current_env_instance_store()` raises an error when no store is open. It
  never reads the disk instead. Reason: a silent switch to the disk mixes the two runs.
- **The disk is the previous run, the store is the current run.** `get_namespaces(env_dir)` and
  `get_bgd_object(env_dir)` read the disk only. The store has its own `namespaces()` and `bg_domain()`. A
  function that needs both runs makes both calls.
- **Early steps render without a store and write no drafts.** The render methods return the rendered object.
  `EnvBuildStep` puts the returned object into the store. The early steps use the object and drop it.
  Reason: their BG Domain, Namespace, and Cloud are drafts rendered with a reduced context. A draft in the
  env directory would be committed in a run where `EnvBuildStep` does not start, for example BGD warmup.
- **A step returns only what a later step needs.** The pipeline passes the returned value on.
- **The build has one env directory.** The build reads its input from the env directory and writes the
  result to the same directory. The separate output directory and the `env_instances_dir` variable of the
  render context go away. Reason: with no temporary render directory the two paths were always equal
  outside the tests.
- **The prepared `env_definition` is not in the store.** The step prepares the copy once and passes it to
  the build functions as a parameter. Reason: the copy is never written to the disk, so it is not an
  object of the env instance. The lookup of `env_definition` by the path of an object goes away.

## What passes between steps

| Value                           | Produced by                     | Used by                   | Carried by                         |
|---------------------------------|---------------------------------|---------------------------|------------------------------------|
| Names of the rendered RegDefs   | `AppregdefRenderStep`           | `RegdefV2AdapterStep`     | `ctx.rendered_regdef_names`        |
| Deploy postfix to Namespace map | Namespace map step              | Deployment plan steps     | `ctx.namespace_by_deploy_postfix`  |
| RegDefs of version 2            | `RegdefV2AdapterStep`           | `ProcessSdStep`           | `ctx.transient_regdefs_dir`        |
| Rendered ParameterSets          | `RegdefV2AdapterStep`           | `EnvBuildStep`            | `tmp/render-workspace/parameters`  |

AppDefs and RegDefs go straight to their final directories. They never enter the store, because an
environment can have many of them and the next step needs only the names.

## Changes by module

- `modules/envgene/envgenehelper/object_store.py` becomes `current_env_instance_store.py`. `ObjectStore`
  becomes `CurrentEnvInstanceStore`. The module gets `current_env_instance_store()` and the function that
  opens the store for a step. The store gets `namespaces()` and `bg_domain()`.
- `modules/envgene/envgenehelper/business_helper.py`: `get_namespaces`, `get_bgd_object`, and
  `NamespaceFile` lose the `object_store` argument and read the disk only.
- `scripts/pipeline/orchestrator.py`: `EnvBuildStep` decrypts the Credentials, opens the store, runs the
  build, cleans the generated objects in the env directory, and flushes the store. The flush happens
  before the Credentials are encrypted again. When the step fails, it writes the objects as they are to
  the job artifact.
- `scripts/build_env/main.py`: the build functions only fill the store.
- `scripts/build_env/render_config_env.py`: `EnvGenerator` no longer owns a store. `generate_bgd_file`,
  `generate_namespace_files_and_map`, and `generate_cloud_file` each split into a part that renders and
  returns the object and a part that puts it into the store. `apply_template_override` works on the object
  it gets. `build_minimal_render_context` returns the changed copy of `env_definition` and does not put it
  anywhere. `EnvBuildStep` puts each Namespace into the store right after its render, before the template
  override and the schema check, so a failed build still writes the Namespaces that were rendered.
- `scripts/build_env/namespace_render.py`, `scripts/build_env/appregdef_render.py`, and
  `scripts/regdefv2_adapter/regdefv2_adapter.py`: no store.
- `scripts/build_env/build_env.py`: `convertParameterSetsToParameters` splits in the same way.
  `mergeParameterSetsIntoParameters` returns the parameters and uses no store. `RegdefV2AdapterStep` calls
  it for the e2e parameters of Cloud. `convertParameterSetsToParameters` calls it and then writes the
  Application objects into the store.
- `scripts/build_env/resource_profiles.py`: a Resource Profile that the env needs is looked up by name.
  The store is asked first for a profile rendered from the template. A ready profile of the template is
  then read from the disk and put into the store. The `Profiles` directory of the env is not a source:
  its disk copy is the previous run, and the build fills it only after the lookup. An env-specific
  profile from the Instance Repository is read once and put into the store.
- `scripts/build_env/build_env.py`, `create_credentials.py`, `resource_profiles.py`,
  `env_specific_overrides.py`, `scripts/cloud_passport/cloud_passport.py`, and
  `modules/envgene/envgenehelper/creds_helper.py`: the `object_store` parameter goes away.

## What stays the same

- The objects in the store: Tenant, Cloud, Namespace, Application, BG Domain, Composite Structure, Resource
  Profiles, and Credentials.
- The store methods `put`, `list`, `beautify`, and `flush`. `find_yaml` is new: it returns the path of a
  stored object by its name under a directory, for the `.yml` and `.yaml` extensions.
- The order inside `EnvBuildStep`, the single write at its end, and the raw write to the job artifact when
  the step fails.
- The files in the Instance Repository after a run.

## Verification

- The existing test suites pass.
- The output of `scripts/tests/env-build/test_render_envs.py` is byte-identical to the output before the
  change.
- New tests: `current_env_instance_store()` fails outside the step, a second store for the same step fails,
  `get_namespaces(env_dir)` does not see an object that is only in the store, the Namespace map step
  leaves no file under the env directory except `Inventory/namespace-map.yml`, and a build over the result
  of a previous build passes and removes the profiles that the previous build left.

## Out of scope

- One store for several steps or for the whole pipeline.
- Reuse of the early renders in `EnvBuildStep`. Cloud is rendered twice per run, BG Domain and Namespace two
  or three times.
- The render `Context`.
- AppDefs, RegDefs, and ParameterSets in the store.

## Open questions

- Peak memory is measured only on test data, where it did not grow. It is not measured on a large
  environment or on a run with several `ENV_NAMES` values.
- `validate_bgd` read an empty directory before the store and always passed. It now checks the current run.
  It is not yet run against a real BG environment.
- `get_namespace_role` reads `bg_domain.yml` of the previous run from the disk when the BG Domain of the
  current run is empty.
- The log line "Input params are" prints `env_definition` a second time. The fix is postponed.

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
