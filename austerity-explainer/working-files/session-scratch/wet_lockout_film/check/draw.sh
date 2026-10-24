#!/bin/bash
C=/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/wet_lockout_film/check
for k in old new; do
 for spec in "house-sample 20" "checkout-test 3"; do
  set -- $spec
  mkdir -p $C/stills/$k/$1
  ( cd $C/kit_$k/paper-film && timeout 900 node tools/render-paper-film.mjs $1 $C/stills/$k/$1 --stills $2 2>&1 | grep -E "still-|rror" | tail -2 )
 done
done
echo ALLDONE
