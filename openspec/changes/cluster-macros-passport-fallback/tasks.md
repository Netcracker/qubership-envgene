# Tasks

## 1. Generator behavior

- [ ] 1.1 In the environment build step, resolve the four `current_env.cluster` connection macros from the Cloud
  Passport cluster values when the Environment Inventory does not set `clusterUrl`. Verify against the spec scenario
  "clusterUrl is not set and the Cloud Passport provides the cluster values".
- [ ] 1.2 Keep `clusterUrl` as the source whenever it is set, without consulting the Cloud Passport for these macros.
  Verify against the scenarios "clusterUrl is set and no Cloud Passport is used" and "clusterUrl is set and a Cloud
  Passport is also present".
- [ ] 1.3 Leave a macro an empty string when neither source provides its value. Verify against the scenarios
  "clusterUrl is not set and no Cloud Passport is used" and "clusterUrl is not set and the Cloud Passport omits a
  cluster value".

## 2. Tests

- [ ] 2.1 Add unit tests for the environment configuration generation covering the five spec scenarios (clusterUrl
  present with and without a passport, clusterUrl absent with a full passport, with no passport, and with a passport
  missing a field). Verify: the new tests pass and the baseline suite is unaffected.
- [ ] 2.2 Add or adjust the BDD scenarios that map the delta spec cases for `cluster-connection-macros`. Verify: the
  cucumber BDD run is green and the scenarios trace to the spec.

## 3. Documentation

- [ ] 3.1 Correct `docs/template-macros.md` for the four macros: replace "overwritten from Cloud Passport file" with
  the fallback statement (the Cloud Passport fills the value when `clusterUrl` is not set), and remove the deprecated
  note on `cloud_public_url`. Verify: the docs match the implemented behavior (docs stage discrepancy check).
