# What this does (plain words): STUDY ONLY, saves nothing. (a) the road's camber: the height of the ground across the street at y = 10, so the crown and gutter can be told from the geometry;
# (b) what the kerb and the flags are made of: how many separate stones the geometry holds, how long they are, which edges are marked sharp, and how many faces face up / sideways;
# (c) the real joint spacing the pictures should show (kerb stone lengths, flag size).
import json, sys
import bpy
import numpy as np
from mathutils import Vector
scene = bpy.context.scene
deps = bpy.context.evaluated_depsgraph_get()
res = {}
ground = [bpy.data.objects[n] for n in ('street_setts', 'street_channels', 'street_kerbs', 'street_pavements')]
row = {}
for x in np.arange(-4.4, 4.41, 0.2):
    hit, loc, n, i, obj, m = scene.ray_cast(deps, Vector((float(x), 10.0, 40.0)), Vector((0, 0, -1)), distance=80.0)
    # only count a hit on the four ground objects
    if hit and obj.name in [g.name for g in ground]:
        row[f'{x:+.1f}'] = (round(loc.z - 10.0 * np.tan(np.radians(4)), 3), round(float(n.z), 3), obj.name.replace('street_', ''))
res['height_above_the_4_degree_line_at_y10(x: z, normal_z, object)'] = row
# kerb stones
kerb = bpy.data.objects['street_kerbs']
me = kerb.data
co = np.empty(len(me.vertices) * 3); me.vertices.foreach_get('co', co); co = co.reshape(-1, 3)
sharp = np.zeros(len(me.edges), bool)
if 'sharp_edge' in me.attributes:
    me.attributes['sharp_edge'].data.foreach_get('value', sharp)
res['kerb'] = dict(faces=len(me.polygons), edges=len(me.edges), sharp_edges=int(sharp.sum()), vertices=len(me.vertices))
# separate pieces by connectivity (loose parts) using a union-find over edges
parent = np.arange(len(me.vertices))
def find(a):
    while parent[a] != a:
        parent[a] = parent[parent[a]]
        a = parent[a]
    return a
for e in me.edges:
    a, b = find(e.vertices[0]), find(e.vertices[1])
    if a != b:
        parent[a] = b
roots = np.array([find(i) for i in range(len(me.vertices))])
pieces = np.unique(roots)
lengths = []
for r in pieces[:2000]:
    sel = co[roots == r]
    lengths.append(float(sel[:, 1].max() - sel[:, 1].min()))
lengths = np.array(lengths)
res['kerb']['loose_pieces'] = int(len(pieces))
res['kerb']['piece_length_y_m'] = dict(min=round(float(lengths.min()), 2), median=round(float(np.median(lengths)), 2), max=round(float(lengths.max()), 2))
# the pavement: faces and the size of its mesh quads
pav = bpy.data.objects['street_pavements'].data
areas = np.array([p.area for p in pav.polygons])
res['pavement'] = dict(faces=len(pav.polygons), median_face_area=round(float(np.median(areas)), 3), max_face_area=round(float(areas.max()), 3), has_flag_geometry=bool(len(pav.polygons) > 1000))
# setts / channels
for n in ('street_setts', 'street_channels'):
    me2 = bpy.data.objects[n].data
    a = np.array([p.area for p in me2.polygons])
    res[n] = dict(faces=len(me2.polygons), median_face_area=round(float(np.median(a)), 3), max_face_area=round(float(a.max()), 3))
json.dump(res, open(sys.argv[sys.argv.index('--') + 1], 'w'), indent=1)
