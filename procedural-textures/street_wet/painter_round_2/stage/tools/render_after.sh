#!/bin/bash
# What this file does (plain words): after the brightness fix is in the COPY of the stage (python3 -I tools/patch_engine.py fix), draws
#   stills/after/          the lockout pictures with the fix SWITCHED ON for the lockout (?tone=painted): the new wet front and behind paintings, the film's old dry behind painting, and the film's own dry painting
#   stills/after_default/  the film's own dry lockout and the other existing scenes drawn WITHOUT asking for the fix (the new stage file, but the fix is off by default): these must be dot for dot the same as stills/before/
# Run: bash tools/render_after.sh
HERE="$(cd "$(dirname "$0")/.." && pwd)"
D="$HERE/tools/draw.sh"
bash "$HERE/tools/render_stage_views.sh" after "tone=painted"
(
 bash "$D" after_default dry_projector "view=projector"
 bash "$D" after_default dry_moved     "view=moved"
 bash "$D" after_default dry_move      "view=move"
) &
bash "$HERE/tools/render_other_scenes.sh" after_default
wait
echo "ALL AFTER DONE $(date +%T)"
