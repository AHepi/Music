#!/bin/bash
V=/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/village-test
export PATH=$PATH:/home/user/Music/plugins/explainer-film/bin
cd $V/work/forest
( time EXPLAINER_FILM_BLENDER_THREADS=2 explainer-film-place finish-part --blender /home/user/work/blender-app/blender-5.2.2-linux-x64/blender --scene $V/work/forest/scene.blend --settings $V/plan/place-settings.json --owner forest --quick --save-as $V/work/forest/part.blend ) > $V/work/forest/finish_part.log 2>&1
