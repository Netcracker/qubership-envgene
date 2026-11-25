# Deployment profile use cases

- [Deployment profile use cases](#deployment-profile-use-cases)
  - [Overview](#overview)
  - [Baseline through the Effective Set](#baseline-through-the-effective-set)
    - [UC-DP-ES-1: A run with PROFILE applies its baseline through the Effective Set](#uc-dp-es-1-a-run-with-profile-applies-its-baseline-through-the-effective-set)
    - [UC-DP-ES-2: The values of the environment override win over PROFILE](#uc-dp-es-2-the-values-of-the-environment-override-win-over-profile)
    - [UC-DP-ES-3: PROFILE wins over the baseline an application has in the environment override](#uc-dp-es-3-profile-wins-over-the-baseline-an-application-has-in-the-environment-override)
    - [UC-DP-EM-1: PROFILE changes the baseline and keeps the values of the environment override](#uc-dp-em-1-profile-changes-the-baseline-and-keeps-the-values-of-the-environment-override)
  - [Active side selection](#active-side-selection)
    - [UC-DP-AS-1: The generated profile makes a Namespace without a profile the active side over the Cloud](#uc-dp-as-1-the-generated-profile-makes-a-namespace-without-a-profile-the-active-side-over-the-cloud)
  - [Merge and replace modes](#merge-and-replace-modes)
    - [UC-DP-RP-1: Replace mode leaves the generated profile as the only override of the Namespace](#uc-dp-rp-1-replace-mode-leaves-the-generated-profile-as-the-only-override-of-the-namespace)
    - [UC-DP-RP-2: Merge mode keeps the template override and changes only the baseline](#uc-dp-rp-2-merge-mode-keeps-the-template-override-and-changes-only-the-baseline)
    - [UC-DP-RP-3: Replace mode drops the template override and keeps the values of the environment override](#uc-dp-rp-3-replace-mode-drops-the-template-override-and-keeps-the-values-of-the-environment-override)
  - [A baseline the application does not have](#a-baseline-the-application-does-not-have)
    - [UC-DP-NB-1: A baseline the deployed application does not have layers nothing under its services](#uc-dp-nb-1-a-baseline-the-deployed-application-does-not-have-layers-nothing-under-its-services)
  - [Namespace selection](#namespace-selection)
    - [UC-DP-NS-1: Only the namespaces the run deploys get the PROFILE override](#uc-dp-ns-1-only-the-namespaces-the-run-deploys-get-the-profile-override)
    - [UC-DP-PF-1: One run with PROFILE writes one override per deployPostfix](#uc-dp-pf-1-one-run-with-profile-writes-one-override-per-deploypostfix)
  - [Runs that follow a run with PROFILE](#runs-that-follow-a-run-with-profile)
    - [UC-DP-AC-1: A run keeps the applications of the earlier runs and rewrites only its own](#uc-dp-ac-1-a-run-keeps-the-applications-of-the-earlier-runs-and-rewrites-only-its-own)
    - [UC-DP-AC-2: A rerun with the same PROFILE names its application once](#uc-dp-ac-2-a-rerun-with-the-same-profile-names-its-application-once)
    - [UC-DP-AC-3: A key that already names the generated override is not written again](#uc-dp-ac-3-a-key-that-already-names-the-generated-override-is-not-written-again)
  - [Blue-Green pair](#blue-green-pair)
    - [UC-DP-BG-1: Only the Blue-Green side the run deploys gets a key of its own](#uc-dp-bg-1-only-the-blue-green-side-the-run-deploys-gets-a-key-of-its-own)
    - [UC-DP-BG-2: The run of the other side adds its key and rewrites the shared override](#uc-dp-bg-2-the-run-of-the-other-side-adds-its-key-and-rewrites-the-shared-override)
  - [The reserved name and the marker](#the-reserved-name-and-the-marker)
    - [UC-DP-RS-1: An author entry that names the generated override is ignored](#uc-dp-rs-1-an-author-entry-that-names-the-generated-override-is-ignored)
    - [UC-DP-HD-1: The generated override says that EnvGene wrote it](#uc-dp-hd-1-the-generated-override-says-that-envgene-wrote-it)
  - [Runs that skip PROFILE](#runs-that-skip-profile)
    - [UC-DP-SKIP-1: A run that deploys no application skips PROFILE](#uc-dp-skip-1-a-run-that-deploys-no-application-skips-profile)
    - [UC-DP-SKIP-2: A CLEAN run skips PROFILE](#uc-dp-skip-2-a-clean-run-skips-profile)

## Overview

This document covers use cases for the `PROFILE` pipeline parameter, the baseline a single run applies to the
applications it deploys. The parameter is one of the ways to choose a baseline, next to the baseline an author sets
on a Namespace object and the baseline an override carries. For the resolution model itself, see
[Resource Profiles](/docs/features/resource-profile.md) and its
[use cases](/docs/use-cases/resource-profiles.md).

A run with `PROFILE` does not edit the authored configuration. The `env_build` job writes an override of its own,
`Inventory/resource_profiles/<deployPostfix>-profile-override.yml`, and records it in
`envTemplate.generatedProfileDefaults` of `Inventory/env_definition.yml`, keyed by the folder name of each Namespace
the run rendered. That generated override is the last layer of the Namespace profile, so its baseline is what the
applications the run deploys get, while the custom values an author set in another override stay.

`PROFILE` has an effect only in a run that deploys: the parameter is set, the operation is a deploy, and the
environment build runs. Any other run keeps the parameter unused and says so in its log.

The generated override and its entries are maintained by EnvGene. The suffix `-profile-override` is reserved for it,
and a file of that name that EnvGene did not generate is replaced with a warning.

## Baseline through the Effective Set

The generated override reaches the applications through the Effective Set: `env_build` writes the baseline into the
profile layer of the Namespace, and the calculator resolves the parameters of every service of every application the
run deploys against it. These use cases show what the run changes in the Effective Set and what an author's override
keeps over it.

### UC-DP-ES-1: A run with PROFILE applies its baseline through the Effective Set

**Pre-requisites:**

1. An Environment Instance whose Namespace has no resource profile of its own:

   ```yaml
   # Namespaces/bss/namespace.yml
   # no profile attribute
   ```

2. A deployment plan that names an application whose services provide the baseline `prod`.

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `ENV_NAMES: <cluster>/<env>`
2. `OPERATION_TYPE: DEPLOY`
3. `SD_DATA` or `SD_VERSION` that deploys the application to the Namespace above
4. `PROFILE: prod`
5. `GENERATE_EFFECTIVE_SET: true`

**Steps:**

1. The `env_build` job renders the Environment Instance and writes the generated override for the deployPostfix the
   plan names.
2. The same job records the generated override in `envTemplate.generatedProfileDefaults` and assembles the profile of
   the Namespace from it.
3. The `generate_effective_set` job resolves the parameters of the deployed application.

**Results:**

1. `Inventory/resource_profiles/bss-profile-override.yml` exists, named after the deployPostfix, and names the
   deployed application with `baseline: prod`.
2. `Inventory/env_definition.yml` has `envTemplate.generatedProfileDefaults.bss: bss-profile-override`.
3. `Namespaces/bss/namespace.yml` has `profile.name: bss-profile-override`, because the Namespace had no profile of
   its own.
4. The Effective Set of the deployed application carries the values of the `prod` baseline, for example
   `BASELINE_MEMORY: prod-mem` and `REPLICAS: 2`.

### UC-DP-ES-2: The values of the environment override win over PROFILE

**Pre-requisites:**

1. A Namespace whose environment-specific override sets custom values for a service of an application and names no
   baseline for it:

   ```yaml
   # Inventory/resource_profiles/bss-tuning.yml
   name: bss-tuning
   applications:
     - name: app1
       services:
         - name: svc1
           parameters:
             - name: REPLICAS
               value: 9
   ```

2. `Inventory/env_definition.yml` references it: `envTemplate.envSpecificResourceProfiles.bss: bss-tuning`.

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `ENV_NAMES: <cluster>/<env>`
2. `OPERATION_TYPE: DEPLOY`
3. `SD_DATA` or `SD_VERSION` that deploys `app1` to that Namespace
4. `PROFILE: prod`
5. `GENERATE_EFFECTIVE_SET: true`

**Steps:**

1. The `env_build` job writes the generated override and merges it into the profile of the Namespace as its last
   layer.
2. The `generate_effective_set` job resolves the parameters of `app1`.

**Results:**

1. `envTemplate.envSpecificResourceProfiles.bss` still reads `bss-tuning`, and
   `envTemplate.generatedProfileDefaults.bss` names the generated override.
2. `Namespaces/bss/namespace.yml` still has `profile.name: bss-tuning`, because a Namespace that owns a profile keeps
   its name in the merge mode.
3. The Effective Set of `app1` has `REPLICAS: 9` from the custom value of `bss-tuning` and the values of the `prod`
   baseline, so `BASELINE_MEMORY: prod-mem`.
4. No profile named `bss-profile-override` is assembled into `Profiles/`, because the generated override was merged
   into the profile of the Namespace instead of becoming a profile of its own.

### UC-DP-ES-3: PROFILE wins over the baseline an application has in the environment override

**Pre-requisites:**

1. A Namespace whose environment-specific override names the baseline `dev` for an application:

   ```yaml
   # Inventory/resource_profiles/bss-dev-baseline.yml
   name: bss-dev-baseline
   applications:
     - name: app1
       baseline: dev
       services: []
   ```

2. `Inventory/env_definition.yml` references it: `envTemplate.envSpecificResourceProfiles.bss: bss-dev-baseline`.

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters identical to those of
[UC-DP-ES-2](#uc-dp-es-2-the-values-of-the-environment-override-win-over-profile), with `PROFILE: prod`.

**Steps:**

1. The `env_build` job merges the generated override into the profile of the Namespace after the author's override,
   so the baseline of `app1` is written again, this time as `prod`.
2. The `generate_effective_set` job resolves the parameters of `app1`.

**Results:**

1. `Namespaces/bss/namespace.yml` has `profile.name: bss-dev-baseline`.
2. The Effective Set of `app1` carries the values of the `prod` baseline, not those of `dev`.

### UC-DP-EM-1: PROFILE changes the baseline and keeps the values of the environment override

**Pre-requisites:**

1. A Namespace whose template carries a resource profile with custom values, and whose environment-specific override
   sets other custom values for the same service with the same baseline:

   ```yaml
   # resource_profiles/core-tmpl.yml.j2 of the Environment Template
   name: core-tmpl
   baseline: dev
   applications:
     - name: app1
       services:
         - name: svc1
           parameters:
             - name: TEMPLATE_PARAM
               value: from-template
             - name: REPLICAS
               value: 3
   ```

   ```yaml
   # Inventory/resource_profiles/core-tuning.yml of the Instance repository
   name: core-tuning
   baseline: dev
   applications:
     - name: app1
       services:
         - name: svc1
           parameters:
             - name: REPLICAS
               value: 7
   ```

2. `Inventory/env_definition.yml` references the environment-specific override:
   `envTemplate.envSpecificResourceProfiles.core: core-tuning`.
3. `inventory.config.mergeEnvSpecificResourceProfiles` is unset or `true`.

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters identical to those of
[UC-DP-ES-2](#uc-dp-es-2-the-values-of-the-environment-override-win-over-profile), deploying to the Namespace above.

**Steps:**

1. The `env_build` job joins the environment-specific override into the profile of the Namespace, then merges the
   generated override as its last layer.
2. The `generate_effective_set` job resolves the parameters of `app1`.

**Results:**

1. `envTemplate.envSpecificResourceProfiles.core` still reads `core-tuning` and
   `envTemplate.generatedProfileDefaults.core` names `core-profile-override`.
2. `Namespaces/core/namespace.yml` has `profile.name: core-tmpl` and `profile.baseline: dev`, the name and the
   baseline of the profile the Namespace already owned.
3. The Effective Set of `app1` has `REPLICAS: 7` from the environment-specific override, `TEMPLATE_PARAM` from the
   template override, and the values of the `prod` baseline that `PROFILE` set.
4. No profile named `core-profile-override` appears in `Profiles/`, because both overrides were merged into the
   profile of the Namespace.

## Active side selection

The calculator resolves the profile of a Namespace from the Namespace or from the Cloud, never from both. A Namespace
with no resource profile of its own normally leaves the Cloud as the active side. A run with `PROFILE` gives such a
Namespace a profile of its own, which moves the active side to the Namespace for every application of that Namespace,
not only for the application the run deploys.

### UC-DP-AS-1: The generated profile makes a Namespace without a profile the active side over the Cloud

**Pre-requisites:**

1. A Namespace whose template carries no resource profile, as in
   [UC-DP-ES-1](#uc-dp-es-1-a-run-with-profile-applies-its-baseline-through-the-effective-set).
2. The Cloud has an environment-specific override with custom values:

   ```yaml
   # Inventory/resource_profiles/cloud-env-over.yml
   name: cloud-env-over
   baseline: prod
   applications:
     - name: app1
       services:
         - name: svc1
           parameters:
             - name: REPLICAS
               value: 5
             - name: CLOUD_PARAM
               value: from-cloud
   ```

3. `Inventory/env_definition.yml` references it: `envTemplate.envSpecificResourceProfiles.cloud: cloud-env-over`.
   Without `PROFILE` this configuration makes the Cloud the active side, which is
   [UC-RP-SS-3](/docs/use-cases/resource-profiles.md#uc-rp-ss-3-cloud-is-the-active-side-when-the-namespace-has-no-baseline-or-override).

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters identical to those of
[UC-DP-ES-1](#uc-dp-es-1-a-run-with-profile-applies-its-baseline-through-the-effective-set), with `PROFILE: prod`.

**Steps:**

1. The `env_build` job writes the generated override and assembles the profile of the Namespace from it, because the
   Namespace has no profile of its own.
2. The same job sets `profile.name` of the Namespace object to the assembled profile and leaves the Cloud object
   untouched.
3. The `generate_effective_set` job sees a Namespace with a profile and stops consulting the Cloud.

**Results:**

1. `Inventory/resource_profiles/bss-profile-override.yml` exists with `baseline: prod` for the deployed application,
   and `envTemplate.generatedProfileDefaults.bss` names it.
2. `Namespaces/bss/namespace.yml` has `profile.name: bss-profile-override` and no `profile.baseline`, because neither
   the Namespace nor the generated override sets a baseline of the profile itself.
3. `cloud.yml` keeps `profile: {name: cloud-env-over, baseline: prod}`.
4. The Effective Set of the deployed application is resolved on the Namespace side, so it has the values of the `prod`
   baseline, `BASELINE_MEMORY: prod-mem` and `REPLICAS: 2`, and it has neither `CLOUD_PARAM` nor the `REPLICAS: 5` of
   the Cloud override.
5. The other applications of the Namespace also lose the Cloud override, because the active side is chosen per
   Namespace. This is the intended consequence of giving the Namespace a profile of its own.

## Merge and replace modes

`inventory.config.mergeEnvSpecificResourceProfiles` decides whether an override survives the run. These use cases run
the same deploy with `PROFILE` against a Namespace that owns a template override, once in each mode, and once with an
environment-specific override as well.

### UC-DP-RP-1: Replace mode leaves the generated profile as the only override of the Namespace

**Pre-requisites:**

1. A Namespace whose template carries a resource profile with custom values and the baseline `dev`, as in
   [UC-DP-EM-1](#uc-dp-em-1-profile-changes-the-baseline-and-keeps-the-values-of-the-environment-override).
2. `Inventory/env_definition.yml` sets `inventory.config.mergeEnvSpecificResourceProfiles: false`.

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters identical to those of
[UC-DP-ES-1](#uc-dp-es-1-a-run-with-profile-applies-its-baseline-through-the-effective-set), deploying to the
Namespace above, with `PROFILE: prod`.

**Steps:**

1. The `env_build` job drops the template override of the Namespace, because the mode replaces instead of joining.
2. The same job assembles the profile of the Namespace from the generated override and names it after the generated
   override.
3. The `generate_effective_set` job resolves the parameters of the deployed application.

**Results:**

1. `Inventory/resource_profiles/core-profile-override.yml` exists with `baseline: prod`, and
   `envTemplate.generatedProfileDefaults.core` names it.
2. `Profiles/core-profile-override.yml` is the assembled profile, and `Namespaces/core/namespace.yml` has
   `profile.name: core-profile-override` with `profile.baseline: dev`, the baseline the Namespace object carries.
3. The profile of the template is not in `Profiles/`.
4. The Effective Set of the deployed application has the values of the `prod` baseline, `REPLICAS: 2`, and none of the
   custom values of the template override, so `TEMPLATE_PARAM` is absent.

### UC-DP-RP-2: Merge mode keeps the template override and changes only the baseline

**Pre-requisites:**

1. The same Namespace as in [UC-DP-RP-1](#uc-dp-rp-1-replace-mode-leaves-the-generated-profile-as-the-only-override-of-the-namespace),
   with `inventory.config.mergeEnvSpecificResourceProfiles` unset or `true`.

**Trigger:**

Identical to [UC-DP-RP-1](#uc-dp-rp-1-replace-mode-leaves-the-generated-profile-as-the-only-override-of-the-namespace).

**Steps:**

1. The `env_build` job merges the generated override into the profile of the Namespace, which keeps its own name.
2. The `generate_effective_set` job resolves the parameters of the deployed application.

**Results:**

1. `Inventory/resource_profiles/core-profile-override.yml` exists with `baseline: prod`, and
   `envTemplate.generatedProfileDefaults.core` names it.
2. `Namespaces/core/namespace.yml` still has `profile.name: core-tmpl` and `profile.baseline: dev`, and no profile
   named `core-profile-override` is assembled into `Profiles/`.
3. The Effective Set of the deployed application keeps the custom values of the template override, `TEMPLATE_PARAM`
   and `REPLICAS: 3`, and takes the values of the `prod` baseline that `PROFILE` set.

### UC-DP-RP-3: Replace mode drops the template override and keeps the values of the environment override

**Pre-requisites:**

1. The Namespace of [UC-DP-EM-1](#uc-dp-em-1-profile-changes-the-baseline-and-keeps-the-values-of-the-environment-override),
   which carries both a template override and an environment-specific override.
2. `Inventory/env_definition.yml` sets `inventory.config.mergeEnvSpecificResourceProfiles: false`.

**Trigger:**

Identical to [UC-DP-RP-1](#uc-dp-rp-1-replace-mode-leaves-the-generated-profile-as-the-only-override-of-the-namespace).

**Steps:**

1. The `env_build` job drops the template override and takes the environment-specific override as the base of the
   Namespace profile.
2. The same job merges the generated override on top of that base and names the assembled profile after the generated
   override.
3. The `generate_effective_set` job resolves the parameters of the deployed application.

**Results:**

1. `Inventory/resource_profiles/core-profile-override.yml` exists with `baseline: prod`,
   `envTemplate.generatedProfileDefaults.core` names it, and `envTemplate.envSpecificResourceProfiles.core` still
   reads `core-tuning`.
2. `Profiles/core-profile-override.yml` is the assembled profile and `Namespaces/core/namespace.yml` has
   `profile.name: core-profile-override` with `profile.baseline: dev`.
3. The profile of the template is not in `Profiles/`.
4. The Effective Set of the deployed application has `REPLICAS: 7` from the environment-specific override and the
   values of the `prod` baseline, and it has no `TEMPLATE_PARAM`, because that value came from the template override.

## A baseline the application does not have

`PROFILE` names a baseline for every application the run deploys, whether or not the application provides it. EnvGene
does not check the name against the application, because the baselines an application provides are published by its
SBOM, which the effective-set stage generates after the environment build.

### UC-DP-NB-1: A baseline the deployed application does not have layers nothing under its services

**Pre-requisites:**

1. A Namespace that owns a resource profile whose custom values apply to a service of the deployed application.
2. That service provides the baselines `dev` and `prod` and no baseline named `perf-test`.

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters identical to those of
[UC-DP-RP-2](#uc-dp-rp-2-merge-mode-keeps-the-template-override-and-changes-only-the-baseline), with
`PROFILE: perf-test`.

**Steps:**

1. The `env_build` job writes the generated override with `baseline: perf-test` for the deployed application and
   merges it into the profile of the Namespace.
2. The `generate_effective_set` job finds no `perf-test` baseline for the service, warns, and resolves the service
   from the baseline of the profile instead.

**Results:**

1. `Inventory/resource_profiles/core-profile-override.yml` names the deployed application with `baseline: perf-test`.
2. The Effective Set of the application keeps the custom values of the profile, `TEMPLATE_PARAM` and `REPLICAS: 3`.
3. The service keeps the baseline of the profile it owns, so `BASELINE_MEMORY` stays `dev-mem`, and the missing
   `perf-test` baseline adds no parameter of its own.
4. The pipeline does not fail.

## Namespace selection

A run with `PROFILE` writes an override per deployPostfix it deploys to, and keys it by the folder of the Namespace it
rendered. Namespaces the plan does not touch are left as they are.

### UC-DP-NS-1: Only the namespaces the run deploys get the PROFILE override

**Pre-requisites:**

1. An Environment Instance with two Namespaces: `bss` with no resource profile of its own, and `core` with the
   template profile `core-tmpl` of baseline `dev`.

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `ENV_NAMES: <cluster>/<env>`
2. `OPERATION_TYPE: DEPLOY`
3. `SD_DATA` or `SD_VERSION` that deploys an application with deployPostfix `bss`
4. `PROFILE: prod`

**Steps:**

1. The `env_build` job writes the generated override for the deployPostfix `bss` and records one entry in
   `envTemplate.generatedProfileDefaults`.

**Results:**

1. `envTemplate.generatedProfileDefaults` has the key `bss` and no key `core`.
2. `Namespaces/core/namespace.yml` still carries its own `core-tmpl` profile with baseline `dev`, and no override of
   `core` is written.

### UC-DP-PF-1: One run with PROFILE writes one override per deployPostfix

**Pre-requisites:**

1. An Environment Instance with two Namespaces, whose templates carry the deployPostfixes `bss` and `core`.
2. A Solution Descriptor that deploys one application to both deployPostfixes.

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `ENV_NAMES: <cluster>/<env>`
2. `OPERATION_TYPE: DEPLOY`
3. `SD_DATA` or `SD_VERSION` that deploys `app1` with deployPostfix `bss` and with deployPostfix `core`
4. `PROFILE: prod`

**Steps:**

1. The `env_build` job groups the deployed applications by deployPostfix and writes one generated override per
   deployPostfix.
2. The same job records one key per rendered Namespace folder.

**Results:**

1. `Inventory/resource_profiles/bss-profile-override.yml` and `Inventory/resource_profiles/core-profile-override.yml`
   both exist, each naming `app1` with `baseline: prod`.
2. `envTemplate.generatedProfileDefaults` has `bss: bss-profile-override` and `core: core-profile-override`.

## Runs that follow a run with PROFILE

The generated override is committed to the Instance repository, so the next run reads it and rewrites only the
baseline of the applications it deploys. The applications of the earlier runs keep theirs.

### UC-DP-AC-1: A run keeps the applications of the earlier runs and rewrites only its own

**Pre-requisites:**

1. A committed generated override of an earlier run:

   ```yaml
   # Inventory/resource_profiles/bss-profile-override.yml
   # Generated by EnvGene from the PROFILE pipeline parameter.
   name: bss-profile-override
   applications:
     - name: app3
       baseline: prod
       services: []
   ```

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `ENV_NAMES: <cluster>/<env>`
2. `OPERATION_TYPE: DEPLOY`
3. `SD_DATA` or `SD_VERSION` that deploys `app1` to the same deployPostfix
4. `PROFILE: dev`

**Steps:**

1. The `env_build` job reads the committed override, updates the entry of `app1` and keeps the entries it does not
   deploy.

**Results:**

1. `Inventory/resource_profiles/bss-profile-override.yml` names `app1` with `baseline: dev` and still names `app3`
   with `baseline: prod`.
2. `envTemplate.generatedProfileDefaults.bss` still names `bss-profile-override`.
3. The run reports no warning about a hand-written override, because the file carries the marker of EnvGene.

### UC-DP-AC-2: A rerun with the same PROFILE names its application once

**Pre-requisites:**

1. A committed generated override that already names the application the run deploys, with the same baseline the run
   sets:

   ```yaml
   # Inventory/resource_profiles/bss-profile-override.yml
   # Generated by EnvGene from the PROFILE pipeline parameter.
   name: bss-profile-override
   applications:
     - name: app1
       baseline: prod
       services: []
   ```

**Trigger:**

Identical to [UC-DP-AC-1](#uc-dp-ac-1-a-run-keeps-the-applications-of-the-earlier-runs-and-rewrites-only-its-own),
with `PROFILE: prod`.

**Results:**

1. `Inventory/resource_profiles/bss-profile-override.yml` names `app1` once, with `baseline: prod`.
2. `envTemplate.generatedProfileDefaults.bss` still names `bss-profile-override`, and the run reports no warning
   about the override it rewrites.

### UC-DP-AC-3: A key that already names the generated override is not written again

**Pre-requisites:**

1. A committed `Inventory/env_definition.yml` whose map already carries the entry:

   ```yaml
   # envTemplate section of Inventory/env_definition.yml
   generatedProfileDefaults:
     # Generated by EnvGene from the PROFILE pipeline parameter, do not edit.
     bss: bss-profile-override
   ```

2. The committed `Inventory/resource_profiles/bss-profile-override.yml` of that earlier run.

**Trigger:**

Identical to [UC-DP-AC-2](#uc-dp-ac-2-a-rerun-with-the-same-profile-names-its-application-once).

**Steps:**

1. The `env_build` job rewrites the override of the deployPostfix and finds that the key of the Namespace already
   names it, so it writes no entry.

**Results:**

1. `envTemplate.generatedProfileDefaults.bss` still reads `bss-profile-override`, and the entry carries the same
   comment EnvGene writes.
2. The override names `app1` once, with `baseline: prod`.
3. The log states that every deployed Namespace already references its override.

## Blue-Green pair

The two sides of a Blue-Green pair share one deployPostfix, so one generated override serves both of them, while each
side gets a key of its own in the recorded map.

### UC-DP-BG-1: Only the Blue-Green side the run deploys gets a key of its own

**Pre-requisites:**

1. An Environment Instance with a Blue-Green Domain whose pair shares the deployPostfix `bss`.

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `ENV_NAMES: <cluster>/<env>`
2. `PIPELINE_TYPE: GITLAB_DEPLOY`
3. `OPERATION_TYPE: DEPLOY`
4. `BG_NS_TARGET: ORIGIN`
5. `APPLICATION_VERSIONS` or a Solution Descriptor that deploys an application with deployPostfix `bss`
6. `PROFILE: prod`

**Steps:**

1. The `env_build` job renders the side the run deploys and writes the generated override of the shared deployPostfix.
2. The same job records the entry under the folder of that side.

**Results:**

1. `Inventory/resource_profiles/bss-profile-override.yml` exists with `baseline: prod`.
2. `envTemplate.generatedProfileDefaults` has the key `bss-origin` and no key `bss-peer`.

### UC-DP-BG-2: The run of the other side adds its key and rewrites the shared override

**Pre-requisites:**

1. The Environment Instance of [UC-DP-BG-1](#uc-dp-bg-1-only-the-blue-green-side-the-run-deploys-gets-a-key-of-its-own)
   after that run, so the committed `env_definition.yml` already has the key `bss-origin` and the committed
   `Inventory/resource_profiles/bss-profile-override.yml` names the application of that run.

**Trigger:**

Identical to [UC-DP-BG-1](#uc-dp-bg-1-only-the-blue-green-side-the-run-deploys-gets-a-key-of-its-own), with
`BG_NS_TARGET: PEER` and `PROFILE: prod2`.

**Steps:**

1. The `env_build` job rewrites the one shared override with the baseline of this run.
2. The same job adds the key of the side it rendered and keeps the key of the other side.

**Results:**

1. `Inventory/resource_profiles/bss-profile-override.yml` names the deployed application with `baseline: prod2`, and
   it is still the only generated override of the pair.
2. `envTemplate.generatedProfileDefaults` has both `bss-origin` and `bss-peer`, and both name
   `bss-profile-override`.

## The reserved name and the marker

The suffix `-profile-override` belongs to the generated override, and every file EnvGene generates says so in its own
text. These use cases take that name from an author and that text from a reader.

### UC-DP-RS-1: An author entry that names the generated override is ignored

**Pre-requisites:**

1. `Inventory/env_definition.yml` whose author list names the reserved name for a Namespace:

   ```yaml
   # envTemplate section of Inventory/env_definition.yml
   envSpecificResourceProfiles:
     bss: bss-profile-override
   ```

2. `Inventory/resource_profiles/bss-profile-override.yml` written by hand, without the marker of EnvGene.

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters identical to those of
[UC-DP-ES-1](#uc-dp-es-1-a-run-with-profile-applies-its-baseline-through-the-effective-set), with `PROFILE: prod`.

**Steps:**

1. The `env_build` job skips the entry of the author list, because the suffix is reserved.
2. The same job writes the override of the deployPostfix over the hand-written file.

**Results:**

1. The log states that the entry is ignored because the suffix is reserved.
2. The log states that the file was not generated by EnvGene and is overwritten.
3. `Inventory/resource_profiles/bss-profile-override.yml` names only `app1` with `baseline: prod`, and it opens with
   the marker of EnvGene.
4. `envTemplate.generatedProfileDefaults.bss` names `bss-profile-override`.

### UC-DP-HD-1: The generated override says that EnvGene wrote it

**Pre-requisites:**

1. A Namespace with no resource profile of its own, as in
   [UC-DP-ES-1](#uc-dp-es-1-a-run-with-profile-applies-its-baseline-through-the-effective-set).

**Trigger:**

Identical to [UC-DP-ES-1](#uc-dp-es-1-a-run-with-profile-applies-its-baseline-through-the-effective-set).

**Steps:**

1. The `env_build` job writes the generated override with a header, and records its entry in `env_definition.yml` with
   a comment.

**Results:**

1. The first line of `Inventory/resource_profiles/<deployPostfix>-profile-override.yml` is
   `# Generated by EnvGene from the PROFILE pipeline parameter.`, and the header links to the description of the
   generated override.
2. The entry EnvGene writes into `envTemplate.generatedProfileDefaults` carries the comment that says the same, so a
   reader of the file learns who maintains it.

## Runs that skip PROFILE

A run that deploys no application must not write a baseline that then sits in the committed environment definition.
Such a run leaves the generated override and the recorded map alone and warns that the parameter has no effect.

### UC-DP-SKIP-1: A run that deploys no application skips PROFILE

**Pre-requisites:**

1. No Solution Descriptor and no deployment plan that names an application.

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `ENV_NAMES: <cluster>/<env>`
2. `ENV_BUILDER: true`
3. `PROFILE: prod`

**Steps:**

1. The `env_build` job finds no deployment plan that names an application and generates no override.

**Results:**

1. No `Inventory/resource_profiles/<deployPostfix>-profile-override.yml` is written and
   `envTemplate.generatedProfileDefaults` gains no key.
2. The log states that the applications the run deploys are unknown and that no override is generated.

### UC-DP-SKIP-2: A CLEAN run skips PROFILE

**Pre-requisites:**

1. A generated override and a recorded map of an earlier deploy run, so that the result of the CLEAN run is the
   absence of a change.

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `ENV_NAMES: <cluster>/<env>`
2. `PIPELINE_TYPE: GITLAB_DEPLOY`
3. `OPERATION_TYPE: CLEAN`
4. `PROFILE: prod`

**Steps:**

1. The `env_build` job sees an operation that is not a deploy and generates no override.

**Results:**

1. No generated override is written or changed, and `envTemplate.generatedProfileDefaults` keeps the keys of the
   earlier deploy runs.
2. The log states that the run does not deploy, so the parameter has no effect.
