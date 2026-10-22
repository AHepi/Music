"""stage_roof.py - ROOF BUILDER of the garden character round (22 October), FIX ROUND copy (changes marked FIX ROUND).  apply(options) works on the open starting scene
(garden_real_fixed.blend), touches only what the roof builder owns, and can be run twice (it first removes what it made earlier).
Plain words: gives the roof, plaster walls and caps, stones and the lantern hand-made character (tile variety and damage, moss,
lichen, drip stains, ridge and eave details, plaster loss and cracks, moss caps on rocks, a cracked chipped lantern) in the garden's
own simplified style, with real normal maps and real geometry.  Steps: 0 UV test, 1 tile variety, 2 marks and glaze normal map,
3 ridge and eave, 4 walls, 5 stones, 6 lantern (options['steps'] picks which)."""
import bpy
import json
import math
import os
import sys
import time
import numpy as np
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import importlib
import r_common
importlib.reload(r_common)
from r_common import *
import r_maps
importlib.reload(r_maps)
import r_tiles
importlib.reload(r_tiles)
import r_marks
importlib.reload(r_marks)
import r_ridge
importlib.reload(r_ridge)
import r_walls
importlib.reload(r_walls)
import r_stones
importlib.reload(r_stones)
import r_lantern
importlib.reload(r_lantern)
import r_moss
importlib.reload(r_moss)

DEFAULTS = {'steps': [0, 1, 2, 3, 4, 5, 6], 'seed': 22, 'maps_dir': None, 'save_maps': False,
            'map_sizes': {'glaze': 1024, 'plaster': 2048, 'stone': 1024, 'moss': 1024}, 'cameras': True, 'debug_mask': False}

# FIX ROUND: the stone colour's wavy "agate" stripes, grey-green bands and diamond lines are the weathering kit's foot, wall-crack and wall-growth
# layers (found by drawing the kit chain step by step). The kit reads its strengths from custom properties of the object, so the stones get
# calmer numbers: each value below is the factor applied to the object's ORIGINAL value (originals are remembered and put back by cleanup()).
WK_CALM_STONE = {'wk_foot_amount': 0.35, 'wk_foot_splash_strength': 0.40, 'wk_foot_tide_green': 0.30, 'wk_wallcracks_amount': 0.33,
                 'wk_wallgrowth_algae_amount': 0.35, 'wk_wallgrowth_amount': 0.75, 'wk_dirt_water_marks': 0.5, 'wk_groundmoss_algae_fan': 0.5}
WK_CALM_LANTERN = {'wk_foot_amount': 0.5, 'wk_foot_splash_strength': 0.5, 'wk_foot_tide_green': 0.3, 'wk_wallcracks_amount': 0.5,
                   'wk_wallgrowth_algae_amount': 0.2, 'wk_wallgrowth_amount': 0.45, 'wk_wallgrowth_lichen_amount': 0.6, 'wk_dirt_water_marks': 0.5,
                   'wk_groundmoss_algae_fan': 0.4}

OWN_OBJECTS = (['Hall roof', 'CT / Ceramic pan prototype', 'Hall plaster', 'Back wall, left', 'Back wall, left cap', 'Back wall, right',
                'Back wall, right cap', 'Right wall behind hall', 'Right wall behind hall cap', 'Lantern base', 'Lantern post',
                'Lantern gallery', 'Lantern firebox', 'Lantern cap', 'Lantern finial', 'Water basin', 'Basin front stone',
                'Basin candle stone', 'Basin bucket stone', 'Basin drain pebbles', 'Shore stones']
               + ['Rock %d' % i for i in range(5)] + ['Pond edge stone %d' % i for i in range(15)])


# ------------------------------------------------------------------------------------------------- cleanup (idempotence)
def cleanup():
    n_rest = 0
    for o in list(bpy.data.objects):
        if 'g6_orig' in o.keys():
            info = json.loads(o['g6_orig'])
            me = bpy.data.meshes.get(info['mesh'])
            if me is not None and o.type == 'MESH':
                o.data = me
                me.use_fake_user = False
            if info.get('mats') is not None and o.type == 'MESH':
                o.data.materials.clear()
                for mn in info['mats']:
                    o.data.materials.append(bpy.data.materials.get(mn) if mn else None)
            del o['g6_orig']
            n_rest += 1
    for o in bpy.data.objects:
        if 'g6_wk_orig' in o.keys():            # FIX ROUND: put the weathering kit's strengths of the stones back
            for k, v in json.loads(o['g6_wk_orig']).items():
                o[k] = v
            del o['g6_wk_orig']
    roof = bpy.data.objects.get('Hall roof')
    if roof is not None and 'g6_orig_group' in roof.keys():
        mod = roof.modifiers[0]
        mod.node_group = bpy.data.node_groups[roof['g6_orig_group']]
        del roof['g6_orig_group']
    for ng in [g for g in bpy.data.node_groups if g.name.startswith(PFX)]:
        bpy.data.node_groups.remove(ng)
    for o in [o for o in bpy.data.objects if o.name.startswith(PFX) or o.name.startswith('G6 roof cam')]:
        bpy.data.objects.remove(o, do_unlink=True)
    for coll in (bpy.data.meshes, bpy.data.materials, bpy.data.images, bpy.data.cameras, bpy.data.curves, bpy.data.lights):
        for d in [d for d in coll if d.name.startswith(PFX)]:
            coll.remove(d)
    c = bpy.data.collections.get(COLL)
    if c is not None:
        bpy.data.collections.remove(c)
    for me in [m for m in bpy.data.meshes if m.users == 0 and m.name.startswith('tmp')]:
        bpy.data.meshes.remove(me)
    return n_rest


def calm_wk(obj, factors):
    """multiply the weathering kit's strengths (custom properties wk_*) of a stone by the given factors, always from the original values"""
    orig = json.loads(obj['g6_wk_orig']) if 'g6_wk_orig' in obj.keys() else {}
    for k, f in factors.items():
        if k in obj.keys():
            if k not in orig:
                orig[k] = float(obj[k])
            obj[k] = orig[k] * f
    obj['g6_wk_orig'] = json.dumps(orig)


def swap_mesh(obj, new_mesh_name_suffix=''):
    """give obj its own copy of its mesh (original kept with a fake user and remembered in obj['g6_orig'])"""
    if 'g6_orig' not in obj.keys():
        obj['g6_orig'] = json.dumps({'mesh': obj.data.name, 'mats': [m.name if m else None for m in obj.data.materials]})
        obj.data.use_fake_user = True
    new = obj.data.copy()
    new.name = PFX + obj.name
    obj.data = new
    return new


def snapshot():
    return {'objects': sorted(o.name for o in bpy.data.objects), 'materials': sorted(m.name for m in bpy.data.materials)}


CAMERAS = [  # name, location, target, lens (mm)
    ('eave from the garden', (-1.5, 3.2, 1.3), (-1.0, 6.0, 3.3), 35),
    ('roof from a ladder', (0.2, 2.2, 4.6), (0.2, 7.0, 3.9), 35),
    ('right wall from 3 m', (7.1, 5.6, 1.5), (10.1, 6.4, 1.1), 35),
    ('lantern from 2.2 m', (-0.85, -0.55, 1.4), (0.95, 1.1, 1.2), 50),
    ('two rocks from 2 m', (-2.15, 1.35, 0.85), (-2.15, 3.5, 0.35), 35),
    ('back wall from 3 m', (7.6, 7.2, 1.5), (8.0, 10.2, 1.2), 35),
]


def make_cameras():
    from mathutils import Vector
    out = []
    for i, (nm, loc, tgt, lens) in enumerate(CAMERAS, 1):
        cd = bpy.data.cameras.new(PFX + 'cam %d' % i)
        cd.lens = lens
        co = bpy.data.objects.new('G6 roof cam %d' % i, cd)
        tag(co, 'camera')
        co['view'] = nm
        co.location = loc
        d = Vector(tgt) - Vector(loc)
        co.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
        collection().objects.link(co)
        out.append(co.name)
    return out


# ------------------------------------------------------------------------------------------------- apply
def apply(options=None):
    t0 = time.time()
    opts = dict(DEFAULTS)
    opts.update(options or {})
    rep = {'steps': opts['steps'], 'notes': []}
    r_marks.DEBUG_WET = bool(opts.get('wet_debug'))
    before = snapshot()
    rep['restored_objects'] = cleanup()
    base = snapshot()
    steps = opts['steps']
    sizes = opts['map_sizes']
    normals = None
    if any(s in steps for s in (1, 2, 4, 5, 6)):
        normals = r_maps.all_normals(sizes)
        imgs = {}
        for k, (n, s) in normals.items():
            imgs[k] = make_image(k + ' normal', n * 0.5 + 0.5, 'Non-Color')
            if opts['save_maps'] and opts['maps_dir']:
                os.makedirs(opts['maps_dir'], exist_ok=True)
                save_png(imgs[k], os.path.join(opts['maps_dir'], k + '_normal.png'))
        rep['normal_strength_used'] = {k: round(float(s), 4) for k, (n, s) in normals.items()}
    ctx = {'opts': opts, 'rep': rep, 'imgs': imgs if normals else {}}
    ctx['rng'] = np.random.default_rng(opts['seed'])
    if 1 in steps or 2 in steps or 0 in steps:
        step_tiles(ctx)
    for st, fn in ((3, step_ridge), (4, step_walls), (5, step_stones), (6, step_lantern)):
        if st in steps:
            t1 = time.time()
            fn(ctx)
            rep.setdefault('step_seconds', {})[st] = round(time.time() - t1, 1)
    if opts['cameras']:
        rep['cameras'] = make_cameras()
    if opts.get('mask_render'):
        sc_ = bpy.context.scene
        cdt = bpy.data.cameras.new(PFX + 'cam top')
        cdt.type = 'ORTHO'
        cdt.ortho_scale = 12.4
        cot = bpy.data.objects.new('G6 roof cam top', cdt)
        cot.location = (0.2, 5.7, 9.0)
        collection().objects.link(cot)
        for o in bpy.data.objects:
            if o.type in ('MESH', 'CURVE', 'SURFACE', 'FONT') and o.name != 'Hall roof':
                o.hide_render = True
        sc_.render.film_transparent = False
        sc_.view_settings.view_transform = 'Raw'
        sc_.view_settings.look = 'None'
        sc_.view_settings.exposure = 0.0
        sc_.view_settings.gamma = 1.0
        if sc_.world is not None:
            sc_.world.use_nodes = False
            sc_.world.color = (0, 0, 0)
    if opts.get('save_blend'):
        os.makedirs(os.path.dirname(opts['save_blend']), exist_ok=True)
        bpy.ops.wm.save_as_mainfile(filepath=opts['save_blend'], copy=True)
        rep['saved_blend'] = opts['save_blend']
    rep['seconds'] = round(time.time() - t0, 1)
    after = snapshot()
    rep['new_objects'] = sorted(set(after['objects']) - set(base['objects']))
    rep['new_materials'] = sorted(set(after['materials']) - set(base['materials']))
    rep['removed_objects'] = sorted(set(before['objects']) - set(after['objects']))
    print('[roof] report', json.dumps({k: v for k, v in rep.items() if k not in ('new_objects', 'new_materials')}, default=str)[:3000])
    return rep


# ------------------------------------------------------------------------------------------------- steps 0 to 2: the roof tiles
def step_tiles(ctx):
    rep, opts = ctx['rep'], ctx['opts']
    M, counts0 = r_tiles.eval_instances()
    rep['tiles_found'] = len(M)
    plan = r_tiles.make_plan(M, opts['seed'])
    rep['tile_plan'] = {k: v for k, v in plan['lists'].items()}
    rep['drip_tiles'] = plan['drip_tiles']
    rep['hero_visible_tiles'] = plan['hero_visible_count']
    rep['tone_std'] = round(float(plan['tone'].std()), 4)
    mat_tile = mat_copy('CT / Ceramic painterly surface', 'ceramic')
    if opts.get('mat_mode') != 'plain':
        r_tiles.build_ceramic(mat_tile, 'INSTANCER', None if opts.get('mat_mode') == 'nonormal' else ctx['imgs'].get('glaze'), debug=opts.get('debug'))
    if opts.get('uv_test'):
        r_tiles.add_uv_test(mat_tile)
    mat_under = r_tiles.make_underlay_material()
    metas = r_tiles.make_variant_meshes(mat_tile, mat_under)
    var_objs = []
    for me in metas:
        o = bpy.data.objects.new(me.name, me)
        tag(o, 'roof.tile')
        o.hide_render = True          # source shapes for the roof node group: in 'G6 roof' but never drawn on their own
        collection().objects.link(o)
        var_objs.append(o)
    table = r_tiles.make_table(M, plan)
    # FIX ROUND: the pale mint slivers between the eave discs are the roof's timber pieces (CT / Timber painterly surface) where the weathering kit's
    # growth layer turns dark brown wood mint. The roof gets its own copy that keeps the soot but not the growth layer: plain dark rafter wood.
    timber = mat_copy('CT / Timber painterly surface', 'roof timber')
    _nt = timber.node_tree
    _b = [n for n in _nt.nodes if n.bl_idname == 'ShaderNodeBsdfPrincipled'][0]
    _nt.links.new(_nt.nodes['WK soot'].outputs['Colour'], _b.inputs['Base Color'])
    vc = [len(me.vertices) for me in metas]
    for offs in ((r_tiles.NB, 0), (0, r_tiles.NB)):          # which bank group makes instances 0..343? try the likely order first
        root, banks = r_tiles.install_groups(table, var_objs, offs, timber)
        bpy.context.view_layer.update()
        M2, counts = r_tiles.eval_instances()
        bad = [k for k in range(len(M2)) if counts[k] != vc[int(plan['variant'][k])]]
        if len(bad) < 5:
            break
        r_tiles.uninstall_groups()
    have, miss = r_tiles.test_uv_reaches_instances()
    rep['step0_uv'] = {'instances': len(M2), 'with_UVMap': have, 'without': miss}
    rep['variant_check_mismatch'] = len(bad)
    rep['bank_offsets'] = offs
    rep['shape_vertex_counts'] = dict(zip(r_tiles.VAR_NAMES, vc))
    ctx['plan'] = plan
    ctx['M'] = M2
    ctx['metas'] = metas


def opts_seed(ctx):
    return ctx['opts']['seed']


def _link_new(o, collections=()):
    for c in collections:
        link_to(o, c)


# ------------------------------------------------------------------------------------------------- step 3: ridge and eave
def step_ridge(ctx):
    rep, imgs = ctx['rep'], ctx['imgs']
    mat = mat_copy('CT / Ceramic ridge host-local surface', 'ridge ceramic')
    r_marks.build_marks(mat, nrm_img=imgs['glaze'], nrm_scale=1.5, nrm_strength=0.8, moss={'scale': 7.0, 'lo': 0.575, 'top': 0.5},
                        lichen={'dots': 20.0, 'zone': 2.4, 'lo': 0.6}, tone=0.3, bump_strength=0.2)
    me, nseg = r_ridge.build_ridge(mat)
    o = new_object('ridge course', me, 'roof.tile', receivers=True)
    rep['ridge'] = {'segments': nseg, 'end_caps': 2}
    mat2 = mat_copy('CT / Ceramic painterly surface', 'eave disc')
    r_marks.build_marks(mat2, nrm_img=imgs['glaze'], nrm_scale=1.5, nrm_strength=0.8, tone=0.35, bump_strength=0.2,
                        lichen={'dots': 22.0, 'zone': 2.8, 'lo': 0.62})
    me2, nd = r_ridge.build_eave_discs(ctx['M'], ctx['plan'], mat2)
    r_marks.add_attr_tint(mat2, 'g6_drip', '#26242f', 1.0)           # FIX ROUND: the disc under a drip stain is dark too
    o2 = new_object('eave discs', me2, 'roof.tile', receivers=True)
    rep['eave_discs'] = nd
    me3, lv = r_ridge.build_leaves(ctx['M'], ctx['plan'], r_ridge.leaf_material(), np.random.default_rng(opts_seed(ctx) + 3), 8)
    new_object('roof leaves', me3, 'leaf', receivers=True)
    rep['roof_leaves'] = len(lv)
    # FIX ROUND: moss as soft cushions at the eave, the ridge foot and on the ridge cap (geometry, a cluster of round lumps each)
    mat_rm = r_stones.moss_cap_material(ctx['imgs']['moss'], name='roof moss', dark='#232a16', lit='#465326', high='#5f6e31', ring='#6c7b38',
                                        nm_strength=0.9, nm_scale=1.0, lump_scale=22.0, lump_dark=0.55)
    bpy.context.view_layer.update()
    ridge_obj = bpy.data.objects.get(PFX + 'ridge course')
    surf = r_moss.RoofSurface(ctx['M'], ctx['plan'], ctx['metas'], [ridge_obj] if ridge_obj is not None else [])
    cush = r_moss.place_roof_cushions(ctx['M'], ctx['plan'], np.random.default_rng(opts_seed(ctx) + 31), surf)
    kinds = {}
    for kind, nm_, me_, k in cush:
        me_.materials.append(mat_rm)
        o_ = new_object(nm_, me_, 'growth', receivers=True)
        o_['on_tile'] = int(k)
        kinds[kind] = kinds.get(kind, 0) + 1
    rep['roof_moss_cushions'] = kinds


# ------------------------------------------------------------------------------------------------- step 4: walls and caps
def step_walls(ctx):
    rep, imgs, opts = ctx['rep'], ctx['imgs'], ctx['opts']
    rng = np.random.default_rng(opts['seed'] + 4)
    blot = r_maps.plaster_blotch(os.path.join(HERE, 'maps', 'sw_plaster.jpg'), 1024)
    imgs['blotch'] = make_image('plaster blotch', np.clip(blot * 0.5, 0, 1), 'Non-Color')
    mat_wall = mat_copy('GARDEN wall.garden', 'wall.garden')
    r_walls.build_wall_material(mat_wall, imgs)
    mat_cap = mat_copy('Wall cap tile', 'cap tile')
    r_walls.build_wall_material(mat_cap, imgs, cap=True)
    mat_crack = r_walls.crack_material()
    mat_foot = mat_copy('GARDEN stone.lantern', 'footing stone')
    r_marks.build_marks(mat_foot, nrm_img=imgs['stone'], nrm_strength=0.8, blotch=0.8, tone=0.12, bump_strength=0.25)
    wr = {}
    for (name, gn, npatch, ncrack, axis, ztop) in r_walls.WALLS:
        obj = bpy.data.objects[name]
        obj['g6_ztop'] = ztop
        stats, cracks, nrm, vs, axis = r_walls.build_wall(obj, gn, npatch, ncrack, axis, ztop, rng, imgs)
        me = obj.data
        me.materials.clear()
        me.materials.append(mat_wall)
        set_uv(me, 'UVMap', box_uv_fn(2.5, off=((obj.location.x * 0.0 + rng.uniform(0, 1)), rng.uniform(0, 1))))
        d = nrm.dot(vs[0])
        n_ = Vector(nrm)
        b_ax = 1 - axis
        def surf(s, t, axis=axis, b_ax=b_ax, d=d, n_=n_):
            p = [0.0, 0.0, t]
            p[axis] = s
            p[b_ax] = (d - n_[axis] * s - n_[2] * t) / n_[b_ax]
            return Vector(p)
        cm = r_walls.crack_ribbons(PFX_NAME(name) + ' cracks', cracks, surf, n_)
        cm.materials.append(mat_crack)
        co = new_object(name + ' cracks', cm, 'wall.crack')
        s0, s1 = stats['s_range']
        fm = r_walls.footing_blocks(name + ' footing', surf(s0 + 0.1, 0.0), surf(s1 - 0.1, 0.0), Vector(gn), Vector((0, 0, 1)), rng)
        fm.materials.append(mat_foot)
        set_uv(fm, 'UVMap', box_uv_fn(1.0))
        fo = new_object(name + ' footing', fm, 'stone.dressed')
        cap = bpy.data.objects[r_walls.CAPS[name]]
        nchip = r_walls.chip_caps(cap, rng, 5 if axis == 1 else 4)
        cap.data.materials.clear()
        cap.data.materials.append(mat_cap)
        set_uv(cap.data, 'UVMap', box_uv_fn(1.0))
        wr[name] = {'plaster_loss_patches': stats['patches'], 'hairline_cracks': stats['cracks'], 'drip_streaks': stats['streaks'],
                    'chipped_cap_tiles': nchip, 'footing_blocks': len(fm.polygons) // 8, 'verts': len(me.vertices)}
    hp = bpy.data.objects.get('Hall plaster')
    if hp is not None:
        mp = mat_copy('Plaster wall', 'plaster wall')
        r_marks.build_marks(mp, nrm_img=imgs['plaster'], nrm_strength=1.0, blotch=0.5, bump_strength=0.28)
        r_stones.give_stone_uv_and_mesh(hp, 2.5)
        hp.data.materials.clear()
        hp.data.materials.append(mp)
    rep['walls'] = wr


def PFX_NAME(n):
    return n


# ------------------------------------------------------------------------------------------------- step 5: stones
def _stone_mat(obj, label, imgs, **kw):
    src = obj.data.materials[0].name
    m = mat_copy(src, label)
    r_marks.build_marks(m, nrm_img=imgs['stone'], nrm_strength=kw.pop('nrm_strength', 0.8), **kw)
    return m


def step_stones(ctx):
    rep, imgs, opts = ctx['rep'], ctx['imgs'], ctx['opts']
    rng = np.random.default_rng(opts['seed'] + 5)
    rocks = ['Rock %d' % i for i in range(5)]
    ponds = ['Pond edge stone %d' % i for i in range(15)]
    others = ['Water basin', 'Basin front stone', 'Basin candle stone', 'Basin bucket stone']
    shared = {}
    for name in rocks + ponds + others + ['Shore stones', 'Basin drain pebbles']:
        obj = bpy.data.objects[name]
        r_stones.give_stone_uv_and_mesh(obj, 1.0)
        if name in ('Shore stones', 'Basin drain pebbles'):
            if 'rock' not in shared:
                shared['rock'] = _stone_mat(obj, 'stone.rock', imgs, wet=True, blotch=0.9, tone=0.1, bump_strength=0.28, blocks=0.8)
            m = shared['rock']
        else:
            m = _stone_mat(obj, name.replace(' ', '_') + ' ' + obj.data.materials[0].name.replace('CT / ', ''), imgs, wet=True, blotch=0.75,
                           tone=0.1, bump_strength=0.28, blocks=0.8)
        obj.data.materials[0] = m
        calm_wk(obj, WK_CALM_STONE)
    bpy.context.view_layer.update()
    cams = [bpy.data.objects['photo'], bpy.data.objects['veranda']]
    mat_moss = r_stones.moss_cap_material(imgs['moss'])
    mat_crack = r_walls.crack_material()
    # which pond-edge stones get a moss cap: the 5 that the two cameras see best from above
    scores = []
    for name in ponds:
        obj = bpy.data.objects[name]
        pts, ws = r_stones.top_candidates(obj, 0.5)
        scores.append((r_stones.visibility_score(obj, cams, pts, ws, 40, rng), name))
    scores.sort(reverse=True)
    pond_pick = [n for s, n in scores[:5]]
    caps = []
    n_cap = 0
    for name in rocks + pond_pick:
        obj = bpy.data.objects[name]
        pts, ws = r_stones.top_candidates(obj, 0.6)
        if not pts:
            continue
        order = np.argsort([-p.z for p in pts])[:max(3, len(pts) // 6)]
        w = np.array([ws[i] for i in order])
        cx = sum(pts[i].x * ws[i] for i in order) / w.sum()
        cy = sum(pts[i].y * ws[i] for i in order) / w.sum()
        dim = obj.dimensions
        R = float(np.clip(0.42 * min(dim.x, dim.y), 0.2, 0.5))
        bvh = r_stones.make_bvh(obj)
        me = r_stones.moss_cap_mesh(bvh, (cx, cy), R, rng.uniform(0.042, 0.062), rng, 'moss cap %d' % n_cap)
        if me is None:
            continue
        me.materials.append(mat_moss)
        o = new_object('moss cap %d' % n_cap, me, 'growth')
        o['on_stone'] = name
        caps.append((name, round(R, 2)))
        n_cap += 1
    rep['moss_caps'] = caps
    # chips and a crack on three rocks
    ch = {}
    cr = 0
    for name, nchip in (('Rock 0', 2), ('Rock 1', 1), ('Rock 3', 2)):
        obj = bpy.data.objects[name]
        nv = r_stones.chip_rock(obj, rng, nchip)
        r_stones.add_chip_colour(obj.data.materials[0])
        ch[name] = nchip
        bvh = r_stones.make_bvh(obj)
        pts, ws = r_stones.top_candidates(obj, 0.45)
        if pts:
            p = pts[int(rng.integers(len(pts)))]
            cm = r_stones.crack_on_top(bvh, rng, (p.x, p.y), rng.uniform(0.35, 0.6), 0.014, 'rock crack %s' % name)
            if cm is not None:
                cm.materials.append(mat_crack)
                new_object('rock crack %s' % name, cm, 'stone.natural')
                cr += 1
    rep['rock_chips'] = ch
    rep['rock_cracks'] = cr


# ------------------------------------------------------------------------------------------------- step 6: lantern
def step_lantern(ctx):
    rep, imgs, opts = ctx['rep'], ctx['imgs'], ctx['opts']
    rng = np.random.default_rng(opts['seed'] + 6)
    parts = ['Lantern base', 'Lantern post', 'Lantern gallery', 'Lantern firebox', 'Lantern cap', 'Lantern finial']
    # FIX ROUND: the lantern's moss is its own, darker olive (the rock caps keep theirs); smaller, and it follows the cap's hip edges and
    # lies in the joints like a crescent instead of one bright round blob
    mat_moss = r_stones.moss_cap_material(imgs['moss'], name='lantern moss', dark='#22281a', lit='#3f4c25', high='#556230', ring='#5f6d35',
                                          nm_strength=0.6, nm_scale=1.0, lump_scale=18.0, lump_dark=0.35)
    mat_crack = r_walls.crack_material()
    for name in parts:
        obj = bpy.data.objects[name]
        r_stones.give_stone_uv_and_mesh(obj, 1.0)
        calm_wk(obj, WK_CALM_LANTERN)
        kw = dict(wet=False, blotch=0.6, tone=0.08, bump_strength=0.28, blocks=0.5)
        if name in ('Lantern post', 'Lantern gallery'):
            kw['lichen'] = {'dots': 20.0, 'zone': 3.4, 'lo': 0.62}
        m = _stone_mat(obj, name.replace(' ', '_') + ' ' + obj.data.materials[0].name.replace('CT / ', ''), imgs, **kw)
        obj.data.materials[0] = m
    # chipped cap corners (the part's own coordinates: the cap sits at a fixed place, no rotation)
    cap = bpy.data.objects['Lantern cap']
    c1 = r_lantern.chip_corner(cap, -1, -1, 0.065, 0.45)
    c2 = r_lantern.chip_corner(cap, 1, 1, 0.045, 0.45)
    # cracks: two on the post (one per camera side), one on the gallery
    n_cr = 0
    post = bpy.data.objects['Lantern post']
    gal = bpy.data.objects['Lantern gallery']
    bp = r_stones.make_bvh(post)
    bg = r_stones.make_bvh(gal)
    pc = (post.location.x, post.location.y)
    gc = (gal.location.x, gal.location.y)
    specs = [(bp, (-1, 0), pc, post.location.z + 0.62, 0.42, 0.04, 'post a'), (bp, (0, 1), pc, post.location.z + 0.7, 0.38, -0.03, 'post b'),
             (bg, (0, 1), gc, gal.location.z + 0.2, 0.17, 0.12, 'gallery a')]
    for bvh, fd, cen, z0, ln, lat, nm in specs:
        cm = r_lantern.crack_on_face(bvh, fd, cen, z0, ln, rng, lat, 0.011, 'lantern crack ' + nm)
        if cm is not None:
            cm.materials.append(mat_crack)
            new_object('lantern crack ' + nm, cm, 'stone.dressed')
            n_cr += 1
    # moss in the joints and along the cap's hip edges: small soft cushions (FIX ROUND), elongated along the direction they follow
    base, firebox = bpy.data.objects['Lantern base'], bpy.data.objects['Lantern firebox']
    bb, bc = r_stones.make_bvh(base), r_stones.make_bvh(cap)
    bgal = bg
    cx_l, cy_l = post.location.x, post.location.y

    def pol(r, az):
        a = math.radians(az)
        return (cx_l + r * math.cos(a), cy_l + r * math.sin(a))
    # (bvh, radius from the lantern axis, azimuth degrees, size along, stretch across, turn of the long axis from radial, thickness, label)
    blobs = [(bc, 0.34, 197.5, 0.078, 0.92, 0.0, 0.034, 'cap hip a'), (bc, 0.39, 317.5, 0.056, 0.92, 0.0, 0.028, 'cap hip b'),
             (bc, 0.17, 257.5, 0.040, 0.9, 90.0, 0.020, 'finial foot'),
             (bb, 0.235, 215.0, 0.09, 0.55, 90.0, 0.03, 'post foot a'), (bb, 0.24, 322.0, 0.07, 0.58, 90.0, 0.026, 'post foot b'),
             (bgal, 0.30, 205.0, 0.09, 0.55, 90.0, 0.028, 'gallery joint a'), (bgal, 0.315, 332.0, 0.07, 0.58, 90.0, 0.024, 'gallery joint b')]
    nb = 0
    for bvh, r_, az, R, asp, turn, th, lab in blobs:
        me = r_moss.cushion_mesh(lambda x, y, bvh=bvh: r_stones.surface_hit(bvh, x, y), pol(r_, az), R, th, rng, 'lantern moss %d' % nb,
                                 aspect=asp, angle=math.radians(az + turn), S=36, lumps=2, max_dz=0.10, min_nz=0.45, uv_tile=0.3, wobble=0.25)
        if me is None:
            continue
        me.materials.append(mat_moss)
        o_ = new_object('lantern moss %d' % nb, me, 'growth')
        o_['follows'] = lab
        nb += 1
    rep['lantern'] = {'cracks': n_cr, 'chipped_cap_corners': 2, 'moss_blobs': nb, 'cap_chip_corners': [tuple(round(v, 2) for v in c1), tuple(round(v, 2) for v in c2)]}


if __name__ == '__main__':
    print(apply())
