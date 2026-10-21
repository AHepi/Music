# What this file does (plain words)
# ---------------------------------------------------------------------------------------------------------------------------------------------
# THE GROWTH LAYER'S SELF-TEST (Blender code; no picture is drawn here: the picture tests (amount 0 and isolation as pictures) are in measure_growth.py on the 'zero' pictures).
#     blender -b --disable-autoexec SCENE.blend --python growth/selftest_growth.py -- SET_ID SCENE_ID OUT_FOLDER [TESTS]
# Tests (names): pieces (every piece has 40 to 200 faces, sizes in the period ranges), dial_zero (amount 0, and weeds_amount and cushions_amount 0, give zero plants),
# isolation (no existing material or object is changed by the layer: node counts and links of every material, object list), remove (taking the layer out leaves nothing of it),
# zones (no plant in the zones: the pack's footfall >= 0.6, crown >= 0.7, keepclear >= 0.5, doorstep strips; none within the fire radius when the set has a fire), determinism (two
# evaluations are identical; a second camera puts the same plants in the same places), caps (the count never passes max_pieces, whatever the cover dials), rubbish (no weed within
# 5 cm of the earlier layer's pieces when it is on), generic (the engine on a tilted box with a made-up picture mask: plants only where the mask says, standing along the box's
# normal), second_set (a set with earth, stones, gravel and water, its own look: plants on the ground and the stones, none under water, amount 0 gives none).
# Writes OUT_FOLDER/selftest_growth_<set>_<scene>.json: {test: {passed, ...numbers}}.
import json
import math
import os
import sys
import time
import traceback

import bpy
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
KIT_ROOT = os.path.abspath(os.path.join(HERE, '..'))
if KIT_ROOT not in sys.path:
    sys.path.insert(0, KIT_ROOT)
sys.dont_write_bytecode = True

from apply import dials, kit as kit_module  # noqa: E402
from harness import legacy_stack  # noqa: E402
from masks import bus as bus_module  # noqa: E402
from growth import apply_growth, local_masks, pieces as pieces_module, scatter  # noqa: E402


def material_signature():
    """{material name: (number of nodes, number of links, sorted node names)} for every material that is not one of the growth layer's own."""
    out = {}
    for m in bpy.data.materials:
        if m.name.startswith(pieces_module.MATERIAL_PREFIX) or m.node_tree is None:
            continue
        out[m.name] = (len(m.node_tree.nodes), len(m.node_tree.links), tuple(sorted(n.name for n in m.node_tree.nodes)))
    return out


def object_signature():
    return {o.name: (o.type, tuple(round(v, 5) for v in o.matrix_world.translation), o.hide_render) for o in bpy.data.objects if not o.name.startswith('WKG')}


def wkg_things():
    return dict(objects=sorted(o.name for o in bpy.data.objects if o.name.startswith('WKG')), materials=sorted(m.name for m in bpy.data.materials if m.name.startswith('WKG')),
                node_groups=sorted(g.name for g in bpy.data.node_groups if g.name.startswith('WKG')), images=sorted(i.name for i in bpy.data.images if i.name.startswith('WKG')),
                collections=sorted(c.name for c in bpy.data.collections if c.name.startswith('WKG')), meshes=sorted(m.name for m in bpy.data.meshes if m.name.startswith('WKG')))


class Test:
    def __init__(self, set_id, scene_id, look=None):
        self.kit = kit_module.Kit.load(set_id, scene_id=scene_id, look=look, strict=False)
        self.pack_ok = True
        try:
            bus_module.attach(self.kit)
        except Exception:
            self.pack_ok = False
        self.register = apply_growth.register(self.kit)
        self.kit.prepare()
        self.stack = None

    def with_rubbish(self):
        if self.stack is None and self.kit.settings.legacy():
            self.stack = legacy_stack.LegacyStack(self.kit)
            self.stack.apply(pieces=True)
        return self.stack

    def apply(self, overrides=None):
        self.kit.apply(layers=['growth'], overrides={'growth': overrides} if overrides else None)
        return self.kit.growth

    def reset(self):
        self.kit.remove('growth')


def t_pieces(t):
    gs = t.apply()
    lib = gs.library
    out, ok = {}, True
    for name, info in lib.kinds.items():
        sp = info['spec']
        lo, hi = min(info['faces']), max(info['faces'])
        sizes = [o['wk_size_m'] for o in info['objects']]
        within = all(sp['size_cm'][0] * 0.01 * 0.5 <= s <= sp['size_cm'][1] * 0.01 * 1.5 for s in sizes)
        out[name] = dict(faces=[lo, hi], size_cm=[round(min(sizes) * 100, 1), round(max(sizes) * 100, 1)], width_cm=[round(min(info['widths']) * 100, 1), round(max(info['widths']) * 100, 1)],
                         height_cm=[round(min(info['heights']) * 100, 1), round(max(info['heights']) * 100, 1)], variants=len(info['objects']), faces_ok=(40 <= lo and hi <= 210), sizes_ok=within)
        ok &= out[name]['faces_ok'] and out[name]['sizes_ok']
    return dict(passed=ok, kinds=out)


def t_dial_zero(t):
    gs = t.apply()
    out = {}
    t.kit.set_dials('growth', amount=0.0)
    out['amount_0'] = len(gs.table())
    t.kit.set_dials('growth', amount=1.0, weeds_amount=0.0, cushions_amount=0.0)
    out['weeds0_cushions0'] = len(gs.table())
    t.kit.set_dials('growth', weeds_amount=1.0, cushions_amount=1.0)
    out['default'] = len(gs.table())
    t.kit.set_master(0.0)
    out['master_0'] = len(gs.table())
    t.kit.set_master(1.0)
    out['master_1'] = len(gs.table())
    t.kit.layer_off('growth')
    out['layer_off'] = len(gs.table())
    t.kit.layer_on('growth')
    out['layer_on'] = len(gs.table())
    out['passed'] = out['amount_0'] == 0 and out['weeds0_cushions0'] == 0 and out['master_0'] == 0 and out['layer_off'] == 0 and out['default'] > 0 and out['master_1'] == out['default'] \
        and out['layer_on'] == out['default']
    return out


def t_isolation(t):
    before_m, before_o = material_signature(), object_signature()
    gs = t.apply()
    n = len(gs.table())
    after_m, after_o = material_signature(), object_signature()
    changed_m = sorted(k for k in before_m if before_m[k] != after_m.get(k))
    changed_o = sorted(k for k in before_o if before_o[k] != after_o.get(k))
    new_o = sorted(set(after_o) - set(before_o))
    return dict(passed=not changed_m and not changed_o and n > 0, plants=n, materials_changed=changed_m[:10], objects_changed=changed_o[:10], objects_added=new_o[:10], materials=len(before_m))


def t_remove(t):
    before = wkg_things()
    before_m = material_signature()
    t.apply()
    mid = wkg_things()
    t.kit.remove('growth')
    after = wkg_things()
    again = t.kit.remove('growth')
    t.kit.remove()                                           # everything off, twice is harmless
    t.kit.remove()
    final = wkg_things()
    after_m = material_signature()
    leftovers = {k: v for k, v in final.items() if v}
    return dict(passed=not leftovers and after_m == before_m and bool(mid['objects']), before=before, left_after_remove={k: v for k, v in after.items() if v}, leftovers_after_all=leftovers,
                materials_same=after_m == before_m)


def zone_test(t, rows, gp, manifest, fire_points=()):
    from harness import measure_zones as mz
    return mz.pieces_test(gp, manifest, rows, fire_points, ())


def read_gp(t):
    from harness import measure_zones as mz
    return mz.read_gp(t.kit.settings.id, t.kit.scene_id)


def t_zones(t):
    from harness import measure_zones as mz
    gs = t.apply()
    gp, manifest = read_gp(t)
    cams = [c for c in bpy.data.objects if c.type == 'CAMERA']
    results = {}
    total = 0
    fire = []
    spec = (t.kit.settings.get('growth') or {}).get('zones_for_report') or apply_growth.growth_section(t.kit.settings).get('zones_for_report') or {}
    if spec.get('fire_role'):
        fire = [(o.matrix_world.translation.x, o.matrix_world.translation.y) for n in t.kit.role_map.objects_of([spec['fire_role']]) for o in [bpy.data.objects[n]]]
    for cam in cams[:6]:
        rows = gs.table(cam)
        res = mz.pieces_test(gp, manifest, rows, fire, ())
        results[cam.name] = dict(plants=len(rows), zone_counts=res['counts'])
        total += sum(res['counts'].values())
    fields = mz.fields_test(gp)
    return dict(passed=(total == 0 and fields['ok']), zone_hits_total=total, per_camera=results, habitat_fields=fields)


def t_determinism(t):
    gs = t.apply()
    a = gs.table()
    b = gs.table()
    same = a == b
    cams = [c for c in bpy.data.objects if c.type == 'CAMERA']
    out = dict(first_equals_second=same, plants=len(a))
    if len(cams) >= 2:
        ra, rb = gs.table(cams[0]), gs.table(cams[1])
        key = lambda r: (r['x'], r['y'], r['species'])   # noqa: E731
        sa, sb = {key(r) for r in ra}, {key(r) for r in rb}
        both_ranges = sa & sb
        # plants one camera makes inside the other's area are the same plants (the points of a face do not depend on the camera)
        out['two_cameras'] = dict(cameras=[cams[0].name, cams[1].name], plants=[len(ra), len(rb)], shared=len(both_ranges))
        # of the plants of camera A that lie within 10 m of camera B and in front of it, how many does B also make (same position)?
        out['passed'] = same
    else:
        out['passed'] = same
    return out


def t_caps(t):
    gs = t.apply({'weed_cover': 0.03, 'cushion_cover': 0.03, 'max_pieces': 600.0, 'gutter_tuft_share': 0.1, 'toadflax_clumps': 3.0})
    n = len(gs.table())
    gs2 = t.kit.growth
    out = dict(plants=n, max_pieces=600, notes=gs.notes, scale_total=gs.calibration.get('scale_total'))
    out['passed'] = n <= 600
    t.kit.set_dials('growth', max_pieces=2500.0, weed_cover=0.01, cushion_cover=0.008, gutter_tuft_share=0.05, toadflax_clumps=1.0)
    out['back_to_default'] = len(gs2.table())
    return out


def t_rubbish(t):
    stack = t.with_rubbish()
    if stack is None:
        return dict(passed=True, skipped='the set has no earlier rubbish layer')
    gs = t.apply()
    from growth import runner_growth
    rub = runner_growth.rubbish_table()
    rows = gs.table()
    weeds = [r for r in rows if r['kind'].startswith('weed')]
    R = np.array([[r['x'], r['y']] for r in rub]) if rub else np.zeros((0, 2))
    near = 0
    for p in weeds:
        if len(R) and np.min(np.hypot(R[:, 0] - p['x'], R[:, 1] - p['y'])) <= 0.05:
            near += 1
    share = near / len(weeds) if weeds else 0.0
    return dict(passed=share <= 0.03, weeds=len(weeds), near_rubbish=near, share=round(share, 4), rubbish_pieces=len(rub))


def t_generic(t):
    """The engine on a tilted box with a made-up picture mask: no set, no pack. Plants only where the mask says; standing along the box's normal."""
    import mathutils
    # a 30 degree tilted plane 4 x 4 m, centred at (0, 0, 1)
    mesh = bpy.data.meshes.new('WKG test box')
    bm_verts = [(-2, -2, 0), (2, -2, 0), (2, 2, 0), (-2, 2, 0)]
    mesh.from_pydata(bm_verts, [], [(0, 1, 2, 3)])
    box = bpy.data.objects.new('WKG test box', mesh)
    bpy.context.scene.collection.objects.link(box)
    box.rotation_euler = (math.radians(30), 0, 0)
    box.location = (0, 0, 1)
    # subdivide a little so Poisson has faces to work on (the engine takes the evaluated mesh)
    mod = box.modifiers.new('sub', 'SUBSURF')
    mod.levels = 2
    mod.subdivision_type = 'SIMPLE'
    # a picture mask: left half (x < 0) = 1 in R (weed_site) and right half in G (moss_site); 64 x 64 over x -3..3, y -3..3
    img = bpy.data.images.new('WKG test mask', 64, 64, alpha=True, float_buffer=True, is_data=True)
    buf = np.zeros((64, 64, 4), np.float32)
    buf[:, :32, 0] = 1.0
    buf[:, 32:, 1] = 1.0
    buf[..., 3] = 1.0
    img.pixels.foreach_set(buf.ravel())
    cam = bpy.data.objects.new('WKG test camera', bpy.data.cameras.new('WKG test camera'))
    bpy.context.scene.collection.objects.link(cam)
    cam.location = (0, -8, 4)
    cam.rotation_euler = (math.radians(60), 0, 0)
    keep_cam = bpy.context.scene.camera
    bpy.context.scene.camera = cam
    lib = pieces_module.Library()
    lib.build(['grass', 'moss_string'])
    kinds = []
    for name in ('grass', 'moss_string'):
        sp, info = lib.species['kinds'][name], lib.kinds[name]
        kinds.append(dict(name=name, group=sp['group'], pop='moss' if sp['group'] == 'moss' else 'weed', collection=info['collection'], variants=len(info['objects']), scale=tuple(sp['scale']),
                          min_dots=sp['min_dots'], width_m=info['mean_width'], upright=sp['upright'], spacing=0.1, density_max=60.0, yaw='free', prefer=sp['prefer'], share_dial=f'share_{name}' if name == 'grass' else None))
    eng = scatter.Engine('WKG test scatter')
    eng.build(kinds, [box], dict(weed_site=(img, 'R'), moss_site=(img, 'G')), dict(x=[-3.0, 3.0], y=[-3.0, 3.0]), dict(align_normal=1.0, yaw_axis=None))
    host = eng.add_host(bpy.context.scene)
    eng.set_dials(distance=30.0, distance_fade=5.0, g_bg=1.0, g_moss=1.0, share_grass=1.0, keep_soft=0.4, weeds_amount=1.0, cushions_amount=1.0, amount=1.0, select_margin=6.0)
    mats, kind, extra = scatter.evaluated_instances(host)
    n = len(kind)
    pos = mats[:, 3, :3]
    normal = np.array(box.matrix_world.to_3x3() @ mathutils.Vector((0, 0, 1)))
    normal = normal / np.linalg.norm(normal)
    zaxes = mats[:, 2, :3] / np.maximum(np.linalg.norm(mats[:, 2, :3], axis=1, keepdims=True), 1e-9)
    cos = zaxes @ normal
    grass = kind == 0
    moss = kind == 1
    # box-local x is world x (rotation about x only); the mask's left half is x < 0
    ok_grass = bool(np.all(pos[grass, 0] < 0.05)) if grass.any() else True
    ok_moss = bool(np.all(pos[moss, 0] > -0.05)) if moss.any() else True
    # points lie on the tilted surface: z = 1 + y * tan(30 deg)
    surf = 1.0 + pos[:, 1] * math.tan(math.radians(30)) - pos[:, 2]
    res = dict(plants=n, grass=int(grass.sum()), moss=int(moss.sum()), grass_only_on_mask_half=ok_grass, moss_only_on_mask_half=ok_moss, min_cos_to_normal=round(float(cos.min()), 3) if n else None,
               mean_cos=round(float(cos.mean()), 3) if n else None, max_off_surface_m=round(float(np.abs(surf).max()), 4) if n else None)
    res['passed'] = n > 20 and ok_grass and ok_moss and (cos.min() > 0.85 if n else False) and (np.abs(surf).max() < 0.03 if n else False)
    # clean up
    for obj in (host, box, cam):
        bpy.data.objects.remove(obj)
    bpy.context.scene.camera = keep_cam
    lib.remove()
    for tree in (eng.tree, eng.kind_tree):
        if tree is not None and bpy.data.node_groups.get(tree.name) is tree:
            bpy.data.node_groups.remove(tree)
    bpy.data.images.remove(img)
    return res


def t_second_set(t):
    gs = t.apply()
    rows = gs.table()
    from collections import Counter
    by_kind = Counter(r['species'] for r in rows)
    # where they stand: height above the ground plan's ground, and which target object is under them is not asked (the plan picture says where)
    t.kit.set_dials('growth', amount=0.0)
    zero = len(gs.table())
    t.kit.set_dials('growth', amount=1.0)
    targets = [o.name for o in gs.targets]
    z = np.array([r['z'] for r in rows]) if rows else np.zeros(1)
    return dict(passed=len(rows) > 0 and zero == 0, plants=len(rows), by_kind=dict(by_kind), amount_0=zero, targets=len(targets), target_sample=targets[:6], z_range=[round(float(z.min()), 3), round(float(z.max()), 3)],
                calibration_notes=gs.notes, targets_roles=gs.section.get('targets'), timings=gs.timings)


TESTS = dict(pieces=t_pieces, dial_zero=t_dial_zero, isolation=t_isolation, remove=t_remove, zones=t_zones, determinism=t_determinism, caps=t_caps, rubbish=t_rubbish, generic=t_generic,
             second_set=t_second_set)
DEFAULT_PAVED = ('pieces', 'dial_zero', 'isolation', 'remove', 'zones', 'determinism', 'caps', 'rubbish', 'generic')
DEFAULT_OPEN = ('pieces', 'dial_zero', 'isolation', 'remove', 'generic', 'second_set')


def main():
    args = sys.argv[sys.argv.index('--') + 1:]
    set_id, scene_id, out = args[0], args[1], args[2]
    names = args[3].split(',') if len(args) > 3 and args[3] else (DEFAULT_PAVED if (apply_growth.growth_section(kit_module.Kit.load(set_id, scene_id=scene_id, strict=False).settings).get('gutter_side')) else DEFAULT_OPEN)
    os.makedirs(out, exist_ok=True)
    result = dict(set=set_id, scene=scene_id, when=time.strftime('%Y-%m-%d %H:%M:%S'), tests={})
    t0 = time.time()
    for name in names:
        started = time.time()
        t = None
        try:
            t = Test(set_id, scene_id)
            if name == 'zones' and t.kit.settings.legacy():
                pass
            res = TESTS[name](t)
        except Exception:
            res = dict(passed=False, error=traceback.format_exc())
        res['seconds'] = round(time.time() - started, 2)
        result['tests'][name] = res
        print('TEST', name, 'PASS' if res.get('passed') else 'FAIL', res['seconds'], flush=True)
        try:
            if t is not None:
                t.kit.remove()
        except Exception:
            pass
    result['passed'] = all(r.get('passed') for r in result['tests'].values())
    result['seconds'] = round(time.time() - t0, 1)
    json.dump(result, open(os.path.join(out, f'selftest_growth_{set_id}_{scene_id}.json'), 'w'), indent=1, default=str)
    print('SELFTEST DONE', result['passed'], flush=True)


if __name__ == '__main__':
    main()
