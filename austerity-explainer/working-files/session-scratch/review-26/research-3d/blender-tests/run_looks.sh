#!/bin/bash
B=/home/user/work/blender-app/blender-5.2.2-linux-x64/blender
D=/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/review-26/research-3d/blender-tests
cd $D; pgrep -f "Xvfb :97" >/dev/null || (Xvfb :97 -screen 0 1920x1080x24 >/dev/null 2>&1 &); sleep 1; export DISPLAY=:97
for m in plain fog lines kuwahara fog_lines_kuwahara; do timeout 900 $B -b --factory-startup --python $D/look_test.py -- $m $D/out/look_$m.jpg 2>&1 | grep -E "LOOK_SECONDS|Error|Traceback|type" >> $D/looks.log; done
echo DONE >> $D/looks.log
