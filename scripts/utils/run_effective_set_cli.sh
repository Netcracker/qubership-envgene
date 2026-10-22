#!/bin/sh

native_opts=""
for opt in ${JAVA_OPTIONS:-} ${CALCULATOR_CLI_JAVA_OPTIONS:-}; do
  case "$opt" in
    -Xms*|-Xmx*|-Djava.util.concurrent.ForkJoinPool.common.parallelism=*)
      native_opts="${native_opts:+$native_opts }$opt"
      ;;
  esac
done

exec /deployments/envgene-es $native_opts generate-effective-set "$@"
