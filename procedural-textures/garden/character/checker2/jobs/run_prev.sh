cd /tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/garden/character/checker2
G=/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/garden
mkdir -p out/prev out/crops
/workspace/blender/blender -b --disable-autoexec $G/character/final/garden_character.blend -P $G/character/final/render_character.py -- jobs/prev_job.json 2>&1 | grep -E "PREVIEW_DONE|CHARACTER_RENDER_ALL|WARNING|Error|Traceback" | tail -20
/workspace/blender/blender -b --disable-autoexec --python scripts/crops2.py 2>&1 | grep -E "CROPS2|Error|Traceback" | tail
ls -la out/prev out/crops | head -40
