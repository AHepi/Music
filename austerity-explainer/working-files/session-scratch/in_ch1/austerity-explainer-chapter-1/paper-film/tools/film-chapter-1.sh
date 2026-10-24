#!/bin/bash
# What this does: films the whole of chapter 1 in the paper look, one chunk at a time, then joins
# the chunks into one silent video.
#
# Each chunk is one page: it starts the moment that page's sheet lies flat (the page turn before it
# has finished) and ends when its own page turn has finished. So a change to one page only needs
# that page's chunk filmed again: delete the chunk's file and run this script; chunks that already
# exist are kept. Filming takes about 0.85 seconds a frame (about 95 minutes for all 6,641 frames).
#
# The chunk edges are frame numbers (30 a second): the end of each page turn, which is 0.3 s + 0.8 s
# after the page's last word in narration/chapter-1-timeline-steady-accent.json.
#
# Use: bash film-chapter-1.sh        (writes out/chapter-1-chunks/ and out/chapter-1-silent.mp4)

set -u
cd "$(dirname "$0")/.."
OUT=out/chapter-1-chunks
mkdir -p "$OUT"
EDGES=(0 741 1527 2222 2558 3132 3971 4571 5500 6072 6641)

for page in $(seq 1 10); do
  from=${EDGES[$((page - 1))]}
  to=${EDGES[$page]}
  file="$OUT/page-$(printf %02d "$page")-frames-$from-to-$to.mp4"
  if [ -s "$file" ]; then echo "page $page: already filmed"; continue; fi
  echo "page $page: filming frames $from to $((to - 1)) ($(date +%H:%M:%S))"
  if node tools/render-paper-film.mjs chapter-1 "$OUT/in-progress.mp4" --frames "$from" "$to"; then
    mv "$OUT/in-progress.mp4" "$file"
    mv "$OUT/in-progress.json" "${file%.mp4}.json"
  else
    echo "page $page: filming failed"
    exit 1
  fi
done

# join the chunks without re-encoding them
LIST="$OUT/join-list.txt"
: > "$LIST"
for file in "$OUT"/page-*.mp4; do echo "file '$(realpath "$file")'" >> "$LIST"; done
ffmpeg -hide_banner -loglevel error -y -f concat -safe 0 -i "$LIST" -c copy -movflags +faststart out/chapter-1-silent.mp4
echo "joined: out/chapter-1-silent.mp4 ($(date +%H:%M:%S))"
