# Calculator CLI New Use Cases

- [Overview](#overview)
- [Deployment Context](#deployment-context)
  - [UC-ES-DEP-14: deploy_param Image Keys](#uc-es-dep-14-deploy_param-image-keys)
  - [UC-ES-DEP-15: Pipeline DEPLOYMENT_SESSION_ID in deployment-parameters](#uc-es-dep-15-pipeline-deployment_session_id-in-deployment-parameters)
  - [UC-ES-DEP-16: MANAGED_BY Default](#uc-es-dep-16-managed_by-default)
  - [UC-ES-DEP-17: Cloud, Tenant, and Application Name Mapping](#uc-es-dep-17-cloud-tenant-and-application-name-mapping)
  - [UC-ES-DEP-18: DBaaS and Vault Disabled Flags](#uc-es-dep-18-dbaas-and-vault-disabled-flags)
  - [UC-ES-DEP-19: Public and Private Gateway URLs](#uc-es-dep-19-public-and-private-gateway-urls)
  - [UC-ES-DEP-20: Collision Files for Service-Name Keys](#uc-es-dep-20-collision-files-for-service-name-keys)
  - [UC-ES-DEP-A2: Mandatory deployment-parameters Keys](#uc-es-dep-a2-mandatory-deployment-parameters-keys)
  - [UC-ES-DEP-A3: MANAGED_BY When Other Defaults Apply](#uc-es-dep-a3-managed_by-when-other-defaults-apply)
  - [UC-ES-DEP-A4: Optional URLs Omitted When Features Off](#uc-es-dep-a4-optional-urls-omitted-when-features-off)
  - [UC-ES-DEP-A6: credentials.yaml and Optional Secure Keys](#uc-es-dep-a6-credentialsyaml-and-optional-secure-keys)
  - [UC-ES-DEP-A7: Collision Exceptions](#uc-es-dep-a7-collision-exceptions)
  - [UC-ES-DEP-A8: custom-params.yaml From CLI Flag](#uc-es-dep-a8-custom-paramsyaml-from-cli-flag)
  - [UC-ES-DEP-A9: deploy-descriptor.yaml Structure and Session ID](#uc-es-dep-a9-deploy-descriptoryaml-structure-and-session-id)
  - [UC-ES-DEP-A10: SSL Bundle Copied to Secure Keys](#uc-es-dep-a10-ssl-bundle-copied-to-secure-keys)
  - [UC-ES-DEP-A11: per-service-parameters Folder Layout](#uc-es-dep-a11-per-service-parameters-folder-layout)
  - [UC-ES-DEP-A12: Resource Profile in Per-Service Output](#uc-es-dep-a12-resource-profile-in-per-service-output)
  - [UC-ES-DEP-A13: Config Service Artifacts in deploy-descriptor](#uc-es-dep-a13-config-service-artifacts-in-deploy-descriptor)
  - [UC-ES-DEP-A14: Deployment mapping.yaml Entries](#uc-es-dep-a14-deployment-mappingyaml-entries)
- [Pipeline Context](#pipeline-context)
  - [UC-ES-PIPE-1: pipeline/parameters.yaml From Cloud e2eParameters](#uc-es-pipe-1-pipelineparametersyaml-from-cloud-e2eparameters)
  - [UC-ES-PIPE-2: pipeline/credentials.yaml From Cloud e2eParameters](#uc-es-pipe-2-pipelinecredentialsyaml-from-cloud-e2eparameters)
  - [UC-ES-PIPE-3: Consumer File Names From Schema Path](#uc-es-pipe-3-consumer-file-names-from-schema-path)
  - [UC-ES-PIPE-4: Consumer Copies Root Keys From Pipeline Context](#uc-es-pipe-4-consumer-copies-root-keys-from-pipeline-context)
  - [UC-ES-PIPE-5: Consumer Uses Schema Default Only](#uc-es-pipe-5-consumer-uses-schema-default-only)
  - [UC-ES-PIPE-6: Consumer Omits Optional Schema-Only Key](#uc-es-pipe-6-consumer-omits-optional-schema-only-key)
  - [UC-ES-PIPE-7: Consumer Mandatory Key Without Value Fails](#uc-es-pipe-7-consumer-mandatory-key-without-value-fails)
- [Topology Context](#topology-context)
  - [UC-ES-TOP-1: Cluster Endpoint from Cloud Passport](#uc-es-top-1-cluster-endpoint-from-cloud-passport)
  - [UC-ES-TOP-2: Cluster Endpoint from inventory.clusterUrl](#uc-es-top-2-cluster-endpoint-from-inventoryclusterurl)
  - [UC-ES-TOP-3: Cluster Endpoint with Non-Standard Port](#uc-es-top-3-cluster-endpoint-with-non-standard-port)
  - [UC-ES-TOP-4: Cluster Endpoint with HTTP Protocol](#uc-es-top-4-cluster-endpoint-with-http-protocol)
  - [UC-ES-TOP-5: Cluster Endpoint with Non-Standard Hostname](#uc-es-top-5-cluster-endpoint-with-non-standard-hostname)
  - [UC-ES-TOP-6: Cloud Passport Overrides inventory.clusterUrl](#uc-es-top-6-cloud-passport-overrides-inventoryclusterurl)
  - [UC-ES-TOP-7: Missing Cluster Information Produces Empty Cluster Fields](#uc-es-top-7-missing-cluster-information-produces-empty-cluster-fields)
- [Runtime Context](#runtime-context)
  - [UC-ES-RUN-1: runtime/parameters.yaml from technicalConfigurationParameters](#uc-es-run-1-runtimeparametersyaml-from-technicalconfigurationparameters)
  - [UC-ES-RUN-2: runtime/credentials.yaml Includes Sensitive and Custom Runtime](#uc-es-run-2-runtimecredentialsyaml-includes-sensitive-and-custom-runtime)
  - [UC-ES-RUN-3: runtime/mapping.yaml Matches Deployment Mapping Logic](#uc-es-run-3-runtimemappingyaml-matches-deployment-mapping-logic)
- [Cleanup Context](#cleanup-context)
  - [UC-ES-CLN-1: cleanup/parameters.yaml from deployParameters](#uc-es-cln-1-cleanupparametersyaml-from-deployparameters)
  - [UC-ES-CLN-2: cleanup/credentials.yaml Includes Sensitive and Custom Runtime](#uc-es-cln-2-cleanupcredentialsyaml-includes-sensitive-and-custom-runtime)
  - [UC-ES-CLN-3: cleanup/mapping.yaml Matches Deployment Mapping Logic](#uc-es-cln-3-cleanupmappingyaml-matches-deployment-mapping-logic)
- [Validation Summary](#validation-summary)

## Overview

This document defines test-oriented use cases for Effective Set v2.0 outputs under deployment (`deployment-parameters.yaml`, credentials, collision files, `custom-params.yaml`, `deploy-descriptor.yaml`, `per-service-parameters`, deployment `mapping.yaml`), pipeline (`pipeline/parameters.yaml`, `pipeline/credentials.yaml`, optional `<consumer>-*.yaml` pairs derived from consumer JSON schemas), topology (`topology/parameters.yaml`, `topology/credentials.yaml`), runtime (`runtime/parameters.yaml`, `runtime/credentials.yaml`, `runtime/mapping.yaml`), and cleanup (`cleanup/parameters.yaml`, `cleanup/credentials.yaml`, `cleanup/mapping.yaml`).

## Deployment Context

### UC-ES-DEP-14: deploy_param Image Keys

**Pre-requisites:**

1. Effective Set generation runs in version `v2.0`.
2. Application SBOM includes:
   1. Component with MIME type `application/octet-stream`, property `deploy_param: IMAGE_QA_KEY`, and `full_image_name: registry.example.local/ns/app:1.2.3`.
   2. Component with MIME type `application/octet-stream`, property `deploy_param: billing-service`, and `full_image_name: registry.example.local/ns/billing:9.0.0`.
   3. A service whose name is `billing-service`.

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `GENERATE_EFFECTIVE_SET: true`
2. `EFFECTIVE_SET_CONFIG: {"version":"v2.0"}`

**Steps:**

1. The `generate_effective_set` job runs Effective Set v2.0 for the application.
2. The Calculator derives root deployment parameters from SBOM components with MIME type `application/octet-stream`.
3. For each such component with non-empty `deploy_param`, the system considers a root entry `<deploy_param value>: <full_image_name value>`.
4. If the `deploy_param` value equals an existing service name, that entry is not added to root deployment parameters.

**Results:**

1. `deployment-parameters.yaml` contains `IMAGE_QA_KEY: registry.example.local/ns/app:1.2.3`.
2. `deployment-parameters.yaml` does not contain a root key `billing-service`.

Source:

- `docs/features/calculator-cli.md` (sections: `Image parameters derived from deploy_param`, `Service Inclusion Criteria and Naming Convention`)
- [GitHub Issue #766](https://github.com/Netcracker/qubership-envgene/issues/766)

### UC-ES-DEP-15: Pipeline DEPLOYMENT_SESSION_ID in deployment-parameters

**Pre-requisites:**

1. Effective Set generation runs in version `v2.0`.
2. Pipeline parameter `DEPLOYMENT_SESSION_ID` is set to `550e8400-e29b-41d4-a716-446655440000`.

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `GENERATE_EFFECTIVE_SET: true`
2. `EFFECTIVE_SET_CONFIG: {"version":"v2.0"}`
3. `DEPLOYMENT_SESSION_ID: 550e8400-e29b-41d4-a716-446655440000`

**Steps:**

1. The `generate_effective_set` job supplies `DEPLOYMENT_SESSION_ID` to the Calculator through the instance pipeline integration (EnvGene passes it into Calculator CLI extra parameters).
2. The Effective Set job writes predefined deployment parameters including that session value.

**Results:**

1. `deployment-parameters.yaml` contains `DEPLOYMENT_SESSION_ID: "550e8400-e29b-41d4-a716-446655440000"`.

Source:

- `docs/features/calculator-cli.md` (section: `Predefined deployment-parameters.yaml parameters`)
- `docs/instance-pipeline-parameters.md` (section: `DEPLOYMENT_SESSION_ID`)

### UC-ES-DEP-16: MANAGED_BY Default

**Pre-requisites:**

1. Effective Set generation runs in version `v2.0`.
2. Nothing overrides predefined `MANAGED_BY`.

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `GENERATE_EFFECTIVE_SET: true`

**Steps:**

1. The `generate_effective_set` job resolves predefined deployment parameters for the application namespace.

**Results:**

1. `deployment-parameters.yaml` contains `MANAGED_BY: argocd`.

Source:

- `docs/features/calculator-cli.md` (section: `Predefined deployment-parameters.yaml parameters`)

### UC-ES-DEP-17: Cloud, Tenant, and Application Name Mapping

**Pre-requisites:**

1. Effective Set generation runs in version `v2.0`.
2. Environment Instance and SBOM supply:
   1. Cloud `apiUrl: api.cluster-01.example.com`
   2. Tenant `name: tenant-a`
   3. SBOM application component name `billing-app`

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `GENERATE_EFFECTIVE_SET: true`

**Steps:**

1. The `generate_effective_set` job loads Cloud, Tenant, namespace, and SBOM metadata.
2. It maps documented predefined keys from those sources into `deployment-parameters.yaml`.

**Results:**

1. `deployment-parameters.yaml` contains:
   1. `CLOUD_API_HOST: api.cluster-01.example.com`
   2. `TENANTNAME: tenant-a`
   3. `APPLICATION_NAME: billing-app`

Source:

- `docs/features/calculator-cli.md` (section: `Predefined deployment-parameters.yaml parameters`)

### UC-ES-DEP-18: DBaaS and Vault Disabled Flags

**Pre-requisites:**

1. Effective Set generation runs in version `v2.0`.
2. Cloud DBaaS is absent or disabled (`dbaasConfigs` not enabling usage).
3. Cloud Vault is absent or disabled (`vaultConfig` not enabling usage).

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `GENERATE_EFFECTIVE_SET: true`

**Steps:**

1. The `generate_effective_set` job evaluates DBaaS and Vault toggles from the Cloud definition.

**Results:**

1. `deployment-parameters.yaml` contains `DBAAS_ENABLED: false` and `VAULT_ENABLED: false`.

Source:

- `docs/features/calculator-cli.md` (section: `Predefined deployment-parameters.yaml parameters`)

### UC-ES-DEP-19: Public and Private Gateway URLs

**Pre-requisites:**

1. Effective Set generation runs in version `v2.0`.
2. Inputs resolve to:
   1. `CLOUD_PROTOCOL: https`
   2. `CLOUD_PUBLIC_HOST: apps.cluster-01.example.com`
   3. `ORIGIN_NAMESPACE: billing-origin`
   4. `PRIVATE_GATEWAY_ROUTE_HOST: private-gw.team.example.com`
   5. `CLOUD_API_HOST: api.cluster-01.example.com`
3. `PUBLIC_GATEWAY_ROUTE_HOST` is unset.

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `GENERATE_EFFECTIVE_SET: true`

**Steps:**

1. The `generate_effective_set` job computes `PUBLIC_GATEWAY_URL` using the default formula when no public gateway route host override is set.
2. It sets `PRIVATE_GATEWAY_URL` from `PRIVATE_GATEWAY_ROUTE_HOST`.

**Results:**

1. `deployment-parameters.yaml` contains:
   1. `PUBLIC_GATEWAY_URL: https://public-gateway-billing-origin.apps.cluster-01.example.com`
   2. `PRIVATE_GATEWAY_URL: https://private-gw.team.example.com`

Source:

- `docs/features/calculator-cli.md` (section: `Predefined deployment-parameters.yaml parameters`)

### UC-ES-DEP-20: Collision Files for Service-Name Keys

**Pre-requisites:**

1. Effective Set generation runs in version `v2.0`.
2. Resolved deployment data includes a `services` map listing SBOM service names.
3. At least one root-level deployment key equals one of those service names and is not a structural bucket key (`services`, `configurations`, `frontends`, `smartplug`, `cdn`, `sampleRepo`).
4. Among those keys, at least one is non-sensitive and at least one is sensitive when collision routing runs.

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `GENERATE_EFFECTIVE_SET: true`
2. `EFFECTIVE_SET_CONFIG: {"version":"v2.0"}`

**Steps:**

1. The `generate_effective_set` job identifies root-level keys whose names match entries under `services`.
2. It removes those keys from the main deployment and secured deployment outputs.
3. It writes non-sensitive matches to `collision-deployment-parameters.yaml` and sensitive matches to `collision-credentials.yaml` under the application deployment values directory.

**Results:**

1. `collision-deployment-parameters.yaml` exists under `deployment/<namespace-folder>/<application>/values/` and lists only service-named root keys treated as non-sensitive.
2. `collision-credentials.yaml` exists beside it and lists only service-named root keys treated as sensitive.

Source:

- `docs/features/calculator-cli.md` (section: `Collision Parameters`)
- `build_effective_set_generator/parameters-processor/src/main/java/org/qubership/cloud/parameters/processor/service/ParametersCalculationServiceV2.java`
- `build_effective_set_generator/effective-set-generator/src/main/java/org/qubership/cloud/devops/cli/parser/CliParameterParser.java`

### UC-ES-DEP-A2: Mandatory deployment-parameters Keys

**Pre-requisites:**

1. Effective Set generation runs in version `v2.0`.
2. Pipeline sets `DEPLOYMENT_SESSION_ID`.
3. Tenant, Cloud (including `apiUrl`, `publicUrl`, `protocol`, `apiPort`), namespace, and SBOM application name are present so mandatory sources resolve.

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `GENERATE_EFFECTIVE_SET: true`

**Steps:**

1. The `generate_effective_set` job resolves the full predefined deployment parameter set for the application.

**Results:**

1. `deployment-parameters.yaml` includes all of:
   1. `DEPLOYMENT_SESSION_ID`
   2. `MANAGED_BY`
   3. `CLOUD_API_HOST`
   4. `CLOUD_PUBLIC_HOST`
   5. `CLOUD_PROTOCOL`
   6. `CLOUD_API_PORT`
   7. `TENANTNAME`
   8. `NAMESPACE`
   9. `APPLICATION_NAME`

Source:

- `docs/features/calculator-cli.md` (section: `Predefined deployment-parameters.yaml parameters`)

### UC-ES-DEP-A3: MANAGED_BY When Other Defaults Apply

**Pre-requisites:**

1. Effective Set generation runs in version `v2.0`.
2. Satisfies UC-ES-DEP-16 pre-requisites (no `MANAGED_BY` override).
3. Satisfies UC-ES-DEP-18 pre-requisites (DBaaS and Vault off on Cloud).

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `GENERATE_EFFECTIVE_SET: true`

**Steps:**

1. The `generate_effective_set` job resolves predefined deployment parameters once for an application whose Cloud matches UC-ES-DEP-18.

**Results:**

1. `deployment-parameters.yaml` contains `MANAGED_BY: argocd`.
2. `deployment-parameters.yaml` contains `DBAAS_ENABLED: false` and `VAULT_ENABLED: false`.

Source:

- `docs/features/calculator-cli.md` (section: `Predefined deployment-parameters.yaml parameters`)

### UC-ES-DEP-A4: Optional URLs Omitted When Features Off

**Pre-requisites:**

1. Effective Set generation runs in version `v2.0`.
2. Cloud has `dbaasConfigs[0].enable: false` and `vaultConfig.enable: false`.

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `GENERATE_EFFECTIVE_SET: true`

**Steps:**

1. The `generate_effective_set` job resolves deployment parameters without emitting DBaaS- or Vault-dependent optional URLs.

**Results:**

1. `deployment-parameters.yaml` omits `API_DBAAS_ADDRESS`, `DBAAS_AGGREGATOR_ADDRESS`, `VAULT_ADDR`, and `PUBLIC_VAULT_URL`.

Source:

- `docs/features/calculator-cli.md` (section: `Predefined deployment-parameters.yaml parameters`)

### UC-ES-DEP-A6: credentials.yaml and Optional Secure Keys

**Pre-requisites:**

1. Effective Set generation runs in version `v2.0`.
2. Namespace or Cloud default credentials reference yields a cluster API token.
3. Cloud optionally enables DBaaS, MaaS, Vault, and Consul with credential IDs pointing at stored secrets.

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `GENERATE_EFFECTIVE_SET: true`

**Steps:**

1. The `generate_effective_set` job resolves sensitive values from Environment Instance credential bindings.
2. It writes deployment-context secrets to `credentials.yaml`.

**Results:**

1. `credentials.yaml` includes `K8S_TOKEN`.
2. Keys such as DBaaS, MaaS, Vault, or Consul credentials appear only when the related Cloud feature is enabled and its credential reference is set.

Source:

- `docs/features/calculator-cli.md` (sections: `credentials.yaml`, `Predefined credentials.yaml parameters`)

### UC-ES-DEP-A7: Collision Exceptions

**Pre-requisites:**

1. Effective Set generation runs in version `v2.0`.
2. Preconditions for UC-ES-DEP-20 are satisfied so collision files are produced.
3. At least one nested parameter uses a service name as a key under a parent object (not at root).

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `GENERATE_EFFECTIVE_SET: true`

**Steps:**

1. The `generate_effective_set` job applies collision routing only to root-level keys that match `services` entries.

**Results:**

1. Nested keys that coincide with service names stay in their parent maps and do not appear only because of collision extraction.
2. If `deploy_param` equals a service name on an `application/octet-stream` component, no root image parameter is emitted for that pair (see UC-ES-DEP-14), so collision files do not gain an extra entry from that rule alone.

Source:

- `docs/features/calculator-cli.md` (sections: `Collision Parameters`, `Image parameters derived from deploy_param`)

### UC-ES-DEP-A8: custom-params.yaml From CLI Flag

**Pre-requisites:**

1. Effective Set generation runs in version `v2.0`.
2. Run A: Calculator receives `--custom-params` whose payload includes a `deployment` section with known keys.
3. Run B: same inputs except `--custom-params` is omitted.

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `GENERATE_EFFECTIVE_SET: true`

**Steps:**

1. Run A: the job passes custom parameters into the Calculator and writes the deployment subsection to `custom-params.yaml`.
2. Run B: the job writes `custom-params.yaml` with no deployment keys.

**Results:**

1. Run A: `custom-params.yaml` contains exactly the deployment keys from the custom-params payload.
2. Run B: `custom-params.yaml` is empty.

Source:

- `docs/features/calculator-cli.md` (section: `custom-params.yaml`)

### UC-ES-DEP-A9: deploy-descriptor.yaml Structure and Session ID

**Pre-requisites:**

1. Effective Set generation runs in version `v2.0`.
2. SBOM lists at least one image-type and one configuration-type service so both shapes contribute to the descriptor.
3. Pipeline sets `DEPLOYMENT_SESSION_ID` to a known UUID.

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `GENERATE_EFFECTIVE_SET: true`
2. `DEPLOYMENT_SESSION_ID: <known-uuid>`

**Steps:**

1. The `generate_effective_set` job builds `deploy-descriptor.yaml` from SBOM artifact metadata per service type.
2. It supplies `DEPLOYMENT_SESSION_ID` for common service fields from pipeline input when provided; otherwise generation uses a newly issued identifier.

**Results:**

1. `deploy-descriptor.yaml` contains `global`, a top-level `deployDescriptor` map, and per-service sections aligned with the Effective Set v2.0 descriptor layout.
2. When the pipeline passes `DEPLOYMENT_SESSION_ID`, the common `DEPLOYMENT_SESSION_ID` field matches that value.

Source:

- `docs/features/calculator-cli.md` (sections: `deploy-descriptor.yaml`, `Predefined deploy-descriptor.yaml parameters`)
- `build_effective_set_generator/parameters-processor/src/main/java/org/qubership/cloud/parameters/processor/service/ParametersCalculationServiceV2.java`
- `build_effective_set_generator/effective-set-generator/src/main/java/org/qubership/cloud/devops/cli/utils/BomReaderUtilsImplV2.java`

### UC-ES-DEP-A10: SSL Bundle Copied to Secure Keys

**Pre-requisites:**

1. Effective Set generation runs in version `v2.0`.
2. Resolved deployment parameters include `DEFAULT_SSL_CERTIFICATES_BUNDLE` set to a fixed non-empty string at Tenant, Cloud, Namespace, or Application level.

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `GENERATE_EFFECTIVE_SET: true`
2. `EFFECTIVE_SET_CONFIG: {"version":"v2.0"}`

**Steps:**

1. The `generate_effective_set` job copies the resolved bundle value into secured deployment credentials alongside other sensitive predefined keys.

**Results:**

1. `credentials.yaml` contains `SSL_SECRET_VALUE` and `CA_BUNDLE_CERTIFICATE`, both equal to the resolved `DEFAULT_SSL_CERTIFICATES_BUNDLE` value.

Source:

- `docs/features/calculator-cli.md` (section: `Predefined credentials.yaml parameters`)
- `build_effective_set_generator/parameters-processor/src/main/java/org/qubership/cloud/parameters/processor/service/ParametersCalculationServiceV2.java`

### UC-ES-DEP-A11: per-service-parameters Folder Layout

**Pre-requisites:**

1. Effective Set generation runs in version `v2.0`.
2. Scenario charted SBOM includes `application/vnd.qubership.app.chart` and a chart name that needs normalization (mixed case or underscores).
3. Scenario flat SBOM omits `application/vnd.qubership.app.chart` and includes two distinct services.

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `GENERATE_EFFECTIVE_SET: true`
2. `EFFECTIVE_SET_CONFIG: {"version":"v2.0"}`

**Steps:**

1. Charted scenario: the job emits one `per-service-parameters/<normalized-chart-folder>/deployment-parameters.yaml` whose content groups parameters by service name.
2. Flat scenario: the job emits `per-service-parameters/<service-name>/deployment-parameters.yaml` per service with a flat map in each file.

**Results:**

1. Charted scenario: the directory under `values/per-service-parameters/` uses the normalized chart name, not the raw chart string from SBOM.
2. Flat scenario: one subdirectory exists per service.
3. For a given service, the parameter keys match between the grouped chart layout and the flat file layout for that service.

Source:

- `docs/features/calculator-cli.md` (section: `Per Service parameters`)
- `build_effective_set_generator/effective-set-generator/src/main/java/org/qubership/cloud/devops/cli/parser/CliParameterParser.java`
- `build_effective_set_generator/commons/src/main/java/org/qubership/cloud/devops/commons/utils/HelmNameNormalizer.java`

### UC-ES-DEP-A12: Resource Profile in Per-Service Output

**Pre-requisites:**

1. Effective Set generation runs in version `v2.0`.
2. A supported service component includes optional `application/vnd.qubership.resource-profile-baseline` content in SBOM.
3. Environment Instance defines a resource profile override for that application and service.

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `GENERATE_EFFECTIVE_SET: true`
2. `EFFECTIVE_SET_CONFIG: {"version":"v2.0"}`

**Steps:**

1. The `generate_effective_set` job decodes baseline profile data from SBOM when present.
2. It merges Environment Instance overrides according to product profile rules.

**Results:**

1. Per-service deployment parameters include entries originating from the SBOM baseline payload.
2. Override values from the Environment Instance supersede or extend baseline entries per documented merge semantics.

Source:

- `docs/features/calculator-cli.md` (section: `Resource Profile Processing`)
- `build_effective_set_generator/effective-set-generator/src/main/java/org/qubership/cloud/devops/cli/utils/BomReaderUtilsImplV2.java`

### UC-ES-DEP-A13: Config Service Artifacts in deploy-descriptor

**Pre-requisites:**

1. Effective Set generation runs in version `v2.0`.
2. SBOM defines one configuration-type service (`application/vnd.qubership.configuration.smartplug`, `application/vnd.qubership.configuration.frontend`, `application/vnd.qubership.configuration.cdn`, or `application/vnd.qubership.configuration`).
3. Under that service, child components include artifact MIME types that populate `artifacts[]`, plus two `application/zip` children where one omits classifier and two others reuse the same classifier value.

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `GENERATE_EFFECTIVE_SET: true`
2. `EFFECTIVE_SET_CONFIG: {"version":"v2.0"}`

**Steps:**

1. The job maps smartplug services to OSGi bundle metadata for primary artifact fields and maps frontend, CDN, and generic configuration services to zip metadata per feature documentation.
2. It emits one `artifacts[]` element per qualifying child artifact MIME type.
3. It builds `tArtifactNames` from zip children, using default classifier `ecl` when classifier is missing or blank.

**Results:**

1. The service section inside `deploy-descriptor.yaml` has a non-empty `artifacts` list when qualifying children exist.
2. `tArtifactNames` includes `ecl: <name>-<version>.zip` when classifier is absent or empty on the zip child used for that entry.
3. Duplicate classifier keys from multiple zip children keep the last processed mapping.

Source:

- `docs/features/calculator-cli.md` (sections: `Service Artifacts`, `Primary Service Artifact`, `tArtifactNames`, `Config Type Service Predefined Parameters`)
- `build_effective_set_generator/effective-set-generator/src/main/java/org/qubership/cloud/devops/cli/utils/BomReaderUtilsImplV2.java`
- `build_effective_set_generator/commons/src/main/java/org/qubership/cloud/devops/commons/utils/ServiceArtifactType.java`

### UC-ES-DEP-A14: Deployment mapping.yaml Entries

**Pre-requisites:**

1. Effective Set generation runs in version `v2.0`.
2. Solution Descriptor references at least one application so deployment mapping is emitted.
3. Namespace records expose the logical `name` attribute and folder keys used in Effective Set paths.

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `GENERATE_EFFECTIVE_SET: true`
2. `EFFECTIVE_SET_CONFIG: {"version":"v2.0"}`

**Steps:**

1. The `generate_effective_set` job records each namespace logical name alongside its deployment Effective Set path fragment beginning with `/environments`.
2. It persists the sorted map to `deployment/mapping.yaml` at the Effective Set output root (implementation uses the `.yaml` suffix).

**Results:**

1. `<effective-set-output>/deployment/mapping.yaml` exists.
2. Each key is the Namespace `name` attribute.
3. Each value starts with `/environments` and includes the Environment Instance namespace folder segment used under `effective-set/deployment/`.

Source:

- `docs/features/calculator-cli.md` (section: `mapping.yml`)
- `build_effective_set_generator/effective-set-generator/src/main/java/org/qubership/cloud/devops/cli/parser/CliParameterParser.java`

## Pipeline Context

### UC-ES-PIPE-1: pipeline/parameters.yaml From Cloud e2eParameters

**Pre-requisites:**

1. Effective Set generation runs in version `v2.0`.
2. Cloud Environment Instance defines `e2eParameters` with at least one non-sensitive root parameter whose resolved value is known (scalar, map, or list).

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `GENERATE_EFFECTIVE_SET: true`
2. `EFFECTIVE_SET_CONFIG: {"version":"v2.0"}`

**Steps:**

1. The `generate_effective_set` job completes Effective Set calculation for the tenant and cloud.
2. The Calculator emits pipeline context by splitting Cloud `e2eParameters` into sensitive and non-sensitive sets.
3. Non-sensitive values are written to the shared pipeline parameters file.

**Results:**

1. `pipeline/parameters.yaml` exists under the Effective Set output directory.
2. The file contains the expected non-sensitive root keys from Cloud `e2eParameters` with values matching the resolved Environment Instance data (including nested maps or lists where applicable).

Source:

- `docs/features/calculator-cli.md` (sections: `Pipeline Parameter Context`, `parameters.yaml` under pipeline context)
- `build_effective_set_generator/effective-set-generator/src/main/java/org/qubership/cloud/devops/cli/parser/CliParameterParser.java`

### UC-ES-PIPE-2: pipeline/credentials.yaml From Cloud e2eParameters

**Pre-requisites:**

1. Effective Set generation runs in version `v2.0`.
2. Cloud Environment Instance defines `e2eParameters` with at least one sensitive root parameter bound to a known secret value.

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `GENERATE_EFFECTIVE_SET: true`
2. `EFFECTIVE_SET_CONFIG: {"version":"v2.0"}`

**Steps:**

1. The `generate_effective_set` job resolves Cloud `e2eParameters` including credential-backed entries.
2. Sensitive pipeline values are written to the pipeline credentials file.

**Results:**

1. `pipeline/credentials.yaml` exists under the Effective Set output directory.
2. The file contains the expected sensitive root keys and resolved secret values (structure may be nested per sensitive parameter processing rules).

Source:

- `docs/features/calculator-cli.md` (sections: `Pipeline Parameter Context`, `credentials.yaml` under pipeline context, `Sensitive parameters processing`)
- `build_effective_set_generator/effective-set-generator/src/main/java/org/qubership/cloud/devops/cli/parser/CliParameterParser.java`

### UC-ES-PIPE-3: Consumer File Names From Schema Path

**Pre-requisites:**

1. Effective Set generation runs in version `v2.0`.
2. Calculator CLI receives at least one `--pipeline-consumer-specific-schema-path` (`-pcssp`) argument pointing to a consumer JSON schema file whose basename yields a defined consumer prefix (filename pattern described in feature documentation).

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `GENERATE_EFFECTIVE_SET: true`
2. `EFFECTIVE_SET_CONFIG: {"version":"v2.0"}` (including wiring that passes consumer schema path(s) to the Calculator when applicable).

**Steps:**

1. The `generate_effective_set` job loads consumer schema definitions from the configured paths.
2. The Calculator derives the consumer name from each schema filename.
3. For each consumer, it prepares consumer-specific pipeline outputs alongside the general pipeline pair.

**Results:**

1. Under `pipeline/`, files `<consumer>-parameters.yaml` and `<consumer>-credentials.yaml` exist for each configured consumer schema.
2. The `<consumer>` prefix matches the value derived from that schema path per product rules (filename with `.schema.json` removed as documented).

Source:

- `docs/features/calculator-cli.md` (sections: `Consumer Specific Context of Pipeline Context`, CLI attributes table for `--pipeline-consumer-specific-schema-path`/`-pcssp`)
- `build_effective_set_generator/effective-set-generator/src/main/java/org/qubership/cloud/devops/cli/repository/implementation/FileDataRepositoryImpl.java`

### UC-ES-PIPE-4: Consumer Copies Root Keys From Pipeline Context

**Pre-requisites:**

1. Effective Set generation runs in version `v2.0`.
2. Consumer JSON schema lists root property `PIPE_PUBLIC_KEY` as non-sensitive and root property `PIPE_SECRET_KEY` as sensitive.
3. General pipeline context (`pipeline/parameters.yaml` / `pipeline/credentials.yaml`) already contains matching resolved values for both keys after Cloud `e2eParameters` processing.
4. Calculator CLI receives `-pcssp` for that consumer schema.

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `GENERATE_EFFECTIVE_SET: true`
2. `EFFECTIVE_SET_CONFIG: {"version":"v2.0"}`

**Steps:**

1. The `generate_effective_set` job builds general pipeline parameters and credentials from Cloud `e2eParameters`.
2. For each root property declared in the consumer schema, the Calculator copies the value from the general pipeline output when that key exists.

**Results:**

1. `<consumer>-parameters.yaml` contains `PIPE_PUBLIC_KEY` with the same value as in `pipeline/parameters.yaml`.
2. `<consumer>-credentials.yaml` contains `PIPE_SECRET_KEY` with the same value as in `pipeline/credentials.yaml`.

Source:

- `docs/features/calculator-cli.md` (section: `Consumer Specific Context of Pipeline Context`, principle 1)
- `build_effective_set_generator/effective-set-generator/src/main/java/org/qubership/cloud/devops/cli/parser/CliParameterParser.java`

### UC-ES-PIPE-5: Consumer Uses Schema Default Only

**Pre-requisites:**

1. Effective Set generation runs in version `v2.0`.
2. Consumer schema declares optional root property `EXTRA_PIPELINE_FLAG` with a documented default value and the property is not listed as required, or is optional with default only.
3. General pipeline context does not define root key `EXTRA_PIPELINE_FLAG`.
4. Calculator CLI receives `-pcssp` for that consumer.

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `GENERATE_EFFECTIVE_SET: true`
2. `EFFECTIVE_SET_CONFIG: {"version":"v2.0"}`

**Steps:**

1. The `generate_effective_set` job builds general pipeline outputs without `EXTRA_PIPELINE_FLAG`.
2. When assembling consumer-specific files, the Calculator applies schema defaults for declared properties missing from the general parameters.

**Results:**

1. `<consumer>-parameters.yaml` contains `EXTRA_PIPELINE_FLAG` equal to the schema default value.

Source:

- `docs/features/calculator-cli.md` (section: `Consumer Specific Context of Pipeline Context`, principle 2.1)
- `build_effective_set_generator/effective-set-generator/src/main/java/org/qubership/cloud/devops/cli/parser/CliParameterParser.java`

### UC-ES-PIPE-6: Consumer Omits Optional Schema-Only Key

**Pre-requisites:**

1. Effective Set generation runs in version `v2.0`.
2. Consumer schema declares root property `UNUSED_PIPELINE_OPT` as optional, not required, with no default.
3. General pipeline context has no root key `UNUSED_PIPELINE_OPT`.
4. Calculator CLI receives `-pcssp` for that consumer.

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `GENERATE_EFFECTIVE_SET: true`
2. `EFFECTIVE_SET_CONFIG: {"version":"v2.0"}`

**Steps:**

1. The `generate_effective_set` job builds consumer-specific pipeline files from the schema and general pipeline maps.
2. Optional schema properties without defaults and without a general pipeline value are skipped.

**Results:**

1. Neither `<consumer>-parameters.yaml` nor `<consumer>-credentials.yaml` contains root key `UNUSED_PIPELINE_OPT`.

Source:

- `docs/features/calculator-cli.md` (section: `Consumer Specific Context of Pipeline Context`, principle 2.2)
- `build_effective_set_generator/effective-set-generator/src/main/java/org/qubership/cloud/devops/cli/parser/CliParameterParser.java`

### UC-ES-PIPE-7: Consumer Mandatory Key Without Value Fails

**Pre-requisites:**

1. Effective Set generation runs in version `v2.0`.
2. Consumer schema lists root property `MISSING_REQUIRED_PIPE_KEY` as required and supplies no default.
3. General pipeline context does not define root key `MISSING_REQUIRED_PIPE_KEY`.
4. Calculator CLI receives `-pcssp` for that consumer.

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `GENERATE_EFFECTIVE_SET: true`
2. `EFFECTIVE_SET_CONFIG: {"version":"v2.0"}`

**Steps:**

1. The `generate_effective_set` job evaluates consumer schema properties against general pipeline outputs.
2. For a required root property with no value in general parameters and no schema default, generation stops with an error.

**Results:**

1. Effective Set generation does not complete successfully.
2. The failure indicates a required consumer pipeline property has no value in E2E configuration (aligned with consumer processing error semantics).

Source:

- `docs/features/calculator-cli.md` (section: `Consumer Specific Context of Pipeline Context`, principle 2.3)
- `build_effective_set_generator/effective-set-generator/src/main/java/org/qubership/cloud/devops/cli/parser/CliParameterParser.java`

## Topology Context

### UC-ES-TOP-1: Cluster Endpoint from Cloud Passport

**Pre-requisites:**

1. Environment `cluster01/env-with-passport` exists.
2. Cloud Passport is configured and contains cluster endpoint data.
3. Calculator CLI execution is enabled.

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `ENV_NAMES: cluster01/env-with-passport`
2. `CALCULATOR_CLI: true`

**Steps:**

1. The `generate_effective_set` job runs for the target environment.
2. The topology context is generated and `cluster` endpoint fields are resolved from Cloud Passport data.

**Results:**

1. `topology/parameters.yaml` contains `cluster` with values from Cloud Passport:
   1. `api_url`
   2. `api_port`
   3. `public_url`
   4. `protocol`

Source:

- `docs/test-cases/cluster-endpoint-topology-context.md` (`TC-CETC-001`)

### UC-ES-TOP-2: Cluster Endpoint from inventory.clusterUrl

**Pre-requisites:**

1. Environment `cluster01/env-without-passport` exists.
2. Cloud Passport is not configured.
3. `inventory.clusterUrl` is set to `https://API.cl-03.managed.qubership.cloud:6443`.
4. Calculator CLI execution is enabled.

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `ENV_NAMES: cluster01/env-without-passport`
2. `CALCULATOR_CLI: true`

**Steps:**

1. The `generate_effective_set` job runs for the target environment.
2. The topology context derives `cluster` endpoint values from `inventory.clusterUrl`.

**Results:**

1. `topology/parameters.yaml` contains:
   1. `cluster.api_url: API.cl-03.managed.qubership.cloud`
   2. `cluster.api_port: 6443`
   3. `cluster.public_url: apps.cl-03.managed.qubership.cloud`
   4. `cluster.protocol: https`

Source:

- `docs/test-cases/cluster-endpoint-topology-context.md` (`TC-CETC-002`)

### UC-ES-TOP-3: Cluster Endpoint with Non-Standard Port

**Pre-requisites:**

1. Environment `cluster01/env-nonstandard-port` exists.
2. Cloud Passport is not configured.
3. `inventory.clusterUrl` is set to `https://API.cl-03.managed.qubership.cloud:8443`.
4. Calculator CLI execution is enabled.

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `ENV_NAMES: cluster01/env-nonstandard-port`
2. `CALCULATOR_CLI: true`

**Steps:**

1. The `generate_effective_set` job runs for the target environment.
2. The topology context derives `cluster` endpoint values from `inventory.clusterUrl`, preserving the specified port.

**Results:**

1. `topology/parameters.yaml` contains:
   1. `cluster.api_url: API.cl-03.managed.qubership.cloud`
   2. `cluster.api_port: 8443`
   3. `cluster.public_url: apps.cl-03.managed.qubership.cloud`
   4. `cluster.protocol: https`

Source:

- `docs/test-cases/cluster-endpoint-topology-context.md` (`TC-CETC-003`)

### UC-ES-TOP-4: Cluster Endpoint with HTTP Protocol

**Pre-requisites:**

1. Environment `cluster01/env-http-protocol` exists.
2. Cloud Passport is not configured.
3. `inventory.clusterUrl` is set to `http://API.cl-03.managed.qubership.cloud:6443`.
4. Calculator CLI execution is enabled.

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `ENV_NAMES: cluster01/env-http-protocol`
2. `CALCULATOR_CLI: true`

**Steps:**

1. The `generate_effective_set` job runs for the target environment.
2. The topology context derives `cluster` endpoint values from `inventory.clusterUrl`, preserving protocol.

**Results:**

1. `topology/parameters.yaml` contains:
   1. `cluster.api_url: API.cl-03.managed.qubership.cloud`
   2. `cluster.api_port: 6443`
   3. `cluster.public_url: apps.cl-03.managed.qubership.cloud`
   4. `cluster.protocol: http`

Source:

- `docs/test-cases/cluster-endpoint-topology-context.md` (`TC-CETC-004`)

### UC-ES-TOP-5: Cluster Endpoint with Non-Standard Hostname

**Pre-requisites:**

1. Environment `cluster01/env-nonstandard-hostname` exists.
2. Cloud Passport is not configured.
3. `inventory.clusterUrl` is set to `https://cluster.cl-03.managed.qubership.cloud:6443`.
4. Calculator CLI execution is enabled.

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `ENV_NAMES: cluster01/env-nonstandard-hostname`
2. `CALCULATOR_CLI: true`

**Steps:**

1. The `generate_effective_set` job runs for the target environment.
2. The topology context derives `cluster` endpoint values from `inventory.clusterUrl`.

**Results:**

1. `topology/parameters.yaml` contains:
   1. `cluster.api_url: cluster.cl-03.managed.qubership.cloud`
   2. `cluster.api_port: 6443`
   3. `cluster.public_url: cluster.cl-03.managed.qubership.cloud`
   4. `cluster.protocol: https`

Source:

- `docs/test-cases/cluster-endpoint-topology-context.md` (`TC-CETC-005`)

### UC-ES-TOP-6: Cloud Passport Overrides inventory.clusterUrl

**Pre-requisites:**

1. Environment `cluster01/env-passport-override` exists.
2. Cloud Passport is configured and contains cluster endpoint data.
3. `inventory.clusterUrl` is set to `https://API.cl-03.managed.qubership.cloud:6443`.
4. Calculator CLI execution is enabled.

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `ENV_NAMES: cluster01/env-passport-override`
2. `CALCULATOR_CLI: true`

**Steps:**

1. The `generate_effective_set` job runs for the target environment.
2. The topology context resolves `cluster` endpoint values using Cloud Passport when both Cloud Passport and `inventory.clusterUrl` are present.

**Results:**

1. `topology/parameters.yaml` contains `cluster` values from Cloud Passport.
2. `inventory.clusterUrl` value is not used for final `cluster` fields in this scenario.

Source:

- `docs/test-cases/cluster-endpoint-topology-context.md` (`TC-CETC-006`)

### UC-ES-TOP-7: Missing Cluster Information Produces Empty Cluster Fields

**Pre-requisites:**

1. Environment `cluster01/env-missing-cluster-info` exists.
2. Cloud Passport is not configured.
3. `inventory.clusterUrl` is not specified.
4. Calculator CLI execution is enabled.

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `ENV_NAMES: cluster01/env-missing-cluster-info`
2. `CALCULATOR_CLI: true`

**Steps:**

1. The `generate_effective_set` job runs for the target environment.
2. The topology context attempts to resolve `cluster` endpoint values without Cloud Passport and without `inventory.clusterUrl`.

**Results:**

1. `topology/parameters.yaml` contains `cluster` with empty values:
   1. `cluster.api_url: ""`
   2. `cluster.api_port: ""`
   3. `cluster.public_url: ""`
   4. `cluster.protocol: ""`

Source:

- `docs/test-cases/cluster-endpoint-topology-context.md` (`TC-CETC-007`)

## Runtime Context

### UC-ES-RUN-1: runtime/parameters.yaml from technicalConfigurationParameters

**Pre-requisites:**

1. Effective Set generation runs in version `v2.0`.
2. Tenant, Cloud, Namespace, or Application define non-sensitive `technicalConfigurationParameters`.

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `GENERATE_EFFECTIVE_SET: true`
2. `EFFECTIVE_SET_CONFIG: {"version":"v2.0"}`

**Steps:**

1. The `generate_effective_set` job merges runtime non-sensitive parameters from technical configuration sections.
2. It writes runtime non-sensitive output per namespace and application.

**Results:**

1. `runtime/<namespace-folder>/<application>/parameters.yaml` exists for processed applications.
2. The file contains merged non-sensitive runtime parameters.

Source:

- `docs/features/calculator-cli.md` (section: `Runtime Parameter Context`)
- `build_effective_set_generator/effective-set-generator/src/main/java/org/qubership/cloud/devops/cli/parser/CliParameterParser.java`
- `build_effective_set_generator/parameters-processor/src/main/java/org/qubership/cloud/parameters/processor/service/ParametersCalculationServiceV2.java`

### UC-ES-RUN-2: runtime/credentials.yaml Includes Sensitive and Custom Runtime

**Pre-requisites:**

1. Effective Set generation runs in version `v2.0`.
2. Runtime-sensitive `technicalConfigurationParameters` are defined.
3. `--custom-params` includes `runtime` section with at least one key.

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `GENERATE_EFFECTIVE_SET: true`
2. `EFFECTIVE_SET_CONFIG: {"version":"v2.0"}`
3. `CUSTOM_PARAMS` passes runtime values to Calculator `--custom-params`.

**Steps:**

1. The `generate_effective_set` job builds runtime sensitive context.
2. It merges runtime values from `--custom-params` into runtime credentials with higher priority.
3. It writes runtime sensitive output.

**Results:**

1. `runtime/<namespace-folder>/<application>/credentials.yaml` exists.
2. The file contains sensitive runtime parameters.
3. For keys defined in both runtime technical parameters and runtime custom params, value in output equals custom runtime value.

Source:

- `docs/features/calculator-cli.md` (section: `Runtime Parameter Context`)
- `docs/instance-pipeline-parameters.md` (section: `CUSTOM_PARAMS`)
- `build_effective_set_generator/parameters-processor/src/main/java/org/qubership/cloud/parameters/processor/service/ParametersCalculationServiceV2.java`
- `build_effective_set_generator/effective-set-generator/src/main/java/org/qubership/cloud/devops/cli/parser/CliParameterParser.java`

### UC-ES-RUN-3: runtime/mapping.yaml Matches Deployment Mapping Logic

**Pre-requisites:**

1. Effective Set generation runs in version `v2.0`.
2. Solution Descriptor contains at least one application in at least one namespace.

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `GENERATE_EFFECTIVE_SET: true`
2. `EFFECTIVE_SET_CONFIG: {"version":"v2.0"}`

**Steps:**

1. The `generate_effective_set` job computes namespace-to-path mapping for runtime output.
2. It writes runtime mapping file.

**Results:**

1. `runtime/mapping.yaml` exists.
2. Keys are namespace logical names and values start with `/environments/.../effective-set/runtime/<namespace-folder>`.
3. Mapping keys are consistent with deployment mapping key set for processed namespaces.

Source:

- `docs/features/calculator-cli.md` (section: `Runtime Parameter Context`, `mapping.yml`)
- `build_effective_set_generator/effective-set-generator/src/main/java/org/qubership/cloud/devops/cli/parser/CliParameterParser.java`
- `build_effective_set_generator/effective-set-generator/src/test/resources/environments/cluster-01/pl-01/effective-set/runtime/mapping.yaml`

## Cleanup Context

### UC-ES-CLN-1: cleanup/parameters.yaml from deployParameters

**Pre-requisites:**

1. Effective Set generation runs in version `v2.0`.
2. Tenant, Cloud, or Namespace define non-sensitive `deployParameters`.

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `GENERATE_EFFECTIVE_SET: true`
2. `EFFECTIVE_SET_CONFIG: {"version":"v2.0"}`

**Steps:**

1. The `generate_effective_set` job calculates cleanup non-sensitive context from deploy parameter hierarchy.
2. It writes cleanup parameters per namespace.

**Results:**

1. `cleanup/<namespace-folder>/parameters.yaml` exists.
2. The file contains merged non-sensitive cleanup parameters from Tenant, Cloud, and Namespace deploy parameters.

Source:

- `docs/features/calculator-cli.md` (section: `Cleanup Context`)
- `build_effective_set_generator/parameters-processor/src/main/java/org/qubership/cloud/parameters/processor/service/ParametersCalculationServiceV2.java`
- `build_effective_set_generator/effective-set-generator/src/main/java/org/qubership/cloud/devops/cli/parser/CliParameterParser.java`

### UC-ES-CLN-2: cleanup/credentials.yaml Includes Sensitive and Custom Runtime

**Pre-requisites:**

1. Effective Set generation runs in version `v2.0`.
2. Cleanup-sensitive deploy parameters are defined at Tenant, Cloud, or Namespace levels.
3. `--custom-params` includes `runtime` section with at least one key.

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `GENERATE_EFFECTIVE_SET: true`
2. `EFFECTIVE_SET_CONFIG: {"version":"v2.0"}`
3. `CUSTOM_PARAMS` passes runtime values to Calculator `--custom-params`.

**Steps:**

1. The `generate_effective_set` job calculates cleanup sensitive context.
2. It merges runtime custom parameters from `--custom-params` into cleanup credentials with higher priority.
3. It writes cleanup credentials per namespace.

**Results:**

1. `cleanup/<namespace-folder>/credentials.yaml` exists.
2. The file contains sensitive cleanup parameters.
3. For keys defined in both cleanup-sensitive parameters and custom runtime params, value in output equals custom runtime value.

Source:

- `docs/features/calculator-cli.md` (section: `Cleanup Context`)
- `docs/instance-pipeline-parameters.md` (section: `CUSTOM_PARAMS`)
- `build_effective_set_generator/parameters-processor/src/main/java/org/qubership/cloud/parameters/processor/service/ParametersCalculationServiceV2.java`
- `build_effective_set_generator/effective-set-generator/src/main/java/org/qubership/cloud/devops/cli/parser/CliParameterParser.java`

### UC-ES-CLN-3: cleanup/mapping.yaml Matches Deployment Mapping Logic

**Pre-requisites:**

1. Effective Set generation runs in version `v2.0`.
2. Solution Descriptor contains at least one application in at least one namespace.

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `GENERATE_EFFECTIVE_SET: true`
2. `EFFECTIVE_SET_CONFIG: {"version":"v2.0"}`

**Steps:**

1. The `generate_effective_set` job computes namespace-to-path mapping for cleanup output.
2. It writes cleanup mapping file.

**Results:**

1. `cleanup/mapping.yaml` exists.
2. Keys are namespace logical names and values start with `/environments/.../effective-set/cleanup/<namespace-folder>`.
3. Mapping keys are consistent with deployment mapping key set for processed namespaces.

Source:

- `docs/features/calculator-cli.md` (section: `Cleanup Context`, `mapping.yml`)
- `build_effective_set_generator/effective-set-generator/src/main/java/org/qubership/cloud/devops/cli/parser/CliParameterParser.java`
- `build_effective_set_generator/effective-set-generator/src/test/resources/environments/cluster-01/pl-01/effective-set/cleanup/mapping.yaml`

## Validation Summary

- **Removed UC-ES-DEP-A1 and UC-ES-DEP-A5:** Those identifiers only repeated UC-ES-DEP-14 and UC-ES-DEP-19 in full; use UC-ES-DEP-14 and UC-ES-DEP-19 for tests that previously targeted A1 and A5.
- **Overlap reduction:** UC-ES-DEP-A3 keeps one combined run for `MANAGED_BY` plus DBaaS/Vault defaults with explicit Results; UC-ES-DEP-A7 references UC-ES-DEP-20 and UC-ES-DEP-14 for collision and `deploy_param` context without duplicating their full steps.
- **Steps:** Java method names removed from Steps and Results; file paths kept under Source for implementers.
- **Titles:** Shortened to a consistent `Topic: outcome` style without altering covered behavior.
- **Pipeline context:** UC-ES-PIPE-1 through UC-ES-PIPE-7 cover Cloud `e2eParameters` outputs under `pipeline/` and consumer-specific subsets driven by `--pipeline-consumer-specific-schema-path`/`-pcssp` (see `docs/features/calculator-cli.md`; some narrative paragraphs still mention `--pipeline-context-schema-path` while the CLI table lists `--pipeline-consumer-specific-schema-path`).
