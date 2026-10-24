#!/bin/bash
# draws graphics-test at 3 s and house-sample at 20 s, three times with the old stage and three times with the new
D=/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/plugin-work/lessons/code-and-stage/draw
cd "$D"
for v in old new; do
  mkdir -p "$D/pictures-$v"
  for k in 1 2 3; do
    for pair in "graphics-test 3" "house-sample 20" "lockout-test 5"; do
      set -- $pair
      rm -rf "$D/tmp-$v-$k"; mkdir -p "$D/tmp-$v-$k"
      start=$(date +%s.%N)
      node "kit-$v/paper-film/tools/render-paper-film.mjs" "$1" "$D/tmp-$v-$k" --stills "$2" > "$D/log-$v-$k-$1.txt" 2>&1
      end=$(date +%s.%N)
      f=$(ls "$D/tmp-$v-$k"/still-*.jpg 2>/dev/null | head -1)
      if [ -n "$f" ]; then mv "$f" "$D/pictures-$v/$1-$k.jpg"; echo "$v $k $1 drawn in $(echo "$end - $start" | bc) s"; else echo "$v $k $1 FAILED"; fi
    done
  done
done
rm -rf "$D"/tmp-*
echo done
