#!/usr/bin/env bash
# What this does: one Blender run that dresses the Works in a view and state, draws a film-size picture of it (1080 wide)
# and measures it for the shot checker, then the checker's report and the relaxed light report (the dark men and thin
# gate bars left out of the "picture matches the scene" test, as in rounds 3 to 5) (scratch, round 6 set).
# Use: check_view.sh VIEW STATE CHECK_NAME OUT_NAME [more Blender options]
set -uo pipefail
S=/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/redesign/round6-set
KIT=/home/user/Music/austerity-explainer/film-kit
W=$KIT/assets/models/inflation-chapter-2-newcomers/works
view=$1; state=$2; check=$3; name=$4; shift 4
out=$S/checks/$name
mkdir -p $out
cd $KIT
BLEND=$W/works-lane.blend RENDER_LOG=$out/blender.log paper-film/tools/check-shot.sh \
  paper-film/blender/inflation-chapter-2-newcomers/works/assemble_works.py examples/inflation-chapter-2-newcomers/works-$check-shot-check.json \
  $out $out/picture.png -- --view $view --state $state --preview $out/picture.png --preview-width 1080 --samples ${SAMPLES:-12} "$@" > $out/run.out 2>&1 || true
python3 $S/tools/check_dark_picture.py --check examples/inflation-chapter-2-newcomers/works-$check-shot-check.json --facts $out/facts --picture $out/picture.png \
  --out $out/light --render-log $out/blender.log > $out/light.out 2>&1 || true
echo "$name: $(sed -n 3p $out/report.md 2>/dev/null) | light: $(sed -n 3p $out/light/report.md 2>/dev/null)"
