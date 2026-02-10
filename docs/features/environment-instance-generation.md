# Environment Instance Generation

- [Environment Instance Generation](#environment-instance-generation)
  - [Description](#description)
  - [Namespace Folder Name Generation](#namespace-folder-name-generation)
    - [Folder Name Generation Rules](#folder-name-generation-rules)
      - [Namespace NOT in BG Domain](#namespace-not-in-bg-domain)
      - [Namespace in BG Domain (origin or peer)](#namespace-in-bg-domain-origin-or-peer)
  - [Template Artifacts](#template-artifacts)
    - [Common Artifact](#common-artifact)
    - [Blue-Green Artifact](#blue-green-artifact)
  - [Related Features](#related-features)

> [!WARNING]
> This documentation is incomplete. It currently covers only specific aspects of Environment Instance Generation.

## Description

This feature describes the process of generating an [Environment Instance](/docs/envgene-objects.md#environment-instance-objects) from an [Environment Template](/docs/envgene-objects.md#environment-template-objects) and [Environment Inventory](/docs/envgene-configs.md#env_definitionyml). The generation process creates the directory structure and files for the Environment Instance, including Namespaces, Applications, Resource Profiles, Credentials, and other EnvGene objects.

## Namespace Folder Name Generation

This section explains the method used to determine the folder name for each [Namespace](/docs/envgene-objects.md#namespace) and its child [Application](/docs/envgene-objects.md#application) objects. The resulting folder name defines the path structure for namespaces in the Environment Instance: `/environments/<cluster-name>/<env-name>/Namespaces/<folder-name>/`.

The folder name generation logic depends on:

- Whether the namespace is part of a [Blue-Green Deployment](/docs/envgene-objects.md#bg-domain) (BG Domain)
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

## Template Artifacts

The Environment Inventory specifies which Environment Template artifact(s) to use for rendering the Environment Instance. The artifact selection depends on whether the environment uses Blue-Green Deployment (BGD) support.

### Common Artifact

For environments that do **not** use Blue-Green Deployment, or for standard rendering of most objects:

`envTemplate.artifact`- Template artifact in `application:version` notation. Used for rendering **all** Environment Instance objects:

- All Namespaces (including `controller` namespace in BG Domain, if present)
- Tenant, Cloud, Applications, Resource Profiles, Credentials, and all other objects

**Example:**

```yaml
envTemplate:
  artifact: "project-env-template:v1.2.3"
```

### Blue-Green Artifact

For environments that use Blue-Green Deployment support, the Environment Inventory **can** specify separate template artifacts for `origin` and `peer` namespaces using the `envTemplate.bgNsArtifacts` attribute.

The `envTemplate.artifact` attribute is **always mandatory**, regardless of whether `bgNsArtifacts` is specified.

The `envTemplate.bgNsArtifacts` and `envTemplate.artifact` attributes are **not mutually exclusive**:

**When `envTemplate.bgNsArtifacts` is specified:**

- `envTemplate.bgNsArtifacts` is used **only** for rendering `peer` and `origin` Namespaces in BG Domain:
  - `envTemplate.bgNsArtifacts.origin` is used for rendering the `origin` Namespace
  - `envTemplate.bgNsArtifacts.peer` is used for rendering the `peer` Namespace
- `envTemplate.artifact` is used for rendering all **other** Environment Instance objects:
  - All Namespaces that are not part of the BG Domain
  - The `controller` Namespace in BG Domain (if present)
  - All other Environment Instance objects (Tenant, Cloud, Applications, Resource Profiles, Credentials, etc.)

**When `envTemplate.bgNsArtifacts` is not specified:**

- `envTemplate.artifact` is used for rendering **all** Environment Instance objects, including `origin` and `peer` Namespaces in BG Domain

The role of a Namespace (origin, peer, or controller) is determined through the [BG Domain](/docs/envgene-objects.md#bg-domain) object in the Environment Instance.

**Example:**

```yaml
envTemplate:
  name: "composite-prod"
  artifact: "project-env-template:v1.2.3"
  bgNsArtifacts:
    origin: "project-env-template:v1.2.3-origin"
    peer: "project-env-template:v1.2.3-peer"
```

In this example:

- The `origin` Namespace will be rendered using `project-env-template:v1.2.3-origin`
- The `peer` Namespace will be rendered using `project-env-template:v1.2.3-peer`
- All other objects (including `controller` Namespace) will be rendered using `project-env-template:v1.2.3`

## Related Features

- [Namespace Render Filtering](/docs/features/namespace-render-filtering.md) - Uses namespace folder names for filtering
- [Blue-Green Deployment](/docs/features/blue-green-deployment.md) - Describes BG Domain structure
- [Effective Set Calculator](/docs/features/calculator-cli.md) - Uses folder names for effective set structure
