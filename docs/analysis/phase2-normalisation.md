# Parameter normalization

- [Parameter normalization](#parameter-normalization)
  - [Goal](#goal)
  - [Behavior must not change](#behavior-must-not-change)
  - [The flow](#the-flow)

## Goal

Normalization reduces the risk and the maintenance cost of an environment's configuration. Two outcomes
decide whether it succeeded, in priority order.

1. **Keep secrets contained.** No live secret is readable from Git, and a leaked secret reaches no more
   than its own environment or tenant. A leaked secret is the highest-severity failure a configuration
   can carry.
2. **Author a shared value once.** A value that holds for many environments lives in one file, so a
   change is one edit rather than many. Values duplicated across environments drift apart, and that
   drift is the main maintenance cost.

Casing, quoting, block scalars, flat keys, native types, and reproducible values are subordinate. They
matter only when they serve one of these two outcomes or a rule that EnvGene enforces. Normalization
also never changes what deploys. That is a guarantee of the process,
[Behavior must not change](#behavior-must-not-change), not a benefit it produces.

## Behavior must not change

Normalization changes where and how a parameter is written, never what a consumer resolves, unless a
person approves the change.

The override chain replaces a whole value rather than merging into it, so moving a value between layers
or collapsing two keys can change what resolves with no visible error. The design therefore compares the
resolved configuration, the Effective Set, before and after each change. An unchanged Effective Set is
the acceptance criterion. A clean pipeline run is not, because it proves the output is structurally
valid, not that the resolved values are the same.

Four decisions follow and are fixed:

1. **Unit of work.** Discovery reads all environments, clusters, and the template repository together,
   not one environment at a time.
2. **Consumer knowledge.** The design does not build a map of which consumer reads which key. The
   Effective Set comparison serves that purpose instead.
3. **Acceptance criterion.** The Effective Set difference equals the approved change. Any other
   difference is a defect, and the operation is undone.
4. **Automation boundary.** The Effective Set comparison decides whether an operation changed Behavior,
   not the rule it came from or a regular-expression score.

## The flow

Each rule plays one of four roles. The role, not the rule's area, decides how normalization handles it.

- **Gate.** A mechanical check that blocks generation or catches a new violation. Run before the baseline
  and again at the end.
- **Auto.** The tool applies the rule, and the comparison must show no difference. Safe, because the
  resolved key and value at every consumer stay the same.
- **Confirm.** The tool proposes the change, the comparison shows it, and a person approves it. The
  person weighs the external consumer, which the comparison does not show.
- **Flag.** The tool only detects a candidate. Choosing or making the fix needs consumer or domain
  knowledge, so a person decides and often edits by hand.

The sequence:

1. **Validate and take a baseline.** Run the Gate rules `PLACE-5`, `HYG-3`, `HYG-2`, and `NAME-4`. A
   violation blocks generation, so propose a fix, a person approves it, and apply it - no baseline exists
   yet to check against. Build the inventory across every environment, cluster, and the template
   repository, classify each parameter, and read the `.j2` files for Shared Template Variables. Generate
   the Effective Set for every environment in scope and keep it as the baseline.
2. **Contain secrets.** The Confirm rules `SEC-1` and `SEC-2` - detection proposes each secret, a person
   confirms, then the value is rewritten and compared. The Flag rules `SEC-3` and `SEC-4` are reported
   for a person, because the fix is encryption or rotation, not a parameter edit.
3. **Apply the safe refactors.** The Auto rules `PLACE-1`, `PLACE-2`, and `VAL-3`. Apply each,
   regenerate, and require an empty comparison. A difference is a defect: undo it. `PLACE-3` joins this
   set once the Cloud Passport contract exists.
4. **Propose the surface changes.** The Confirm rules `NAME-2`, `NAME-3`, `VAL-1`, `VAL-2` (trailing
   slash), `VAL-7`, and `HYG-1`. Apply each, regenerate, and show the difference to a person, who
   approves it, weighing the external consumer, or undoes it.
5. **Report the rest for a person.** The Flag rules `PLACE-4`, `NAME-1`, `VAL-4`, `VAL-5`, `VAL-6`,
   `VAL-8`, `VAL-2` (raw IP), `FLAG-1`, `HYG-4`, and `HYG-5`. The tool detects each candidate and reports
   it. Resolving one, for example unifying casing, can enable an Auto or Confirm operation that a later
   pass picks up.
6. **Validate and compare.** Re-run the Gate rules, regenerate the Effective Set, and compare it with the
   baseline. The whole difference equals the approved changes from steps 2 and 4, and nothing else. Write
   to `output-normalised/` only: the inventory, the snapshots and their difference, `normalization-log.yml`,
   and `normalization-report.md`.
