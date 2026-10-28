# Cred store

- [Problem](#problem)
- [Example](#example)
- [Design](#design)
- [Cred store sources](#cred-store-sources)
- [Changes by step and module](#changes-by-step-and-module)
- [What changes for the user](#what-changes-for-the-user)
- [Verification](#verification)
- [Out of scope](#out-of-scope)
- [Open questions](#open-questions)
- [Constraints](#constraints)

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
- **The cred store holds cred files in memory.** Per path: the encrypted bytes from disk and the decrypted
  object.
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
- **The cred store decrypts a file on the first read.** Later reads of the file take the object from memory.
  No SOPS call.
- **Steps write creds into the cred store, not to disk.**
- **At the end the cred store writes only changed files.** A file is changed when its object differs from
  the decrypted object of its original bytes. A changed or new file is encrypted by SOPS. An unchanged file
  is not touched, so `git diff` skips it.
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
- **The Effective Set Calculator CLI gets the env creds as an object** and does not read credentials from disk.
- **The CLI gets the env creds on stdin and returns the ES cred files on stdout.** The output is one JSON
  object, path to content. The CLI logs go to stderr. `vals-reference` already works this way.
- **`external-credential/external-credentials.yaml` is not in the cred store.** It holds references to a
  secret store and no secret values. The CLI writes it to disk as now, and `external-cred-provision` reads
  it from disk as now. Nothing encrypts it.
- **The cred store reads the encrypted bytes of all cred files of the env when it opens, before the first
  step.** The files are those of `get_all_necessary_cred_files`: `Credentials/`, `cloud-passport/`,
  `effective-set/`, and the others. Reading bytes needs no SOPS call. A step that deletes a cred file
  later does not lose its original bytes: `cleanup_dir` of `cloud-passport/`, and the ES modes that delete
  ES directories. So the rules of what each step deletes are not repeated in the cred store. An ES cred
  file that the CLI does not return keeps its state on disk: untouched or deleted by the ES mode.
- **An ES cred file keeps the encryption rule of today.**
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
  schema, `sortYaml(validate=False)` does not turn this off. So the cred store calls `encrypt_file` with
  `validate=False`, and a cred file is validated once. `crypt_cli` and the pre-commit hook call
  `encrypt_file` with the default `validate=True`.
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
| `EnvBuildStep` | always | `cloud_passport/cloud_passport.py::add_cloud_passport_creds` | `<cloud>-creds.yml` next to the Cloud Passport |
| `EnvBuildStep` | always | `CurrentEnvInstanceStore.flush()` | every cred file in the env instance store, mainly `<env>/Credentials/credentials.yml` |
| `GenerateEffectiveSetStep` | always | `effective_set/effective_set_entrypoint.py::_run_cli` | ES cred files the CLI returns on stdout |

A step that changes an object it got from the cred store changes the cred store too, without a `put`.
Readers get cred files through `decrypt_file` or `current_cred_store().get`.

## What changes for the user

- Cred files are never decrypted on disk, also after a failed step. The job artifact has no decrypted
  creds.
- With `crypt: false`, a cred file from discovery creds, `ENV_INVENTORY_CONTENT.credentials`,
  `ENV_INVENTORY_INIT` / `ENV_SPECIFIC_PARAMS`, or creds rotation is validated by the creds schema. Before,
  `crypt: false` skipped validation for them. With `crypt: true` they were validated by `encrypt_file`
  before, and the error message is now shorter: `Document failed schema validation`.
- Cred files from these sources are written sorted, quoted, and without comments, as env creds were before.
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
