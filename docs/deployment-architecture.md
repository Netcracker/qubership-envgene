# Deployment architecture

- [Deployment architecture](#deployment-architecture)
  - [CMDB](#cmdb)
  - [No-CMDB v1](#no-cmdb-v1)
  - [No-CMDB v2](#no-cmdb-v2)
  - [Determine an environment's architecture](#determine-an-environments-architecture)

The DevOps toolset, including EnvGene, operates each environment in one of three deployment
architectures. An architecture defines where EnvGene delivers its output and which component deploys
it. Each environment declares its architecture in its
[Environment Inventory](/docs/envgene-configs.md#env_definitionyml). Environments in the same
repository can use different architectures.

## CMDB

EnvGene imports the Environment Instance into an external CMDB, integrated through
`inventory.deployer`. The deployment tooling reads the parameters from the CMDB.

## No-CMDB v1

EnvGene generates the [Effective Set](/docs/features/effective-set-generation.md) and commits it to
the Instance repository. The deployment tooling reads the Effective Set from the Instance repository.

## No-CMDB v2

EnvGene generates the Effective Set and splits it by context. It commits the topology and pipeline
contexts to the Instance repository and pushes the other contexts to a separate DCL repository. In
this architecture, the EnvGene pipeline also generates the Argo CD configuration and synchronises it
with the cluster.

## Determine an environment's architecture

`inventory.noCmdbVersion` takes precedence over `inventory.deployer`. When `noCmdbVersion` is set, it
selects the architecture on its own. When it is absent, `deployer` decides.

| Architecture | Condition                                   |
|--------------|---------------------------------------------|
| No-CMDB v1   | `noCmdbVersion` is `v1`, or neither is set  |
| No-CMDB v2   | `noCmdbVersion` is `v2`                     |
| CMDB         | `noCmdbVersion` is unset, `deployer` is set |
