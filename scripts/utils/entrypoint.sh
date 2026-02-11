#!/bin/sh

echo "Starting entrypoint..."


[ -n "$JAVA_MEM_INITIAL" ] && JAVA_OPTIONS="$JAVA_OPTIONS $JAVA_MEM_INITIAL"
[ -n "$JAVA_MEM_MAX" ] && JAVA_OPTIONS="$JAVA_OPTIONS $JAVA_MEM_MAX"
[ -n "$THREAD_COUNT" ] && JAVA_OPTIONS="$JAVA_OPTIONS $THREAD_COUNT"


echo "Final JAVA_OPTIONS: $JAVA_OPTIONS"

export JAVA_OPTIONS

exec /deployments/run-java.sh "$@"
