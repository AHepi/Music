import sys, os, tempfile
sys.path.insert(0, '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/garden/character/wood')
import bpy, stage_wood
d = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/garden/character/wood/work/maps_tmp'
made = stage_wood.ensure_maps(d)
print('ENSURE', made, [os.path.getsize(os.path.join(d, f)) for f in sorted(os.listdir(d))])
