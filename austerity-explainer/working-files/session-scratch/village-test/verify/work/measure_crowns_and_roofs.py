# What this does: a fresh checker's second measure of a finished village (read only, never saved). For every small plant, litter piece and stone it asks:
#   1. does it stand under a tree crown (a crown object, role plant.foliage, straight above it), or within 0.3 m of the edge of a crown's shadow on the
#      ground (some points 0.3 m round it are under a crown and some are not) - a ring of weeds round each crown's outline is what the kit's "fence line"
#      site would make if it counts crowns as props;
#   2. does it stand inside a building (a roof above it and a building wall within 12 m in all four directions), or buried under an inside floor
#      (an object with a floor.* role just above it).
# Use: blender -b FILE.blend --python measure_crowns_and_roofs.py -- OUT.json
import base64
import json
import math
import sys

import bpy
import mathutils
import numpy as np
from mathutils.bvhtree import BVHTree

output_path = sys.argv[sys.argv.index('--') + 1]
scene = bpy.context.scene
depsgraph = bpy.context.evaluated_depsgraph_get()
BUILDING_OWNERS = {'cottages_north', 'cottages_south', 'stable'}


def role_of(obj):
    return str(obj.get('place_role') or '')


def bvh_of(objects):
    vertices, polygons, offset = [], [], 0
    for obj in objects:
        evaluated = obj.evaluated_get(depsgraph)
        mesh = evaluated.to_mesh()
        mesh.calc_loop_triangles()
        matrix = obj.matrix_world
        vertices.extend([tuple(matrix @ v.co) for v in mesh.vertices])
        polygons.extend([tuple(i + offset for i in t.vertices) for t in mesh.loop_triangles])
        offset += len(mesh.vertices)
        evaluated.to_mesh_clear()
    return BVHTree.FromPolygons(vertices, polygons) if polygons else None


objects = [o for o in scene.objects if o.type == 'MESH' and o.visible_get()]
crowns = bvh_of([o for o in objects if role_of(o) == 'plant.foliage'])
roofs = bvh_of([o for o in objects if role_of(o).startswith('roof.')])
floors = bvh_of([o for o in objects if role_of(o).startswith('floor.')])
walls = bvh_of([o for o in objects if o.get('place_owner') in BUILDING_OWNERS and role_of(o).startswith(('wall.', 'timber.', 'stone.'))])
UP = mathutils.Vector((0, 0, 1))
RING = [mathutils.Vector((0.3 * math.cos(a), 0.3 * math.sin(a), 0.0)) for a in np.linspace(0, 2 * math.pi, 8, endpoint=False)]
SIDES = [mathutils.Vector(v) for v in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0))]


def under(tree, point, reach=40.0):
    return tree is not None and tree.ray_cast(point, UP, reach)[0] is not None


result = {}
for obj in [o for o in scene.objects if o.type == 'MESH' and o.get('pk_scatter')]:
    block = bpy.data.texts.get('pk_roots_' + obj.name)
    if block is None:
        continue
    group = obj.get('pk_scatter_group')
    roots = np.frombuffer(base64.b64decode(block.as_string().encode('ascii')), dtype=np.float32).reshape(-1, 3)
    entry = result.setdefault(group, {'count': 0, 'under_crown': 0, 'at_crown_shadow_edge': 0, 'inside_building': 0, 'buried_under_floor': 0, 'under_roof_eaves_only': 0})
    for x, y, z in roots:
        point = mathutils.Vector((float(x), float(y), float(z) + 0.05))
        entry['count'] += 1
        here = under(crowns, point)
        ring = [under(crowns, point + offset) for offset in RING]
        if here:
            entry['under_crown'] += 1
        elif any(ring):
            entry['at_crown_shadow_edge'] += 1
        if floors is not None and floors.ray_cast(point, UP, 0.6)[0] is not None:
            entry['buried_under_floor'] += 1
        if under(roofs, point, 15.0):
            enclosed = walls is not None and all(walls.ray_cast(point + mathutils.Vector((0, 0, 0.3)), side, 12.0)[0] is not None for side in SIDES)
            if enclosed:
                entry['inside_building'] += 1
            else:
                entry['under_roof_eaves_only'] += 1
with open(output_path, 'w') as handle:
    json.dump(result, handle, indent=1)
print('MEASURED', output_path, json.dumps(result))
