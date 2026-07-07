#!/bin/bash
set -euo pipefail

chmod +x /workspace/python/build_modules.sh
/workspace/python/build_modules.sh

mkdir -p /module
rm -rf /module/scripts
ln -s /workspace/scripts /module/scripts
