# Resolver contract

The three layers that turn an application into a downloaded artifact, and how the service and the library
share them. The object shapes are in [model.md](model.md). This is the high-level picture, the detailed
function contracts follow later.

```mermaid
flowchart LR
  repo[("appregdef storage (git)")]
  subgraph svc["appregdef service"]
    sr["resolve(app) -> Application"]
  end
  subgraph client["appregdef-client (python)"]
    cr["resolve(app) -> Application"]
    ba["build_artifact(appdef, version) -> Artifact"]
    bp["build_provider(registry, creds) -> ArtifactProvider"]
  end
  af["artifacts_finder<br/>probe by strategy, auth, download"]
  repo --> sr
  repo -. "open_defs" .-> cr
  sr -. "connect" .-> cr
  cr -->|appdef| ba
  cr -->|registry| bp
  ba -->|Artifact| af
  bp -->|ArtifactProvider| af
```
