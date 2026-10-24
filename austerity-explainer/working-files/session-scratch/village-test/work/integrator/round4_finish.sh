#!/bin/bash
# What this does (runs on a rented card, where Blender is): the integrator's whole finishing pass for the village, round 4, with the updated
# plugin: (1) finish on the combined scene, (2) audit of the saved file, (3) the preflight stage place, (4) the renderer rule.
# Every output goes to the run folder's reports. The card has no system python3, so the plugin's launchers are replaced by their own
# Blender commands (same options) and the preflight runs with the Python that ships inside Blender.
set -u
B=/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/village-test
PLUGIN=$B/work/integrator/plugin
KIT=$PLUGIN/kit
BLENDER=/workspace/blender/blender
BLENDER_PYTHON=$(ls /workspace/blender/5.2/python/bin/python3.1* | head -1)
export EXPLAINER_FILM_KIT=$KIT
export PLACE_KIT_SCAN_CACHE=$B/work/integrator/scan-cache
SETTINGS=$B/plan/place-settings-round4.json
FACTS=$B/plan/real-world-facts.json
OUT=$B/scene/round4
mkdir -p $OUT $B/reports
place_verb() {   # place_verb SCENE VERB ARGS...
  local scene=$1; local verb=$2; shift 2
  $BLENDER -b --disable-autoexec --python-exit-code 1 "$scene" --python $KIT/place-kit/blender_run.py -- "$verb" "$@" 2>&1 | grep -v -E '^[0-9][0-9]:[0-9][0-9]\.[0-9]+ +[A-Za-z]+ +\|'
  return ${PIPESTATUS[0]}
}
date +%T
echo "=== 1 finish"
place_verb $B/scene/round3/combined.blend finish --settings $SETTINGS --save-as $OUT/finished.blend > $B/reports/finish-round4.txt
echo "finish exit $?"; date +%T
echo "=== 2 audit"
place_verb $OUT/finished.blend audit --settings $SETTINGS --facts $FACTS --out $OUT/place-audit.json > $B/reports/audit-round4.txt
echo "audit exit $?"; date +%T
echo "=== 3 preflight place"
$BLENDER_PYTHON -B $KIT/calculators/preflight.py --kit $KIT place --place-audit $OUT/place-audit.json --blend $OUT/finished.blend --place-settings $SETTINGS --real-world-facts $FACTS --reports $B/reports/preflight-round4 > $B/reports/preflight-round4.txt 2>&1
echo "preflight exit $?"; date +%T
echo "=== 4 renderer rule"
place_verb $OUT/finished.blend renderer-for > $B/reports/renderer-for-round4.txt
echo "renderer-for exit $?"; date +%T
sha256sum $OUT/finished.blend
ls -la $OUT
