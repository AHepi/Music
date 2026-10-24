#!/bin/bash
# What this does: draws stills of every moment of pages 3 to 5 that round 6's page changes touch, one render at a time,
# into OUT, and makes a contact sheet for each shot:
#   W3 labels (MACHINES, WORKERS, the brazier smoke, BANK)        52.9 53.7 54.25 54.7 55.05
#   W1 drum letters and gate lamp, "go" either side, "start", the level PRICES arrow
#                                                                 62.4 66.9 67.5 68.5 69.6 72.0 73.5
#   W2 "busy" burst, the drum letters                             79.0 79.4 79.8 80.2 80.6 81.3 88.5
#   page 5: the climbing PRICES arrow, the rule and "made"        106.6 107.05 112.0 116.3 117.3 119.0 121.8
# Use: bash moments.sh OUT [extra PAPER_FILM_QUERY]
set -u
out="$1"; mkdir -p "$out"
TOOLS=/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/redesign/round6-pages/tools
cd /home/user/Music/austerity-explainer/film-kit
W3="52.9 53.7 54.25 54.7 55.05"; W1="62.4 66.9 67.5 68.5 69.6 72.0 73.5"; W2="79.0 79.4 79.8 80.2 80.6 81.3 88.5"; P5="106.6 107.05 112.0 116.3 117.3 119.0 121.8"
node paper-film/tools/render-paper-film.mjs inflation-chapter-2-newcomers "$out" --stills $W3 $W1 $W2 $P5 > "$out/render.log" 2>&1
grep -c "still-" "$out/render.log"
sheet() { local name=$1; shift; local files=(); for s in "$@"; do files+=("$out/still-$(printf '%.2f' $s).jpg"); done; python3 "$TOOLS/sheet.py" "$out/sheet-$name.jpg" 432 "${files[@]}"; }
sheet page-3-w3 $W3; sheet page-3-w1 $W1; sheet page-4-w2 $W2; sheet page-5 $P5
