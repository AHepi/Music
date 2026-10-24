#!/bin/bash
# usage: go.sh script.py [args after --]
export EXPLAINER_FILM_KIT=/home/user/Music/plugins/explainer-film/kit
B=/home/user/work/blender-app/blender-5.2.2-linux-x64/blender
W=/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/village-test/work/forest
S=$1; shift
BL=${BLEND:-$W/ground_copy.blend}
$B -t 2 -b --disable-autoexec $BL --python-exit-code 1 --python $W/$S -- "$@"
