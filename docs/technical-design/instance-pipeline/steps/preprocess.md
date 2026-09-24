# `preprocess`

- [`preprocess`](#preprocess)
  - [Description](#description)
  - [Input parameters](#input-parameters)
  - [Processing flow](#processing-flow)
  - [Result](#result)
  - [Error handling](#error-handling)
  - [Related documentation](#related-documentation)

## Description

The `preprocess` step prepares the runner for one environment before any environment content is generated. It sets
pipeline defaults, applies certificates, narrows the working tree to the environment being processed, and decrypts
credential material.

## Input parameters

| Parameter               | Source   | Required | Default | Values / format             | Effect                                                       |
|-------------------------|----------|----------|---------|-----------------------------|--------------------------------------------------------------|
| `ENV_NAMES`             | Pipeline | Yes      | None    | `<cluster-name>/<env-name>` | Selects the environment whose paths form the sparse cone     |
| `CRED_ROTATION_PAYLOAD` | Pipeline | No       | None    | JSON payload                | When set, widens the cone to the whole cluster               |

## Processing flow

1. **`set_defaults`**

   TBD.

2. **`cert_apply`**

   TBD.

3. **`checkout`**

   `checkout` narrows the working tree to the environment being processed, checks out the built commit, and removes
   leftovers from previous runs. The built commit is the commit the pipeline builds (`CI_COMMIT_SHA` or `GITHUB_SHA`).
   On a reused node the CI job does a shallow fetch and skips the runner checkout (`GIT_STRATEGY: fetch`,
   `GIT_DEPTH: 1`, `GIT_CHECKOUT: false`), so the runner populates Git objects but leaves the working tree as the
   previous run left it.

   ```bash
   git sparse-checkout init --cone
   git sparse-checkout set <cone>   # keep only the environment's paths; tracked files outside the cone are pruned
   git checkout -f <built commit>   # force the tracked tree to the built commit within the cone
   git clean -ffd                   # remove untracked leftovers of previous runs and other environments
   ```

   The `<cone>`, grouped by condition:

   ```text
   # always
   appdefs/  regdefs/  configuration/  sboms/  templates/
   environments/<cluster-name>/<env-name>
   environments[/<cluster-name>]/{configuration, configurations, resource_profiles, rp_override,
     Profiles, parameters, cloud-passport, cloud-passports, credentials, Credentials, shared-credentials}
   environments/<cluster-name>/{app-deployer, cloud-deployer}

   # only with CRED_ROTATION_PAYLOAD
   environments/<cluster-name>/
   ```

   Without `CRED_ROTATION_PAYLOAD` the cone is the "always" block. `environments[/<cluster-name>]/{...}` means the
   shared-entity dirs are kept at both the `environments/` root and the cluster level. The multi-environment cone and
   flow are TBD.

4. **`crypt.decrypt`**

   TBD.

## Result

After `checkout`, the working tree holds the built commit within the environment's cone. Untracked leftovers of
previous runs and other environments are removed. Ignored files and repository metadata are preserved.

## Error handling

The `checkout` and `clean` calls are not wrapped. A failure propagates as the raw git error and the job fails.
`checkout` does no fetch of its own. The runner fetches the objects.

## Related documentation

- [ADR-0008: Clean the reused node working tree at checkout start](/docs/adr/0008-clean-reused-node-working-tree-at-checkout-start.md)
- [Modern toolset flow](/docs/technical-design/instance-pipeline/flow.md)
