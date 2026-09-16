# Resource profile use cases

- [Resource profile use cases](#resource-profile-use-cases)
  - [Overview](#overview)
  - [Active side selection](#active-side-selection)
    - [UC-RP-SS-1: Namespace is the active side when an override is present](#uc-rp-ss-1-namespace-is-the-active-side-when-an-override-is-present)
    - [UC-RP-SS-2: Namespace is the active side when the namespace object baseline is set](#uc-rp-ss-2-namespace-is-the-active-side-when-the-namespace-object-baseline-is-set)
    - [UC-RP-SS-3: Cloud is the active side when the namespace has no baseline or override](#uc-rp-ss-3-cloud-is-the-active-side-when-the-namespace-has-no-baseline-or-override)
  - [Baseline resolution within the active side](#baseline-resolution-within-the-active-side)
    - [UC-RP-BR-1: Override baseline takes precedence over the object baseline](#uc-rp-br-1-override-baseline-takes-precedence-over-the-object-baseline)
    - [UC-RP-BR-2: Object baseline is used when the override carries no baseline](#uc-rp-br-2-object-baseline-is-used-when-the-override-carries-no-baseline)
    - [UC-RP-BR-3: Empty string baseline is treated as absent](#uc-rp-br-3-empty-string-baseline-is-treated-as-absent)
    - [UC-RP-BR-4: Baseline-only override selects a baseline with no custom values](#uc-rp-br-4-baseline-only-override-selects-a-baseline-with-no-custom-values)
  - [Applying custom values and the baseline](#applying-custom-values-and-the-baseline)
    - [UC-RP-AB-1: Override is always applied and custom values win over the baseline when the name matches](#uc-rp-ab-1-override-is-always-applied-and-custom-values-win-over-the-baseline-when-the-name-matches)
    - [UC-RP-AB-2: Service with no baselines receives the custom values only](#uc-rp-ab-2-service-with-no-baselines-receives-the-custom-values-only)
    - [UC-RP-AB-3: Baseline name mismatch on a service that has baselines emits a warning](#uc-rp-ab-3-baseline-name-mismatch-on-a-service-that-has-baselines-emits-a-warning)
    - [UC-RP-AB-4: Override with custom values and no baseline emits a warning](#uc-rp-ab-4-override-with-custom-values-and-no-baseline-emits-a-warning)
  - [Environment-specific override](#environment-specific-override)
    - [UC-RP-ES-1: Standalone environment-specific override with no template override](#uc-rp-es-1-standalone-environment-specific-override-with-no-template-override)
    - [UC-RP-ES-2: Merge mode with a different baseline is the warned wrong path](#uc-rp-es-2-merge-mode-with-a-different-baseline-is-the-warned-wrong-path)
    - [UC-RP-ES-3: Replace mode changes the baseline for the environment](#uc-rp-es-3-replace-mode-changes-the-baseline-for-the-environment)
    - [UC-RP-ES-4: Merge mode with the same baseline combines both overrides](#uc-rp-es-4-merge-mode-with-the-same-baseline-combines-both-overrides)
  - [Referenced override file resolution](#referenced-override-file-resolution)
    - [UC-RP-LR-1: A referenced override name resolves to the most specific scope](#uc-rp-lr-1-a-referenced-override-name-resolves-to-the-most-specific-scope)

## Overview

This document covers use cases for [Resource Profiles](/docs/features/resource-profile.md), the
mechanism by which performance parameters (CPU, memory, replicas, and similar values) are resolved
during Effective Set generation. A baseline is a named set of performance parameters that the application
provides. Custom values are the performance-parameter values a configurator sets in an override on top of
the baseline. The resolution model spans two phases: the override combination (merge or replace) happens
during environment generation in `env_build`, and both active side selection and baseline lookup happen
during Effective Set calculation in the calculator.

An override applies to a namespace only when it is referenced by name: by `profile.name` on the namespace or
cloud template, or by an entry in `envTemplate.envSpecificResourceProfiles` in `env_definition.yml`. An
override file that no name references is ignored wherever it sits. Location is only the search order that
resolves a referenced name to a file, from the environment Inventory, then the cluster scope, then the
global scope, with the first match winning and the most specific scope winning.

There are two override objects. A template override (Template Resource Profile Override) is authored in the
template repository. An environment-specific override (Environment Specific Resource Profile Override) is
authored in the Instance repository.

For the full resolution rules and the merge algorithm, see the
[Resource Profiles feature doc](/docs/features/resource-profile.md). For the design rationale and
backward-compatibility analysis, see
[ADR-0006](/docs/adr/0006-resource-profile-baseline-override-resolution.md).

## Active side selection

The calculator resolves the override from either the Namespace or the Cloud, never both at once. The
Namespace is the active side when it has any profile signal, meaning its object baseline is set or an
override is present for it. Otherwise the Cloud is the active side.

These use cases demonstrate the side-selection decision under each condition.

### UC-RP-SS-1: Namespace is the active side when an override is present

**Pre-requisites:**

1. An Environment Instance exists with a Namespace that has no `profile.baseline` set on its object:

   ```yaml
   # namespace.yml
   profile:
     name: ns-override
   # baseline is absent
   ```

2. The Cloud object has a `profile.baseline` set and an override of its own.
3. A combined override named `ns-override` is present in the Environment Instance for
   the namespace (produced by a prior `env_build` run that resolved the namespace override).

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `ENV_NAMES: <cluster>/<env>`
2. `GENERATE_EFFECTIVE_SET: true`

**Steps:**

1. The `generate_effective_set` job runs.
2. For each application, the calculator evaluates the namespace: `profile.baseline` is absent, but an
   override is present.
3. The namespace is selected as the active side. The Cloud override and cloud `profile.baseline` are not
   used.
4. The calculator resolves the baseline and applies the override from the namespace side and generates the
   Effective Set.

**Results:**

1. Effective Set is generated successfully.
2. Each service in each application receives the custom values from the namespace override (and the
   resolved namespace baseline, if any). The cloud profile is not applied.

### UC-RP-SS-2: Namespace is the active side when the namespace object baseline is set

**Pre-requisites:**

1. An Environment Instance exists with a Namespace that has `profile.baseline` set on its object:

   ```yaml
   # namespace.yml
   profile:
     baseline: prod
   # name and override may or may not be present
   ```

2. No override is present for the namespace.
3. The Cloud object has its own profile configuration.

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `ENV_NAMES: <cluster>/<env>`
2. `GENERATE_EFFECTIVE_SET: true`

**Steps:**

1. The `generate_effective_set` job runs.
2. For each application, the calculator evaluates the namespace: `profile.baseline` is set.
3. The namespace is selected as the active side. The Cloud profile is not used.
4. The calculator resolves the baseline name from within the namespace side. No override is present, so
   the object baseline (`prod`) is used. The calculator generates the Effective Set.

**Results:**

1. Effective Set is generated successfully.
2. Each service receives parameters from the `prod` baseline (when the application defines it). The
   cloud profile is not applied. No override is applied because none is present.

### UC-RP-SS-3: Cloud is the active side when the namespace has no baseline or override

**Pre-requisites:**

1. An Environment Instance exists with a Namespace that has no `profile.baseline` and no override:

   ```yaml
   # namespace.yml
   # profile block is absent entirely
   ```

2. The Cloud object has a profile configuration:

   ```yaml
   # cloud.yml
   profile:
     name: cloud-override
     baseline: dev
   ```

3. An override named `cloud-override` is present in the Instance repository.
4. A combined override is already present in the Environment Instance for the Cloud (produced by a prior
   `env_build` run).

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `ENV_NAMES: <cluster>/<env>`
2. `GENERATE_EFFECTIVE_SET: true`

**Steps:**

1. The `generate_effective_set` job runs.
2. For each application, the calculator evaluates the namespace: no `profile.baseline` and no override are
   present.
3. The Cloud is selected as the active side.
4. The calculator resolves the baseline and applies the override from the cloud side and generates the
   Effective Set.

**Results:**

1. Effective Set is generated successfully.
2. Each service receives parameters from the `dev` baseline (when the application defines it) and the
   cloud override custom values. The namespace profile is not applied.

## Baseline resolution within the active side

Once the active side is selected, the calculator resolves a single baseline name within that side.
Baseline precedence, highest first, is the environment-specific override's baseline, then the template
override's baseline, then the object baseline. The `baseline` field is optional in the schema but is
mandated by configuration best practice.

### UC-RP-BR-1: Override baseline takes precedence over the object baseline

**Pre-requisites:**

1. An Environment Instance exists with a Namespace that is the active side (it has a baseline or an override).
2. The Namespace object carries `profile.baseline: prod`.
3. The override file for the namespace carries `baseline: perf-test` at the top level.

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `ENV_NAMES: <cluster>/<env>`
2. `GENERATE_EFFECTIVE_SET: true`

**Steps:**

1. The `generate_effective_set` job runs.
2. The calculator resolves the active side as the namespace.
3. The override carries a `baseline` field (`perf-test`). That value is used as the resolved baseline
   name. The namespace object's `profile.baseline` (`prod`) is not used.
4. The calculator looks up `perf-test` among the baselines the application defines and generates the
   Effective Set.

**Results:**

1. Effective Set is generated successfully.
2. Each service is evaluated against the `perf-test` baseline, not `prod`. Services that have a
   `perf-test` baseline receive those parameters plus the custom values. Services that have no baselines
   at all receive the custom values only.

### UC-RP-BR-2: Object baseline is used when the override carries no baseline

**Pre-requisites:**

1. An Environment Instance exists with a Namespace that is the active side.
2. The Namespace object carries `profile.baseline: dev`.
3. The override file for the namespace does not carry a `baseline` field.

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `ENV_NAMES: <cluster>/<env>`
2. `GENERATE_EFFECTIVE_SET: true`

**Steps:**

1. The `generate_effective_set` job runs.
2. The calculator resolves the active side as the namespace.
3. The override does not carry a `baseline` field. The object baseline (`dev`) is used as the resolved
   baseline name.
4. The calculator looks up `dev` among the baselines the application defines and generates the Effective Set.

**Results:**

1. Effective Set is generated successfully.
2. Each service is evaluated against the `dev` baseline. Services that have a `dev` baseline receive those
   parameters plus any custom values. Services that have no baselines at all receive the custom values
   only.

### UC-RP-BR-3: Empty string baseline is treated as absent

**Pre-requisites:**

1. An Environment Instance exists with a Namespace that is the active side.
2. Both the Namespace object and the override file carry a baseline that is either absent or set to an
   empty string (for example, `baseline: ""`).

> [!NOTE]
> Setting a baseline to an empty string is valid YAML but is documented as bad practice. See the
> [configuration standard](/docs/configuration-standard.md) for the recommended form.

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `ENV_NAMES: <cluster>/<env>`
2. `GENERATE_EFFECTIVE_SET: true`

**Steps:**

1. The `generate_effective_set` job runs.
2. The calculator encounters the empty string baseline and treats it as absent.
3. Both sources (the object and the override) carry an empty or absent baseline. No baseline name
   is resolved.
4. The calculator generates the Effective Set with no baseline lookup. Each service receives the custom
   values only (if an override is present).

**Results:**

1. Effective Set is generated successfully.
2. No baseline parameters are applied. Services receive only the custom values, or no performance
   parameters when no override is present either.

### UC-RP-BR-4: Baseline-only override selects a baseline with no custom values

**Pre-requisites:**

1. An Environment Instance exists with a Namespace that is the active side.
2. The override file for the namespace sets only a name and a baseline, with no `applications` list:

   ```yaml
   # override file
   name: my-override
   baseline: perf-test
   # no applications, so no custom values
   ```

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `ENV_NAMES: <cluster>/<env>`
2. `GENERATE_EFFECTIVE_SET: true`

**Steps:**

1. The `generate_effective_set` job runs.
2. The calculator resolves the active side as the namespace and resolves the baseline name as `perf-test`.
3. The override carries no `applications` list, so it sets no custom values. The applications list is
   optional.
4. The calculator looks up `perf-test` among the baselines each application defines and generates the
   Effective Set.

**Results:**

1. Effective Set is generated successfully.
2. Each service that defines a `perf-test` baseline receives those baseline parameters. No custom values
   are layered on top, because the override sets none. The override is used only to select the baseline.

## Applying custom values and the baseline

The override is always applied. Baseline parameters are layered under the custom values only when a
baseline name is resolved and the application defines it for the service. These use cases show the three
possible outcomes for an individual service.

### UC-RP-AB-1: Override is always applied and custom values win over the baseline when the name matches

**Pre-requisites:**

1. An Environment Instance exists with an active side that yields a resolved baseline name (for
   example, `dev`) and a non-empty override that sets custom values.
2. At least one application in the Solution Descriptor provides a service with a
   `dev` baseline and with a matching override entry.

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `ENV_NAMES: <cluster>/<env>`
2. `GENERATE_EFFECTIVE_SET: true`

**Steps:**

1. The `generate_effective_set` job runs.
2. For the service, the calculator applies the override custom values.
3. The resolved baseline name (`dev`) is one the application defines. The baseline
   parameters the application provides for that name are applied as the base layer. Where a
   parameter appears in both the baseline and the custom values, the custom value takes precedence.
4. The merged parameter set is written to the Effective Set as per-service deployment context
   parameters.

**Results:**

1. Effective Set is generated successfully.
2. The service's deployment context includes all custom values plus any baseline parameters not
   overridden. The custom value wins on any conflicting key.

### UC-RP-AB-2: Service with no baselines receives the custom values only

**Pre-requisites:**

1. An Environment Instance exists with a resolved baseline name and an override that sets custom values.
2. At least one application in the Solution Descriptor provides a service that defines no
   resource profile baselines.

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `ENV_NAMES: <cluster>/<env>`
2. `GENERATE_EFFECTIVE_SET: true`

**Steps:**

1. The `generate_effective_set` job runs.
2. For the service, the calculator applies the override custom values.
3. The application defines no resource profile baselines for the service. No baseline lookup is performed.
4. The custom values alone are written to the Effective Set.

**Results:**

1. Effective Set is generated successfully.
2. The service's deployment context includes only the custom values. No warning is emitted because the
   service ships no baselines at all.

### UC-RP-AB-3: Baseline name mismatch on a service that has baselines emits a warning

**Pre-requisites:**

1. An Environment Instance exists with a resolved baseline name (for example, `perf-test`) and an
   override.
2. At least one application in the Solution Descriptor provides a service that defines one
   or more baselines, but none of them is named `perf-test`.

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `ENV_NAMES: <cluster>/<env>`
2. `GENERATE_EFFECTIVE_SET: true`

**Steps:**

1. The `generate_effective_set` job runs.
2. The calculator resolves the baseline name as `perf-test`.
3. The affected service defines baselines, but none is named `perf-test`.
4. The calculator emits a warning that names the service and the resolved baseline name, then
   applies the custom values with no baseline layer for that service and continues generation.

**Results:**

1. Effective Set is generated successfully.
2. The pipeline log contains a warning identifying the service name and the baseline name that
   was not found (`perf-test`).
3. The service's deployment context includes the custom values only, with no baseline
   parameters layered under them.

### UC-RP-AB-4: Override with custom values and no baseline emits a warning

An override is expected to carry a baseline that its custom values sit on top of. When an override sets
custom values but declares no baseline, and no baseline is resolved from the object either, EnvGene keeps
generating but emits a warning, because custom values are then applied with no baseline underneath them.

**Pre-requisites:**

1. An Environment Instance exists with an active side whose override sets custom values but declares no
   `baseline` field.
2. The object on the active side also carries no baseline, so no baseline name is resolved from either
   source.

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `ENV_NAMES: <cluster>/<env>`
2. `GENERATE_EFFECTIVE_SET: true`

**Steps:**

1. The `generate_effective_set` job runs.
2. Baseline resolution finds no baseline name on either the override or the object.
3. EnvGene emits a warning that the override sets custom values without a baseline, then applies the custom
   values with no baseline layer and continues generation.

**Results:**

1. Effective Set is generated successfully. Generation is not stopped.
2. The pipeline log contains a warning that the override sets custom values without a baseline.
3. Each service's deployment context includes the custom values only. No baseline parameters are included.

## Environment-specific override

An environment-specific override is an override defined in the Instance repository that may or may not
have a corresponding template override referenced on the Cloud or Namespace object. When both are present,
merge mode adds custom values on the same baseline, and replace mode changes the baseline for the
environment. Merging a different baseline is the warned wrong path. These use cases cover the standalone
scenario, the warned merge case, and the correct way to change the baseline.

### UC-RP-ES-1: Standalone environment-specific override with no template override

**Pre-requisites:**

1. An Environment Instance exists with a Namespace that has no `profile.name` on its object (no
   template override reference is set).
2. An environment-specific override is referenced in the
   `envTemplate.envSpecificResourceProfiles` section of the Environment Inventory for that namespace:

   ```yaml
   envTemplate:
     envSpecificResourceProfiles:
       <namespace-folder-name>: my-env-specific-override
   ```

3. The corresponding override file is present in the Instance repository search path.

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `ENV_NAMES: <cluster>/<env>`
2. `ENV_BUILDER: true`
3. `GENERATE_EFFECTIVE_SET: true`

**Steps:**

1. The `env_build` job runs.
2. EnvGene finds an environment-specific override for the namespace but no template `profile.name`
   to match it against. Instead of raising an error, EnvGene attaches the override to the namespace
   object directly, setting a profile name on the namespace object to record the attachment.
3. The combined override is written to the Environment Instance.
4. The `generate_effective_set` job runs.
5. The namespace now has an override, so it is the active side.
6. The calculator resolves the baseline and applies the override from the namespace side and generates the
   Effective Set.

**Results:**

1. Environment generation and Effective Set generation both complete successfully.
2. The namespace's override is derived from the environment-specific file alone. No template override is
   required.

### UC-RP-ES-2: Merge mode with a different baseline is the warned wrong path

Merge mode is meant for adding custom values on the same baseline. When the template override carries
custom values and the environment-specific override declares a baseline that differs from the template
override's baseline, EnvGene keeps generating but emits a warning, because parameters bound to one baseline
are then carried onto a different one. To change the baseline for an environment, use replace mode instead
(see UC-RP-ES-3).

**Pre-requisites:**

1. An Environment Instance exists with a Namespace that has a template override with `baseline: dev` and
   custom values at the top level.
2. An environment-specific override is also present for the namespace, with `baseline: perf-test` at the
   top level.
3. The `inventory.config.mergeEnvSpecificResourceProfiles` setting is `true` (merge mode, which is
   the default):

   ```yaml
   inventory:
     config:
       mergeEnvSpecificResourceProfiles: true
   ```

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `ENV_NAMES: <cluster>/<env>`
2. `ENV_BUILDER: true`
3. `GENERATE_EFFECTIVE_SET: true`

**Steps:**

1. The `env_build` job runs.
2. EnvGene merges the template override and the environment-specific override. The result includes their
   applications, services, and custom values. The environment-specific value wins on any conflicting leaf.
3. The environment-specific `baseline` field (`perf-test`) differs from the template `baseline` (`dev`),
   and the template override carries custom values. EnvGene emits a warning that the merge carries custom
   values bound to `dev` onto the `perf-test` baseline, and continues.
4. The environment-specific `baseline` (`perf-test`) is present in the merge result. The template
   `baseline` (`dev`) is not used.
5. The merged override is written to the Environment Instance.
6. The `generate_effective_set` job runs.
7. The calculator resolves the baseline name from the merged override as `perf-test` and generates
   the Effective Set.

**Results:**

1. Environment generation and Effective Set generation both complete successfully. Generation is not
   stopped.
2. The pipeline log contains a warning that a different baseline was merged while the template override
   carries custom values, so those custom values bound to `dev` are carried onto the `perf-test` baseline.
3. The merged override carries `baseline: perf-test`. Services are evaluated against the `perf-test`
   baseline, not `dev`.

### UC-RP-ES-3: Replace mode changes the baseline for the environment

Changing the baseline for an environment is done with replace mode. Replace drops the template override, so
custom values bound to the old baseline are not carried onto the new one. This is the correct alternative to
the warned merge case in UC-RP-ES-2.

**Pre-requisites:**

1. An Environment Instance exists with a Namespace that has a template override with `baseline: dev` and
   custom values at the top level.
2. An environment-specific override is also present for the namespace, with `baseline: perf-test` at the
   top level. It may set only a baseline or may also set custom values.
3. The `inventory.config.mergeEnvSpecificResourceProfiles` setting is `false` (replace mode):

   ```yaml
   inventory:
     config:
       mergeEnvSpecificResourceProfiles: false
   ```

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `ENV_NAMES: <cluster>/<env>`
2. `ENV_BUILDER: true`
3. `GENERATE_EFFECTIVE_SET: true`

**Steps:**

1. The `env_build` job runs.
2. Replace mode drops the template override. The environment-specific override becomes the resulting
   override for the namespace on its own.
3. The resulting override carries `baseline: perf-test`. The template `baseline` (`dev`) and its custom
   values are not carried forward.
4. The resulting override is written to the Environment Instance.
5. The `generate_effective_set` job runs.
6. The calculator resolves the baseline name as `perf-test` and generates the Effective Set. No warning is
   emitted, because no custom values bound to `dev` are carried onto `perf-test`.

**Results:**

1. Environment generation and Effective Set generation both complete successfully.
2. Services are evaluated against the `perf-test` baseline. Only the custom values from the
   environment-specific override are layered on top. The template override's custom values bound to `dev`
   are gone.

### UC-RP-ES-4: Merge mode with the same baseline combines both overrides

Merge mode is meant for adding custom values on the same baseline. When the template override and the
environment-specific override declare the same baseline, their custom values combine and no warning is
emitted. This is the intended merge path.

**Pre-requisites:**

1. An Environment Instance exists with a Namespace that has a template override with `baseline: dev` and
   custom values at the top level.
2. An environment-specific override is also present for the namespace, with the same `baseline: dev` at the
   top level. It sets additional custom values and some custom values that overlap the template override.
3. The `inventory.config.mergeEnvSpecificResourceProfiles` setting is `true` (merge mode, which is the
   default):

   ```yaml
   inventory:
     config:
       mergeEnvSpecificResourceProfiles: true
   ```

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `ENV_NAMES: <cluster>/<env>`
2. `ENV_BUILDER: true`
3. `GENERATE_EFFECTIVE_SET: true`

**Steps:**

1. The `env_build` job runs.
2. EnvGene merges the template override and the environment-specific override into a name-keyed union across
   the application, service, and parameter levels. Custom values present on only one side are kept. Where a
   custom value appears on both sides, the environment-specific value wins.
3. Both overrides declare the same baseline (`dev`), so no warning is emitted. The merged override keeps the
   template override's name and carries `baseline: dev`.
4. The merged override is written to the Environment Instance.
5. The `generate_effective_set` job runs.
6. The calculator resolves the baseline name from the merged override as `dev` and generates the Effective
   Set.

**Results:**

1. Environment generation and Effective Set generation both complete successfully. No warning is emitted,
   because both baselines match.
2. Each service's deployment context shows the template-only custom values preserved, the
   environment-specific-only custom values added, and the overlapping custom values carrying the
   environment-specific value.
3. The `dev` baseline parameters underlie each service where nothing overrides them. The merged override
   keeps the template override's name.

## Referenced override file resolution

An override applies only when a name references it, and that referenced name is resolved to a file by
searching a fixed scope order. This group covers how a referenced name finds its file when files of the same
name exist at more than one scope.

### UC-RP-LR-1: A referenced override name resolves to the most specific scope

**Pre-requisites:**

1. An Environment Instance exists with an environment that references an override by name through
   `envTemplate.envSpecificResourceProfiles` in the Environment Inventory:

   ```yaml
   envTemplate:
     envSpecificResourceProfiles:
       <namespace-folder-name>: shared-override
   ```

2. An override file named `shared-override` exists at more than one scope, for example one in the
   environment folder and one at the cluster scope.

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `ENV_NAMES: <cluster>/<env>`
2. `ENV_BUILDER: true`
3. `GENERATE_EFFECTIVE_SET: true`

**Steps:**

1. The `env_build` job runs.
2. EnvGene resolves the referenced name `shared-override` to a file by searching the environment scope
   first, then the cluster scope, then the global scope, and takes the first match.
3. The file found at the environment scope is the one used. The cluster-scope file of the same name is not
   used.

**Results:**

1. Environment generation completes successfully using the environment-scope override file.
2. When no environment-scope file of that name exists, the cluster-scope file is used instead, and when no
   cluster-scope file exists either, the global-scope file is used. The most specific scope always wins.
3. A single override file placed at the cluster or global scope serves every environment that references
   the name. An override file that no name references is not used.
