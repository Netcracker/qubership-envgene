# Use case design

How to write use cases under `/docs/use-cases/`: observable behavior in a structured format that
doubles as test-design input.

- [Use case design](#use-case-design)
  - [Apply equivalence class partitioning](#apply-equivalence-class-partitioning)
  - [When to split UCs](#when-to-split-ucs)
  - [When to merge UCs](#when-to-merge-ucs)
  - [Abstract steps over implementation mechanics](#abstract-steps-over-implementation-mechanics)
  - [Results: observable outcomes only](#results-observable-outcomes-only)

Use cases (UCs) live in `/docs/use-cases/`. They describe observable system behavior in a
structured format (Pre-requisites, Trigger, Steps, Results) and serve both as documentation and
as test-design input.

**Scope:** All rules in this section apply to **new and modified UCs only**. Existing UCs that
violate these rules are not affected and do not need rewriting unless the surrounding lines are
being edited for other reasons.

**Rationale:**

- **Equivalence Class Partitioning** is the standard test-design technique (ISTQB) and aligns
  with BDD Scenario Outlines and modern API documentation style (Stripe, GitHub, Google API
  Design Guide).
- Matrix decomposition (UC per combination of variables) creates combinatorial bloat where
  most UCs are clones differing in one word.
- Implementation-detail leaks bind documentation to a specific code shape. Abstraction
  decouples docs from implementation churn.

## Apply equivalence class partitioning

**Do not enumerate variants of an identical-behavior UC. Merge them into a single parameterized
UC.**

When two or more candidate UCs would describe the same observable behavior with only a parameter
difference (e.g., job name, trigger flag, environment kind), they belong to the same equivalence
class. They must be merged into a single UC with the variable parameterized via the Trigger
section.

❌ **INCORRECT (enumerated variants):**

```markdown
### UC-X-1: Validation fails at `generate_effective_set`
...

### UC-X-2: Validation fails at `cmdb_import`
...
```

Two UCs that differ only in job name. Both invoke the same validator and produce the same error
message format. This is one equivalence class, not two.

✅ **CORRECT (parameterized trigger):**

```markdown
### UC-X-1: Validation fails

**Trigger:**

> [!NOTE]
> One of the following conditions must be met:

1. Instance pipeline is started with `GENERATE_EFFECTIVE_SET: true`
2. Instance pipeline is started with `CMDB_IMPORT: true`
```

## When to split UCs

Split into separate UCs only when behavior differs in an observable way:

- Different validators or handlers (e.g., parameter validator vs credential validator).
- Different error message format or different output structure.
- Different post-conditions or side effects.

## When to merge UCs

Merge into a single parameterized UC when:

- Same observable behavior.
- Same error message format.
- Same outcome.
- Differences are limited to parameter values (job name, flag values, environment names).

## Abstract steps over implementation mechanics

Steps describe what happens, not how it is implemented. Avoid `Reads X`, `Iterates Y`,
`Detects Z` phrasing - it leaks implementation that the documentation cannot guarantee will
match.

❌ **INCORRECT:**

```markdown
**Steps:**

1. The `generate_effective_set` job runs in the pipeline:
    1. Reads the existing Cloud and Namespace YAMLs from the Environment Instance.
    2. Iterates over `deployParameters`, `e2eParameters`, and ...
    3. Detects a value equal to `envgeneNullValue`.
    4. Aborts with a validation error.
```

✅ **CORRECT:**

```markdown
**Steps:**

1. The `generate_effective_set` job runs.
2. Parameter validation detects an unresolved `envgeneNullValue`.
3. The job aborts with a validation error.
```

## Results: observable outcomes only

Document what the operator observes, not downstream consequences that the documented component
does not control.

❌ **INCORRECT:**

```markdown
**Results:**

1. The job fails with the message: ...
2. No Effective Set is produced.
3. Deployment is blocked.
```

`Deployment is blocked` assumes authority over deployment that the documented component does
not have.

✅ **CORRECT:**

```markdown
**Results:**

1. The job fails with the message: ...
```
