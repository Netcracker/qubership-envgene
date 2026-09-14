# Grounding - the observable-channel gate

Phase 3 is the gate that keeps generated scenarios from being empty. A scenario is only worth writing
if its outcome can be observed from outside the system, because a check against unobservable internal
state passes whether or not the behavior works. This is the exact failure `bdd-test-review` hunts, so
the generator refuses to produce it in the first place.

Run this gate on every case before rendering. A case that passes carries a verified channel into
rendering. A case that fails is reported as `ungroundable`, never rendered as if it were a real test.

## The channel requirement

Every case outcome must attach to an observable channel: something a step can actually assert against.
The channels available in this repository, from the existing suite:

- **a log line** - "the pipeline log contains X".
- **an error message** - the job fails with an error that names the specific cause.
- **an emitted request** - a request arrives at a mock registry or store, with a distinguishing target.
- **an output or golden file** - a file is written, or a directory contains exactly the expected files.

An outcome phrased as internal state ("resolution uses the root-level copy", "the entry is marked
stale") has no channel. Rewrite it into the observable effect that state produces ("the request targets
the root-level registry", "the directory retains exactly K files"), or flag it if no such effect exists.

Give fixtures distinguishing traits so the outcome is checkable. When two copies of a definition could
both satisfy an outcome, a distinct registry name per copy makes the emitted request reveal which copy
won. Without the distinguishing trait, the check cannot tell the right outcome from a wrong one.

## Truth-adaptive verification

Where you confirm the channel exists depends on whether the code exists yet. Phase 1 recorded which
case you are in.

### Post-code (an implemented PR or a shipped feature)

The code and often existing `.feature` and step definitions exist. Verify each channel against reality,
borrowing the discipline from `discrepancy-audit`:

- Confirm the code actually emits the outcome on the channel. Do not trust the outcome's name - trace
  the execution path to the point where the log line, error, request, or file is produced.
- For a file or golden outcome, find the writer. An outcome that asserts a file no code writes is not
  grounded.
- Check whether the existing step vocabulary can already assert the channel. If a step like "the SBOM
  directory X contains N files" exists, the case is paste-ready. If not, note that a new step is needed.
- For a negative, confirm the failure actually reaches the recorded failure point in the code, not an
  earlier stage.

### Pre-code (a CR for unbuilt behavior)

The code does not exist, so there is nothing to trace. Ground against the design instead:

- Require the design or CR to name the channel. "The job fails with an error naming the missing
  definition and both checked locations" names the channel (the error message) even though no code
  produces it yet. The acceptance criterion binds to that named channel.
- Mark these outcomes as pre-code and unverified against code. When the code lands, that named channel
  is exactly what the test will check, which is the point of authoring the acceptance criteria first.
- If the design names no channel for an outcome, the outcome is not yet a testable contract. Flag it as
  an open question for the design rather than inventing a channel.

## The ungroundable report

Collect every case that has no channel - no real one post-code, no design-named one pre-code. Report
them as a short list with the reason each one lacks a channel. These are not failures of the skill, they
are findings: either the outcome needs to be restated observably, or the behavior needs a new observable
effect before it can be tested. Surfacing them is more useful than hiding them inside a scenario whose
Then asserts nothing.
