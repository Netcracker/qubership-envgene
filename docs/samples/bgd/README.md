# Blue-Green Deployment (BGD) Samples

- [Blue-Green Deployment (BGD) Samples](#blue-green-deployment-bgd-samples)
  - [Description](#description)
  - [Layout](#layout)
  - [How to use these samples](#how-to-use-these-samples)
  - [Migration path](#migration-path)
  - [Related documentation](#related-documentation)

## Description

These samples support migrating a **non-BG** Environment Template and Environment Inventory to **Blue-Green Domain (BGD)** configuration.

They are referenced from the [Blue-Green Deployment Configuration](/docs/how-to/blue-green-deployment-configuration.md) how-to guide.

## Layout

```text
docs/samples/bgd/
├── README.md
├── template/
│   ├── non-bgd/          # Before migration (single BSS namespace)
│   │   ├── simple.yaml
│   │   └── bss.yml.j2
│   └── bgd/              # After migration (origin, peer, controller, non-BG)
│       ├── bgd.yaml
│       ├── bg_domain.yml.j2
│       ├── bss.yml.j2
│       ├── bg-controller.yml.j2
│       ├── bg-plugin.yml.j2
│       └── data-management.yml.j2
└── inventory/
    ├── env_definition-non-bgd-baseline.yml
    ├── env_definition-bgd.yml
    └── env_definition-bgd-with-bg-ns-artifacts.yml
```

> [!NOTE]
> Tenant and Cloud templates are not duplicated here. When packaging a template artifact, include shared templates (for example from [`/docs/samples/template-repository/templates/env_templates/common/`](/docs/samples/template-repository/templates/env_templates/common/)) and set `templates_dir` in your build so descriptor paths resolve.

## How to use these samples

1. Copy `template/non-bgd/` into your Template repository under `templates/env_templates/` (or equivalent) to reproduce the starting point.
2. Apply changes from `template/bgd/` and update your Environment Template descriptor name in inventory.
3. Replace or merge `Inventory/env_definition.yml` using the files in `inventory/`.
4. Adjust artifact coordinates (`artifact`, `bgNsArtifacts`) to match your registry.
5. Run the Instance pipeline and verify `bg_domain.yml` and namespace folders under the generated environment.

## Migration path

| Step | Sample location |
|------|-----------------|
| 1. Non-BG template | [`template/non-bgd/simple.yaml`](template/non-bgd/simple.yaml) |
| 2. Non-BG inventory | [`inventory/env_definition-non-bgd-baseline.yml`](inventory/env_definition-non-bgd-baseline.yml) |
| 3. BGD template | [`template/bgd/bgd.yaml`](template/bgd/bgd.yaml) + Jinja files in same folder |
| 4. BGD inventory (single artifact) | [`inventory/env_definition-bgd.yml`](inventory/env_definition-bgd.yml) |
| 5. BGD inventory (split origin/peer artifacts) | [`inventory/env_definition-bgd-with-bg-ns-artifacts.yml`](inventory/env_definition-bgd-with-bg-ns-artifacts.yml) |

## Related documentation

- [Blue-Green Deployment Configuration how-to](/docs/how-to/blue-green-deployment-configuration.md)
- [Blue-Green Deployment feature](/docs/features/blue-green-deployment.md)
- [Template repository sample](/docs/samples/template-repository/templates/env_templates/bgd.yaml) (alternate reference layout)
