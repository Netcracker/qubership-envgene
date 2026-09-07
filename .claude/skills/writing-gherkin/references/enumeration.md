# Enumeration - deriving the case list

Phase 2 turns the behavior and its variation axes into a list of cases. A case is a distinct situation
the behavior must handle, stated precisely enough that one scenario can check it. The list drives
everything downstream, so completeness here matters more than polish.

The method is the union of what the two consumer skills already do by hand: the completeness matrix that
`bdd-test-review` builds, and the independent-failure enumeration that `design-to-cr` writes into an
Acceptance section.

## Step 1 - build the variation matrix

Take the variation axes from phase 1 and cross them. Typical axes in this repository:

- **action** - create, update, delete, warmup, and so on.
- **place** - tenant, cloud, namespace, application, or the topology positions baseline and satellite.
- **mode** - dry-run versus apply, a toggle set versus absent, a run mode.
- **pipeline flow** - the entry path that reaches the behavior. In this repository the same outcome is
  produced by more than one flow: the legacy a-la-carte run (`PIPELINE_TYPE` LEGACY, selected by the
  `ENV_BUILDER` / `GENERATE_EFFECTIVE_SET` toggles) and the modern-toolset run (`PIPELINE_TYPE`
  GITLAB_DEPLOY with an `OPERATION_TYPE`, which reaches env build and effective-set generation with no
  toggles at all). The two flows often run different code for the same output - they even use different
  effective-set entrypoints - so each flow is its own case unless the behavior is provably
  flow-independent.
- **object shape** - the discrete shapes a payload can take (a credential type, a topology case).
- **output surface** - every distinct artifact or context the behavior writes to: each generated file,
  each effective-set context, each output channel. A behavior that writes several outputs usually
  applies a different rule per output, so each surface is its own axis. A surface that explicitly
  EXCLUDES the behavior is a case too - the exclusion is a testable rule, not an absence to skip.
- **entity category** - every kind or role of the central entity the behavior handles: for example a
  user-supplied instance of it, a system-supplied one, and a built-in reference to one. Each category
  often carries its own rules and its own failures, on its own code path.

Cross the axes that actually interact. Do not cross axes that are independent - a full Cartesian product
of unrelated axes produces cases that cannot fail independently, and those are noise. The matrix is a
tool for finding combinations you would otherwise miss, not a mandate to enumerate every cell.

Before you leave Step 1, list every output surface and every entity category the docs name, out loud,
and confirm each one has at least one case or a stated reason it does not apply. The most common miss is
a surface or a category that the docs mention once and the enumeration never returns to - a second
output context that carries the same references under a different rule, or a system or built-in variant
of the entity with its own constraints. Naming them explicitly is what stops the matrix from silently
collapsing to the one surface and the one category you started with.

Do the same for the pipeline flows. When a behavior is reachable through more than one flow, find where
the flows actually diverge - the step whose code differs. A step that runs the same code in both flows
(env build renders the instance identically whether it was reached by a toggle or by a modern-toolset
deploy) is flow-independent: cover it once and say so. A step that differs (effective-set generation
dispatches to a different entrypoint per flow) is a real second case. You need not re-run the full shape
matrix in every flow when the differing step delegates the actual shaping to shared code: cover the
shape variants once under one flow, then add one reachability smoke under each other flow that confirms
that entrypoint reaches the surface and emits it. Either way, state the split in the output - which flow
each case runs under, and why the others are a smoke or omitted - so the flow choice is never left
implicit. Silently covering one flow, legacy or modern, is the most common way a family looks complete
while covering half the behavior; a redundant per-flow copy of a step that behaves identically in both
is the opposite waste. Targeting the divergence avoids both.

## Step 2 - one happy path per valid combination

For each combination that produces an observable success, write one happy-path case. Its outcome is the
success the behavior promises, and it must be observable (see grounding).

## Step 3 - each independent failure mode

Add a case for every way the behavior can fail independently of the others. This is the rule that keeps
the list honest, borrowed from `design-to-cr`:

- A case earns its place only when it can fail on its own. A missing folder and a missing file inside
  that folder are two cases, because each fails for its own reason and produces its own error.
- A case that is only logically derivable from another is not a separate case. If case B cannot fail
  unless case A already failed, B is not independent.
- Enumerate the failure, not the mechanism. "The registry rejects the request" is a failure mode. "The
  retry counter reaches three" is a mechanism, not a case, unless the retry limit is the documented
  behavior under test.

## Step 4 - mark discriminating siblings

Two cases are siblings when they differ only in a precondition that flips the outcome: a mode set versus
absent, a file present versus missing, an external credential versus a local one. For every sibling
pair, record the discriminating precondition. Rendering will put it in the Given so the outcome cannot
be read as applying to the sibling.

## Step 5 - record the failure point for negatives

For each failure case, record where the behavior fails - the stage that produces the error. This is the
rule `bdd-test-review` uses to catch tests that prove nothing: a "rollback on mid-processing failure"
case whose input dies at upfront schema validation never exercises rollback and silently duplicates the
plain schema negative. The failure point is what makes the negative discriminating, and rendering writes
it into the Then.

## What each case carries into phase 3

- A discriminating precondition (fixture, placement, mode).
- The observable outcome the case asserts.
- For negatives, the failure point the outcome must reach.
- A short note on which variation cell or failure mode the case covers, so the list can be checked for
  gaps against the matrix.

## Check the list before grounding

Read the list back against the matrix. Every documented variation is either a case or a deliberate
omission with a reason. Every failure mode named in the source has a case. Present the list to the user
at this point - it is far cheaper to add a missed case here than after both renderings exist.
