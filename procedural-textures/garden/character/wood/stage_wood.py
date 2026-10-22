"""stage_wood.py - the WOOD builder of the Japanese garden character round (22 October).
apply(options) works on the open starting scene (garden_real_fixed.blend), touches only what the wood builder owns, is idempotent
(it first removes what it created earlier, found by garden_owner == 'wood' and wood_new == 1, and restores the original meshes it replaced),
and prints a report of objects created / changed / deleted.

options (all optional): bridge, deck, frame, bars, cameras (bools, default True), seed (int), maps_dir, moss (dict of shader thresholds).
"""
import os
import sys
import json
import math
import time
import numpy as np
import bpy
import bmesh
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import wood_geo as wg
import wood_bridge as wb
import wood_mats as wmat

OWNER = 'wood'
COLL = 'G6 wood'
LAST_CTX = None
ORIG_PREFIX = 'G6 wood / orig '

OWN_OBJECTS = (["Astra / varied planks"] + ["Astra / varied planks.%03d" % i for i in range(1, 8)] + ["Bridge pier %d" % i for i in range(4)] +
               ["Bridge stringers", "Veranda step", "Veranda step, lower", "Hall posts", "Hall beams", "Eave soffit", "Roof carrying frame",
                "Gravel timber edge", "Shoji bars", "Stone plinth"])
OWN_MATS_EXISTING = (["Dark timber", "Beam timber", "GARDEN timber.post", "Plinth stone"] +
                     ["CT / Stone painterly surface.%s" % s for s in ("008", "009", "039", "040", "041", "042")])


# ------------------------------------------------------------------ helpers
def log(*a):
    print('[stage_wood]', *a, flush=True)


def get_collection():
    c = bpy.data.collections.get(COLL)
    if c is None:
        c = bpy.data.collections.new(COLL)
        bpy.context.scene.collection.children.link(c)
    c['garden_owner'] = OWNER
    return c


def cleanup(report):
    """remove everything this stage created earlier; restore replaced meshes of existing objects"""
    removed = 0
    for o in list(bpy.data.objects):
        if o.get('garden_owner') == OWNER and o.get('wood_new'):
            data = o.data
            bpy.data.objects.remove(o, do_unlink=True)
            if data is not None and getattr(data, 'users', 1) == 0:
                if isinstance(data, bpy.types.Mesh):
                    bpy.data.meshes.remove(data)
                elif isinstance(data, bpy.types.Camera):
                    bpy.data.cameras.remove(data)
            removed += 1
    for m in list(bpy.data.materials):
        if m.name.startswith('G6 wood / ') and m.get('garden_owner') == OWNER:
            bpy.data.materials.remove(m)
    for me in list(bpy.data.meshes):
        if me.name.startswith('G6 wood / ') and not me.name.startswith(ORIG_PREFIX) and me.users == 0:
            bpy.data.meshes.remove(me)
    report['deleted_objects'] = removed
    # restore the original geometry of the existing objects that this stage rebuilds from their original shape
    n = 0
    for o in bpy.data.objects:
        orig = bpy.data.meshes.get(ORIG_PREFIX + o.name)
        if orig is not None and o.type == 'MESH' and o.data is not None and o.data.name != orig.name:
            pass
    return removed


def original_mesh(obj):
    """return (a copy of) the original mesh of an existing object; the first call stores a snapshot with a fake user"""
    nm = ORIG_PREFIX + obj.name
    snap = bpy.data.meshes.get(nm)
    if snap is None:
        snap = obj.data.copy()
        snap.name = nm
        snap.use_fake_user = True
        # drop its materials users? keep: they are the original slots
    return snap


def world_to_local(obj, V):
    mw = np.array(obj.matrix_world, dtype=float)
    if np.allclose(mw, np.eye(4), atol=1e-7):
        return V
    inv = np.linalg.inv(mw)
    Vh = np.concatenate([V, np.ones((len(V), 1))], axis=1)
    return (Vh @ inv.T)[:, :3]


def write_mesh(me, md, uv_name='UVMap', sharp_deg=38.0, smooth=True, world_obj=None, extra_int=None):
    """fill the mesh datablock `me` from a MeshData (world metres); the object's own transform is undone when world_obj is given."""
    V = np.array(md.V, dtype=float)
    if world_obj is not None:
        V = world_to_local(world_obj, V)
    me.clear_geometry()
    me.from_pydata([tuple(v) for v in V], [], [tuple(f) for f in md.F])
    n = len(md.F)
    if md.mat:
        me.polygons.foreach_set('material_index', np.array(md.mat, dtype=np.int32))
    for k in list(me.uv_layers.keys()):
        me.uv_layers.remove(me.uv_layers[k])
    if md.uv:
        uvl = me.uv_layers.new(name=uv_name)
        flat = np.array([c for f in wg.unmirror_uv(md.uv) for c in f], dtype=np.float32).ravel()
        uvl.data.foreach_set('uv', flat)
    for k, arr in md.attr.items():
        arr = np.array(arr, dtype=np.float32)
        if len(arr) != len(V):
            arr = np.pad(arr, (0, len(V) - len(arr)))
        a = me.attributes.get(k) or me.attributes.new(k, 'FLOAT', 'POINT')
        a.data.foreach_set('value', arr)
    if md.part:
        a = me.attributes.get('part_id') or me.attributes.new('part_id', 'INT', 'POINT')
        a.data.foreach_set('value', np.array(md.part, dtype=np.int32))
    me.update()
    if smooth:
        bm = bmesh.new()
        bm.from_mesh(me)
        for f in bm.faces:
            f.smooth = True
        lim = math.radians(sharp_deg)
        for e in bm.edges:
            if len(e.link_faces) == 2:
                try:
                    e.smooth = e.calc_face_angle() < lim
                except ValueError:
                    pass
            else:
                e.smooth = False
        bm.to_mesh(me)
        bm.free()
    me.update()
    return me


def set_props(o, role, new=False, **kw):
    o['garden_owner'] = OWNER
    o['garden_role'] = role
    if new:
        o['wood_new'] = 1
    for k, v in kw.items():
        o[k] = v


def put_object(name, md, mats, role, coll, existing=True, world=True, **props):
    """create (or reuse the existing) object `name`, fill its mesh from md, assign materials."""
    o = bpy.data.objects.get(name)
    created = False
    if o is None:
        me = bpy.data.meshes.new(name)
        o = bpy.data.objects.new(name, me)
        coll.objects.link(o)
        created = True
    for m in list(o.modifiers):
        o.modifiers.remove(m)
    write_mesh(o.data, md, world_obj=None if created else o)
    o.data.materials.clear()
    for m in mats:
        o.data.materials.append(m)
    set_props(o, role, new=created, **props)
    return o, created


def hide_astra_controls(report):
    n = 0
    for o in bpy.data.objects:
        if o.name.startswith('Astra / Planked run controls'):
            o['astra_active'] = False
            o.hide_viewport = True
            o.hide_set(True)
            n += 1
    report['hidden_controls'] = n


def make_bed_fn():
    dg = bpy.context.evaluated_depsgraph_get()
    objs = [bpy.data.objects.get(n) for n in ("Life / pond bed", "Astra / Courtyard receiving ground")]
    objs = [o for o in objs if o is not None]
    cache = {}

    def f(x, y):
        key = (round(x, 3), round(y, 3))
        if key in cache:
            return cache[key]
        best = None
        for o in objs:
            ev = o.evaluated_get(dg)
            inv = ev.matrix_world.inverted()
            org = inv @ Vector((x, y, 2.0))
            d = (inv.to_3x3() @ Vector((0, 0, -1))).normalized()
            ok, loc, nrm, idx = ev.ray_cast(org, d)
            if ok:
                z = (ev.matrix_world @ loc).z
                best = z if best is None else max(best, z)
        cache[key] = best if best is not None else -0.44
        return cache[key]
    return f


def rock_list():
    out = []
    for o in bpy.data.objects:
        if o.name.startswith('Rock ') or o.name.startswith('Pond edge stone'):
            c = o.matrix_world.translation
            if -7.5 < c.x < 1.0 and -2.5 < c.y < 3.5:
                out.append((float(c.x), float(c.y), float(max(o.dimensions.x, o.dimensions.y) / 2.0)))
    return out


def ensure_maps(maps_dir):
    """make the normal map pictures when they are not in maps_dir yet (numpy + Blender only; the delivered PNGs are made by gen_maps.py with the same functions)"""
    import wood_maps as wm
    import normal_tools as nt
    os.makedirs(maps_dir, exist_ok=True)
    made = []
    def p(n):
        return os.path.join(maps_dir, n)
    def save_gray(path, arr):
        h, w = arr.shape
        img = bpy.data.images.new('_tmp_gray', w, h, alpha=False)
        img.colorspace_settings.name = 'Non-Color'
        rgba = np.stack([arr[::-1]] * 3 + [np.ones_like(arr)], axis=-1).astype(np.float32)
        img.pixels.foreach_set(rgba.ravel())
        img.filepath_raw = path
        img.file_format = 'PNG'
        img.save()
        bpy.data.images.remove(img)
    if not os.path.exists(p('plank_top_normal.png')) or not os.path.exists(p('plank_top_cavity.png')):
        h = wm.plank_top_height(2048, 512, seed=4)
        nt.save_normal_png(p('plank_top_normal.png'), nt.height_to_normal(wm.calibrate_height(h, 30.0), 1.0, True))
        save_gray(p('plank_top_cavity.png'), wm.plank_cavity(h))
        made += ['plank_top_normal.png', 'plank_top_cavity.png']
    if not os.path.exists(p('end_grain_normal.png')):
        nt.save_normal_png(p('end_grain_normal.png'), nt.height_to_normal(wm.calibrate_height(wm.end_grain_height(1024, seed=6), 28.0), 1.0, True))
        made.append('end_grain_normal.png')
    if not os.path.exists(p('post_timber_normal.png')):
        nt.save_normal_png(p('post_timber_normal.png'), nt.height_to_normal(wm.calibrate_height(wm.post_timber_height(1024, 2048, seed=10), 30.0), 1.0, True))
        made.append('post_timber_normal.png')
    if not os.path.exists(p('footing_stone_normal.png')):
        h = wm.soft_stone_height(1024)
        nt.save_normal_png(p('footing_stone_normal.png'), nt.height_to_normal(wm.calibrate_height(h, 26.0), 1.0, True))
        made.append('footing_stone_normal.png')
    return made


# ------------------------------------------------------------------ the stage
def apply(options=None):
    options = dict(options or {})
    t0 = time.time()
    rep = {'created': [], 'changed': [], 'deleted': []}
    maps_dir = options.get('maps_dir') or os.path.join(HERE, 'maps')
    seed = int(options.get('seed', 7))
    rep['maps_made'] = ensure_maps(maps_dir)
    cleanup(rep)
    coll = get_collection()
    # ---------------- materials
    plank_m = wmat.make_plank_materials(maps_dir, params=options.get('moss'))
    mat_post = wmat.make_post_material(maps_dir)
    mat_stone = wmat.make_stone_material(maps_dir)
    mat_peg = wmat.make_flat_material('G6 wood / peg', wmat.PAL['peg'], rough=0.72)
    mat_nail = wmat.make_flat_material('G6 wood / nail', '#3e2a20', rough=0.7)
    mat_iron = wmat.make_flat_material('G6 wood / iron', wmat.PAL['iron'], rough=0.7, edge=wmat.PAL['iron_edge'])
    planks3 = [plank_m['top'], plank_m['side'], plank_m['end']]
    deck_m = wmat.make_plank_materials(maps_dir, params=options.get('moss'), prefix='deck', pal=wmat.DECK_PAL)
    deck3 = [deck_m['top'], deck_m['side'], deck_m['end']]
    rep['materials_created'] = [m.name for m in bpy.data.materials if m.name.startswith('G6 wood / ')]
    hide_astra_controls(rep)
    ctx = dict(coll=coll, planks3=planks3, deck3=deck3, mat_post=mat_post, mat_stone=mat_stone, mat_peg=mat_peg, mat_nail=mat_nail, mat_iron=mat_iron,
               maps_dir=maps_dir, rep=rep, plank_m=plank_m)
    if options.get('bridge', True):
        build_bridge(ctx, seed, options)
    if options.get('deck', True):
        try:
            import wood_deck
            wood_deck.build_deck(ctx, seed, options, sys.modules[__name__])
        except ImportError:
            log('deck module missing')
    if options.get('frame', True):
        try:
            import wood_frame
            wood_frame.build_frame(ctx, seed, options, sys.modules[__name__])
        except ImportError:
            log('frame module missing')
    if options.get('cameras', True):
        make_cameras(rep)
    rep['seconds'] = round(time.time() - t0, 1)
    global LAST_CTX
    LAST_CTX = ctx
    log('REPORT', json.dumps({k: (v if not isinstance(v, list) else (len(v), v[:40])) for k, v in rep.items()}, default=str))
    return rep


def build_bridge(ctx, seed, options):
    rep, coll = ctx['rep'], ctx['coll']
    bed = make_bed_fn()
    L = wb.layout(seed, bed_fn=bed, rocks=rock_list())
    out, parts = wb.build_meshes(L)
    ctx['bridge_layout'], ctx['bridge_parts'], ctx['bridge_out'] = L, parts, out
    P3 = ctx['planks3']
    mapping = [
        ('planks_arm0', 'Astra / varied planks.005', P3, 'timber.deck'),
        ('planks_arm1', 'Astra / varied planks.004', P3, 'timber.deck'),
        ('planks_arm2', 'Astra / varied planks.003', P3, 'timber.deck'),
        ('planks_n2', 'Astra / varied planks.006', P3, 'timber.deck'),
        ('planks_n1', 'Astra / varied planks.007', P3, 'timber.deck'),
        ('stringers', 'Bridge stringers', [ctx['mat_post']], 'timber.frame'),
        ('sill0', 'Bridge pier 3', None, 'stone.dressed'),
        ('sill3', 'Bridge pier 0', None, 'stone.dressed'),
        ('footing_n1', 'Bridge pier 1', None, 'stone.dressed'),
        ('footing_n2', 'Bridge pier 2', None, 'stone.dressed'),
        ('bearers', 'G6 wood / bridge bearers', [ctx['mat_post']], 'timber.frame'),
        ('posts', 'G6 wood / bridge posts', [ctx['mat_post']], 'timber.frame'),
        ('footings', 'G6 wood / bridge footings', [ctx['mat_stone']], 'stone.dressed'),
        ('pegs', 'G6 wood / bridge pegs', [ctx['mat_peg'], ctx['mat_nail']], 'timber.frame'),
        ('cramps', 'G6 wood / bridge cramps', [ctx['mat_iron']], 'timber.frame'),
    ]
    ct = {'Bridge pier 0': 'CT / Stone painterly surface.039', 'Bridge pier 1': 'CT / Stone painterly surface.040',
          'Bridge pier 2': 'CT / Stone painterly surface.041', 'Bridge pier 3': 'CT / Stone painterly surface.042'}
    for key, oname, mats, role in mapping:
        md = out[key]
        if md.nv() == 0:
            continue
        if mats is None:
            mats = [bpy.data.materials[ct[oname]]]
        o, created = put_object(oname, md, mats, role, coll)
        (rep['created'] if created else rep['changed']).append(oname)
    # normal map on the CT stone materials of the piers (existing materials, owned)
    for pn, mn in ct.items():
        wmat.add_normal_to_chain(bpy.data.materials[mn], os.path.join(ctx['maps_dir'], 'footing_stone_normal.png'), 'UVMap', 0.8, (1, 1, 1))
    # three maple leaves on the planks
    import wood_deck
    lm = wood_deck.make_leaf_material('G6 wood / bridge leaf')
    rng = np.random.default_rng(seed + 300)
    arm_pl = [p for p in L['planks'] if p['kind'] == 'arm']
    for i, pk in enumerate(rng.choice(len(arm_pl), 3, replace=False)):
        p = arm_pl[int(pk)]
        sp = p['spec']
        X = float(rng.uniform(0.3, p['L'] - 0.3))
        Y = float(rng.uniform(-p['w'] * 0.25, p['w'] * 0.25))
        pos = wb._w(sp, X, Y)
        z = wg.plank_top_z(sp, X, Y) + 0.003
        V, F = wg.leaf_mesh((pos[0], pos[1], z), float(rng.uniform(0, 6.28)), float(rng.uniform(0.04, 0.055)), curl=0.01, seed=20 + i)
        md = wg.MeshData()
        md.add_part(V, F, [0] * len(F), [[(0.0, 0.0)] * len(f) for f in F], {}, 0)
        o, created = put_object('G6 wood / bridge leaf %d' % (i + 1), md, [lm], 'leaf', coll)
        rep['created'].append(o.name)
    rep['bridge'] = dict(planks=len(L['planks']), parts=len(parts), cramps=L['n_cramps'])


def make_cameras(rep):
    specs = [
        ('G6 wood cam 3', (-2.9, -2.2, 0.55), (-3.0, 0.7, 0.2), 35.0),
        ('G6 wood cam 4', (-3.6, -1.8, 2.8), (-3.5, 0.7, 0.2), 40.0),
        ('G6 wood cam 5', (-0.2, -1.0, 0.35), (-4.0, 0.4, 0.15), 28.0),
        ('G6 wood cam 6', (-4.55, -0.2, 0.62), (-4.9, 0.55, 0.22), 85.0),
        ('G6 wood cam 7', (2.2, 3.2, 1.6), (2.0, 5.6, 0.6), 28.0),
        ('G6 wood cam 8', (2.3, 3.0, 0.95), (2.2, 4.5, 0.3), 35.0),       # veranda steps
        ('G6 wood cam 9', (-2.3, 4.0, 1.5), (-2.3, 6.5, 1.4), 35.0),      # hall posts and beams
        ('G6 wood cam 12', (-3.3, 0.5, 6.0), (-3.3, 0.5, 0.0), 0.0),      # plan view (orthographic, set by the diagram hook)
    ]
    coll = get_collection()
    for name, loc, tgt, lens in specs:
        cd = bpy.data.cameras.new(name)
        if lens > 0:
            cd.lens = lens
        else:
            cd.type = 'ORTHO'
            cd.ortho_scale = 7.6
        co = bpy.data.objects.new(name, cd)
        coll.objects.link(co)
        co.location = loc
        d = Vector(tgt) - Vector(loc)
        co.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
        co['garden_owner'] = OWNER
        co['wood_new'] = 1
        co['garden_role'] = 'camera'
        rep['created'].append(name)
