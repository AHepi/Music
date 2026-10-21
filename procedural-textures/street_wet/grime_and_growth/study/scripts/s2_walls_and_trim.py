# What this does (plain words): opens the street copy and ONLY LISTS how the cottage walls, trims, pipes, roofs and ground are built: shared meshes, object turns, local size,
# texture-coordinate ranges, and what the trim and pipe pieces are made of (by material and by which way their faces point). Saves nothing.
# Run: blender -b --disable-autoexec street.blend --python s2_walls_and_trim.py -- OUT.json
import json
import math
import re
import sys
from collections import defaultdict

import bpy
import numpy as np

out_path = sys.argv[sys.argv.index('--') + 1]
scene = bpy.context.scene
res = {}


def mesh_info(obj):
    me = obj.data
    co = np.empty(len(me.vertices) * 3)
    me.vertices.foreach_get('co', co)
    co = co.reshape(-1, 3)
    uv = None
    if me.uv_layers:
        arr = np.empty(len(me.uv_layers[0].data) * 2)
        me.uv_layers[0].data.foreach_get('uv', arr)
        arr = arr.reshape(-1, 2)
        uv = [round(float(arr[:, 0].min()), 2), round(float(arr[:, 0].max()), 2), round(float(arr[:, 1].min()), 2), round(float(arr[:, 1].max()), 2)]
    return dict(verts=len(me.vertices), faces=len(me.polygons), local_min=[round(float(v), 3) for v in co.min(0)], local_max=[round(float(v), 3) for v in co.max(0)], uv_range=uv,
                materials=[m.name if m else None for m in me.materials], uv_layers=[u.name for u in me.uv_layers],
                color_attributes=[a.name for a in me.color_attributes], attributes=[a.name for a in me.attributes if not a.name.startswith('.')][:12])


# ---- walls: shared meshes and turns
walls = [o for o in scene.objects if o.type == 'MESH' and re.search(r'_walls$', o.name) and 'cottage' in o.name]
by_mesh = defaultdict(list)
for o in walls:
    by_mesh[o.data.name].append(o)
res['wall_meshes'] = {}
for mesh_name, objs in by_mesh.items():
    first = objs[0]
    entry = mesh_info(first)
    entry['users'] = len(objs)
    entry['objects'] = [(o.name, [round(v, 2) for v in o.location], round(math.degrees(o.rotation_euler.z), 1), [round(v, 3) for v in o.scale]) for o in objs[:3]]
    entry['rotations_deg'] = sorted({round(math.degrees(o.rotation_euler.z), 1) for o in objs})
    res['wall_meshes'][mesh_name] = entry

# the faces of ONE wall mesh: where they are, which way they point, area, material index
o = walls[0]
me = o.data
faces = []
for p in me.polygons:
    c = p.center
    n = p.normal
    faces.append(dict(centre=[round(c.x, 2), round(c.y, 2), round(c.z, 2)], normal=[round(n.x, 2), round(n.y, 2), round(n.z, 2)], area=round(p.area, 2), mat=p.material_index, verts=len(p.vertices)))
res['wall_faces_first'] = {'object': o.name, 'faces': faces}

# ---- trims, rainwater, roofs, chimneys, doors: per material, per direction, per object kind: area and height range of up-facing ledges
def composition(pattern):
    out = {}
    objs = [o for o in scene.objects if o.type == 'MESH' and re.search(pattern, o.name)]
    if not objs:
        return out
    o = objs[0]
    me = o.data
    mw = np.array(o.matrix_world)
    by_mat = defaultdict(lambda: dict(faces=0, area=0.0, up=0.0, down=0.0, side=0.0, zmin=1e9, zmax=-1e9, xmin=1e9, xmax=-1e9))
    for p in me.polygons:
        m = me.materials[p.material_index].name if me.materials[p.material_index] else None
        d = by_mat[m]
        n = np.array(p.normal) @ mw[:3, :3].T
        n = n / max(np.linalg.norm(n), 1e-9)
        d['faces'] += 1
        d['area'] += p.area
        if n[2] > 0.9:
            d['up'] += p.area
        elif n[2] < -0.5:
            d['down'] += p.area
        else:
            d['side'] += p.area
        for v in p.vertices:
            w = mw @ np.append(np.array(me.vertices[v].co), 1.0)
            d['zmin'], d['zmax'] = min(d['zmin'], w[2]), max(d['zmax'], w[2])
            d['xmin'], d['xmax'] = min(d['xmin'], w[0]), max(d['xmax'], w[0])
    out['object'] = o.name
    out['info'] = mesh_info(o)
    out['materials'] = {k: {kk: round(float(vv), 3) for kk, vv in v.items()} for k, v in by_mat.items()}
    return out


res['trim_right_01'] = composition(r'^right_row_a_cottage_01_trim$')
res['rain_right_01'] = composition(r'^right_row_a_cottage_01_rainwater$')
res['roof_right_01'] = composition(r'^right_row_a_cottage_01_roof$')
res['door_right_01'] = composition(r'^right_row_a_cottage_01_door$')
res['window_right_01'] = composition(r'^right_row_a_cottage_01_window_ground$')
res['chimney_right_01'] = composition(r'^right_row_a_cottage_01_chimney$')
res['lamp_post_0'] = composition(r'^gas_lamp_0_post$')

# ---- ground objects
for name in ('street_setts', 'street_channels', 'street_kerbs', 'street_pavements', 'ground'):
    obj = bpy.data.objects[name]
    res[name] = mesh_info(obj)
    res[name]['matrix_world_is_identity'] = bool(np.allclose(np.array(obj.matrix_world), np.eye(4)))
    res[name]['object_scale'] = [round(v, 3) for v in obj.scale]

# ---- material custom properties (tile_metres) and which materials carry them
res['tile_metres'] = {m.name: m.get('tile_metres') for m in bpy.data.materials if m.get('tile_metres') is not None}

# ---- doorway empties
door_empties = [(o.name, [round(v, 2) for v in o.matrix_world.translation]) for o in scene.objects if o.type == 'EMPTY' and o.name.endswith('_doorway')][:4]
res['doorway_empties_sample'] = door_empties
res['empty_kinds'] = sorted({re.sub(r'\d+', 'N', o.name) for o in scene.objects if o.type == 'EMPTY'})
# ---- custom properties on objects (set builder tags?)
tags = defaultdict(set)
for o in scene.objects:
    for k in o.keys():
        if not k.startswith('_'):
            tags[k].add(o.name)
res['object_custom_props'] = {k: sorted(v)[:4] for k, v in tags.items()}
json.dump(res, open(out_path, 'w'), indent=1, default=str)
print('DONE walls', len(walls), 'wall meshes', len(by_mesh))
