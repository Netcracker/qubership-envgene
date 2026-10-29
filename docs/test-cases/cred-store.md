# Cred store test cases

- [Cred store test cases](#cred-store-test-cases)
  - [Overview](#overview)
  - [UC-CS-ENC-1: Plain cred file is encrypted at the end of a run](#uc-cs-enc-1-plain-cred-file-is-encrypted-at-the-end-of-a-run)
  - [UC-CS-DIFF-1: Run that changes no cred leaves cred files byte-equal](#uc-cs-diff-1-run-that-changes-no-cred-leaves-cred-files-byte-equal)
  - [UC-CS-DIFF-2: Rotating one value changes only its ciphertext](#uc-cs-diff-2-rotating-one-value-changes-only-its-ciphertext)
  - [UC-CS-FAIL-1: Failed run writes no cred file](#uc-cs-fail-1-failed-run-writes-no-cred-file)
  - [UC-CS-FAIL-2: Cred file that fails the creds schema fails the run](#uc-cs-fail-2-cred-file-that-fails-the-creds-schema-fails-the-run)
  - [UC-CS-FER-1: Cred file with Fernet tokens fails the run](#uc-cs-fer-1-cred-file-with-fernet-tokens-fails-the-run)
  - [UC-CS-ES-1: Literal values in an ES cred file are encrypted](#uc-cs-es-1-literal-values-in-an-es-cred-file-are-encrypted)
  - [UC-CS-ES-2: VALS and ESO references stay plain](#uc-cs-es-2-vals-and-eso-references-stay-plain)
  - [UC-CS-ES-3: Second ES run with the same inputs leaves ES cred files byte-equal](#uc-cs-es-3-second-es-run-with-the-same-inputs-leaves-es-cred-files-byte-equal)
  - [UC-CS-ES-4: New literal key in an ES cred file is encrypted](#uc-cs-es-4-new-literal-key-in-an-es-cred-file-is-encrypted)
  - [Related scenarios in other features](#related-scenarios-in-other-features)

## Overview

The cred store keeps the decrypted cred files of a run in memory. At the end of the run it writes only the
changed cred files, encrypted with SOPS. A failed run writes nothing. See
[cred store design](/docs/dev/designs/cred-store.md).

The scenarios live in `cucumber_tests/features/cred-store.feature`. They run with the real `sops` binary and
the test AGE keys of the BDD workspace. A fixture without `configuration/config.yml` runs with `crypt: true`.

Two helpers are used across the cases:

- **SOPS-encrypted with the test key.** The plain fixture cred files are encrypted before the run, so no
  ciphertext is stored in Git.
- **Baseline.** The bytes of all cred files are recorded before the run, or between two runs, and compared
  after it.

## UC-CS-ENC-1: Plain cred file is encrypted at the end of a run

**Status:** Active

**Description:** With `crypt: true` a plain cred file in scope is encrypted at the end of the run, even
when no step changes it.

**Test Data:**

- `cucumber_tests/test_data/e2e/uc_cp_01_auto_association`

**Steps:**

- Run the pipeline with `ENV_BUILDER: true`

**Expected Results:**

- The run succeeds
- `Credentials/credentials.yml` of the environment is SOPS-encrypted
- `data` values are encrypted, `type` is plain
- The file decrypts to the original values

## UC-CS-DIFF-1: Run that changes no cred leaves cred files byte-equal

**Status:** Active

**Description:** An unchanged cred file is not rewritten.

**Test Data:**

- `cucumber_tests/test_data/e2e/uc_cp_01_auto_association`

**Pre-requisites:**

1. The cred files are SOPS-encrypted with the test key
2. A baseline is recorded

**Steps:**

- Run the pipeline with `ENV_BUILDER: true`

**Expected Results:**

- The run succeeds
- Every cred file is byte-equal to the baseline

## UC-CS-DIFF-2: Rotating one value changes only its ciphertext

**Status:** Active

**Description:** A changed cred file is written over its original bytes, so unchanged values keep their
ciphertext.

**Test Data:**

- `cucumber_tests/test_data/e2e/uc_cr_common_sops`

**Pre-requisites:**

1. The cred files are SOPS-encrypted with the test key
2. A baseline is recorded

**Steps:**

- Run the pipeline with `CRED_ROTATION_PAYLOAD` that rotates `TOKEN_PARAM` and `CRED_ROTATION_FORCE: true`

**Expected Results:**

- The run succeeds
- In `Credentials/credentials.yml` only `token-cred.data.secret` has a new ciphertext
- The file decrypts to the rotated value

## UC-CS-FAIL-1: Failed run writes no cred file

**Status:** Active

**Description:** Cred files are written only when the run succeeds. A plain cred file stays plain when the
run fails.

**Test Data:**

- `cucumber_tests/test_data/e2e/uc_cp_02_no_match`

**Pre-requisites:**

1. A baseline is recorded

**Steps:**

- Run the pipeline with `ENV_BUILDER: true`. The environment build fails: the named Cloud Passport does not
  exist

**Expected Results:**

- The run fails
- Every cred file is byte-equal to the baseline

## UC-CS-FAIL-2: Cred file that fails the creds schema fails the run

**Status:** Active

**Description:** The cred store validates every cred file it writes against the creds schema before it
writes any of them.

**Test Data:**

- `cucumber_tests/test_data/e2e/uc_cs_invalid_cred`: a cluster cred file with an unknown credential type

**Pre-requisites:**

1. A baseline is recorded

**Steps:**

- Run the pipeline with `ENV_BUILDER: true`

**Expected Results:**

- The run fails with `Cred file validation failed`
- Every cred file is byte-equal to the baseline

## UC-CS-FER-1: Cred file with Fernet tokens fails the run

**Status:** Active

**Description:** Fernet is no longer a repository backend. A cred file with Fernet tokens fails the run.

**Test Data:**

- `cucumber_tests/test_data/e2e/uc_cs_fernet_creds`: the environment credentials file holds a Fernet token

**Pre-requisites:**

1. A baseline is recorded

**Steps:**

- Run the pipeline with `ENV_BUILDER: true`

**Expected Results:**

- The run fails with a message that the file is encrypted with Fernet
- Every cred file is byte-equal to the baseline

## UC-CS-ES-1: Literal values in an ES cred file are encrypted

**Status:** Active

**Description:** The Calculator command-line tool returns the ES cred files to EnvGene, and the cred store
encrypts their literal values.

**Test Data:**

- `cucumber_tests/test_data/e2e/uc_cc_cp_5`

**Steps:**

- Run the pipeline with `GENERATE_EFFECTIVE_SET: true` and `CUSTOM_PARAMS` with the service key `web`

**Expected Results:**

- The Effective Set is generated
- `collision-credentials.yaml` of `test-app` is SOPS-encrypted, and the value of `web` is encrypted

## UC-CS-ES-2: VALS and ESO references stay plain

**Status:** Active

**Description:** References to an external secret store are not secrets. An ES cred file with only
references is written plain.

**Test Data:**

- `cucumber_tests/test_data/e2e/uc_ec_d_5_mixed_flows`

**Steps:**

- Run the pipeline with `PIPELINE_TYPE: GITLAB_DEPLOY`, `OPERATION_TYPE: DEPLOY`, and `APPLICATION_VERSIONS`
  for `app-vals` and `app-eso`

**Expected Results:**

- The Effective Set is generated
- No deployment `credentials.yaml` is SOPS-encrypted
- `app-vals` holds VALS references, `app-eso` holds ESO references

## UC-CS-ES-3: Second ES run with the same inputs leaves ES cred files byte-equal

**Status:** Active

**Description:** The Effective Set directory is regenerated in every run. An unchanged ES cred file keeps its
bytes.

**Test Data:**

- `cucumber_tests/test_data/e2e/uc_cc_cp_5`

**Steps:**

- Run the pipeline with `GENERATE_EFFECTIVE_SET: true` and `CUSTOM_PARAMS`
- Record a baseline
- Run the pipeline again with the same parameters

**Expected Results:**

- The Effective Set is generated
- `collision-credentials.yaml` of `test-app` is byte-equal to the baseline

## UC-CS-ES-4: New literal key in an ES cred file is encrypted

**Status:** Active

**Description:** A new literal key changes the set of encrypted keys of an ES cred file. The cred store
encrypts the file anew, so the new key is not left plain.

**Test Data:**

- `cucumber_tests/test_data/e2e/uc_cc_cp_5`

**Steps:**

- Run the pipeline with `GENERATE_EFFECTIVE_SET: true` and `CUSTOM_PARAMS` with the key `web`
- Run the pipeline again with `CUSTOM_PARAMS` with the keys `web` and `worker`

**Expected Results:**

- The Effective Set is generated
- In `collision-credentials.yaml` of `test-app` the values of `web` and `worker` are encrypted

## Related scenarios in other features

| Scenario | Feature file | What it checks |
| --- | --- | --- |
| UC-CR-ENC-1 | `credential-rotation.feature` | Rotation of a SOPS-encrypted environment credentials file |
| UC-CR-ENC-4 | `credential-rotation.feature` | Rotation of a SOPS-encrypted shared cred file |
| UC-CR-ENC-5 | `credential-rotation.feature` | A failed rotation leaves encrypted cred files byte-equal |
| UC-09 | `cloud-passport.feature` | Encrypted Cloud Passport creds reach the encrypted environment credentials file |
