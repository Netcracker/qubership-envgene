# App Reg Def service - design docs

> _Placeholder. One paragraph: what the service is - a runtime resolver and cache over a git source of
> truth that turns `application:version` into artifact download-info plus registry sections, blind on
> credentials._

## Documentation map

> _Placeholder. The table below is the real map. Each row is one document and the single job it does._

| Document                        | Audience              | Job                                         |
|---------------------------------|-----------------------|---------------------------------------------|
| architecture.md                 | developer, architect  | components, flows, logical topology         |
| consistency-and-sync.md         | developer             | cache, watermark, resync, commit race       |
| api-reference.md + openapi.yaml | consumer, developer   | the API contract                            |
| data-model-and-layout.md        | def author, developer | RegDef v2, AppDef, repo layout, naming      |
| deployment-and-operations.md    | operator              | profiles, config, scaling, failure, metrics |
| adr/                            | architect, reviewer   | the load-bearing decisions and why          |
| glossary.md                     | all                   | the terms used across these docs            |

## Source

> _Placeholder. These docs render from the exploration brief (../brief.md), which holds the Decision Log
> and the open backlog._
