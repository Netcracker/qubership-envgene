#!/bin/bash
# A script to clean up temporary files and restore modified test data after local cucumber test runs.

echo "Restoring modified files in test_data to their original state..."
git checkout -- ../test_data/

echo "Removing untracked directories and files created by tests..."
git clean -fd ../test_data/
rm -rf ../tests/reports/
rm -rf ../tests/.pytest_cache/
rm -rf ../test_results.txt
rm -rf ../test_data/test_inventory_generation/output/

echo "✅ Test data and workspace successfully cleaned!"
