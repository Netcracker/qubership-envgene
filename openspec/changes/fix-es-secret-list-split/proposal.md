# Proposal

## Why

When the Effective Set generator separates secured parameters from non-secured ones, it splits a
parameter whose value is a list across the deployment parameters file and the credentials file. The
deployer hands these to Helm as separate value files, and Helm replaces a list wholesale instead of
merging it element by element. The two partial lists overwrite each other at deploy time, so the secured
value, and part of the non-secured data, are silently lost. Every environment that places a secret inside
a list value is exposed today.

## What Changes

Effective Set generation, secured and non-secured separation:

- Treat a list parameter as an atomic unit during separation. A list that holds a secured value at any
  depth is written whole to the credentials file. A list that holds no secured value stays whole in the
  deployment parameters file. Map parameters keep their current per-key separation, which Helm merges
  correctly.
- Apply the same atomic rule to local secrets and to external credential references. A list that carries
  an external credential reference is written whole with every reference resolved and no element dropped.
  This also corrects a pre-existing defect where a list containing an external credential reference lost
  its remaining elements.
- The behavior change is confined to the version 2 Effective Set path, which is the default. The version 1
  path already separates whole top-level keys atomically and is unchanged.

Accepted trade-off: the non-secured fields of a mixed list are now co-located with the secret in the
credentials file. For a local secret they are encrypted together with it, which lowers their plaintext
visibility. For an external credential reference they stay readable, because the credentials file holds
references, not ciphertext. Alternatives that keep every field in its original file were rejected because
they require a change on the deployer side. The reasoning is recorded in
[ADR-0013](/docs/adr/0013-keep-list-parameters-atomic-in-effective-set-separation.md).

## Capabilities

### New Capabilities

- `secured-parameter-separation`: how the Effective Set generator routes each parameter to the deployment
  parameters file or the credentials file by its sensitivity, including the atomicity rule for list values
  and the handling of external credential references.

### Modified Capabilities

<!-- None. No existing specs under openspec/specs/. -->

## Impact

- Effective Set deployment context, for environments that place a secret inside a list value: a mixed list
  now appears whole in the credentials file and no longer appears in the deployment parameters file. This
  removes the deploy-time data loss.
- No change to the deployer, to Helm charts, to credential encryption, or to any Effective Set file layout
  or schema. No new Effective Set artifact.
- Environments on the version 1 Effective Set path are unaffected.
- Documentation: the description of secured and non-secured parameter separation gains a note that list
  values are atomic. Confirmed during the documentation stage.
