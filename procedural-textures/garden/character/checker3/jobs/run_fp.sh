cd /tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/garden/character/checker3
mkdir -p out
G=/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/garden
/workspace/blender/blender -b --disable-autoexec $G/fix/garden_real_fixed.blend --python scripts/fp.py -- out/fp_start.json 2>&1 | grep -E "FP DONE|Error|Traceback"
/workspace/blender/blender -b --disable-autoexec $G/character/fix/final/garden_character_fix.blend --python scripts/fp.py -- out/fp_fix.json 2>&1 | grep -E "FP DONE|Error|Traceback"
python3 -I scripts/own_diff.py 2>&1 | head -80 || true
