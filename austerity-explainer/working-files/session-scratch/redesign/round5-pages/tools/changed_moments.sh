#!/bin/bash
# What this does: draws stills of every moment of pages 3 to 5 that round 5's page changes touch (the W3 labels, the
# arrow to the chain, No. 1's smoke after "start", page 4's burst on "busy", the smoke under the words and under the
# rule cards, No. 1's smoke on "made", the dim BANK), one render at a time, into OUT, and makes contact sheets.
# Use: bash changed_moments.sh OUT
set -u
out="$1"; mkdir -p "$out"
cd /home/user/Music/austerity-explainer/film-kit
TOOLS=/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/redesign/round5-pages/tools
node paper-film/tools/render-paper-film.mjs inflation-chapter-2-newcomers "$out" --stills \
  52.9 53.7 54.25 54.7 55.05 \
  58.0 62.0 64.6 66.5 67.6 69.5 72.0 73.8 \
  79.0 79.4 79.8 80.2 80.6 81.3 86.0 92.0 \
  100.0 107.6 112.0 116.4 117.0 117.6 119.6 122.0 > "$out/render.log" 2>&1
grep -c "still-" "$out/render.log"
python3 "$TOOLS/sheet.py" "$out/sheet-page-3-w3.jpg" 432 $out/still-52.90.jpg $out/still-53.70.jpg $out/still-54.25.jpg $out/still-54.70.jpg $out/still-55.05.jpg
python3 "$TOOLS/sheet.py" "$out/sheet-page-3-w1.jpg" 432 $out/still-58.00.jpg $out/still-62.00.jpg $out/still-64.60.jpg $out/still-66.50.jpg $out/still-67.60.jpg $out/still-69.50.jpg $out/still-72.00.jpg $out/still-73.80.jpg
python3 "$TOOLS/sheet.py" "$out/sheet-page-4-w2.jpg" 432 $out/still-79.00.jpg $out/still-79.40.jpg $out/still-79.80.jpg $out/still-80.20.jpg $out/still-80.60.jpg $out/still-81.30.jpg $out/still-86.00.jpg $out/still-92.00.jpg
python3 "$TOOLS/sheet.py" "$out/sheet-page-5.jpg" 432 $out/still-100.00.jpg $out/still-107.60.jpg $out/still-112.00.jpg $out/still-116.40.jpg $out/still-117.00.jpg $out/still-117.60.jpg $out/still-119.60.jpg $out/still-122.00.jpg
