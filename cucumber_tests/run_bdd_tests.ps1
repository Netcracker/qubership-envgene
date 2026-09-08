param([string]$Target = "cucumber_tests/step_defs/", 
    [string]$Scenarios = "",
    [string]$SourceRoot = ""
)

$ErrorActionPreference = "Stop"

# Navigate to project root (parent of cucumber_tests)
Set-Location -Path "$PSScriptRoot\.."

# Resolve the envgene source root: defaults to sibling 'qubership-envgene' directory
if (-not $SourceRoot) {
    $SourceRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..\qubership-envgene")).Path
}

Write-Host "Starting Environment Inventory Generation Tests in Docker..." -ForegroundColor Cyan
Write-Host "Source repo: $SourceRoot" -ForegroundColor Gray

# 1. Rebuild the production base image from the current checkout.
#    The 'cucumber' service (devtools/cucumber/Dockerfile) is FROM local-envgene-main,
#    which bakes in scripts/ and modules/dpg at build time. Docker will happily reuse a
#    stale local-envgene-main tag left over from a previous run, silently testing old code
#    even though /workspace is volume-mounted with the current checkout - so this rebuild
#    is not optional. This mirrors what the perform_e2e_tests.yml CI workflow does.
Write-Host "Rebuilding local-envgene-main base image..." -ForegroundColor Yellow
docker build -t local-envgene-main -f build_envgene/build/Dockerfile .

# 2. Build and start the cucumber container
Write-Host "Building and starting the Docker Compose environment..." -ForegroundColor Yellow
docker compose -f devtools/docker-compose.yml up -d --build cucumber

try {
    # 2. Install envgene Python packages from mounted source repo
    Write-Host "Installing Python packages from source repo..." -ForegroundColor Yellow
    docker compose -f devtools/docker-compose.yml exec -T cucumber `
        bash -c "chmod +x /workspace/devtools/cucumber/up.sh && /workspace/devtools/cucumber/up.sh"

    # 3. Build pytest command
    if ($Scenarios) {
        $ScenariosExpr = $Scenarios -replace '\s*,\s*', ' or '
        $PytestCmd = "pytest cucumber_tests/step_defs/ -c cucumber_tests/pytest.ini -k `"$ScenariosExpr`" -v -s"
    } else {
        $PytestCmd = "pytest cucumber_tests/step_defs/ -c cucumber_tests/pytest.ini -v -s"
    }

    # 4. Execute pytest inside the container
    Write-Host "Executing BDD tests inside the container..." -ForegroundColor Yellow
    docker compose -f devtools/docker-compose.yml exec -T cucumber `
        bash -c "set -o pipefail; export PYTHONPATH=/workspace:/workspace/scripts:/envgene-src && cd /workspace && mkdir -p reports && $PytestCmd --junitxml=reports/eig.xml | tee bdd_tests.log"
    $TestExitCode = $LASTEXITCODE

} finally {
    # 5. Tear down the container (--rmi local removes locally built images to free disk space)
    Write-Host "Tearing down Docker Compose environment..." -ForegroundColor Yellow
    docker compose -f devtools/docker-compose.yml down --rmi local
}

if ($TestExitCode -ne 0) {
    Write-Host "Tests FAILED. Check bdd_tests.log and reports/eig.xml for details." -ForegroundColor Red
    exit $TestExitCode
} else {
    Write-Host "All tests PASSED." -ForegroundColor Green
    Write-Host "JUnit report: $PSScriptRoot\reports\eig.xml" -ForegroundColor Green
}
