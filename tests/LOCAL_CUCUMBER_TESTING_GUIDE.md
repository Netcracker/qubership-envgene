# Local Cucumber Testing Guide

This guide explains how to run Cucumber (BDD) tests locally using Docker Compose, how to run specific tests, generate HTML reports, and update golden data.

## Prerequisites
- Docker Desktop installed and running
- Docker Compose installed

## Step 1: Initialize the Environment

Before running any tests, you need to build the Docker image and start the Docker Compose environment:

```powershell
# 1. Build the main production Docker image
docker build -t local-envgene-main -f build_envgene/build/Dockerfile .

# 2. Build and start the testing container
docker-compose -f devtools/docker-compose.yml up -d --build cucumber

# 3. Install required Python modules inside the container
docker-compose -f devtools/docker-compose.yml exec -T cucumber bash -c "chmod +x /workspace/devtools/cucumber/up.sh && /workspace/devtools/cucumber/up.sh"
```

## Step 2: Running the Tests

Once the environment is running, you can execute the tests using `pytest` inside the `cucumber` container.

### Run All Tests
```powershell
docker-compose -f devtools/docker-compose.yml exec -T cucumber bash -c "export PYTHONPATH=/workspace && cd /workspace && pytest"
```

### Run a Specific Test Case
You can run a specific test file or a specific scenario by using the `-k` keyword filter or explicitly providing the path:

```powershell
# Run by keyword
docker-compose -f devtools/docker-compose.yml exec -T cucumber bash -c "export PYTHONPATH=/workspace && cd /workspace && pytest -k 'test_uceiges3_apply_custom_params'"

# Run by explicit path
docker-compose -f devtools/docker-compose.yml exec -T cucumber bash -c "export PYTHONPATH=/workspace && cd /workspace && pytest tests/step_defs/test_environment_instance_generation.py"
```

### Run Multiple Specific Tests (Array of Tests)
You can chain multiple test names using the `or` keyword:
```powershell
docker-compose -f devtools/docker-compose.yml exec -T cucumber bash -c "export PYTHONPATH=/workspace && cd /workspace && pytest -k 'test_scenario_1 or test_scenario_2'"
```

## 5. Дополнительно: Очистка рабочего пространства (Cleanup)

При запуске тестов локально они часто модифицируют файлы в папке `test_data` или создают временные артефакты в корне проекта, что "загрязняет" git. Чтобы быстро вернуть проект в чистое состояние:

В папке `tests` созданы два вспомогательных скрипта:
- `tests/clean_test_workspace.ps1` (для PowerShell)
- `tests/clean_test_workspace.sh` (для Bash/Linux)

Просто запустите их из терминала:
```powershell
# Для Windows
cd tests
.\clean_test_workspace.ps1
```

Эти скрипты автоматически выполнят `git checkout -- test_data/` для сброса изменений и удалят весь временный мусор вроде `reports` и `.pytest_cache`.

## Step 3: Generating HTML Reports

To generate a self-contained HTML report with test results, use the `--html` flag provided by `pytest-html`:

```powershell
# Ensure the reports directory exists
mkdir -p tests/reports

# Run tests and output the report to tests/reports/report.html
docker-compose -f devtools/docker-compose.yml exec -T cucumber bash -c "export PYTHONPATH=/workspace && cd /workspace && pytest --html=tests/reports/report.html --self-contained-html"
```
The report will be available locally in the `tests/reports` directory on your host machine.

## Step 4: Updating Golden Data (Expected Outputs)

Many tests rely on Golden Data (expected output directories) to verify correctness. If a test fails because the golden data is missing or out-of-date due to a legitimate codebase change, you can automatically update it by setting `UPDATE_GOLDEN=1`:

```powershell
docker-compose -f devtools/docker-compose.yml exec -T cucumber bash -c "export PYTHONPATH=/workspace && export UPDATE_GOLDEN=1 && cd /workspace && pytest -k 'test_name'"
```
This will overwrite the `test_data/golden/...` directories with the actual output of the test. You should then review and commit these changes to Git.

## Step 5: Tear Down the Environment
When you are finished testing, gracefully shut down the Docker Compose environment to free up resources:

```powershell
docker-compose -f devtools/docker-compose.yml down
```
