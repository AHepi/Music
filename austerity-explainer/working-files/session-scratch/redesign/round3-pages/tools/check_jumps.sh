#!/bin/bash
# What this does: runs the kit's jump finder on each filmed chunk of pages 3 to 5 of chapter 2 for newcomers, one at a
# time, telling it where the planned cuts are (so each listed jump is named "planned cut" or "JUMP"), then joins the
# chunks into one silent film in scratch and runs the jump finder on a 2-second clip round every place two chunks meet.
# Use: bash check_jumps.sh CHUNKS_FOLDER OUT_FOLDER
set -u
chunks="$1"; out="$2"; mkdir -p "$out/seams" "$out/sheets"
FIND=/home/user/Music/austerity-explainer/film-kit/paper-film/tools/find_jumps.py
# the planned cuts and steps, chapter seconds: W3 to W1 on "In"; the time cut on "go"; the three window steps on
# "start"; the start of page 3's peel (the curling page is shaded as paper, 11% darker, from its first frame); the cut
# from W2 to W3 on "Most"; the start of page 5's peel
PLANNED="55.100 67.233 68.733 69.000 69.267 74.300 107.167 122.633"
for f in $(ls "$chunks"/chunk-*.mp4 | sort); do
  first=$(basename "$f" | sed -E 's/chunk-0*([0-9]+)-to-.*/\1/')
  rel=$(python3 -c "import sys; a=int(sys.argv[1]); print(' '.join(f'{float(p) - a / 30:.3f}' for p in sys.argv[2:] if 0 < float(p) - a / 30 < 30))" "$first" $PLANNED)
  echo "== $(basename "$f") (chapter $(python3 -c "print(f'{$first / 30:.2f}')") s on)"
  python3 -I "$FIND" "$f" "$out/sheets/$(basename "${f%.mp4}").jpg" 4 $rel | grep -v "^sheet" | python3 -c "
import sys
first = $first
for line in sys.stdin:
    line = line.rstrip()
    import re
    m = re.search(r'\((\d+\.\d+) s\)', line)
    if m: line += f'   [chapter {float(m.group(1)) + first / 30:.2f} s]'
    print(line)"
done
list="$out/join-list.txt"; : > "$list"
for f in $(ls "$chunks"/chunk-*.mp4 | sort); do echo "file '$(realpath "$f")'" >> "$list"; done
ffmpeg -hide_banner -loglevel error -y -f concat -safe 0 -i "$list" -c copy -movflags +faststart "$out/pages-3-to-5-silent.mp4"
start=$(ls "$chunks"/chunk-*.mp4 | sort | head -1 | sed -E 's/.*chunk-0*([0-9]+)-to-.*/\1/')
for f in $(ls "$chunks"/chunk-*.mp4 | sort | tail -n +2); do
  first=$(basename "$f" | sed -E 's/chunk-0*([0-9]+)-to-.*/\1/')
  at=$(python3 -c "print(round(($first - $start) / 30, 3))")
  from=$(python3 -c "print(max(0, $at - 1.0))")
  ffmpeg -hide_banner -loglevel error -y -ss "$from" -t 2.0 -i "$out/pages-3-to-5-silent.mp4" -c:v libx264 -crf 12 "$out/seams/seam-$first.mp4"
  echo "== where chunks meet at frame $first (chapter $(python3 -c "print(f'{$first / 30:.2f}')") s)"
  python3 -I "$FIND" "$out/seams/seam-$first.mp4" "$out/seams/seam-$first.jpg" 4 | grep -v "^sheet"
done
