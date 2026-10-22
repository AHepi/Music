cd /tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/garden/character/checker2
G=/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/garden
ls -la $G/fix/garden_real_fixed.blend $G/character/direction/start/
sha256sum $G/fix/garden_real_fixed.blend $G/character/direction/start/garden_real_fixed.blend
/workspace/blender/blender -b --disable-autoexec $G/character/direction/start/garden_real_fixed.blend --python scripts/fp.py -- out/fp_start.json 2>&1 | tail -6
