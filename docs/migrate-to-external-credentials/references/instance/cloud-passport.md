# Cloud Passport Credentials

Policy: [credential-policy.md](credential-policy.md) (read before convert).

## Scope

One Cloud Passport per apply batch: `*-creds.yml` + matching main file.

```text
environments/<cluster>/cloud-passport/*-creds.yml
environments/<cluster>/cloud-passport/<passport>.yml
```

Warn if other environments share this passport.

## Defaults (proposals only)

From policy: `tier: passport-tier`, path proposal `<cluster>`, create proposal `false`
(`creationOwner: pre-existing`). Confirm before apply. `create: true` only with explicit
EnvGene generation confirmation.

Heuristic provider markers in `credId` → `NEEDS_INPUT` (do not convert, do not remove `data`).

## Apply

1. Run `classify_credentials.py` - review decision records and evidence.
2. Confirm decisions (`confidence: confirmed`, `needsReview: false`).
3. `convert_credential_files.py --decisions-json ... --plan` then `--apply`.
4. `replace_macros.py` on the main file.

Shapes: [transforms.md](transforms.md).
