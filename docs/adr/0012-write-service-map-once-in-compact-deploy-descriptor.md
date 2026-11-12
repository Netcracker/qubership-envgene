# ADR-0012: Write the service map once in a compact deploy descriptor

Status: Proposed

## Context

In `deploy-descriptor.yaml`, every service section contains the list of all application services twice: in
`deployDescriptor` and in `global`. For an application with many services, the file reaches tens of MB, and YAML
aliases do not help because Helm rejects a file with too many aliases. With a file this large, ArgoCD manifest
generation hits its timeout.

## Decision

An application can request a compact `deploy-descriptor.yaml` in its Deployment Descriptor.

- The service list is written once, under `global`.
- Service sections contain only the common parameters.
- Other Effective Set files do not change.
- Applications that do not request it keep the current form.
- The form is chosen per application.

Rejected:

- Keep the current form with aliases, because Helm rejects the file.
- Keep only `global` without service sections, because the chart reads the common parameters from its own section.
- Remove the service list completely, because some charts read it.
- Make the compact form the default, because current charts read the service list from their own section.

## Consequences

- The file becomes much smaller.
- An application that uses the compact form must read the service list from `global` in its charts. This includes
  charts that find services through the shared template library.
- The choice is stored in the Application SBOM, which is generated once per application version. EnvGene does not
  notice a changed Deployment Descriptor of a released version. To change the form of such a version, including a
  switch back to the current form, the user releases a new version or deletes the cached Application SBOM.
- EnvGene supports and tests two forms of the file.

See [`deploy-descriptor.yaml` layouts](/docs/features/calculator-cli.md#version-20-deploy-descriptoryaml-layouts) and
[Application SBOM Metadata](/docs/features/sbom-generation.md#application-sbom-metadata).
