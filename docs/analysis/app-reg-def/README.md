# App Reg Def design docs

The App Reg Def capability resolves an application to its registry definition and artifact coordinates, so a
consumer can download its deployment descriptor. It has two variants over one shared model and contract, a
central blind service and an in-process library.

## Documentation map

Shared, read first:

- [brief.md](brief.md) - the exploration brief, decisions and the open backlog.
- [model.md](model.md) - the objects and the repository layout.
- [resolver-contract.md](resolver-contract.md) - the three layers and the resolve-and-build contract.
- [glossary.md](glossary.md) - the terms.

Service variant:

- [service/architecture.md](service/architecture.md) - components, flows, topology.
- [service/consistency-and-sync.md](service/consistency-and-sync.md) - cache, resync, commit race.
- [service/api-reference.md](service/api-reference.md) - the HTTP contract.
- [service/openapi.yaml](service/openapi.yaml) - the machine-readable contract.
- [service/deployment-and-operations.md](service/deployment-and-operations.md) - profiles, scaling, metrics.

Library variant:

- [library/interface-spec.md](library/interface-spec.md) - the python client and the build functions.
