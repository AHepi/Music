cd /tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/garden/character/checker2
mkdir -p out
/workspace/blender/blender -b --disable-autoexec --python scripts/nm_dir.py -- /tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/garden/character/final/garden_character.blend out/nm_dir.json scripts/nm_images.json 2>&1 | tail -40
