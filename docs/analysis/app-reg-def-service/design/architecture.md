# Architecture

> _Placeholder. The internal wiring for a developer: the components, how the three flows run through them,
> and the logical topology. Not the API contract (see api-reference) and not the hard consistency model
> (see consistency-and-sync)._

## System overview

> _Placeholder. One paragraph plus a context diagram: the service sits over the git defs repo, serves
> consumers (EnvGene, DPG), and never holds a registry secret (blind)._

## Components

> _Placeholder. The five runtime components (HTTP API, Resolver, Cache, Indexer, Writer) and the two
> shared modules (Normalizer, Git adapter), each with its one responsibility and its dependencies._

## Data flows

> _Placeholder. A sequence diagram per flow: read (API to Resolver to Cache), sync (webhook or backstop to
> Indexer to Normalizer to Cache), write (API to Writer to git to Indexer to the response)._

## Logical topology

> _Placeholder. The lite and HA shapes and the multi-cluster model at the logical level. The operational
> detail (manifests, config) lives in deployment-and-operations._

## Dependency direction

> _Placeholder. Ports and adapters: the domain (Resolver, Normalizer) depends on the Cache and Git ports,
> not on git, HTTP, or the store implementation._
