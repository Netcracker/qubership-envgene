#!/bin/bash
set -euo pipefail

chmod +x /workspace/devtools/tests/build_modules.sh
/workspace/devtools/tests/build_modules.sh

mkdir -p /module
rm -rf /module/scripts
ln -s /workspace/scripts /module/scripts
