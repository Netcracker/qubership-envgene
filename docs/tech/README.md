# Technical documentation

This directory holds implementer-facing technical contracts for EnvGene: resolution algorithms,
internal pipeline artefacts, and validation rules that do not belong in user-facing feature
explanations.

Use a feature document under `/docs/features/` for the problem statement and product behaviour.
Use an object entry under `/docs/envgene-objects.md` for the authored or generated file shape.
Put the detailed algorithm here and link both ways.

## Documents

- [Namespace map](/docs/tech/namespace-map.md) - How `compute_namespace_map` resolves
  `deployPostfix` to a Namespace `name`, including Blue-Green Domain sides
