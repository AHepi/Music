#!/usr/bin/env bash
# What this does: one Blender run that dresses the Works in a view and state, draws a film-size picture of it (1080 wide)
# and measures it for the shot checker, then the checker's report (scratch, round 5).
# Use: check_view.sh VIEW STATE CHECK_NAME OUT_NAME [more Blender options]
set -euo pipefail
S=/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/redesign/round5-set
KIT=/home/user/Music/austerity-explainer/film-kit
W=$KIT/assets/models/inflation-chapter-2-newcomers/works
view=$1; state=$2; check=$3; name=$4; shift 4
out=$S/checks/$name
mkdir -p $out
cd $KIT
# the picture is drawn in the same run, before the measuring; the checker reads it and that run's log afterwards
BLEND=$W/works-lane.blend RENDER_LOG=$out/blender.log paper-film/tools/check-shot.sh \
  paper-film/blender/inflation-chapter-2-newcomers/works/assemble_works.py examples/inflation-chapter-2-newcomers/works-$check-shot-check.json \
  $out $out/picture.png -- --view $view --state $state --preview $out/picture.png --preview-width 1080 --samples ${SAMPLES:-12} "$@" > $out/run.out 2>&1 || true
sed -n 3p $out/report.md
