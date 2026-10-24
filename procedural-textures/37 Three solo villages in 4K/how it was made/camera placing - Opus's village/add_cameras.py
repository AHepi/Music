# Add the six new cameras (exact matrices from CAMS.json) to the open scene and save a COPY. Changes nothing else.
# Run: blender -b SCENE.blend --python add_cameras.py -- CAMS.json OUT.blend
import bpy, json, sys
from mathutils import Matrix

a = sys.argv[sys.argv.index('--') + 1:]
cams, out = json.load(open(a[0])), a[1]
sc = bpy.context.scene
col = bpy.data.collections.get("Cameras")
assert col is not None, "no Cameras collection"
before = {k: len(getattr(bpy.data, k)) for k in ('objects', 'cameras', 'meshes', 'materials', 'node_groups', 'images', 'collections', 'lights', 'worlds')}
active_before = sc.camera.name if sc.camera else None
for c in cams:
    name = c['name']
    assert bpy.data.objects.get(name) is None and bpy.data.cameras.get(name) is None, name + " already exists"
    cd = bpy.data.cameras.new(name)
    cd.type = 'PERSP'
    cd.lens = c['lens']
    cd.sensor_width = 36.0
    cd.sensor_fit = 'AUTO'
    cd.clip_start = 0.05
    cd.clip_end = 1500.0
    cd.shift_x = c.get('shift_x', 0.0)
    cd.shift_y = c.get('shift_y', 0.0)
    if c.get('dof'):
        cd.dof.use_dof = True
        cd.dof.focus_distance = c['dof'][0]
        cd.dof.aperture_fstop = c['dof'][1]
    else:
        cd.dof.use_dof = False
    ob = bpy.data.objects.new(name, cd)
    col.objects.link(ob)
    ob.rotation_mode = 'QUATERNION'
    ob.matrix_world = Matrix(c['matrix'])
bpy.context.view_layer.update()
assert (sc.camera.name if sc.camera else None) == active_before
after = {k: len(getattr(bpy.data, k)) for k in before}
print('COUNTS_BEFORE', json.dumps(before))
print('COUNTS_AFTER', json.dumps(after))
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=out, compress=True, copy=True)
print('SAVED', out, flush=True)
