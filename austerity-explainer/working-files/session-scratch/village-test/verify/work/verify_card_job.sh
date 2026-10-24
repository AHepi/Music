#!/bin/bash
# What this does (runs on a rented card, for the fresh checker): (1) prints the size, SHA-256 and SHA-1 of the rebuilt village file and of the first village's
# finished file; (2) runs the checker's own measure (measure_village.py) on the rebuilt village; (3) draws the first village's ground close-up from the same
# spot as the rebuild's close-up with the plugin's own render verb. Nothing is saved into any scene file.
set -u
B=/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/village-test
V=/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/village-test/verify
BLENDER=/workspace/blender/blender
mkdir -p $V/logs $V/work; date +%T
for f in $B/scene/round4/finished.blend $B/scene/round3/finished.blend; do
  if [ -f "$f" ]; then echo "$f size $(stat -c %s "$f") sha256 $(sha256sum "$f" | cut -c1-64) sha1 $(sha1sum "$f" | cut -c1-40)"; else echo "$f MISSING"; fi
done
mkdir -p $V/logs $V/work; date +%T
$BLENDER -b --disable-autoexec $B/scene/round4/finished.blend --python $V/work/measure_village.py -- $V/work/measure-round4.json > $V/logs/measure-round4.log 2>&1
echo "measure exit $?"; grep -E "MEASURED|Error|Traceback" $V/logs/measure-round4.log | head -5; date +%T
if [ -f $B/scene/round3/finished.blend ]; then
  rm -rf $V/work/before-closeup; mkdir -p $V/work/before-closeup
  $BLENDER -b --disable-autoexec --python-exit-code 1 $B/scene/round3/finished.blend --python $V/work/draw_before_closeup.py -- $B/work/integrator/plugin/kit/place-kit $V/work/before-closeup-job.json 2>&1 | grep -v -E '^[0-9][0-9]:[0-9][0-9]\.[0-9]+ +[A-Za-z]+ +\|' > $V/logs/draw-before.log
  echo "draw exit ${PIPESTATUS[0]}"; grep -E "closeup|PASS|FAIL" $V/logs/draw-before.log | head
fi
mkdir -p $V/logs $V/work; date +%T
ls -la $V/work/before-closeup $V/work/measure-round4.json
