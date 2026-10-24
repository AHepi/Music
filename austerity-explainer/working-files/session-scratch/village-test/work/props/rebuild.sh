#!/bin/bash
V=/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/village-test
cd $V/work/props
EXPLAINER_FILM_KIT=/home/user/Music/plugins/explainer-film/kit /home/user/work/blender-app/blender-5.2.2-linux-x64/blender -t 2 -b --disable-autoexec $V/scene/ground.blend --python run_stage.py --python-exit-code 1 -- $V/work/props/scene.blend 2>&1 | grep -E "PROBLEM|STAGE|TOTAL|SECONDS|Error|Traceback|File |line " 
