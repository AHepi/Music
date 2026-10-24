#!/bin/bash
# usage: measure.sh LABEL args...   -> appends "LABEL seconds peak_MB" to measure.log
label=$1; shift
log=/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/ground_dev/measure.log
start=$(date +%s)
"$@" > /tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/ground_dev/measure_$label.out 2>&1 &
pid=$!
peak=0
while kill -0 $pid 2>/dev/null; do
  rss=$(awk '/VmRSS/ {print $2}' /proc/$pid/status 2>/dev/null)
  [ -n "$rss" ] && [ "$rss" -gt "$peak" ] && peak=$rss
  sleep 1
done
end=$(date +%s)
echo "$label seconds $((end-start)) peak_MB $((peak/1024))" >> $log
