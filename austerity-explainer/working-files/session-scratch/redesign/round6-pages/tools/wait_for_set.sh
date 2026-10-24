#!/bin/bash
# What this does: waits until the set helper's new Works export is in place for round 6: works-shot.json, the W1, W2
# and W3 plates are newer than START (a time such as "2026-10-16 09:51"), and nothing in the
# folder has changed for 4 minutes (so the export has finished writing). Checks every 3 minutes and gives up at
# GIVE_UP (a time). Prints what it found, including whether a W3 "No. 1 working" picture is named in works-shot.json.
# Use: bash wait_for_set.sh "2026-10-16 09:51" "2026-10-16 13:30"
start=$(date -d "$1" +%s); limit=$(date -d "$2" +%s)
W=/home/user/Music/austerity-explainer/film-kit/assets/models/inflation-chapter-2-newcomers/works
while true; do
  fresh=1
  for f in works-shot.json works-w1-plate.jpg works-w2-plate.jpg works-w3-plate.jpg; do
    [ -e "$W/$f" ] && [ "$(stat -c %Y "$W/$f")" -gt "$start" ] || fresh=0
  done
  newest=$(find "$W" -maxdepth 1 -type f -printf '%T@\n' | sort -n | tail -1 | cut -d. -f1)
  settled=$(( $(date +%s) - newest > 240 ? 1 : 0 ))
  if [ $fresh = 1 ] && [ $settled = 1 ]; then
    echo "new set ready at $(date +%H:%M)"
    ls -la --time-style=+%H:%M "$W" | grep -v "\.blend$"
    grep -o '"works-w3-[a-z0-9-]*working[a-z0-9.-]*"' "$W/works-shot.json" | sort -u
    exit 0
  fi
  [ "$(date +%s)" -gt "$limit" ] && { echo "gave up waiting at $(date +%H:%M)"; ls -la --time-style=+%H:%M "$W" | grep -v "\.blend$"; exit 1; }
  sleep 180
done
