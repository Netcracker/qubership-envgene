# Local Testing Guide (E2E Tests)

This guide provides step-by-step instructions on how to locally execute the End-to-End (BDD) tests for the EnvGene project and generate human-readable HTML reports.

## Prerequisites

1. **Docker Desktop** (or Docker Engine) installed and running on your local machine.
2. **PowerShell** or **Bash** terminal.

## Step 1: Prepare the Docker Environment

All tests execute in an isolated container that replicates the CI/CD environment. The EnvGene project directory is mounted inside the container, meaning any changes you make locally—and any reports generated—are instantly synced to your machine.

1. Build the production image (this also compiles necessary Java tools like `effective-set-generator`):
   ```bash
   docker build -t local-envgene-main -f build_envgene/build/Dockerfile .
   ```

2. Start the testing container in the background:
   ```bash
   docker-compose -f devtools/docker-compose.yml up -d --build cucumber
   ```

3. Install required Python packages inside the container:
   ```bash
   docker-compose -f devtools/docker-compose.yml exec -T cucumber bash -c "chmod +x /workspace/devtools/cucumber/up.sh && /workspace/devtools/cucumber/up.sh"
   ```

## Step 2: Run Tests with HTML Reporting

To generate beautiful HTML reports, the `pytest-html` plugin is used. The output report will be saved inside the `tests/reports` folder, which syncs directly to your local PC.

### Run All Tests
```bash
docker-compose -f devtools/docker-compose.yml exec -T cucumber bash -c "export PYTHONPATH=/workspace && cd /workspace && pytest tests/ -v -s --html=tests/reports/report.html --self-contained-html"
```

### Run a Specific Scenario (by name)
You can filter tests by name using the `-k` parameter:
```bash
docker-compose -f devtools/docker-compose.yml exec -T cucumber bash -c "export PYTHONPATH=/workspace && cd /workspace && pytest tests/ -k 'UC-SD-1' -v -s --html=tests/reports/report.html --self-contained-html"
```

### Run a Specific Test File
```bash
docker-compose -f devtools/docker-compose.yml exec -T cucumber bash -c "export PYTHONPATH=/workspace && cd /workspace && pytest tests/step_defs/test_sd_processing.py -v -s --html=tests/reports/report.html --self-contained-html"
```

## Step 3: View the Report

Once the tests finish running, navigate to the `tests/reports` folder in your local project repository.
Open the `report.html` file in any web browser by double-clicking it. The report will show detailed information about passed, failed, and skipped scenarios, along with the logs for each step.

## Step 4: Cleanup (Optional)

When you are finished working with the tests, you can stop and remove the containers:
```bash
docker-compose -f devtools/docker-compose.yml down
```
