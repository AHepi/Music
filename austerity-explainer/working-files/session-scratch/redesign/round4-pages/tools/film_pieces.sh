#!/bin/bash
# What this does: films short pieces of chapter 2 for newcomers round the moments changed in round 4 (the two cuts,
# the two page turns, NO SPARE, and held stretches of W1 and W2 for the smoke), one after another, into OUT, and runs
# the jump finder on each with the planned cuts named (chapter seconds turned into seconds into the piece).
# A piece already filmed (its sheet exists) is skipped. Before each piece it waits until about 6 GB of memory is free:
# the other helper's Blender can take 12 GB, and a page turn loads two Works pages (the first try was stopped by the
# machine running out of memory).
# Use: bash film_pieces.sh OUT
set -u
out="$1"; mkdir -p "$out"
cd /home/user/Music/austerity-explainer/film-kit
FIND=paper-film/tools/find_jumps.py
# name first_frame end_frame planned_cut_frames...
pieces=(
  "cut-to-w1 1630 1680 1653"
  "page-3-turn 2205 2250 2229"
  "no-spare 2860 2900"
  "cut-to-w3 3190 3235 3215"
  "page-5-turn 3660 3704 3679"
  "w1-smoke 2100 2160"
  "w2-smoke 2700 2790"
)
for p in "${pieces[@]}"; do
  set -- $p
  name=$1; a=$2; b=$3; shift 3
  [ -e "$out/$name-sheet.jpg" ] && { echo "== $name: already filmed"; continue; }
  until [ "$(awk '/MemAvailable/ {print int($2 / 1048576)}' /proc/meminfo)" -ge 6 ]; do sleep 20; done
  rel=$(python3 -c "import sys; a=int(sys.argv[1]); print(' '.join(f'{(int(f) - a) / 30:.3f}' for f in sys.argv[2:]))" "$a" "$@")
  start=$(date +%s)
  node paper-film/tools/render-paper-film.mjs inflation-chapter-2-newcomers "$out/$name.mp4" --frames "$a" "$b" > "$out/$name.log" 2>&1
  echo "== $name: frames $a to $b ($(( $(date +%s) - start )) s)"
  python3 -I "$FIND" "$out/$name.mp4" "$out/$name-sheet.jpg" 4 $rel | grep -v "^sheet"
done
