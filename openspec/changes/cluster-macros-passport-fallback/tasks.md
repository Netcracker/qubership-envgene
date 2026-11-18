# Tasks

## 1. Generator behavior

- [x] 1.1 In the environment build step, resolve the four `current_env.cluster` connection macros from the Cloud
  Passport cluster values when the Environment Inventory does not set `clusterUrl`. Verify against the spec scenario
  "clusterUrl is not set and the Cloud Passport provides the cluster values".
- [x] 1.2 Keep `clusterUrl` as the source whenever it is set, without consulting the Cloud Passport for these macros.
  Verify against the scenarios "clusterUrl is set and no Cloud Passport is used" and "clusterUrl is set and a Cloud
  Passport is also present".
- [x] 1.3 Leave a macro an empty string when neither source provides its value. Verify against the scenarios
  "clusterUrl is not set and no Cloud Passport is used" and "clusterUrl is not set and the Cloud Passport omits a
  cluster value".

## 2. Tests

- [x] 2.1 Add unit tests for the environment configuration generation covering the five spec scenarios (clusterUrl
  present with and without a passport, clusterUrl absent with a full passport, with no passport, and with a passport
  missing a field). Verify: the new tests pass and the baseline suite is unaffected.
- [x] 2.2 Integration coverage: the existing `test_render_envs[cluster01-env03-test-template-1]` full-render test
  exercises a passport-based environment without `clusterUrl` end to end. Its golden reference was corrected from the
  truncated hosts to the passport domain. A separate cucumber fixture would be disproportionate for a template
  fallback, so this real-pipeline test covers the behavior.

## 3. Documentation

- [x] 3.1 Correct `docs/template-macros.md` for the four macros: replace "overwritten from Cloud Passport file" with
  the fallback statement (the Cloud Passport fills the value when `clusterUrl` is not set), and remove the deprecated
  note on `cloud_public_url`. Verify: the docs match the implemented behavior (docs stage discrepancy check).
