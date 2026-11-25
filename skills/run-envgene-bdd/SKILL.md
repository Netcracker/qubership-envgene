---
name: run-envgene-bdd
description: Run this repository's Cucumber/pytest-bdd suites on Linux using the GitHub Actions-compatible Docker workflow. Use when running, debugging, or validating BDD tests in this project.
---

# Run EnvGene BDD tests

Use the repository's GitHub Actions sequence on Linux. This avoids stale prebuilt
images and keeps the test container aligned with the checked-out source.

## Standard workflow

Run from the repository root:

```bash
docker build -t local-envgene-main -f build_envgene/build/Dockerfile .
docker compose -f devtools/docker-compose.yml up -d --build cucumber
docker compose -f devtools/docker-compose.yml exec -T cucumber \
  bash -c "chmod +x /workspace/devtools/cucumber/up.sh && /workspace/devtools/cucumber/up.sh"
docker compose -f devtools/docker-compose.yml exec -T cucumber \
  bash /workspace/cucumber_tests/run_suites.sh
```

The `up.sh` step is required. It builds and installs the current repository
modules inside the test environment.

## Run one suite

Use the same setup steps, then run the selected runner with the repository's
pytest configuration:

```bash
docker compose -f devtools/docker-compose.yml exec -T cucumber \
  bash -c "cd /workspace && pytest cucumber_tests/step_defs/test_<suite>.py \
  -c cucumber_tests/pytest.ini -v -s --junitxml=reports/<suite>.xml"
```

For example:

```bash
docker compose -f devtools/docker-compose.yml exec -T cucumber \
  bash -c "cd /workspace && pytest cucumber_tests/step_defs/test_env_prepare_report.py \
  -c cucumber_tests/pytest.ini -v -s --junitxml=reports/env_prepare_report.xml"
```

## Target scenarios

To select scenarios by pytest-bdd-generated test name:

```bash
docker compose -f devtools/docker-compose.yml exec -T cucumber \
  bash -c "cd /workspace && pytest cucumber_tests/step_defs/test_<suite>.py \
  -c cucumber_tests/pytest.ini -k '<expression>' -v -s"
```

Prefer the suite runner for normal validation. Use a targeted command when
iterating on a specific feature or diagnosing a failure.

## Cleanup

Always tear down the service after the run, especially after a failed build or
test:

```bash
docker compose -f devtools/docker-compose.yml down
```

Keep JUnit output under `reports/` when the result may be consumed by CI.

## Troubleshooting

- If `docker-compose` is unavailable, use `docker compose`.
- If `service "cucumber" is not running`, start it with
  `docker compose -f devtools/docker-compose.yml up -d --build cucumber`.
- If imports come from an old installed package, rebuild `local-envgene-main`
  and rerun `up.sh`; do not patch the container with ad hoc symlinks as the
  normal solution.
- If the run is interrupted, execute the cleanup command before retrying.
