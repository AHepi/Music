cd /tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/garden/character/checker3
mkdir -p out
G=/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/garden
/workspace/blender/blender -b --disable-autoexec $G/character/fix/final/garden_character_fix.blend --python scripts/rails.py -- out/rails_fix.json 2>&1 | tail -12
