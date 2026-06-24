#!/bin/bash
set -euo pipefail

# shellcheck disable=SC1091
source /module/venv/bin/activate
chmod +x /workspace/python/build_modules.sh
/workspace/python/build_modules.sh
