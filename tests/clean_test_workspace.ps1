# A PowerShell script to clean up temporary files and restore modified test data after local cucumber test runs.

Write-Host "Restoring modified files in test_data to their original state..." -ForegroundColor Cyan
git checkout -- ../test_data/

Write-Host "Removing untracked directories and files created by tests..." -ForegroundColor Cyan
git clean -fd ../test_data/

$foldersToRemove = @(
    "../tests/reports",
    "../tests/.pytest_cache",
    "../test_results.txt",
    "../test_data/test_inventory_generation/output"
)

foreach ($folder in $foldersToRemove) {
    if (Test-Path $folder) {
        Remove-Item -Recurse -Force $folder
    }
}

Write-Host "✅ Test data and workspace successfully cleaned!" -ForegroundColor Green
