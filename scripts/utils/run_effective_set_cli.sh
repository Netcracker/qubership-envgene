#!/bin/sh

merge_java_opts() {
  base="$1"
  override="$2"

  result="$base"
  allowed_override=""

  for opt in $override; do
    case "$opt" in
      -Xms*)
        result=$(echo "$result" | sed -E 's/-Xms[^ ]+//g')
		allowed_override="$opt${allowed_override:+ $allowed_override}"
        ;;
      -Xmx*)
        result=$(echo "$result" | sed -E 's/-Xmx[^ ]+//g')
		allowed_override="$opt${allowed_override:+ $allowed_override}"
        ;;
      -Djava.util.concurrent.ForkJoinPool.common.parallelism=*)
        result=$(echo "$result" | sed -E 's|-Djava.util.concurrent.ForkJoinPool.common.parallelism=[^ ]+||g')
		allowed_override="$opt${allowed_override:+ $allowed_override}"
        ;;
    esac
  done
  echo "$result${allowed_override:+ $allowed_override}"
}

if [ -n "${CALCULATOR_CLI_JAVA_OPTIONS:-}" ]; then
	JAVA_OPTIONS=$(merge_java_opts "$JAVA_OPTIONS" "$CALCULATOR_CLI_JAVA_OPTIONS" | tr -s '[:space:]')
fi
export JAVA_OPTIONS
exec /deployments/run-java.sh "$@"