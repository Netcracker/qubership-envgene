#!/bin/bash
set -euo pipefail

# shellcheck disable=SC1091
source /module/venv/bin/activate
chmod +x /workspace/devtools/tests/build_modules.sh
/workspace/devtools/tests/build_modules.sh
