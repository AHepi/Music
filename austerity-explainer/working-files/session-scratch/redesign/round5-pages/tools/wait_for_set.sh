#!/bin/bash
# What this does: waits until the set helper's new Works export is in place: works-shot.json holds the "machines" key
# and the W1, W2 and W3 plates are newer than START (a time such as "2026-10-16 02:40"). Checks every 3 minutes and
# gives up after HOURS hours. Prints what it found.
# Use: bash wait_for_set.sh "2026-10-16 02:40" 2.4
start=$(date -d "$1" +%s); limit=$(( $(date +%s) + ${2%.*} * 3600 + (${2#*.} * 360) ))
W=/home/user/Music/austerity-explainer/film-kit/assets/models/inflation-chapter-2-newcomers/works
while true; do
  if grep -q '"machines"' $W/works-shot.json 2>/dev/null; then
    fresh=1
    for f in works-w1-plate.jpg works-w2-plate.jpg works-w3-plate.jpg; do [ "$(stat -c %Y $W/$f)" -gt "$start" ] || fresh=0; done
    if [ $fresh = 1 ]; then echo "new set ready at $(date +%H:%M)"; ls -la --time-style=+%H:%M $W | grep -v blend; exit 0; fi
  fi
  [ "$(date +%s)" -gt "$limit" ] && { echo "gave up waiting at $(date +%H:%M)"; exit 1; }
  sleep 180
done
