cd /tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/garden/character/checker2
/workspace/blender/blender -b --disable-autoexec /tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/garden/character/final/garden_character.blend --python scripts/warp_stats.py -- out/warp.json 2>&1 | grep -E "WARP|Error|Traceback|line" | tail
