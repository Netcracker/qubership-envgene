#!/bin/bash
ts=$(date +%s%N)
cat /workspace/instance-project/environments/REDACTED-ocp-mdc-08/cloud-passport/shades-REDACTED-ocp-mdc-08-creds/shade-coreexternal-cred.yml | sops --encrypt -age age1y4hfj9zz05dtqycfk55y4csddch6w2lu9l6wx7r68at5x897ea3qjh0gl9 --input-type yaml --output-type yaml /dev/stdin > shade-file.yml
echo $((($(date +%s%N) - $ts)/1000000))