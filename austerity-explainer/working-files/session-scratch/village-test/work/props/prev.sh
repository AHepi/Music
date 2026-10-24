#!/bin/bash
# usage: prev.sh 'views json' [scene] [w] [h]
V=/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/village-test
cd $V/work/props
SCENE=${2:-$V/work/props/scene.blend}
EXPLAINER_FILM_BLENDER_THREADS=2 /home/user/work/blender-app/blender-5.2.2-linux-x64/blender -t 2 -b --disable-autoexec --python-exit-code 1 $SCENE --python preview.py -- "$1" $V/work/props/prev ${3:-640} ${4:-420} 2>&1 | grep -E "rendered|Error|Traceback"
