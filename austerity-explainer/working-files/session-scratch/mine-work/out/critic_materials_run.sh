#!/bin/bash
# usage: name camera lens extra...
name=$1; cam=$2; lens=$3; shift 3
/home/user/work/blender-app/blender-5.2.2-linux-x64/blender -b --disable-autoexec -t 2 --python /tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/mine-work/assemble_mine.py -- /tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/mine-work/out/critic_materials_$name --quick --camera $cam --lens $lens --width 720 --samples 24 "$@" > /tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/mine-work/out/critic_materials_$name.log 2>&1
