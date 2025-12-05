# Environment Instance Generation

- [Environment Instance Generation](#environment-instance-generation)
  - [Description](#description)
  - [Namespace Folder Name Generation](#namespace-folder-name-generation)
    - [Folder Name Generation Rules](#folder-name-generation-rules)
      - [Namespace NOT in BG Domain](#namespace-not-in-bg-domain)
      - [Namespace in BG Domain (origin or peer)](#namespace-in-bg-domain-origin-or-peer)
  - [Related Features](#related-features)

## Description

This feature describes the process of generating an [Environment Instance](/docs/envgene-objects.md#environment-instance) from an [Environment Template](/docs/envgene-objects.md#environment-template) and [Environment Inventory](/docs/envgene-configs.md#env_definitionyml). The generation process creates the directory structure and files for the Environment Instance, including Namespaces, Applications, Resource Profiles, Credentials, and other EnvGene objects.

## Namespace Folder Name Generation

This section explains the method used to determine the folder name for each [Namespace](/docs/envgene-objects.md#namespace) and its child [Application](/docs/envgene-objects.md#application) objects. The resulting folder name defines the path structure for namespaces in the Environment Instance: `/environments/<cluster-name>/<env-name>/Namespaces/<folder-name>/`.

The folder name generation logic depends on:

- Whether the namespace is part of a [Blue-Green Domain](/docs/envgene-objects.md#bg-domain) (BG Domain)
- Whether `deploy_postfix` is specified in the [Template Descriptor](/docs/envgene-objects.md#template-descriptor)
- The BG role of the namespace (origin, peer, or controller)

### Folder Name Generation Rules

#### Namespace NOT in BG Domain

If the namespace is **not** part of a BG Domain (not `peer` or `origin`):

1. **If `deploy_postfix` is specified** in Template Descriptor:
   - Folder name = `<deploy_postfix>`

2. **If `deploy_postfix` is NOT specified** in Template Descriptor:
   - Folder name = `<ns-template-name>`
   - Where `<ns-template-name>` is the name of the namespace template file without extension

#### Namespace in BG Domain (origin or peer)

If the namespace is part of a BG Domain as `origin` or `peer`:

1. **If `deploy_postfix` is specified** in Template Descriptor:
   - Folder name = `<deploy_postfix>-<ns-bg-role>`
   - Where `<ns-bg-role>` is `origin` or `peer`

2. **If `deploy_postfix` is NOT specified** in Template Descriptor:
   - Folder name = `<ns-template-name>-<ns-bg-role>`
   - Where `<ns-template-name>` is the name of the namespace template file without extension
   - And `<ns-bg-role>` is `origin` or `peer`

**Note:** The `controller` namespace in BG Domain follows the same rules as namespaces not in BG Domain (no suffix is added).

## Related Features

- [Namespace Render Filtering](/docs/features/namespace-render-filtering.md) - Uses namespace folder names for filtering
- [Blue-Green Deployment](/docs/features/blue-green-deployment.md) - Describes BG Domain structure
- [Effective Set Calculator](/docs/features/calculator-cli.md) - Uses folder names for effective set structure
