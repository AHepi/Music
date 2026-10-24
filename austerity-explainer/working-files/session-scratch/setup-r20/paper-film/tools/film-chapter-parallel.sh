#!/bin/bash
# What this does: films a whole chapter scene in short stretches ("chunks"), two at a time, then
# joins them into one silent video. Like film-chapter.sh, but each page is split into chunks of at
# most CHUNK_FRAMES frames and WORKERS chunks are filmed at once, which on a 4-processor machine is
# about 17% faster than one at a time (measured on chapter 2: 1.44 against 1.68 seconds a frame).
#
# Chunks that already exist are kept, so if filming stops, run the script again and it carries on.
# A change to one page only needs that page's chunks deleted and the script run again.
#
# Use (from the kit folder): bash paper-film/tools/film-chapter-parallel.sh SCENE [WORKERS] [CHUNK_FRAMES]
#   writes paper-film/out/SCENE-chunks/chunk-FROM-to-TO.mp4 and paper-film/out/SCENE-silent.mp4,
#   and paper-film/out/SCENE-filming.log (one line per chunk). Then join the sound with
#   narration-tools/finish_film.sh.

set -u
cd "$(dirname "$0")/.."
SCENE="$1"; WORKERS="${2:-2}"; CHUNK_FRAMES="${3:-240}"
OUT="out/$SCENE-chunks"; LOG="out/$SCENE-filming.log"
mkdir -p "$OUT"

INFO=$(node tools/render-paper-film.mjs "$SCENE" --info | tail -1)
# the chunk list: page edges first, then each page cut into pieces of at most CHUNK_FRAMES
CHUNKS=$(echo "$INFO" | python3 -c "
import json, sys
d = json.load(sys.stdin)
edges = [0] + d['page_edge_frames'] + [d['frames']]
for a, b in zip(edges, edges[1:]):
    n = max(1, round((b - a) / $CHUNK_FRAMES))
    cuts = [a + round(i * (b - a) / n) for i in range(n + 1)]
    for x, y in zip(cuts, cuts[1:]): print(x, y)
")
echo "$SCENE: $(echo "$CHUNKS" | wc -l) chunks, $WORKERS at a time ($(date +%H:%M:%S))" | tee -a "$LOG"

film_one() {
  local from=$1 to=$2 file="$OUT/chunk-$(printf %05d "$1")-to-$(printf %05d "$2").mp4"
  if [ -s "$file" ]; then return 0; fi
  local started=$(date +%s)
  if node tools/render-paper-film.mjs "$SCENE" "$file.part.mp4" --frames "$from" "$to" > "$file.log" 2>&1; then
    mv "$file.part.mp4" "$file"; mv "$file.part.json" "${file%.mp4}.json"
    echo "frames $from-$to filmed in $(( $(date +%s) - started )) s ($(date +%H:%M:%S))" >> "$LOG"
  else
    echo "frames $from-$to FAILED, see $file.log ($(date +%H:%M:%S))" >> "$LOG"
  fi
}
export -f film_one; export OUT SCENE LOG
echo "$CHUNKS" | xargs -P "$WORKERS" -L 1 bash -c 'film_one "$0" "$1"'

# join only when every chunk exists
LIST="$OUT/join-list.txt"; : > "$LIST"; MISSING=0
while read -r from to; do
  file="$OUT/chunk-$(printf %05d "$from")-to-$(printf %05d "$to").mp4"
  if [ -s "$file" ]; then echo "file '$(realpath "$file")'" >> "$LIST"; else MISSING=$((MISSING + 1)); fi
done <<< "$CHUNKS"
if [ "$MISSING" -gt 0 ]; then echo "$MISSING chunks missing: run again to finish them" | tee -a "$LOG"; exit 1; fi
ffmpeg -hide_banner -loglevel error -y -f concat -safe 0 -i "$LIST" -c copy -movflags +faststart "out/$SCENE-silent.mp4"
echo "joined: paper-film/out/$SCENE-silent.mp4 ($(date +%H:%M:%S))" | tee -a "$LOG"
