#!/bin/bash
# What this file does (plain words): draws the stills needed to look for dry-looking patches along the move: the same moments of the clip (view=move, seconds 3, 4, 5, 6 and 7)
# drawn with the wet front painting used as its own behind painting (the reference: no behind painting seam can show, because front and behind are the same picture).
# Run after the clips are filmed (it uses the machine's whole processor).
W="$(cd "$(dirname "$0")/.." && pwd)"
for t in 3.0 4.0 5.0 6.0 7.0; do
  bash $W/tools/draw_still.sh $W/kit_check $W/stills/own own_$t "view=move&painting=lockout-painted.jpg&behind=lockout-painted.jpg" $t lockout-newlook-hook
done
echo "REFERENCE DONE $(date +%T)"
