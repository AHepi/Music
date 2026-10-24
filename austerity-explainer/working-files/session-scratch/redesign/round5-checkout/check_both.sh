#!/usr/bin/env bash
# What this does: draws the checkout's C1 preview at the composed spot and at the plate spot (film lens) and runs the
# shot checker on each; prints each report's problems. Use: check_both.sh NAME
set -u
S=/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/redesign/round5-checkout
K=/home/user/Music/austerity-explainer/film-kit
B=/home/user/work/blender-app/blender-5.2.2-linux-x64/blender
A=$K/paper-film/blender/inflation-chapter-2-newcomers/checkout/assemble_checkout.py
C=$K/examples/inflation-chapter-2-newcomers/checkout-c1-shot-check.json
n=$1
for spot in composed plate; do
  DISPLAY=:96 $B -b --python $A -- --preview $S/previews/$n-$spot.png --spot $spot --samples 16 --preview-width 1080 > $S/previews/$n-$spot.log 2>&1 || { echo "render failed"; grep -n "Error" -A5 $S/previews/$n-$spot.log | head; }
  extra=""
  [[ $spot == plate ]] && extra="-- --camera-at -0.16,-1.1,1.6 --yaw 0 --fov 60.4"
  (cd $K && BLEND=$S/checkout-empty.blend paper-film/tools/check-shot.sh $A $C $S/check-$n-$spot $S/previews/$n-$spot.png $extra > /dev/null 2>&1)
  echo "== $spot: $(sed -n 3p $S/check-$n-$spot/report.md)"
  sed -n '/^## Problems/,/^## Passed/p' $S/check-$n-$spot/report.md | grep "^[0-9]*\. \*\*" | cut -c1-260
done
