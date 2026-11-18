# Plan: cluster-macros-passport-fallback

**Goal:** the four `current_env.cluster` connection macros fall back to the Cloud Passport when the Environment
Inventory does not set `clusterUrl`.
**Approach:** add one `elif` branch to the cluster block of the environment configuration template so the four macros
read the passport cluster values when `clusterUrl` is absent, keeping `clusterUrl` as the source when it is set and an
empty string when neither provides a value. Correct the template-macros documentation to match.
**Change:** openspec/changes/cluster-macros-passport-fallback/ (proposal, specs, design, tasks)
**Commands:** one test: `PYTHONPATH=".:./scripts" python -m pytest scripts/tests/env-build/test_cluster_macros_passport_fallback.py`; all tests: `PYTHONPATH=".:./scripts" python -m pytest scripts/tests/`; lint: super-linter (markdownlint/textlint) via docker, or "not run: no docker"

## Global constraints

- Precedence is fallback, not override: when `clusterUrl` is set the Cloud Passport is not consulted for these macros.
- Each macro uses a default of empty string, so a passport that omits a value yields an empty macro, not an error.
- The passport protocol value is upper-cased, to match the `clusterUrl` path.
- Only the cluster block of `env_config.yml.j2` and the four macro entries in `docs/template-macros.md` change.
- No comments or docstrings in new code or tests. Name values for what they are.
- Tests drive the real environment configuration render, never a reimplementation of the resolution rules.

## Contracts

- C-1: render context exposes top-level `cloud_passport` with `cloud.CLOUD_PROTOCOL`, `cloud.CLOUD_API_HOST`,
  `cloud.CLOUD_API_PORT`, `cloud.CLOUD_PUBLIC_HOST`, loaded fresh from the passport file; covered in step 1.3 and 1.5.
- C-2: the four `current_env.cluster` macros resolve to clusterUrl, else passport, else empty; covered in steps
  1.1 through 1.5.
- C-3: with `clusterUrl` set the existing branch is unchanged and the passport is not consulted; covered in steps
  1.1 and 1.2.

## Review focus

- `clusterUrl` set and a passport also present -> clusterUrl wins; test in step 1.2.
- passport present but one cluster key absent -> only that macro is empty; test in step 1.5.
- passport absent entirely -> all four macros empty, no error; test in step 1.4.

## Task 1.1 through 1.3, 2.1: cluster block fallback with real-render tests

**Files:** modify `scripts/build_env/templates/env_config.yml.j2:54-64`; create
`scripts/tests/env-build/test_cluster_macros_passport_fallback.py`
**Interfaces:** test helper `render_cluster(env_definition, cloud_passport)` returning the generated
`current_env.cluster` block, driving the real `EnvGenerator` render (`generate_config`).
**Scenario:** specs/cluster-connection-macros/spec.md, all five scenarios.

- [ ] 1. Write the failing tests in `test_cluster_macros_passport_fallback.py`, one per spec scenario:
  - `test_clusterurl_set_no_passport`: `inventory.clusterUrl` set, no passport -> cluster values parsed from
    `clusterUrl`.
  - `test_clusterurl_set_with_passport`: `clusterUrl` set and a passport present -> cluster values from `clusterUrl`,
    passport ignored.
  - `test_clusterurl_absent_full_passport`: no `clusterUrl`, passport with all four cluster values -> cluster values
    from the passport; `cloud_public_url` equals the passport public host.
  - `test_clusterurl_absent_no_passport`: no `clusterUrl`, no passport -> all four cluster values empty.
  - `test_clusterurl_absent_passport_missing_port`: no `clusterUrl`, passport without the API port -> `cloud_api_port`
    empty, `cloud_public_url` set from the passport.
- [ ] 2. Run `<one-test command>`; expect FAIL on the three `clusterurl_absent` tests with a passport (empty cluster
  values today); the two `clusterurl_set` tests pass as regression guards.
- [ ] 3. Minimal code: in the cluster block add, between the `clusterUrl` `if` and the empty `else`:
  `{% elif cloud_passport.cloud is defined %}` setting
  `cloud_api_protocol: "{{ cloud_passport.cloud.CLOUD_PROTOCOL | default('') | upper }}"`,
  `cloud_api_url: "{{ cloud_passport.cloud.CLOUD_API_HOST | default('') }}"`,
  `cloud_api_port: "{{ cloud_passport.cloud.CLOUD_API_PORT | default('') }}"`,
  `cloud_public_url: "{{ cloud_passport.cloud.CLOUD_PUBLIC_HOST | default('') }}"`.
- [ ] 4. Run `<one-test command>`; expect PASS on all five; run `<all-tests command>`; no new failures against the
  baseline.
- [ ] 5. Tick 1.1, 1.2, 1.3, 2.1 in tasks.md; commit `fix: resolve cluster.* macros from Cloud Passport when clusterUrl is unset`.

## Task 2.2: BDD coverage

**Files:** `cucumber_tests/` env-build feature and a passport-based fixture environment, if a low-cost hook exists.
**Scenario:** specs/cluster-connection-macros/spec.md, "clusterUrl is not set and the Cloud Passport provides the
cluster values".

- [ ] 1. Assess whether the existing env-build BDD feature has a passport-based environment the scenario can reuse.
- [ ] 2. If yes, add a scenario asserting a rendered host carries the passport domain; verify with
  `cd cucumber_tests && ./run_bdd_tests.sh`. If adding a full passport fixture is disproportionate for a template
  fallback, record in the ledger that the real-render unit tests of task 1 cover the behavior, and tick 2.2 with that
  note.

## Task 3.1: documentation

**Files:** modify `docs/template-macros.md` (the four `current_env.cluster.*` macro entries).
**Scenario:** none (documentation).

- [ ] 1. Replace "the value will be overwritten from Cloud Passport file" in the four macro entries with the fallback
  statement: the Cloud Passport provides the value when `clusterUrl` is not set.
- [ ] 2. Verify: the four entries read as fallback and no entry still says "overwritten"; markdownlint and textlint
  pass (or "not run: no docker"). Tick 3.1; commit `docs: state cluster.* macros fall back to the Cloud Passport`.
