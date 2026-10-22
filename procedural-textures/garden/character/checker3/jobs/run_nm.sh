cd /tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/garden/character/checker3
mkdir -p out
G=/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/garden
B=$G/character/fix/final/garden_character_fix.blend
/workspace/blender/blender -b --disable-autoexec $B --python scripts/nm_struct.py -- out/nm_struct_fix.json 2>&1 | grep -E "NM STRUCT DONE|Error|Traceback"
/workspace/blender/blender -b --disable-autoexec --python scripts/nm_sem.py -- $B out/nm_sem_fix.json 2>&1 | tail -30
