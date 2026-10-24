#!/bin/bash
# What this does: joins the filmed chunks of pages 3 to 5 (film-chapter-parallel.sh's chunk files, in order) into one
# silent film in scratch, then cuts a short film round every place two chunks meet (filmed by different browsers)
# and round the page 4 to 5 run-on, and runs the kit's jump finder on each short film, one at a time.
# Use: bash join_and_check_seams.sh CHUNKS_FOLDER OUT_FOLDER
set -e
chunks="$1"; out="$2"
mkdir -p "$out/seams"
list="$out/join-list.txt"; : > "$list"
for f in $(ls "$chunks"/chunk-*.mp4 | sort); do echo "file '$(realpath "$f")'" >> "$list"; done
ffmpeg -hide_banner -loglevel error -y -f concat -safe 0 -i "$list" -c copy -movflags +faststart "$out/pages-3-to-5-silent.mp4"
first=$(ls "$chunks"/chunk-*.mp4 | sort | head -1 | sed -E 's/.*chunk-0*([0-9]+)-to-.*/\1/')
echo "joined $(wc -l < "$list") chunks from frame $first: $out/pages-3-to-5-silent.mp4"
# the seams: every chunk's first frame after the first, and the run-on (page 4's dissolve, about 95.3 s)
seams=$(ls "$chunks"/chunk-*.mp4 | sort | tail -n +2 | sed -E 's/.*chunk-0*([0-9]+)-to-.*/\1/' | while read f; do python3 -c "print(round(($f - $first) / 30, 3))"; done)
seams="$seams $(python3 -c "print(round(95.35 - $first / 30, 3))")"
for s in $seams; do
  start=$(python3 -c "print(max(0, $s - 1.0))")
  ffmpeg -hide_banner -loglevel error -y -ss "$start" -t 2.0 -i "$out/pages-3-to-5-silent.mp4" -c:v libx264 -crf 12 "$out/seams/seam-$s.mp4"
  echo "== seam at $s s into the film ($(python3 -c "print(round($s + $first / 30, 2))") s on the chapter's timeline)"
  python3 -I /home/user/Music/austerity-explainer/film-kit/paper-film/tools/find_jumps.py "$out/seams/seam-$s.mp4" "$out/seams/seam-$s.jpg" 4 | grep -v "^sheet"
done
