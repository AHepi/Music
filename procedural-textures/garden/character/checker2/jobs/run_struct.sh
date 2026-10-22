cd /tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/garden/character/checker2
mkdir -p out
/workspace/blender/blender -b --disable-autoexec /tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/garden/character/final/garden_character.blend --python scripts/struct.py -- out/struct.json 2>&1 | tail -30
