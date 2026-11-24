# App Reg Def resolver - interface specification

The library (working name `appregdef-resolver`) is the python client of the App Reg Def capability. It
resolves an application to its defs and maps them to artifacts_finder inputs. The three-layer split and the
contract are in [resolver-contract.md](../resolver-contract.md), and the objects are in
[model.md](../model.md).

## What it does

- `resolve(app) -> Application` - join the AppDef to its RegDef, over a git backend or over the service.
- `build_artifact(appdef, version) -> Artifact` - the DD or SD artifact coordinates.
- `build_provider(registry, creds) -> ArtifactProvider` - the configured registry provider, for a v1 or a
  v2 RegDef.

The registry probing, the snapshot resolution, the auth, and the download are artifacts_finder's, not the
library's.

The detailed function contracts, the parameters, the errors, and the scenarios follow later.
