import bpy, sys, bmesh
sys.path.insert(0, '/home/user/Music/plugins/explainer-film/kit/place-kit'); sys.path.insert(0, '/home/user/Music/plugins/explainer-film/kit/calculators')
from place_kit.checks import construction as C
import numpy as np
from place_kit import house_numbers
def box(name, size, location):
    mesh = bpy.data.meshes.new(name); b = bmesh.new(); bmesh.ops.create_cube(b, size=1.0)
    for v in b.verts: v.co.x*=size[0]; v.co.y*=size[1]; v.co.z*=size[2]
    b.to_mesh(mesh); b.free(); o = bpy.data.objects.new(name, mesh); bpy.context.scene.collection.objects.link(o); o.location = location; return o
bpy.ops.wm.read_factory_settings(use_empty=True)
box('block 1', (0.3,0.3,0.3), (-1.4,0,0.15)); box('block 2', (0.3,0.3,0.3), (1.4,0,0.15)); box('plank long', (3.2,0.2,0.04), (0,0,0.32))
bpy.context.view_layer.update()
objs = [bpy.data.objects[n] for n in ('block 1','block 2','plank long')]
plist = []
for o in objs:
    plist += C._loose_parts(o, {'role': 'timber.plank' if 'plank' in o.name else 'stone.footing'}, __import__('place_kit').settings_file.roles_table())
print('PARTS', [(p.name, p.bmin.round(3).tolist(), p.bmax.round(3).tolist(), p.max_span) for p in plist])
bvh = C._build_tree([p.V for p in plist], [p.T for p in plist])
plank = plist[2]
step = house_numbers.value('place_construction.walk_ray_step_metres'); reach = house_numbers.value('place_construction.rest_patch_reach_millimetres')/1000
print('STEP', step, 'REACH', reach)
print('SPAN', C.unsupported_span(plank, bvh, step, reach))
centre, axis = C.long_axis(plank)
print('AXIS', centre, axis)
step = 0.05
centre, axis = C.long_axis(plank)
from mathutils import Vector
own = plank.bvh
along = (plank.V[:, :2] - centre[:2]) @ axis[:2]
low, high = float(along.min()), float(along.max())
out = []
for t in np.arange(low + step/2, high, step)[::6]:
    x, y = centre[0] + axis[0]*t, centre[1] + axis[1]*t
    bottom = own.ray_cast(Vector((x, y, plank.bmin[2] - 1.0)), Vector((0, 0, 1)))
    hit = bvh.ray_cast(Vector((x, y, (bottom[0].z if bottom[0] else 9) - reach)), Vector((0, 0, 1)), reach + 0.003)
    out.append((round(t,2), None if bottom[0] is None else round(bottom[0].z,3), None if hit[0] is None else (round(hit[0].z,3), round(hit[1].z,2))))
print('TRACE', out)
