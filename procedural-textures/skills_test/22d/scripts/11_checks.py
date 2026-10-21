# What this does (plain words)
# --------------------------------------------------------------------------------------------------------------------------------------------
# Trial 22d, step 2. Opens street_litter.blend (made by 10_build_litter.py) and runs the geometry-nodes skill's own checks on the "Gutter Litter" tree:
#   count against the sum "density x area x mask", the same on several seeds, how the pieces split into paper / leaves / bottles / the 10 shapes,
#   whether every piece sits on the surface and lies along its normal, the "turn it" and "flip it" test, the "double the mesh detail" test,
#   how long one re-evaluation takes, how much of the litter lies near the kerb compared with the host area near the kerb,
#   and the skill's OWN ready-made recipe (G.scatter_tree) on a copy of the same host, for comparison.
# It also draws a Workbench contact sheet of a 8 m slice of gutter with the skill's G.snapshot. It saves nothing back into the street files.
# Run: xvfb-run -a blender -b --disable-autoexec --factory-startup --python-exit-code 1 set_copy/street_litter.blend -P scripts/11_checks.py -- OUT_FOLDER
import json
import math
import os
import random
import sys

sys.dont_write_bytecode = True
sys.path.append('/home/user/Music/.claude/skills/scenario-blender-geometry-nodes/scripts')
import bmesh  # noqa: E402
import bpy  # noqa: E402
import numpy as np  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402
from mathutils.bvhtree import BVHTree  # noqa: E402

import bx_gn as G  # noqa: E402

OUT = sys.argv[sys.argv.index('--') + 1]
os.makedirs(OUT, exist_ok=True)
scene = bpy.context.scene
host = bpy.data.objects['gutter_litter']
kerbs = bpy.data.objects['street_kerbs']
md = host.modifiers['Gutter Litter']
res = {}

# ---- host numbers
dg = bpy.context.evaluated_depsgraph_get()
me = host.data
up = Vector((0, 0, 1))
eligible_area = sum(p.area for p in me.polygons if p.normal.angle(up) <= math.radians(35.0))
total_area = sum(p.area for p in me.polygons)
res['host'] = {'faces': len(me.polygons), 'area_m2': round(total_area, 2), 'eligible_area_m2_slope_le_35deg': round(eligible_area, 2)}
inputs = G.get_inputs(md)
res['inputs'] = {k: (v if not isinstance(v, tuple) else list(v)) for k, v in inputs.items()}
print('INPUTS', res['inputs'])


def counts():
    n_inst = len(G.instance_transforms(host))
    if n_inst == 0:
        return 0, [0, 0, 0]          # a flipped host has no eligible faces: the evaluated result holds no instances at all
    kinds = G.attribute(host, 'litter_kind', 'instances')[0]
    return n_inst, [int((kinds == k).sum()) for k in range(3)]


def with_inputs(values, fn):
    old = {k: inputs[k] for k in values}
    G.set_inputs(md, values)
    try:
        return fn()
    finally:
        G.set_inputs(md, old)


# ---- (a) plain count: mask 1 everywhere, Count = density x eligible area, five seeds
# bottles are rare at the shipped density (about 17 in the whole street), too few for a count test: the test runs at 1.2 per square metre
plain = {'Kerb Pull': 0.0, 'Clumping': 0.0, 'Bottle Density': 1.2}
exp = {'paper': 1.2 * eligible_area, 'leaves': 3.0 * eligible_area, 'bottles': 1.2 * eligible_area}
rows = []
for sd in (1, 2, 3, 4, 5):
    n, kinds = with_inputs(dict(plain, Seed=sd), counts)
    rows.append(kinds)
mean = np.mean(rows, axis=0)
res['count_plain_mask1'] = {'expected': [round(exp['paper'], 1), round(exp['leaves'], 1), round(exp['bottles'], 1)], 'mean_of_5_seeds': [round(float(x), 1) for x in mean],
                            'per_seed': rows, 'percent_off': [round(100 * (float(m) - e) / e, 1) for m, e in zip(mean, exp.values())]}
print('PLAIN', res['count_plain_mask1'])

# ---- (b) kerb pull only: expected = density x area x mean(mask) with the mask worked out by hand (BVH nearest distance to the kerb mesh)
kb = bmesh.new()
kb.from_mesh(kerbs.data)
kb.transform(kerbs.matrix_world)
kbvh = BVHTree.FromBMesh(kb)
rng = random.Random(5)
polys = [p for p in me.polygons if p.normal.angle(up) <= math.radians(35.0)]
areas = np.array([p.area for p in polys])
cum = np.cumsum(areas) / areas.sum()
masks = []
reach, pull = inputs['Kerb Reach'], 0.75
for _ in range(20000):
    p = polys[int(np.searchsorted(cum, rng.random()))]
    vs = [me.vertices[i].co for i in p.vertices]
    # random point inside the (planar quad or triangle) face: a random triangle of its fan, then barycentric
    t = rng.randrange(len(vs) - 2)
    a, b2, c = vs[0], vs[t + 1], vs[t + 2]
    r1, r2 = rng.random(), rng.random()
    if r1 + r2 > 1:
        r1, r2 = 1 - r1, 1 - r2
    q = a + (b2 - a) * r1 + (c - a) * r2
    loc, nrm, idx, dist = kbvh.find_nearest(q)
    near = min(max(1.0 - dist / reach, 0.0), 1.0)
    masks.append(1.0 - pull + pull * near)
mean_mask = float(np.mean(masks))
rows = []
for sd in (1, 2, 3, 4, 5):
    n, kinds = with_inputs({'Kerb Pull': pull, 'Clumping': 0.0, 'Seed': sd, 'Bottle Density': 1.2}, counts)
    rows.append(kinds)
mean = np.mean(rows, axis=0)
expk = [1.2 * eligible_area * mean_mask, 3.0 * eligible_area * mean_mask, 1.2 * eligible_area * mean_mask]
res['count_kerb_pull_only'] = {'mean_mask_by_hand': round(mean_mask, 3), 'expected': [round(e, 1) for e in expk], 'mean_of_5_seeds': [round(float(x), 1) for x in mean],
                               'percent_off': [round(100 * (float(m) - e) / e, 1) for m, e in zip(mean, expk)]}
print('KERB', res['count_kerb_pull_only'])

# ---- (c) the shipped settings: counts, shapes used, placement on the surface
n, kinds = counts()
res['count_shipped_settings'] = {'instances': n, 'paper': kinds[0], 'leaves': kinds[1], 'bottles': kinds[2]}
st = G.stats(host)
res['stats'] = {'instances': st['instances']['count'], 'references': st['instances']['references'], 'mesh_faces_out': st.get('mesh', {}).get('faces', 0), 'bbox': st['bbox']}
gs = G.evaluated(host).evaluated_geometry()
ipc = gs.instances_pointcloud()
ridx = G._read(ipc.attributes['.reference_index']) if '.reference_index' in ipc.attributes else None
if ridx is not None:
    res['reference_index_use'] = {int(k): int((ridx == k).sum()) for k in np.unique(ridx)}
refs = list(gs.instance_references())
res['reference_count'] = len(refs)
hb = bmesh.new()
hb.from_mesh(host.data)
hb.transform(host.matrix_world)
hbvh = BVHTree.FromBMesh(hb)   # the host's own mesh: the evaluated one holds only the litter (Keep Surface is off)
mats = G.instance_transforms(host, world=True)
gap, tilt = [], []
for m in mats:
    loc = m.translation
    hit, nrm, idx, dist = hbvh.find_nearest(loc)
    gap.append(dist)
    zaxis = (m.to_3x3() @ Vector((0, 0, 1))).normalized()
    tilt.append(math.degrees(zaxis.angle(nrm)))
res['placement'] = {'instances': len(mats), 'max_distance_origin_to_surface_m': round(max(gap), 6), 'max_tilt_vs_surface_normal_deg': round(max(tilt), 3),
                    'scale_range': [round(min(m.to_scale().x for m in mats), 3), round(max(m.to_scale().x for m in mats), 3)]}
print('PLACEMENT', res['placement'])

# ---- near-kerb share: litter vs host area
kdist = []
for m in mats:
    loc, nrm, idx, d = kbvh.find_nearest(m.translation)
    kdist.append(d)
kdist = np.array(kdist)
near_area = 0.0
for p in me.polygons:
    loc, nrm, idx, d = kbvh.find_nearest(Vector(p.center))
    if d < inputs['Kerb Reach']:
        near_area += p.area
res['kerb_share'] = {'litter_within_reach_percent': round(100 * float((kdist < inputs['Kerb Reach']).mean()), 1), 'host_area_within_reach_percent': round(100 * near_area / total_area, 1)}
print('KERBSHARE', res['kerb_share'])

# ---- turn / flip / double-detail probes (kerb pull and clumping off, so only the world-up rule can change the count)
base_n = with_inputs(plain, lambda: counts()[0])
saved_rot = tuple(host.rotation_euler)


def rot_probe(euler):
    host.rotation_euler = euler
    bpy.context.view_layer.update()
    host.update_tag()
    try:
        return with_inputs(plain, lambda: counts()[0])
    finally:
        host.rotation_euler = saved_rot
        bpy.context.view_layer.update()
        host.update_tag()


res['probes'] = {'base_count_mask1': base_n, 'turned_90_about_z': rot_probe((0, 0, math.pi / 2)), 'flipped_180_about_x': rot_probe((math.pi, 0, 0)), 'tilted_25_about_x': rot_probe((math.radians(25), 0, 0)), 'tilted_40_about_x': rot_probe((math.radians(40), 0, 0))}
# double the mesh detail: a copy of the host cut once more (bmesh subdivide), same tree
dup = host.copy()
dup.data = host.data.copy()
dup.name = 'probe_double'
host.users_collection[0].objects.link(dup)
bm = bmesh.new()
bm.from_mesh(dup.data)
bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=1, use_grid_fill=True)
bm.to_mesh(dup.data)
bm.free()
dmd = dup.modifiers['Gutter Litter']
G.set_inputs(dmd, dict(plain))
dbl, base5 = [], []
for sd in (1, 2, 3, 4, 5):
    G.set_inputs(dmd, {'Seed': sd})
    dbl.append(len(G.instance_transforms(dup)))
    base5.append(with_inputs(dict(plain, Seed=sd), lambda: counts()[0]))
res['probes']['double_detail_host_faces'] = len(dup.data.polygons)
res['probes']['double_detail_mean_count_5_seeds'] = round(float(np.mean(dbl)), 1)
res['probes']['normal_detail_mean_count_5_seeds'] = round(float(np.mean(base5)), 1)
res['probes']['double_detail_percent_vs_normal'] = round(100 * (float(np.mean(dbl)) - float(np.mean(base5))) / float(np.mean(base5)), 1)
bpy.data.objects.remove(dup)
print('PROBES', res['probes'])

# ---- how many pieces each camera sees and how big they come out (540 x 960), shipped settings and the heavier 'messy' settings
from bpy_extras.object_utils import world_to_camera_view  # noqa: E402
cams = {'film_main_camera': bpy.data.objects['main_camera']}
scene.render.resolution_x, scene.render.resolution_y, scene.render.resolution_percentage = 540, 960, 100
lock = bpy.data.objects.new('lockout_cam_probe', bpy.data.cameras.new('lockout_cam_probe'))
scene.collection.objects.link(lock)
lock.location = (-1.0, 1.2, 1.69709)
lock.rotation_mode = 'QUATERNION'
lock.rotation_quaternion = (0.65516, 0.753675, -0.039498, -0.034335)
lock.data.sensor_fit = 'VERTICAL'
lock.data.angle_y = math.radians(44.0)
cams['lockout_camera'] = lock
res['camera_view'] = {}
for label, vals in (('shipped', {}), ('messy', {'Paper Density': 3.5, 'Leaf Density': 9.0, 'Bottle Density': 0.5, 'Clumping': 0.5, 'Seed': 11})):
    def look():
        out = {}
        ms = G.instance_transforms(host, world=True)
        kinds = G.attribute(host, 'litter_kind', 'instances')[0]
        for cname, cam in cams.items():
            scene.camera = cam
            bpy.context.view_layer.update()
            seen, sizes = 0, []
            for m, kd in zip(ms, kinds):
                co = world_to_camera_view(scene, cam, m.translation)
                if 0 <= co.x <= 1 and 0 <= co.y <= 1 and co.z > 0:
                    seen += 1
                    # on-screen size of a 10 cm piece at that distance, in pixels of a 960-pixel-tall frame
                    dist = (m.translation - cam.matrix_world.translation).length
                    fov = cam.data.angle_y if cam.data.sensor_fit == 'VERTICAL' else 2 * math.atan(math.tan(cam.data.angle / 2) / (540 / 960))
                    sizes.append(0.10 / dist / (2 * math.tan(fov / 2)) * 960)
            out[cname] = {'pieces_in_frame': seen, 'of': len(ms), 'size_of_a_10cm_piece_px_median': round(float(np.median(sizes)), 1) if sizes else None,
                          'pieces_bigger_than_8px': int(sum(1 for z in sizes if z >= 8))}
        return out
    res['camera_view'][label] = with_inputs(vals, look) if vals else look()
scene.camera = bpy.data.objects['main_camera']
bpy.data.objects.remove(lock)
print('CAMERAVIEW', json.dumps(res['camera_view']))

# ---- timing
res['time_to_evaluate_seconds'] = round(G.time_eval(host), 4)
print('TIME', res['time_to_evaluate_seconds'])

# ---- the skill's own ready-made recipe on a copy of the same host, same mask-free rules
rec_host = host.copy()
rec_host.data = host.data.copy()
rec_host.name = 'probe_recipe'
host.users_collection[0].objects.link(rec_host)
rec_host.modifiers.clear()
tree2 = G.scatter_tree()
rmd = G.attach(rec_host, tree2, inputs={'Instance': bpy.data.objects['litter_bottle_brown'], 'Instances': bpy.data.collections['litter_leaves'], 'Density': 12.0, 'Seed': 3})
rrep = G.check(rmd)
rst = G.stats(rec_host)
ex = 12.0 * eligible_area
res['skill_recipe_scatter_tree'] = {'check_ok': rrep['ok'], 'instances': rst['instances']['count'], 'expected_density12_x_eligible_area': round(ex, 1),
                                    'percent_off': round(100 * (rst['instances']['count'] - ex) / ex, 1), 'surface_faces_also_in_output': rst.get('mesh', {}).get('faces', 0),
                                    'time_s': round(G.time_eval(rec_host), 4)}
print('RECIPE', res['skill_recipe_scatter_tree'])
bpy.data.objects.remove(rec_host)

# ---- a Workbench contact sheet of an 8 m slice, with the skill's snapshot (surface kept so shadows show contact)
bm = bmesh.new()
bm.from_mesh(host.data)
drop = [f for f in bm.faces if not (8.0 <= f.calc_center_median().y <= 16.0 and f.calc_center_median().x > 0)]
bmesh.ops.delete(bm, geom=drop, context='FACES')
sl_me = bpy.data.meshes.new('slice')
bm.to_mesh(sl_me)
bm.free()
sl = bpy.data.objects.new('slice', sl_me)
host.users_collection[0].objects.link(sl)
smd = G.attach(sl, md.node_group, name='slice', inputs={'Kerb': kerbs, 'Seed': 7, 'Keep Surface': True, 'Paper': bpy.data.collections['litter_paper'],
                                                         'Leaves': bpy.data.collections['litter_leaves'], 'Bottles': bpy.data.collections['litter_bottles'],
                                                         'Paper Density': 3.0, 'Leaf Density': 6.0, 'Bottle Density': 0.4})
res['slice'] = {'faces': len(sl_me.polygons), 'instances': len(G.instance_transforms(sl)), 'check_ok': G.check(smd)['ok']}
sheet = G.snapshot([sl], os.path.join(OUT, 'slice_sheet.png'), views=('top', 'threequarter'), res=700)
print('SNAPSHOT', sheet, res['slice'])
bpy.data.objects.remove(sl)

with open(os.path.join(OUT, 'litter_numbers.json'), 'w') as f:
    json.dump(res, f, indent=1)
print('DONE')
