#!/bin/sh
echo "am inside entrypoint"
export JAVA_OPTIONS="$JAVA_OPTIONS $JAVA_MEM_INITIAL $JAVA_MEM_MAX $THREAD_COUNT"
exec /deployments/run-java.sh "$@"
