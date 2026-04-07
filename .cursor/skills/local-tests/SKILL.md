---
name: local-tests
description: Runs qubership-envgene tests and Python tooling in the tests Docker service via the root Makefile (make run-tests, make bash-tests, make tests-run CMD=..., make up-tests). Forbids host python/pytest/pip unless the user asks. Prefer make run-tests for validation; targeted pytest is only for iterative debugging. Use when running tests, pytest, CI parity, validating changes, or docker compose vs Make for tests. Triggers include make run-tests, bash-tests, tests-run, env-build tests, scripts/build_env tests, local verification.
---

# Local tests (Docker + Make)

Single workflow: **repository root**, **`tests` service** in `devtools/docker-compose.yml`, **Make targets only** for routine work (not raw `docker compose`).

## Preconditions

- Docker available (see `devtools/readme.md`; often WSL + Docker).
- Run commands from the **repository root** (where `Makefile` and `devtools/docker-compose.yml` live).

## Mandatory rules

- **Do not** run `python`, `python3`, `pytest`, `python -m pytest`, `pip`, or `CI_PROJECT_DIR=… python …` on the **host** for this repo unless the user explicitly wants the host interpreter.
- **Do not** type `docker compose -f devtools/docker-compose.yml …` for normal tasks. Use **`make`** so compose flags and paths stay in the `Makefile`. Exception: editing the `Makefile` or `devtools/docker-compose.yml`.

## Pick a command

| Goal | Command |
|------|---------|
| Validate changes (authoritative, CI-like) | `make run-tests` |
| Interactive shell in `tests` container | `make bash-tests` (after `make up-tests`) |
| Ad hoc command (pytest subset, `python3`, etc.) | `make tests-run CMD='…'` |
| Image missing or Dockerfile changed | `make build-tests` |
| Service not running | `make up-tests` |

**`bash-%` in the Makefile:** `make bash-tests` runs `docker compose … exec tests bash` (interactive). **`tests-run`** runs `exec -T tests bash -lc 'cd /workspace && $(CMD)'` (non-interactive). See root `Makefile` for exact definitions.

## Default full run (use this to confirm a change)

```sh
make run-tests
```

Runs `devtools/tests/run.sh` inside the `tests` service. Treat this as the **source of truth** for whether tests pass.

## Targeted pytest or Python (debugging only)

Many tests in this repo **depend on shared state, order, or fixtures** that only the full runner sets up reliably. Running **pytest subsets or single files** can pass while `make run-tests` fails, or the opposite. Do **not** report "all tests pass" based only on a subset.

Use targeted commands only to **iterate on a known failing test** or a tight loop while fixing something; finish with **`make run-tests`**.

**Interactive:** `make up-tests` → `make bash-tests` → run `pytest` or `python3` in that shell.

**Non-interactive:**

```sh
make tests-run CMD='pytest scripts/build_env/tests/env-build/test_render_envs.py::TestEnvBuild::test_render_envs -v'
```

```sh
make tests-run CMD='python3 -m some.module'
```

Paths in `CMD` are relative to repo root (`/workspace` in the container). Omitting `CMD` fails with usage text.

## When `run-tests` fails or first-time setup

Use **in order** as needed:

1. **Image missing or Dockerfile/dependencies changed** → `make build-tests`
2. **Container not running** (down after reboot, never started, after `make down`) → `make up-tests`
3. Run again → `make run-tests` (not a pytest subset alone)

**Typical cold start:** `make build-tests` → `make up-tests` → `make run-tests`.

## Other useful Make targets (`tests` service and compose)

| Command | Use |
|---------|-----|
| `make tests-run CMD='…'` | Single non-interactive command in `tests` |
| `make stop-tests` | Stop the `tests` service |
| `make rm-tests` | Remove the `tests` container |
| `make down` | Stop all devtools compose services |

## Notes

- Repo is bind-mounted at `/workspace` (`CI_PROJECT_DIR=/workspace` in compose). Edits on the host apply without rebuilding unless the image or dependencies change.
- Complex quoting inside `CMD` may be awkward; use `make bash-tests` interactively instead.

## More detail

See `devtools/readme.md` for the full devtools Make pattern.
