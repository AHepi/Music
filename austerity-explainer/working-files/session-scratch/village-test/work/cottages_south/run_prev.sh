#!/bin/bash
# usage: run_prev.sh 'views json' [scene]
cd /tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/village-test/work/cottages_south
SCENE=${2:-scene.blend}
EXPLAINER_FILM_BLENDER_THREADS=2 /home/user/work/blender-app/blender-5.2.2-linux-x64/blender -t 2 -b --disable-autoexec --python-exit-code 1 $SCENE --python run_stage.py --python preview.py -- "$1" prev 2>&1 | grep -v "^$" | tail -8
