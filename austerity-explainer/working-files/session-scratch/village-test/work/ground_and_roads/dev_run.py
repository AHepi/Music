import sys, time, importlib.util, os
sys.path.insert(0, '/home/user/Music/plugins/explainer-film/kit/place-kit')
import bpy
t0 = time.time()
spec = importlib.util.spec_from_file_location('stage_ground', '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/village-test/stages/stage_ground_and_roads.py')
mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
rep = mod.apply({})
print('apply seconds', round(time.time()-t0,1), flush=True)
out = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/village-test/work/ground_and_roads/dev_scene.blend'
bpy.ops.wm.save_as_mainfile(filepath=out, compress=True)
print('saved', os.path.getsize(out), flush=True)
