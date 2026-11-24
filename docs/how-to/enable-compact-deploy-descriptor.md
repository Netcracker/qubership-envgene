# Enable the compact `deploy-descriptor.yaml` layout

- [Enable the compact `deploy-descriptor.yaml` layout](#enable-the-compact-deploy-descriptoryaml-layout)
  - [Prerequisites](#prerequisites)
  - [Update the application chart](#update-the-application-chart)
  - [Set the layout in the Deployment Descriptor](#set-the-layout-in-the-deployment-descriptor)
  - [Generate the Effective Set](#generate-the-effective-set)
  - [Verify the result](#verify-the-result)
  - [Switch back to the full layout](#switch-back-to-the-full-layout)

Switch an application to the compact layout of the Effective Set `deploy-descriptor.yaml`, and switch it back. For
the layouts and their structure, see
[`deploy-descriptor.yaml` layouts](/docs/features/calculator-cli.md#version-20-deploy-descriptoryaml-layouts).

## Prerequisites

- Access to the application chart source.
- A way to release a new application version with a changed Deployment Descriptor (DD).

## Update the application chart

In the compact layout, the list of services is available only in `.Values.global.deployDescriptor`. Update the chart
before you set the layout. Otherwise Helm fails to render the chart.

1. Find the templates that read `deployDescriptor`, including subcharts:

   ```bash
   grep -rn "\.Values\.deployDescriptor" <chart-dir>/
   ```

   If the chart uses a shared template library to find services, check its templates too.

2. Replace every `.Values.deployDescriptor` with `.Values.global.deployDescriptor`. If a template does not need the
   list of services, remove the reference.

3. Run the search again. It must return nothing.

> [!NOTE]
> `.Values.global.deployDescriptor` exists in both layouts. You can release the updated chart before you switch the
> layout.

## Set the layout in the Deployment Descriptor

In the DD of a new application version, set `metadata.deployContextLayout` to `compact`:

```json
{
  "metadata": {
    "deployContextLayout": "compact"
  }
}
```

Release the chart change and the DD change in the same application version.

## Generate the Effective Set

1. Reference the new application version in the deploy plan of the environment.
2. Run the Instance pipeline with Effective Set generation. See
   [Generate an Effective Set](/docs/how-to/generate-effective-set.md).

## Verify the result

Open
`/environments/<cluster-name>/<env-name>/effective-set/deployment/<namespace-folder>/<application-name>/values/deploy-descriptor.yaml`:

- `global.deployDescriptor` lists all services.
- Service sections contain only the
  [common predefined parameters](/docs/features/calculator-cli.md#version-20-predefined-deploy-descriptoryaml-parameters).
- There is no top-level `deployDescriptor`.

Deploy the application as usual.

## Switch back to the full layout

Do one of the following:

- Release a new application version whose DD sets `metadata.deployContextLayout` to `full` or does not set it.
- For an application version that already has an Application SBOM, change its DD, delete
  `/sboms/<application-name>/<application-name>-<version>.sbom.json` from the Instance Repository, and generate the
  Effective Set again.

EnvGene generates the [Application SBOM](/docs/features/sbom.md) once per application version. Without one of these
actions, the previous layout stays.

The chart does not need to change back.
