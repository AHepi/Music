import sys, os, time
sys.path.insert(0, '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/garden/character/wood')
import bpy, stage_wood
t = time.time()
opts = eval(os.environ.get('WOOD_OPTS', "{'frame': False}"))
rep = stage_wood.apply(opts)
print('APPLY DONE', time.time() - t)
if os.environ.get('WOOD_SAVE'):
    bpy.ops.wm.save_as_mainfile(filepath=os.environ['WOOD_SAVE'], copy=True)
