#!/bin/bash
set -e
diff_status=0
git diff --cached --exit-code || diff_status=$?
if [ $diff_status -ne 0 ]; then 
  echo "See diff above for changed files. Committing..."
else
  echo "We have NOTHING to commit. Skipping..."
fi