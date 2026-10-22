#!/bin/bash
# usage: run_local.sh script.py [args after --]  (opens the read-only garden scene locally, headless, never saves)
D=/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/garden
S=$1; shift
cd /tmp; /home/user/work/blender-app/blender-5.2.2-linux-x64/blender -b --disable-autoexec $D/fix/garden_real_fixed.blend --python $S -- "$@" 2>&1 | grep -v -E "^(Blender [0-9]|Read blend|$)"
