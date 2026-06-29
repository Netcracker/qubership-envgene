param(
    [string]$Scenarios = ""
)

$ErrorActionPreference = "Stop"# Navigate to project root
Set-Location -Path $PSScriptRoot

Write-Host "Starting EnvGene Integration Tests in Docker..." -ForegroundColor Cyan

# 1. Build the main production Docker image (required for cucumber E2E tests)
Write-Host "Building the main EnvGene Docker image..."
docker build -t local-envgene-main -f build_envgene/build/Dockerfile .

# 2. Start the Docker Compose environment
Write-Host "Building and starting the Docker Compose environment..."
docker-compose -f devtools/docker-compose.yml up -d --build cucumber

try {
    # 3. Wait for the container to initialize
    Write-Host "Running up.sh to install python modules..."
    docker-compose -f devtools/docker-compose.yml exec -T cucumber bash -c "chmod +x /workspace/devtools/cucumber/up.sh && /workspace/devtools/cucumber/up.sh"
    
    # 4. Run pytest inside the container
    Write-Host "Executing pytest inside the container..."
    if ($Scenarios) {
        $ScenariosExpr = $Scenarios -replace '\s*,\s*', ' or '
        $PytestCmd = "export UPDATE_GOLDEN=1 && pytest -k `"$ScenariosExpr`""
    } else {
        $PytestCmd = "export UPDATE_GOLDEN=1 && pytest"
    }
    docker-compose -f devtools/docker-compose.yml exec -T cucumber bash -c "export PYTHONPATH=/workspace && cd /workspace && $PytestCmd"
    $TestExitCode = $LASTEXITCODE
} finally {
    # 4. Tear down the environment
    Write-Host "Tearing down Docker Compose environment..."
    docker-compose -f devtools/docker-compose.yml down
}

if ($TestExitCode -ne 0) {
    Write-Host "Tests failed!" -ForegroundColor Red
    exit $TestExitCode
} else {
    Write-Host "All tests passed successfully." -ForegroundColor Green
}
