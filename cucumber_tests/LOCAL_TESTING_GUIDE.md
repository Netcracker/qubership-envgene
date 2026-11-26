# Local Testing Guide (End-to-End BDD Tests)

This guide describes the supported local workflow for running EnvGene's
pytest-bdd tests in the same Docker setup used by GitHub Actions.

## Prerequisites

1. Docker Engine or Docker Desktop installed and running.
2. Bash.

## Run the tests

From the repository root, use the canonical runner:

```bash
./cucumber_tests/run_bdd_tests.sh
```

The runner rebuilds the production image, starts the cucumber container,
installs the current repository modules, runs the BDD suites, writes JUnit
results under `reports/`, and cleans up Docker on exit.

To select scenarios by pytest-bdd test name:

```bash
./cucumber_tests/run_bdd_tests.sh "UC-SD-1"
```

The argument is passed to pytest's `-k` filter. Use the suite runner directly
when you need to run only one test file:

```bash
docker compose -f devtools/docker-compose.yml exec -T cucumber \
  bash -c "cd /workspace && pytest cucumber_tests/step_defs/test_sd_processing.py \
  -c cucumber_tests/pytest.ini -v -s"
```

## Results

The runner writes:

- `reports/eig.xml` — JUnit test results
- `bdd_tests.log` — captured BDD output

The Docker environment is removed automatically, including after failures.

## Troubleshooting

If the runner is interrupted or Docker was left running by another command:

```bash
docker compose -f devtools/docker-compose.yml down --rmi local
```

Use `docker compose`, not the legacy `docker-compose` command.
