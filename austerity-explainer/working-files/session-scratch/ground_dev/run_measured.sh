#!/bin/bash
# runs a command and records the peak memory used (from /proc) and the time
start=$(date +%s)
"$@" > /tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/ground_dev/full_render.log 2>&1 &
pid=$!
peak=0
while kill -0 $pid 2>/dev/null; do
  rss=$(awk '/VmRSS/ {print $2}' /proc/$pid/status 2>/dev/null)
  # include children
  for c in $(pgrep -P $pid); do r2=$(awk '/VmRSS/ {print $2}' /proc/$c/status 2>/dev/null); rss=$((rss + ${r2:-0})); done
  [ -n "$rss" ] && [ "$rss" -gt "$peak" ] && peak=$rss
  sleep 2
done
end=$(date +%s)
echo "seconds $((end-start)) peak_rss_MB $((peak/1024))" >> /tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/ground_dev/full_render.log
