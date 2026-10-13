#!/bin/bash
# What this does: films a whole chapter scene in the paper look, one page at a time, then joins the
# pages into one silent video.
#
# Each chunk is one page: it starts the moment that page's sheet lies flat (the page turn before it
# has finished) and ends when its own page turn has finished. The scene itself reports where its
# pages end (render-paper-film.mjs SCENE --info). So a change to one page only needs that page's
# chunk filmed again: delete the chunk's file and run this script again; chunks that already exist
# are kept. Filming takes about 0.6 to 0.9 seconds a frame on a 2-processor machine (about 80
# minutes for a 3.7-minute chapter). Filming two chunks at once is not faster there.
#
# Use (from the kit folder): bash paper-film/tools/film-chapter.sh SCENE
#   writes paper-film/out/SCENE-chunks/page-NN-frames-A-to-B.mp4 and paper-film/out/SCENE-silent.mp4
# Then join the sound with narration-tools/finish_film.sh.

set -u
cd "$(dirname "$0")/.."
SCENE="$1"
OUT="out/$SCENE-chunks"
mkdir -p "$OUT"

INFO=$(node tools/render-paper-film.mjs "$SCENE" --info | tail -1)
FRAMES=$(echo "$INFO" | python3 -c "import json,sys; print(json.load(sys.stdin)['frames'])")
EDGES=($(echo "$INFO" | python3 -c "import json,sys; d=json.load(sys.stdin); print(' '.join(map(str, [0] + d['page_edge_frames'] + [d['frames']])))"))
echo "$SCENE: $FRAMES frames, page edges at frames ${EDGES[*]}"

for ((page = 1; page < ${#EDGES[@]}; page++)); do
  from=${EDGES[$((page - 1))]}
  to=${EDGES[$page]}
  file="$OUT/page-$(printf %02d "$page")-frames-$from-to-$to.mp4"
  if [ -s "$file" ]; then echo "page $page: already filmed"; continue; fi
  echo "page $page: filming frames $from to $((to - 1)) ($(date +%H:%M:%S))"
  if node tools/render-paper-film.mjs "$SCENE" "$OUT/in-progress.mp4" --frames "$from" "$to"; then
    mv "$OUT/in-progress.mp4" "$file"
    mv "$OUT/in-progress.json" "${file%.mp4}.json"
  else
    echo "page $page: filming failed"
    exit 1
  fi
done

# join the chunks without re-encoding them (only this scene's current chunk names)
LIST="$OUT/join-list.txt"
: > "$LIST"
for ((page = 1; page < ${#EDGES[@]}; page++)); do
  file="$OUT/page-$(printf %02d "$page")-frames-${EDGES[$((page - 1))]}-to-${EDGES[$page]}.mp4"
  echo "file '$(realpath "$file")'" >> "$LIST"
done
ffmpeg -hide_banner -loglevel error -y -f concat -safe 0 -i "$LIST" -c copy -movflags +faststart "out/$SCENE-silent.mp4"
echo "joined: paper-film/out/$SCENE-silent.mp4 ($(date +%H:%M:%S))"
