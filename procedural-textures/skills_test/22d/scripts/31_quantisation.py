# What this does (plain words)
# --------------------------------------------------------------------------------------------------------------------------------------------
# Trial 22d, step 3b. The "web" preset squeezes the mesh data (meshopt). This measures what that does to the positions: it opens street_litter.blend with
# the litter realized, imports the web file back next to it, and for the road, the gutter stones and the litter mesh it measures how far every point moved
# (nearest original point, in millimetres). It also counts how much of the litter ends up lower than the re-imported road surface by more than 2 mm.
# Also lists the file's cameras/lights/extras facts and compares the node, mesh and picture counts with the film's own street.glb (read only).
# Run: xvfb-run -a blender -b --disable-autoexec --factory-startup set_copy/street_litter.blend -P scripts/31_quantisation.py -- OUT_FOLDER
import json
import os
import struct
import sys

sys.dont_write_bytecode = True
sys.path.append('/home/user/Music/.claude/skills/scenario-blender-geometry-nodes/scripts')
import bpy  # noqa: E402
import numpy as np  # noqa: E402
from mathutils import Vector  # noqa: E402
from mathutils.bvhtree import BVHTree  # noqa: E402
from mathutils.kdtree import KDTree  # noqa: E402

import bx_gn as G  # noqa: E402

OUT = sys.argv[sys.argv.index('--') + 1]
host = bpy.data.objects['gutter_litter']
G.set_inputs(host.modifiers['Gutter Litter'], {'Realize': True})
dg = bpy.context.evaluated_depsgraph_get()


def world_verts(obj, evaluated=True):
    if evaluated:
        eo = obj.evaluated_get(dg)
        me = eo.to_mesh()
        pts = np.array([tuple(obj.matrix_world @ v.co) for v in me.vertices])
        tris = [(p.vertices[0], p.vertices[1], p.vertices[2]) for p in me.polygons if len(p.vertices) == 3]
        eo.to_mesh_clear()
        return pts, tris
    me = obj.data
    return np.array([tuple(obj.matrix_world @ v.co) for v in me.vertices]), None


orig = {n: world_verts(bpy.data.objects[n])[0] for n in ('street_setts', 'street_channels', 'gutter_litter')}
before_names = set(bpy.data.objects.keys())
bpy.ops.import_scene.gltf(filepath=os.path.join(OUT, 'street_litter_web_realized.glb'))
new = {o.name: o for o in bpy.data.objects if o.name not in before_names}
res = {}
for n in ('street_setts', 'street_channels', 'gutter_litter'):
    cand = [o for k, o in new.items() if k.split('.')[0] == n and o.type == 'MESH']
    pts = world_verts(cand[0], evaluated=False)[0]
    kd = KDTree(len(orig[n]))
    for i, p in enumerate(orig[n]):
        kd.insert(Vector(p), i)
    kd.balance()
    d = np.array([kd.find(Vector(p))[2] for p in pts]) * 1000.0
    res[n] = {'points': len(pts), 'moved_mean_mm': round(float(d.mean()), 2), 'moved_median_mm': round(float(np.median(d)), 2), 'moved_p95_mm': round(float(np.percentile(d, 95)), 2), 'moved_max_mm': round(float(d.max()), 2)}
    if n == 'gutter_litter':
        lit_new = cand[0]
# how much of the litter now sits below the re-imported road/gutter surface (the gutter and the outer road band, as imported)?
surf = []
for n in ('street_setts', 'street_channels'):
    surf += [o for k, o in new.items() if k.split('.')[0] == n and o.type == 'MESH']
bm_pts, bm_tris, off = [], [], 0
for o in surf:
    p = np.array([tuple(o.matrix_world @ v.co) for v in o.data.vertices])
    me = o.data
    me.calc_loop_triangles()
    bm_pts += [Vector(x) for x in p]
    bm_tris += [tuple(off + i for i in t.vertices) for t in me.loop_triangles]
    off += len(p)
bvh = BVHTree.FromPolygons(bm_pts, bm_tris)
lit = np.array([tuple(lit_new.matrix_world @ v.co) for v in lit_new.data.vertices])
below = 0
depth = []
for p in lit:
    hit = bvh.ray_cast(Vector((p[0], p[1], p[2] + 1.0)), Vector((0, 0, -1)), 2.0)
    if hit[0] is not None:
        gap = p[2] - hit[0].z                 # negative = under the road surface
        depth.append(gap * 1000)
        if gap < -0.002:
            below += 1
depth = np.array(depth)
res['litter_vs_reimported_road'] = {'litter_points': len(lit), 'points_with_road_below': int(len(depth)), 'points_more_than_2mm_under_the_road': below,
                                    'share_under_percent': round(100 * below / max(1, len(depth)), 1), 'lowest_mm_vs_road': round(float(depth.min()), 1), 'median_mm_above_road': round(float(np.median(depth)), 1)}
# the same measurement BEFORE the export (original litter vs original road) to see what was already there
bvh0 = BVHTree.FromObject(bpy.data.objects['street_setts'], dg)
d0 = []
for p in orig['gutter_litter']:
    hit = bvh0.ray_cast(Vector((p[0], p[1], p[2] + 1.0)), Vector((0, 0, -1)), 2.0)
    if hit[0] is not None:
        d0.append((p[2] - hit[0].z) * 1000)
res['litter_vs_original_road_setts_only'] = {'points_checked': len(d0), 'lowest_mm': round(float(min(d0)), 1) if d0 else None}


def glb_json(p):
    d = open(p, 'rb').read()
    n, _k = struct.unpack_from('<I4s', d, 12)
    return json.loads(d[20:20 + n]), len(d)


facts = {}
for label, p in (('film_street_glb', '/home/user/Music/austerity-explainer/film-kit/assets/models/pit-village/street.glb'), ('web_realized_cams', os.path.join(OUT, 'street_litter_web_realized_cams.glb')),
                 ('web_realized', os.path.join(OUT, 'street_litter_web_realized.glb')), ('gltf_realized', os.path.join(OUT, 'street_litter_gltf_realized.glb'))):
    g, size = glb_json(p)
    bv = g['bufferViews']
    img_bytes = sum(bv[i['bufferView']]['byteLength'] for i in g.get('images', []) if 'bufferView' in i)
    facts[label] = {'file_mb': round(size / 1e6, 2), 'image_mb': round(img_bytes / 1e6, 2), 'mesh_and_other_mb': round((size - img_bytes) / 1e6, 2), 'nodes': len(g['nodes']), 'meshes': len(g['meshes']), 'materials': len(g['materials']),
                    'images': len(g.get('images', [])), 'cameras': len(g.get('cameras', [])), 'lights': len(g.get('extensions', {}).get('KHR_lights_punctual', {}).get('lights', [])),
                    'nodes_with_extras': sum(1 for n in g['nodes'] if n.get('extras')), 'extensions_required': g.get('extensionsRequired', []),
                    'texture_sizes_note': 'see image_mb'}
res['file_facts'] = facts
res['objects_with_custom_properties_in_blend'] = sum(1 for o in bpy.data.objects if any(k for k in o.keys() if not k.startswith('_') and k != 'cycles'))
with open(os.path.join(OUT, 'quantisation_and_facts.json'), 'w') as f:
    json.dump(res, f, indent=1)
print('RES', json.dumps(res))
