# ADR-0013: Keep list parameters atomic when separating secured from non-secured values

Status: Proposed

## Context and problem statement

The Effective Set generator splits every environment parameter into two value files by sensitivity. Secured
values go to the credentials file, everything else to the deployment parameters file. The deployer hands both
to Helm as separate value files. For a map this is safe, because Helm deep-merges maps and the two halves
rejoin. For a list it is not. The generator splits a list element by element into two partial lists under the
same key, and Helm replaces a list wholesale rather than merging it. At deploy time one partial list overwrites
the other, so the secret, and part of the non-secured data, disappears with no error. Any environment that
places a secret inside a list value ships a silently incomplete deployment today.

## Decision drivers

- A lost secret is a correctness and security failure, so the fix must not rest on a mechanism that can leave a
  secret behind.
- The deployer is owned by another team, so a change confined to the Effective Set generator ships far sooner
  than one that changes how the deployer reads value files.
- Local and external credential environments should keep the same file layout, so moving an environment from
  local to external does not reshuffle where parameters live.

## Considered options

- Keep list values atomic, routing a whole list to one file.
- Encrypt only the secured values in place and add a manifest of sensitive keys.
- Merge the two partial lists on the deployer side before Helm sees them.

## Decision outcome

Chosen: keep list values atomic, because it removes the data loss with a change confined to the Effective Set
generator and cannot leave a secret in plaintext. A list that holds a secured value at any depth is written
whole to the credentials file. A list with no secured value stays whole in the deployment parameters file. Maps
keep their per-key separation. The rule applies the same way to local secrets and to external credential
references.

Before, a list that mixes a host and a secret is torn in two, and the halves overwrite each other:

```yaml
# deployment-parameters.yaml  (non-secured half)
DATABASES:
  - name: primary

# credentials.yaml  (secured half)
DATABASES:
  - password: <secret>
```

Helm keeps only one file's list, so the other half is lost. After, the whole list travels together in one file
and arrives intact:

```yaml
# credentials.yaml  (whole list)
DATABASES:
  - name: primary
    password: <secret>
```

## Pros and cons of the options

### Keep list values atomic (chosen)

- Good, because the change is confined to the Effective Set generator and needs nothing from the deployer team,
  so it ships quickly.
- Good, because a list key now exists in exactly one value file, so there is no cross-file merge that can drop
  it and nothing to get wrong.
- Good, because it is fail-closed. A secret is always written to the encrypted credentials file, never left in
  plaintext.
- Good, because local and external environments keep the same file layout, so a local-to-external migration does
  not move parameters between files.
- Neutral, because it also corrects a pre-existing defect where a list carrying an external credential reference
  dropped its remaining elements.
- Bad, because the non-secured fields of a mixed list are now stored together with the secret in the
  credentials file. In a local environment they are encrypted with it, which lowers their visibility in version control and
  makes troubleshooting that data harder.

### Encrypt only the secured values in place, with a manifest

- Good, because every field stays in its original file, so troubleshooting sees the non-secured data in place
  and nothing is over-encrypted.
- Bad, because it requires the deployer team to decrypt the deployment parameters file, a cross-team change that
  delays the fix.
- Bad, because it is fail-open. A secured value that is not marked stays in plaintext, so a marking gap leaks a
  secret.
- Bad, because it adds a new Effective Set artifact and a standing obligation to keep the manifest in step with
  the data.

### Merge the two partial lists on the deployer side

- Bad, because it requires a cross-team change to the deployer.
- Bad, because recombining two partial lists has no natural key to merge on, so the merge is bespoke and can
  silently deliver the wrong value.
- Bad, because the data stays split across two files in version control, so troubleshooting is no better than
  before, while the cost is higher than the manifest option.

## Consequences

- Positive: an environment that places a secret inside a list value now deploys with the secret and all list
  data intact, and the change lives entirely within the Effective Set generator.
- Positive: the long-standing defect that dropped elements from a list carrying an external credential reference
  is resolved by the same rule.
- Negative: the non-secured fields of a mixed list are relocated into the credentials file. In local
  environments they are encrypted alongside the secret, so they no longer appear in plaintext in version control
  and are harder to inspect while troubleshooting. In external environments they remain readable, because that
  file holds references rather than ciphertext.

## More information

- Specs: [secured-parameter-separation](/openspec/changes/fix-es-secret-list-split/specs/secured-parameter-separation/spec.md)
- Proposal: [fix-es-secret-list-split](/openspec/changes/fix-es-secret-list-split/proposal.md)
