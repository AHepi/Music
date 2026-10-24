"""Load the untouched scene, add ONLY the six final cameras, save as a compressed copy."""
import bpy, sys, json, os
sys.path.insert(0, os.path.dirname(__file__))
import camlib
argv = sys.argv[sys.argv.index('--') + 1:]
spec_path, out = argv[0], argv[1]
specs = json.load(open(spec_path))
coll = bpy.data.collections['Cameras']
before = {o.name for o in bpy.data.objects}
for sp in specs:
    assert '__' not in sp['name']
    camlib.make_camera(sp, coll)
after = {o.name for o in bpy.data.objects}
print('ADDED', sorted(after - before))
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=out, compress=True, copy=True)
print('SAVED', out)
