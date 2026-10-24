#!/bin/bash
# What this does (runs on a rented card): (1) writes the audit's plain verdict text for the finished village, (2) draws the four view cameras and two
# ground close-ups of the finished scene with the plugin's own render verb (the renderer the rule picks), at 1200 x 800, into the run folder's rebuild/full.
# The scene is opened and never saved.
set -u
B=/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/village-test
KIT=$B/work/integrator/plugin/kit
BLENDER=/workspace/blender/blender
PY=$(ls /workspace/blender/5.2/python/bin/python3.1* | head -1)
export EXPLAINER_FILM_KIT=$KIT
date +%T
$PY -I -B $KIT/calculators/place_audit_check.py check $B/scene/round4/place-audit.json --facts $B/plan/real-world-facts.json --place-settings $B/plan/place-settings-round4.json --skip-freshness > $B/reports/audit-judged-round4.txt 2>&1
echo "judge exit $?"
rm -rf $B/rebuild/full; mkdir -p $B/rebuild/full
$BLENDER -b --disable-autoexec --python-exit-code 1 $B/scene/round4/finished.blend --python $B/work/integrator/draw_round4.py -- $KIT/place-kit $B/work/integrator/draw-round4-job.json 2>&1 | grep -v -E '^[0-9][0-9]:[0-9][0-9]\.[0-9]+ +[A-Za-z]+ +\|' > $B/reports/draw-round4.txt
echo "draw exit ${PIPESTATUS[0]}"; date +%T
ls -la $B/rebuild/full
