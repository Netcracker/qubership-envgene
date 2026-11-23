# Data model and repository layout

> _Placeholder. The objects the service serves and how they live in git. Fields reference the schemas and
> the RegDef v2 analysis, this doc does not restate them in full._

## Application definition

> _Placeholder. The thin pointer: name, registryName, groupId, artifactId, solutionDescriptor, parameters,
> metadata. References schemas/appdef.schema.json._

## Registry definition (v2)

> _Placeholder. Registry coordinates plus the authConfig map. References schemas/regdef-v2.schema.json and
> docs/analysis/regdef-v2-extensions.md._

## Deployment descriptor and solution descriptor

> _Placeholder. What the DD and the SD are, and that the service resolves coordinates to them but does not
> parse them._

## Repository layout

> _Placeholder. The dedicated defs repo: flat application-definitions/ and registry-definitions/, one file
> per def, zone folders deferred._

## Naming conventions

> _Placeholder. Casing by role: kind PascalCase, path identifiers (folders, files, name) kebab DNS-safe,
> object fields camelCase. The file stem equals the def name._
