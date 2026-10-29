# Cred store

- [Problem](#problem)
- [Design](#design)
- [Cred store sources](#cred-store-sources)
- [Cred store and env instance store](#cred-store-and-env-instance-store)
- [What changes for the user](#what-changes-for-the-user)
- [Out of scope](#out-of-scope)

## Problem

On an instance with 280 SOPS cred files:

- `git_commit` takes 50 s. `minimize_cred_diffs` takes 48.4 s of it.
- `generate_effective_set` takes 22 s. Re-encryption of the cred files takes 14.87 s of it, 67%.

Root cause: `EnvBuildStep` and `GenerateEffectiveSetStep` each decrypt every cred file at start and encrypt
every cred file at end. SOPS writes a new nonce, MAC, and `lastmodified` on each encryption. So every cred
file differs from HEAD, even when its content did not change. `git diff HEAD` then lists all 280 files, and
`minimize_cred_diffs` runs two SOPS processes per file to bring each file back to its HEAD bytes.

Also, cred files lie decrypted on disk during both steps. A failed step leaves them decrypted, and they get
into the job artifact.

## Design

```text
run_single_env_pipeline
  open cred store
    PassportStep ... EnvBuildStep      read and write creds through the cred store
    GenerateEffectiveSetStep           creds to the CLI as an object, ES creds back as an object
    on success: write changed creds encrypted
  GitCommitStep, CMDB_import
```

- **Cred files on disk are always encrypted.** No step decrypts a cred file in place.
- **The cred store lives from the first step to `GitCommitStep`.** It writes changed files after the last
  step before `GitCommitStep`, also when `GenerateEffectiveSetStep` is skipped. It is separate from
  `CurrentEnvInstanceStore`, which lives inside `EnvBuildStep` and ends with `flush()`.
- **The cred store keys a file by its resolved absolute path.** Callers pass `str`, `Path`, and relative
  paths for the same file.
- **A put into the cred store is thread-safe.**
- **`creds_rotation` reads and writes cred files in its own process.** Today it reads with a
  `multiprocessing.Pool` and writes with a `ProcessPoolExecutor` (`creds_rotation/utils/cred_utils.py`).
  A child process does not see the cred store in memory. The pools only parallelized SOPS calls, and the
  cred store makes reads from memory and writes are deferred: the step only puts objects into the store, and SOPS encryption runs once at store close, in parallel threads
- **At the end the cred store writes only changed files.** A file is changed when its object differs from
  the decrypted object of its original bytes. A changed or new file is encrypted by SOPS. An unchanged file
  is not touched, so `git diff` skips it.
- **The cred store compares a cred file in Python, an ES cred file in `sops edit`.** Steps read cred files
  with `get`, so their decrypted original is in memory and the compare costs nothing. Nobody reads ES cred
  files, so the cred store does not decrypt them: an ES cred file the CLI returns goes to `sops edit`
  directly, and the editor script compares the objects. A separate decrypt would repeat the decrypt that
  `sops edit` does anyway. SOPS calls per file:

  | File | Not changed | Changed |
  |---|---|---|
  | Cred file read with `get` | 0 | 1: `sops edit` |
  | Cred file only put: discovery creds, inventory | 1: decrypt to compare | 2: decrypt, `sops edit` |
  | ES cred file | 1: `sops edit`, exit 200, bytes kept | 1: `sops edit` |

  An ES cred file gets no compare when its literal keys changed, or it is written plain: with `crypt: false`
  or without literal values. The rule for ES cred files is not used for other cred files: with
  `crypt: false` there is no `sops edit`, and an unchanged file would be rewritten on every run.
- **A changed file is written with one `sops edit` on its original bytes.** Values that did not change keep
  their old ciphertext, so the diff is minimal at once. A new file has no original bytes and gets a plain
  SOPS encrypt.
- **`minimize_cred_diffs` is removed.** No cred file reaches `GitCommitStep` with a diff that is not
  minimal.
- **`sops edit` runs in parallel.** `max_workers = 1` for `minimize_diff` came in #1511 together with the
  move of `EDITOR` from `os.environ` to the environment of each SOPS process. With that move parallel runs
  are safe. `minimize_cred_diffs` already runs `sops edit` in a thread pool.
- **A failed flow writes no creds.** Disk keeps the encrypted files of the previous run. No `finally` is
  needed.
- **The CLI gets the env creds on stdin and returns the ES cred files in a pipe of their own.** The output is
  one JSON object, path to content. Python opens a pipe and passes its write end as `--creds-output=/dev/fd/N`.
  Stdout is not used for the JSON: `run-java.sh` prints its `exec java ...` line to stdout before Java
  starts, and `JAVA_DIAGNOSTICS` sends GC logs there. Any of them would break the JSON. Without
  `--creds-output` the CLI writes the JSON to stdout, for a manual run. The CLI logs go to stderr.
- **`external-credential/external-credentials.yaml` is not in the cred store.** It holds references to a
  secret store and no secret values. The CLI writes it to disk as now, and `external-cred-provision` reads
  it from disk as now. Nothing encrypts it.
- **The cred store reads the encrypted bytes of all cred files of the env when it opens, before the first
  step.** The files are those of `get_all_necessary_cred_files`: `Credentials/`, `cloud-passport/`,
  `effective-set/`, and the others. Reading bytes needs no SOPS call. The cred store needs the original
  bytes of a file it writes, as the base for `sops edit`. Three steps delete cred files after the cred store
  opens:

  | Step | Deletes | Put again | Needs original bytes |
  |---|---|---|---|
  | `GenerateEffectiveSetStep` | ES directories with `credentials.yaml` and `collision-credentials.yaml` | yes, the CLI returns them | yes |
  | `PassportStep` | `cloud-passport/` except `<cloud>-creds.yml`, so `credentials/<cloud>.yml` | no | no |
  | `InventoryGenerationStep` | a credentials object with `action: delete`, the env directory with `envDefinition` `action: delete` | no | no |

  Only ES needs the original bytes: the ES modes delete a directory long before the cred store writes, and
  without the original bytes every ES cred file would get a plain encrypt and a full diff on each run.
- **The ES modes delete ES cred files with their directories, unlike cloud passport cleanup.** Cloud passport
  cleanup keeps `<cloud>-creds.yml` because discovery returns it on every run. An ES directory is deleted to
  remove the applications that are no longer in the plan. If the ES modes kept `credentials.yaml`, the file
  of a removed application would stay, and something would have to delete the cred files the CLI did not
  return. The original bytes solve it without changes in the ES modes.
- **Comments leave a cred file with its next value change.** The cred store removes the comments of every
  cred file it writes, and it writes a file only when a value changed. The compare ignores comments. So a
  file with no value change keeps its old comments, and a change of a comment alone is not written. Before
  this change it was the same: `minimize_cred_diffs` gave an unchanged file its bytes from HEAD back, with
  the comments. Removing the comments of every file on every run would rewrite every cred file and bring
  back the diff this change removes. The header of discovery creds follows the same rule: a new header text
  reaches `<cloud>-creds.yml` with the next change of the discovered creds.
- **Known limit: an inventory request that deletes an env and creates the same env creds again loses
  them.** `envDefinition` with `action: delete` deletes the env directory, then a credentials object with
  `place: env` puts the creds back. With the same content the cred store sees no change and writes nothing.
- **A `put` of a deleted file writes it only when the object changed.** The cred store does not tell a
  `put` from a `get`, so it never brings back a file that a step deleted after reading it. No step deletes a
  cred file and then puts the same object: cloud passport cleanup keeps `<cloud>-creds.yml`, and an ES cred
  file that nobody read is always written.
- **`get` of a missing file takes `allow_default`, as `decrypt_file` does.** With it the cred store returns
  an empty YAML and writes nothing until a `put`. `Environment` and `regdefv2_adapter` read env creds that
  a new env does not have yet. Without it a missing file fails.
- **Steps read creds with `current_cred_store().get`, not with `decrypt_file`.** `decrypt_file` does not
  look into the cred store. It stays a plain function for `crypt_cli`, the pre-commit hook, and files that
  are not repository creds: discovery creds encrypted with the discovery key.
- **`crypt` decrypts and encrypts bytes.** `decrypt_bytes` and `encrypt_bytes` take the bytes and the path
  of a cred file. SOPS reads them on stdin, with `--filename-override` for the path. The cred store keeps
  bytes in memory and needs no temp file, except for `sops edit`: it works on a file only.
- **`sops edit` keeps the encrypted regex of the old file.** Bugfix: sops edit keeps the encrypted regex of the old file. Before, minimize_cred_diffs ran sops edit for every changed cred file, so a new literal key in an ES cred file (for example, a cred that changed from a ref+ reference to a plain value) could land in git unencrypted. Now an ES cred file gets sops edit only when its old file is encrypted and has the same set of literal keys. Otherwise it gets a plain SOPS encrypt with the new regex, or is written plain.
- **The editor script of `sops edit` compares YAML objects, not bytes.** The editor script of sops edit compares YAML objects, not bytes. The new content now comes from Python, not from a SOPS decrypt, so its bytes differ from the old file even with the same data. The script writes only when the objects differ; otherwise SOPS exits with 200 and keeps the file
- **The literal keys of an old ES cred file are read from its encrypted bytes.** SOPS encrypts values only.
  Keys stay plain, and a literal value is `ENC[...]`.
- **With `crypt: false` the cred store reads and writes plain files.** Nothing to decrypt or encrypt.
- **The cred store formats every cred file the same way before it writes it.** Before, each step formatted
  its own files or did not format them: `flush()` and cloud passport sorted and quoted, inventory only
  quoted, discovery creds, deprecated inventory and creds rotation did nothing. Now the steps only `put`,
  and the cred store sorts the file by the creds schema, quotes the strings, and removes the comments.
  `normalize_comments` is not called: the comments are removed anyway.
- **An ES cred file is not formatted.** It is a file of deployment parameters, not of Credential objects.
  The creds schema does not describe it. The cred store holds it only to encrypt it and keep the diff
  minimal.
- **Sorting by the creds schema validates the file.** `jschon` fails on a document that does not match the
  schema, `sortYaml(validate=False)` does not turn this off. So the cred store calls `encrypt_bytes` with
  `validate=False`, and a cred file is validated once. `encrypt_file` of `crypt_cli` and the pre-commit
  hook validates as before.
- **Validation stays where it was.** Cloud passport creds validated inside `sortYaml` before. Now they
  call `validate_yaml_by_scheme_or_fail` explicitly.
- **A header is passed with `put`.** Only discovery creds have a header. The cred store writes it as text
  at the top of the file after encryption, as `addHeaderToYaml` did before.
- **`sortYaml` and `make_quotes_for_strings` move to `envgene_shared`.** The cred store lives there and
  cannot import `envgenehelper`. `envgenehelper` reexports them. `envgene-shared` gets `jschon` and
  `jschon-sort` as dependencies.

## Cred store sources

The cred store reads the encrypted bytes of every file of `get_all_necessary_cred_files` when it opens.
After that, these steps put cred files into it:

| Step | Trigger | Code | Cred files |
|---|---|---|---|
| `PassportStep` | `GET_PASSPORT` | `cloud_passport/main.py::process_credentials` | `<cluster>/cloud-passport/<cloud>-creds.yml`, discovery creds, with a header |
| `CredentialRotationStep` | `CRED_ROTATION_PAYLOAD` | `creds_rotation/utils/cred_utils.py::update_file` | every env, cluster, and shared cred file that holds a rotated cred |
| `InventoryGenerationStep` | `ENV_INVENTORY_CONTENT.credentials` | `inventory/env_inventory_generation.py::handle_objects` | `<env>/Inventory/credentials/<name>.yml`, `<cluster>/credentials/<name>.yml`, `environments/credentials/<name>.yml` by `place` |
| `InventoryGenerationStep` | `ENV_INVENTORY_INIT`, `ENV_SPECIFIC_PARAMS` (deprecated) | `inventory/env_inventory_generation.py::generate_env` | `<env>/Credentials/credentials.yml`, `<env>/Inventory/credentials/inventory_generation_creds.yml` |
| `EnvBuildStep` | always | `CurrentEnvInstanceStore.put` of a cred path | `<env>/Credentials/credentials.yml` |
| `GenerateEffectiveSetStep` | always | `effective_set/effective_set_entrypoint.py::_run_cli` | ES cred files the CLI returns in `--creds-output` |

A step that changes an object it got from the cred store changes the cred store too, without a `put`.

## Cred store and env instance store

The two stores have different roles. `CurrentEnvInstanceStore` holds the output of one step: the files that
`EnvBuildStep` renders. The cred store holds a decrypted copy of the cred files of the repository for all
steps, so that no cred file is ever decrypted on disk.

| | Env instance store | Cred store |
|---|---|---|
| Role | output of `EnvBuildStep` | decrypted copy of the repository cred files |
| Lifetime | inside `EnvBuildStep` | from the first step to `GitCommitStep` |
| Holds | plain objects | plain objects and the original encrypted bytes |
| At open | empty, reads no disk | reads the bytes of the cred files of the env |
| Filled by | `put` only, the caller reads the disk | `put`, and `get` loads a file from disk on first read |
| `get` of an unknown file | fails | loads it from disk, or returns an empty YAML with `allow_default` |
| `exists` | memory | memory or disk |
| Format | `flush()`, schema and header from `beautify` | `_write`, the creds schema for every cred file, header from `put` |
| Write | `flush()`, every put file | at close, only changed files, encrypted |
| Key | `Path` | `Path` |

- **The env instance store does not hold cred files.** `get`, `put`, and `exists` of a cred path go to the cred
  store. So a cred file has one source of truth during `EnvBuildStep`, and `flush()` writes no cred files.
- **The cred store reads the disk itself.** Steps read cred files they did not create: creds rotation reads
  the creds of every env of the cluster, env build reads shared creds of the cluster and the site, cloud
  passport creds lie in one of two places. If the cred store did not load them, every reader would read the
  disk itself.
- **The disk tells which cred files exist.** Steps delete files on disk, not through the cred store. Only one
  delete matters for the cred store: cloud passport cleanup deletes `cloud-passport/credentials/<cloud>.yml`,
  and `add_cloud_passport_creds` then asks if the file exists. `exists` checks the disk and answers right.
  ES deletes do not matter: nobody reads ES cred files, and the cred store writes only the ones the CLI
  returns. So the cred store has no `delete`.

## What changes for the user

- Cred files are never decrypted on disk, also after a failed step. The job artifact has no decrypted
  creds.
- With `crypt: false`, a cred file from discovery creds, `ENV_INVENTORY_CONTENT.credentials`,
  `ENV_INVENTORY_INIT` / `ENV_SPECIFIC_PARAMS`, or creds rotation is validated by the creds schema. Before,
  `crypt: false` skipped validation for them. With `crypt: true` they were validated by `encrypt_file`
  before, and the error message is now shorter: `Document failed schema validation`.
- Cred files from these sources are written sorted, quoted, and without comments, as env creds were before.
- Fernet is no longer an encryption backend of the repository. `crypt_backend` takes only `SOPS`, and SOPS is
  the default. Fernet only decrypts cloud discovery creds with the `SECRET_KEY` of the discovery project.
- `external-credentials.yaml` is committed unencrypted. Before, `strategy` and the `data` markers were
  encrypted, because `analyze_cred_file` takes every string without `ref+` as a secret.

## Out of scope

- `CurrentEnvInstanceStore` lifetime. It stays inside `EnvBuildStep`. Nothing is taken from
  `perf/widen-object-store`.
- `ThreadPoolExecutor` to `ProcessPoolExecutor`. Decide after the measurement.
- A detailed validation error in the cred store. The only validation there is the one inside sorting by
  `jschon`, with its short error message.
- Validation of ES cred files. `credential-encryption.md` says a file that is not a flat key-value map
  fails with a schema violation. The code does not check it, before and after this change.
