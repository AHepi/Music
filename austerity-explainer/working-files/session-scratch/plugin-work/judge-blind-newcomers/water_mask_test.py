"""Tiny test: does a water object change the plan masks (dampness, shade) near a quay edge? Run inside Blender with: -- WITH_WATER or NO_WATER"""
import sys, bpy, bmesh
KIT = sys.argv[sys.argv.index('--') + 2] if len(sys.argv) > sys.argv.index('--') + 2 else '/home/user/Music/plugins/explainer-film/kit/place-kit'
sys.path.insert(0, KIT)
from place_kit import settings_file, names
from place_kit.wear import masks
mode = sys.argv[sys.argv.index('--') + 1]

def box(name, x0, x1, y0, y1, z0, z1, role):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co.x = x0 if v.co.x < 0 else x1
        v.co.y = y0 if v.co.y < 0 else y1
        v.co.z = z0 if v.co.z < 0 else z1
    mesh = bpy.data.meshes.new(name); bm.to_mesh(mesh); bm.free()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj[names.ROLE] = role; obj[names.OWNER] = 'test'
    return obj

for o in list(bpy.data.objects): bpy.data.objects.remove(o)
box('quay paving', 0, 8, -6, 6, -0.5, 0.0, 'ground.stone_paving')
box('seabed', 8, 24, -6, 6, -3.5, -3.0, 'ground.earth')
box('quay wall', 7.6, 8.0, -6, 6, -3.0, 0.0, 'wall.stone')
if mode == 'WITH_WATER':
    box('sea', 8, 24, -6, 6, -0.62, -0.6, 'water.sea')
settings = settings_file.Settings({'place': 't', 'state': 'wet'})
pm, record = masks.build_plan_masks(settings, quick=True)
print('MASK cell', pm.cell, 'bounds', pm.bounds)
import numpy as np
for x in (2.0, 5.0, 7.0, 7.9, 9.0, 11.0, 14.0, 20.0):
    pts = [[x, 0.0, 0.0]]
    print('MASK', mode, 'x=%5.1f' % x, ' '.join('%s=%.2f' % (n, pm.sample(n, pts)[0]) for n in ('dampness', 'shade', 'wall_dist', 'prop_dist', 'lowness', 'above_water')))
