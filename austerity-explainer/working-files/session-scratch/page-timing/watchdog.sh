#!/bin/bash
# runs a command in its own process group; stops it (by its own group number) if free memory drops under LIMIT_MB
LIMIT_MB=${LIMIT_MB:-1500}
setsid "$@" &
pid=$!
lowest=999999
while kill -0 $pid 2>/dev/null; do
  avail=$(awk '/MemAvailable/ {print int($2/1024)}' /proc/meminfo)
  [ $avail -lt $lowest ] && lowest=$avail
  if [ $avail -lt $LIMIT_MB ]; then echo "watchdog: only $avail MB free, stopping $pid"; kill -TERM -$pid; sleep 2; kill -KILL -$pid 2>/dev/null; fi
  sleep 1
done
wait $pid; code=$?
echo "watchdog: lowest free memory while running: $lowest MB; exit $code"
exit $code
