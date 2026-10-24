film_one() {
  local from=$1 to=$2 file="$OUT/chunk-$(printf %05d "$1")-to-$(printf %05d "$2").mp4"
  if [ -s "$file" ]; then return 0; fi
  local started=$(date +%s) pieces="$file.pieces.txt" a b piece
  : > "$pieces"
  for (( a = from; a < to; a += PIECE_FRAMES )); do
    b=$(( a + PIECE_FRAMES < to ? a + PIECE_FRAMES : to ))
    piece="$file.piece-$(printf %05d "$a")-to-$(printf %05d "$b").mp4"
    if [ ! -s "$piece" ]; then
      if node tools/render-paper-film.mjs "$SCENE" "$piece.part.mp4" --frames "$a" "$b" >> "$file.log" 2>&1; then
        mv "$piece.part.mp4" "$piece"; rm -f "$piece.part.json"
      else
        echo "frames $a-$b FAILED, see $file.log ($(date +%H:%M:%S))" >> "$LOG"; return 0
      fi
    fi
    echo "file '$(realpath "$piece")'" >> "$pieces"
  done
  if ffmpeg -hide_banner -loglevel error -y -f concat -safe 0 -i "$pieces" -c copy "$file.part.mp4" >> "$file.log" 2>&1; then
    python3 -c "import json, sys; print(json.dumps({'scene': sys.argv[1], 'first_frame': int(sys.argv[2]), 'last_frame': int(sys.argv[3]) - 1, 'fps': 30}, indent=1))" \
      "$SCENE" "$from" "$to" > "${file%.mp4}.json"
    mv "$file.part.mp4" "$file"; rm -f "$pieces" "$file".piece-*.mp4
    echo "frames $from-$to filmed in $(( $(date +%s) - started )) s ($(date +%H:%M:%S))" >> "$LOG"
  else
    echo "frames $from-$to FAILED to join its pieces, see $file.log ($(date +%H:%M:%S))" >> "$LOG"
  fi
}
