import sys, os, time, json
import bpy
sys.path.insert(0, '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/village-test/stages')
import importlib, stage_forest
t=time.time()
opts = json.loads(sys.argv[sys.argv.index('--')+1]) if '--' in sys.argv and len(sys.argv)>sys.argv.index('--')+1 else {}
info = stage_forest.apply(opts)
print('stage seconds', round(time.time()-t,1))
out = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/village-test/work/forest/scene.blend'
bpy.ops.wm.save_as_mainfile(filepath=out, compress=True)
print('saved', out)
