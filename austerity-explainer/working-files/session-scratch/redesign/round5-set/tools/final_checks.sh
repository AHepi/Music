#!/usr/bin/env bash
# What this does: the round 5 final shot checks (scratch): for W3, W1 quiet, W1 working, W2 and W2 slowed, one Blender run
# each that draws a film-size picture and measures it, then the checker's report and the relaxed light report (the
# dark men and thin gate bars left out of the "picture matches the scene" test, as in rounds 3 and 4).
set -uo pipefail
S=/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/redesign/round5-set
cd /home/user/Music/austerity-explainer/film-kit
for v in "w3 quiet w3 final-w3-quiet" "w1 quiet w1 final-w1-quiet" "w1 working w1-working final-w1-working" "w2 quiet w2 final-w2-quiet" "w2 slowed w2-slowed final-w2-slowed"; do
  set -- $v
  $S/tools/check_view.sh $1 $2 $3 $4 > /dev/null
  o=$S/checks/$4
  python3 $S/tools/check_dark_picture.py --check examples/inflation-chapter-2-newcomers/works-$3-shot-check.json --facts $o/facts --picture $o/picture.png \
    --out $o/light --render-log $o/blender.log > /dev/null 2>&1
  echo "$4: $(sed -n 3p $o/report.md) | light: $(sed -n 3p $o/light/report.md)"
done
