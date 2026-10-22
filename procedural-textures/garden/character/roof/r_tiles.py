"""Roof tiles (steps 0 to 2 of the roof brief). Plain words: gives the 688 roof tiles individual character.
 * UV map on the tile prototype copy (1 UV unit = one tile) and a test that every instance inherits it,
 * a table object that holds one row per tile (variant, tone, slip, moss, lichen, drip), read inside copies of the roof node groups,
 * 6 tile shapes (whole, corner chip, crack groove, broken half, cracked in two, missing = dark underlay),
 * a copy of the ceramic material with tile tone, soft moss blobs, lichen flecks, drip stains and a glaze normal map."""
import bpy
import bmesh
import math
import numpy as np
from mathutils import Vector, Matrix
from bpy_extras.object_utils import world_to_camera_view
from r_common import *
import r_maps

PROTO = 'CT / Ceramic pan prototype'
ROOF = 'Hall roof'
G_ROOT = 'CT / Complete two-bank ceramic roof'
G_BANKS = ['CT / Roof bank 1 local mechanism', 'CT / Roof bank 2 local mechanism']
NCOL, NCRS = 43, 8
NB = NCOL * NCRS          # 344 tiles a bank, bank 1 = north (indices 0..343), bank 2 = south (344..687), course 0 = ridge, 7 = eave
TL, TW = 0.67, 0.31       # tile length (local Y) and width (local X)
VAR_NAMES = ['pan', 'pan chipped a', 'pan chipped b', 'pan chipped c', 'pan cracked', 'underlay']


# ------------------------------------------------------------------------------------------------- evaluation helpers
def eval_instances():
    """world matrices of the 688 tile instances in evaluation order (index k = bank*344 + column*8 + course)"""
    dg = bpy.context.evaluated_depsgraph_get()
    mats = []
    meshes = []
    for inst in dg.object_instances:
        if inst.is_instance and inst.parent and inst.parent.name == ROOF:
            mats.append(np.array(inst.matrix_world))
            try:
                meshes.append(len(inst.object.data.vertices))
            except Exception:
                meshes.append(-1)
    return np.array(mats), meshes


def visible_from(cam, M, up_offset=0.04):
    """True where a straight line from the camera to a point just above the tile top is not blocked (trees, walls, other tiles)."""
    sc = bpy.context.scene
    dg = bpy.context.evaluated_depsgraph_get()
    cp = cam.matrix_world.translation
    out = np.zeros(len(M), bool)
    uv = np.zeros((len(M), 3))
    for k, m in enumerate(M):
        top = Vector(m[:3, 3]) + Vector(m[:3, 2]) * (0.1 + up_offset)
        co = world_to_camera_view(sc, cam, top)
        uv[k] = (co.x, co.y, co.z)
        if not (0.0 < co.x < 1.0 and 0.0 < co.y < 1.0 and co.z > 0):
            continue
        d = top - cp
        dist = d.length
        hit = sc.ray_cast(dg, cp, d.normalized(), distance=dist - 0.02)[0]
        out[k] = not hit
    return out, uv


# ------------------------------------------------------------------------------------------------- the plan: which tile gets what
def make_plan(M, seed=22):
    rng = np.random.default_rng(seed)
    n = len(M)
    cams = {c: bpy.data.objects[c] for c in ('photo', 'veranda')}
    vis_h, uv_h = visible_from(cams['photo'], M)
    vis_v, uv_v = visible_from(cams['veranda'], M)
    bank = np.arange(n) // NB
    col = (np.arange(n) % NB) // NCRS
    crs = np.arange(n) % NCRS
    x = M[:, 0, 3]
    plan = {'variant': np.zeros(n, np.int32), 'slip': np.zeros(n, np.float32), 'yaw': np.zeros(n, np.float32),
            'vis_hero': vis_h, 'vis_veranda': vis_v, 'bank': bank, 'col': col, 'crs': crs}
    # roof area share seen by the hero camera (for the report)
    plan['hero_visible_count'] = int(vis_h.sum())
    cand = np.where(vis_h & (bank == 1) & (x > -3.6) & (x < 5.4) & (crs >= 1) & (crs <= 7) & (uv_h[:, 0] > 0.18) & (uv_h[:, 0] < 0.74))[0]
    rng.shuffle(cand)
    chosen = []
    taken = []

    def take(cond_fn, count, min_d=0.8):
        got = []
        for k in cand:
            if len(got) >= count:
                break
            if k in chosen or not cond_fn(k):
                continue
            p = M[k, :3, 3]
            if any(np.linalg.norm(p - M[t, :3, 3]) < min_d for t in chosen):
                continue
            got.append(int(k))
            chosen.append(int(k))
        return got
    # the person's counts: 3-6 slipped, 6-12 chipped (3 shapes), 1-2 cracked, 1-2 missing; a few near the ridge
    ridge = take(lambda k: crs[k] <= 2, 4, 1.0)
    missing = take(lambda k: 2 <= crs[k] <= 5, 2, 1.8)
    cracked = take(lambda k: 3 <= crs[k] <= 6, 2, 1.4)
    slipped = ridge[:1] + take(lambda k: crs[k] >= 3, 4, 1.2)
    chipped = ridge[1:] + take(lambda k: True, 8, 0.8)
    # one chipped tile that the veranda camera sees from below (eave) so the second picture shows it too
    ev = np.where(vis_v & (bank == 1) & (crs == 7))[0]
    chip_v = []
    for k in ev[::3][:2]:
        chip_v.append(int(k))
    for k in missing:
        plan['variant'][k] = 5
    for k in cracked:
        plan['variant'][k] = 4
    for idx, k in enumerate(chipped[:9] + chip_v):
        plan['variant'][k] = 1 + (idx % 3)
    for k in slipped:
        plan['slip'][k] = rng.uniform(0.02, 0.05)
        plan['yaw'][k] = math.radians(rng.uniform(2, 4) * rng.choice([-1, 1]))
    # a slipped tile also tilts a little (lower end dips): stored in yaw's sign pattern, applied in the node group as pitch
    plan['lists'] = {'slipped': sorted(slipped), 'chipped': sorted(chipped[:9] + chip_v), 'cracked': sorted(cracked), 'missing': sorted(missing),
                     'near_ridge': sorted(ridge)}
    # ------------------------------------------------ per tile tone (0..1, mean 0.5): luminance std 0.02 .. 0.06 after the gain below
    tone = rng.normal(0.5, 0.21, n)
    tone += 0.05 * np.sin(col * 0.9 + bank * 2.0) + 0.04 * rng.normal(size=n) * (crs % 2)
    plan['tone'] = np.clip(tone, 0.02, 0.98).astype(np.float32)
    # ------------------------------------------------ moss blobs: valleys, last course at the eave, ridge. (size m, cu, cv)
    moss = np.zeros((n, 3), np.float32)
    lich = np.zeros((n, 3), np.float32)
    drip = np.zeros((n, 3), np.float32)
    for k in range(n):
        b, c, r = bank[k], col[k], crs[k]
        south = b == 1
        p = 0.0
        if r == 7:
            p = 0.62
        elif r == 0:
            p = 0.62
        elif r == 1:
            p = 0.34
        else:
            p = 0.19
        if not south:
            p *= 0.6
        if plan['variant'][k] == 5:
            p = 0
        if rng.random() < p:
            if r == 7:
                cu, cv = rng.uniform(0.05, 0.35), rng.choice([rng.uniform(0.05, 0.3), rng.uniform(0.7, 0.95)])
            elif r <= 1:
                cu, cv = rng.uniform(0.45, 0.8), rng.uniform(0.1, 0.9)
            else:
                cu, cv = rng.uniform(0.08, 0.55), rng.choice([rng.uniform(0.0, 0.22), rng.uniform(0.78, 1.0)])
            moss[k] = (rng.uniform(0.10, 0.165), cu, cv)
        q = 0.5 if south else 0.2
        if rng.random() < q and plan['variant'][k] != 5:
            lich[k] = (rng.uniform(0.055, 0.095), rng.uniform(0.08, 0.6), rng.uniform(0.1, 0.9))
    # drip stains: 8 of the 43 eave tiles of the south slope (hero side), spaced out, plus two faint ones next to them
    eave = [k for k in range(n) if bank[k] == 1 and crs[k] == 7 and -4.6 < x[k] < 5.6]
    cols = sorted(set(col[k] for k in eave))
    picks = []
    for c in cols[1::5][:8]:
        picks.append(c)
    for k in eave:
        if col[k] in picks:
            drip[k] = (rng.uniform(0.22, 0.42), rng.uniform(0.35, 0.65), 1.0)
    for k in eave:
        if col[k] in [pp + 2 for pp in picks[:3]]:
            drip[k] = (rng.uniform(0.12, 0.2), rng.uniform(0.35, 0.65), 0.45)
    plan['moss'], plan['lich'], plan['drip'] = moss, lich, drip
    plan['drip_tiles'] = [int(k) for k in np.where(drip[:, 0] > 0)[0]]
    return plan


# ------------------------------------------------------------------------------------------------- tile shapes
def _bm_proto():
    bm = bmesh.new()
    bm.from_mesh(bpy.data.objects[PROTO].data)
    return bm


def _cut(bm, co, no, keep_inner=True):
    geom = list(bm.verts) + list(bm.edges) + list(bm.faces)
    bmesh.ops.bisect_plane(bm, geom=geom, dist=1e-6, plane_co=co, plane_no=no,
                           clear_inner=not keep_inner, clear_outer=keep_inner)


def _close(bm):
    edges = [e for e in bm.edges if e.is_boundary]
    if edges:
        bmesh.ops.holes_fill(bm, edges=edges, sides=64)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)


def _jag(bm, amp, rng, only_new=True):
    """small irregular nudge of the vertices created by a cut so a break does not look machined"""
    for v in bm.verts:
        if not v.is_manifold or len(v.link_faces) >= 3:
            v.co += Vector((rng.uniform(-amp, amp), rng.uniform(-amp, amp), rng.uniform(-amp, amp) * 0.4))


def tile_uv(me, name='UVMap'):
    def fn(co, n):
        if n.z > 0.5:       # top: u along the tile (+Y), v across turned so the island is not mirrored
            return ((co.y + TL / 2) / TL, 1.0 - (co.x + TW / 2) / TW)
        if n.z < -0.5:
            return ((co.y + TL / 2) / TL, (co.x + TW / 2) / TW)
        # side faces get UV outside the 0..1 square (no marks there, no overlap with the top face)
        if abs(n.x) >= abs(n.y):
            return (2.5 + (co.y + TL / 2) / TL, 2.5 + co.z * 1.5)
        return (2.5 + co.z * 1.5, 2.5 + (co.x + TW / 2) / TW)
    set_uv(me, name, fn)


def make_variant_meshes(mat_tile, mat_under, seed=5):
    rng = np.random.default_rng(seed)
    out = []
    # 0 whole tile (copy of the prototype with a UV map)
    me0 = bpy.data.objects[PROTO].data.copy()
    me0.name = PFX + 'pan'
    tile_uv(me0)
    out.append(me0)
    # 1 corner chip: a 5 to 8 cm piece of the lower corner missing (two facets)
    bm = _bm_proto()
    sx = 1.0
    corner = Vector((sx * 0.155, -0.335, 0.0))
    n1 = Vector((sx * 0.80, -0.60, 0)).normalized()
    _cut(bm, corner - n1 * 0.055, n1, keep_inner=True)
    n2 = Vector((sx * 0.30, -0.95, 0)).normalized()
    _cut(bm, Vector((0.10, -0.335, 0)) - n2 * 0.035 + Vector((0, 0.01, 0)), n2, keep_inner=True)
    _close(bm)
    me = bpy.data.meshes.new(PFX + VAR_NAMES[1])
    bm.to_mesh(me)
    bm.free()
    out.append(me)
    # 2 groove: a V-shaped crack across the tile, a notch on one edge
    bm = _bm_proto()
    ang = math.radians(24)
    nrm = Vector((math.cos(ang), math.sin(ang), 0))
    for off in (-0.004, 0.0, 0.004):
        _cut_keep = list(bm.verts) + list(bm.edges) + list(bm.faces)
        bmesh.ops.bisect_plane(bm, geom=_cut_keep, dist=1e-6, plane_co=Vector((0, 0.05, 0)) + nrm * off, plane_no=nrm)
    bm.verts.ensure_lookup_table()
    for v in bm.verts:
        d = (Vector((v.co.x, v.co.y, 0)) - Vector((0, 0.05, 0))).dot(nrm)
        if any(f.normal.z > 0.3 for f in v.link_faces):
            if abs(d) < 1e-4:
                v.co.z -= 0.010
            elif abs(d) < 0.0045:
                v.co.z -= 0.004
    # the notch: cut one edge corner a little too
    n3 = Vector((-0.9, -0.3, 0)).normalized()
    _cut(bm, Vector((-0.155, 0.12, 0)) - n3 * 0.03, n3, keep_inner=True)
    _close(bm)
    me = bpy.data.meshes.new(PFX + VAR_NAMES[2])
    bm.to_mesh(me)
    bm.free()
    out.append(me)
    # 3 broken half: the lower half of the tile is gone with an uneven break line
    bm = _bm_proto()
    nb = Vector((0.12, -1.0, 0)).normalized()
    _cut(bm, Vector((0, 0.03, 0)), nb, keep_inner=True)
    nb2 = Vector((-0.6, -0.8, 0)).normalized()
    _cut(bm, Vector((-0.06, 0.11, 0)), nb2, keep_inner=True)
    _close(bm)
    me = bpy.data.meshes.new(PFX + VAR_NAMES[3])
    bm.to_mesh(me)
    bm.free()
    out.append(me)
    # 4 cracked in two: gap of 7 mm, the far half sunk a little and turned
    bm1 = _bm_proto()
    bm2 = _bm_proto()
    nc = Vector((math.cos(math.radians(14)), math.sin(math.radians(14)), 0))
    _cut(bm1, Vector((0, 0.02, 0)) - nc * 0.0035, nc, keep_inner=True)        # keep the side behind the plane
    _cut(bm2, Vector((0, 0.02, 0)) + nc * 0.0035, nc, keep_inner=False)       # keep the side in front of the plane
    for b_ in (bm1, bm2):
        _close(b_)
    rot = Matrix.Rotation(math.radians(1.6), 4, 'Y') @ Matrix.Rotation(math.radians(2.2), 4, 'Z')
    bmesh.ops.transform(bm2, matrix=rot, verts=bm2.verts)
    for v in bm2.verts:
        v.co.z -= 0.004
    me = bpy.data.meshes.new(PFX + VAR_NAMES[4])
    bm1.to_mesh(me)
    me2 = bpy.data.meshes.new('tmp')
    bm2.to_mesh(me2)
    bm1.free()
    bm2.free()
    bm = bmesh.new()
    bm.from_mesh(me)
    bm.from_mesh(me2)
    bm.to_mesh(me)
    bm.free()
    bpy.data.meshes.remove(me2)
    out.append(me)
    # 5 missing: dark underlay board under the gap (a slab a little lower than the tile)
    z0, z1 = -0.095, -0.075
    v = [(-0.145, -0.325, z0), (0.145, -0.325, z0), (0.145, 0.325, z0 - 0.05), (-0.145, 0.325, z0 - 0.05),
         (-0.145, -0.325, z1), (0.145, -0.325, z1), (0.145, 0.325, z1 - 0.05), (-0.145, 0.325, z1 - 0.05)]
    f = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    me = new_mesh(VAR_NAMES[5], v, f)
    out.append(me)
    for i, me in enumerate(out):
        for p in me.polygons:
            p.use_smooth = False
        if i > 0:
            me.materials.clear()
            me.materials.append(mat_under if i == 5 else mat_tile)
            tile_uv(me)
    out[0].materials.clear()
    out[0].materials.append(mat_tile)
    return out


# ------------------------------------------------------------------------------------------------- the table object
def make_table(M, plan):
    n = len(M)
    me = bpy.data.meshes.new(PFX + 'tile table')
    me.from_pydata([tuple(m[:3, 3]) for m in M], [], [])
    def add(name, typ, arr):
        a = me.attributes.new(name, typ, 'POINT')
        if typ == 'FLOAT_VECTOR':
            a.data.foreach_set('vector', np.asarray(arr, np.float32).ravel())
        elif typ == 'INT':
            a.data.foreach_set('value', np.asarray(arr, np.int32))
        else:
            a.data.foreach_set('value', np.asarray(arr, np.float32))
    add('variant', 'INT', plan['variant'])
    add('slip', 'FLOAT', plan['slip'])
    add('yaw', 'FLOAT', plan['yaw'])
    add('tone', 'FLOAT', plan['tone'])
    add('moss', 'FLOAT_VECTOR', plan['moss'])
    add('lich', 'FLOAT_VECTOR', plan['lich'])
    add('drip', 'FLOAT_VECTOR', plan['drip'])
    o = bpy.data.objects.new(PFX + 'tile table', me)
    tag(o, 'roof.tile')
    o.hide_render = True
    collection().objects.link(o)
    return o


# ------------------------------------------------------------------------------------------------- node group edits
def _find(nt, idname, pred=None):
    for n in nt.nodes:
        if n.bl_idname == idname and (pred is None or pred(n)):
            return n
    return None


def edit_bank(ng, offset, table_obj, var_objs, timber_mat=None):
    nt = ng
    nodes, links = nt.nodes, nt.links
    iop = _find(nt, 'GeometryNodeInstanceOnPoints')
    join = [n for n in nodes if n.bl_idname == 'GeometryNodeJoinGeometry' and any(l.from_node == iop for i in n.inputs for l in i.links)][0]
    for l in list(iop.outputs['Instances'].links):
        links.remove(l)
    x0, y0 = 2000, -300
    # global tile id = point index + bank offset
    idx = nnew(nt, 'GeometryNodeInputIndex', 'G6 index', (x0, y0))
    gid = nnew(nt, 'ShaderNodeMath', 'G6 gid', (x0 + 200, y0), operation='ADD')
    links.new(idx.outputs['Index'], gid.inputs[0])
    gid.inputs[1].default_value = float(offset)
    tab = nnew(nt, 'GeometryNodeObjectInfo', 'G6 table', (x0, y0 - 200), transform_space='ORIGINAL')
    tab.inputs['Object'].default_value = table_obj
    tab.inputs['As Instance'].default_value = False

    def sample(attr, dtype, key):
        s = nnew(nt, 'GeometryNodeSampleIndex', 'G6 sample ' + key, (x0 + 400, y0 - 100 * len(nodes) % 700), data_type=dtype, domain='POINT')
        na = nnew(nt, 'GeometryNodeInputNamedAttribute', 'G6 attr ' + key, (x0 + 200, y0 - 300), data_type=dtype)
        na.inputs['Name'].default_value = attr
        links.new(tab.outputs['Geometry'], s.inputs['Geometry'])
        links.new(na.outputs['Attribute'], sock(s.inputs, 'Value'))
        links.new(gid.outputs[0], s.inputs['Index'])
        return s.outputs[0]
    v_var = sample('variant', 'INT', 'variant')
    v_slip = sample('slip', 'FLOAT', 'slip')
    v_yaw = sample('yaw', 'FLOAT', 'yaw')
    v_tone = sample('tone', 'FLOAT', 'tone')
    v_moss = sample('moss', 'FLOAT_VECTOR', 'moss')
    v_lich = sample('lich', 'FLOAT_VECTOR', 'lich')
    v_drip = sample('drip', 'FLOAT_VECTOR', 'drip')
    # the six tile shapes as instances 0..5
    g2i = nnew(nt, 'GeometryNodeGeometryToInstance', 'G6 tile shapes', (x0 + 600, y0 + 300))
    for vo in reversed(var_objs):      # a multi-input socket reads its links in reverse: link last-to-first so instance 0 is the whole tile
        oi = nnew(nt, 'GeometryNodeObjectInfo', 'G6 shape ' + vo.name, (x0 + 400, y0 + 300), transform_space='ORIGINAL')
        oi.inputs['Object'].default_value = vo
        oi.inputs['As Instance'].default_value = True       # keep OBJECT instances: the material reads the instanced object's wk_* properties, as before
        links.new(oi.outputs['Geometry'], g2i.inputs['Geometry'])
    for l in list(iop.inputs['Instance'].links):
        links.remove(l)
    links.new(g2i.outputs['Instances'], iop.inputs['Instance'])
    iop.inputs['Pick Instance'].default_value = True
    links.new(v_var, iop.inputs['Instance Index'])
    # slip: along the tile (local Y, minus = down the slope) and a turn; chain on the instances
    cxy = nnew(nt, 'ShaderNodeCombineXYZ', 'G6 slip vec', (x0 + 800, y0))
    neg = nnew(nt, 'ShaderNodeMath', 'G6 neg slip', (x0 + 700, y0), operation='MULTIPLY')
    links.new(v_slip, neg.inputs[0])
    neg.inputs[1].default_value = -1.0
    links.new(neg.outputs[0], cxy.inputs['Y'])
    tr = nnew(nt, 'GeometryNodeTranslateInstances', 'G6 slip', (x0 + 1000, y0))
    links.new(iop.outputs['Instances'], tr.inputs['Instances'])
    links.new(cxy.outputs['Vector'], tr.inputs['Translation'])
    tr.inputs['Local Space'].default_value = True
    cz = nnew(nt, 'ShaderNodeCombineXYZ', 'G6 yaw vec', (x0 + 1000, y0 - 150))
    # a slipped tile also dips 1.5 degrees at its lower end: the pitch is a third of the yaw
    pitch = nnew(nt, 'ShaderNodeMath', 'G6 pitch', (x0 + 900, y0 - 150), operation='MULTIPLY')
    links.new(v_yaw, pitch.inputs[0])
    pitch.inputs[1].default_value = 0.45
    links.new(pitch.outputs[0], cz.inputs['X'])
    links.new(v_yaw, cz.inputs['Z'])
    e2r = nnew(nt, 'FunctionNodeEulerToRotation', 'G6 yaw rot', (x0 + 1150, y0 - 150))
    links.new(cz.outputs['Vector'], e2r.inputs['Euler'])
    ro = nnew(nt, 'GeometryNodeRotateInstances', 'G6 turn', (x0 + 1300, y0))
    links.new(tr.outputs['Instances'], ro.inputs['Instances'])
    links.new(e2r.outputs['Rotation'], ro.inputs['Rotation'])
    ro.inputs['Local Space'].default_value = True
    prev = ro.outputs['Instances']
    xx = x0 + 1500
    for name, dtype, v in (('tile_tone', 'FLOAT', v_tone), ('tile_moss', 'FLOAT_VECTOR', v_moss), ('tile_lich', 'FLOAT_VECTOR', v_lich),
                           ('tile_drip', 'FLOAT_VECTOR', v_drip)):
        st = nnew(nt, 'GeometryNodeStoreNamedAttribute', 'G6 store ' + name, (xx, y0), data_type=dtype, domain='INSTANCE')
        st.inputs['Name'].default_value = name
        links.new(prev, st.inputs['Geometry'])
        links.new(v, sock(st.inputs, 'Value'))
        prev = st.outputs['Geometry']
        xx += 200
    links.new(prev, join.inputs['Geometry'])
    if timber_mat is not None:
        for n in nodes:
            if n.bl_idname == 'GeometryNodeSetMaterial':
                m = n.inputs['Material'].default_value
                if m is not None and m.name == 'CT / Timber painterly surface':
                    n.inputs['Material'].default_value = timber_mat
    return ng


def install_groups(table_obj, var_objs, offsets, timber_mat=None):
    root = bpy.data.node_groups[G_ROOT].copy()
    root.name = PFX + 'Complete two-bank ceramic roof'
    banks = []
    for i, gname in enumerate(G_BANKS):
        b = bpy.data.node_groups[gname].copy()
        b.name = PFX + gname.replace('CT / ', '')
        edit_bank(b, offsets[i], table_obj, var_objs, timber_mat)
        banks.append(b)
    for n in root.nodes:
        if n.bl_idname == 'GeometryNodeGroup' and n.node_tree is not None:
            for i, gname in enumerate(G_BANKS):
                if n.node_tree.name == gname:
                    n.node_tree = banks[i]
    roof = bpy.data.objects[ROOF]
    mod = roof.modifiers[0]
    vals = {it.identifier: mod.properties.inputs[it.identifier]['value'] for it in mod.node_group.interface.items_tree
            if it.item_type == 'SOCKET' and it.in_out == 'INPUT' and it.identifier != 'Socket_0'}
    roof['g6_orig_group'] = mod.node_group.name
    mod.node_group = root
    for k, v in vals.items():
        mod.properties.inputs[k]['value'] = v
    return root, banks


def uninstall_groups():
    roof = bpy.data.objects[ROOF]
    if 'g6_orig_group' in roof.keys():
        mod = roof.modifiers[0]
        vals = {it.identifier: mod.properties.inputs[it.identifier]['value'] for it in mod.node_group.interface.items_tree
                if it.item_type == 'SOCKET' and it.in_out == 'INPUT' and it.identifier != 'Socket_0'}
        mod.node_group = bpy.data.node_groups[roof['g6_orig_group']]
        for k, v in vals.items():
            mod.properties.inputs[k]['value'] = v
        del roof['g6_orig_group']
    for ng in [g for g in bpy.data.node_groups if g.name.startswith(PFX)]:
        bpy.data.node_groups.remove(ng)


# ------------------------------------------------------------------------------------------------- the ceramic material
def build_ceramic(mat, attr_type='INSTANCER', normal_img=None, key='', debug=None):
    """Adds to a copy of CT / Ceramic painterly surface: tile tone, moss blobs, lichen flecks, drip stains (read from per-tile attributes),
    and the glaze normal map. Everything comes after the weathering kit's colour so the marks stay as drawn."""
    nt = mat.node_tree
    N = nt.nodes
    L = nt.links
    bsdf = [n for n in N if n.bl_idname == 'ShaderNodeBsdfPrincipled'][0]
    wk = N['WK wallgrowth']
    bump = N['Bump']
    base_in = wk.outputs['Colour']
    rough_in = wk.outputs['Roughness']
    X = -800
    A = {}
    for nm, out in (('tile_tone', 'Fac'), ('tile_moss', 'Vector'), ('tile_lich', 'Vector'), ('tile_drip', 'Vector')):
        a = nnew(nt, 'ShaderNodeAttribute', 'G6 ' + nm, (X, 600 - 120 * len(A)), attribute_type=attr_type, attribute_name=nm)
        A[nm] = a
    uv = nnew(nt, 'ShaderNodeUVMap', 'G6 UV', (X, 0), uv_map='UVMap')
    sep = nnew(nt, 'ShaderNodeSeparateXYZ', 'G6 uv sep', (X + 150, 0))
    L.new(uv.outputs['UV'], sep.inputs['Vector'])
    pu = math_node(nt, 'MULTIPLY', sep.outputs['X'], TL)
    pv = math_node(nt, 'MULTIPLY', sep.outputs['Y'], TW)
    P = nnew(nt, 'ShaderNodeCombineXYZ', 'G6 metres', (X + 400, 0))
    L.new(pu.outputs[0], P.inputs['X'])
    L.new(pv.outputs[0], P.inputs['Y'])
    oi = [n for n in N if n.bl_idname == 'ShaderNodeObjectInfo'][0]
    rnd = oi.outputs['Random']

    def sepv(a):
        s = nnew(nt, 'ShaderNodeSeparateXYZ', 'G6 sep')
        L.new(a.outputs['Vector'] if hasattr(a, 'outputs') and 'Vector' in a.outputs.keys() else a, s.inputs['Vector'])
        return s
    # ---- tone: gain 1 + (tone - 0.5) * 0.6, and a faint warm / cool tint
    tone = A['tile_tone'].outputs['Fac']
    gain = math_node(nt, 'ADD', math_node(nt, 'MULTIPLY', math_node(nt, 'SUBTRACT', tone, 0.5).outputs[0], 0.6).outputs[0], 1.0)
    tint = mix_rgb(nt, tone, (0.955, 0.99, 1.07, 1), (1.05, 1.0, 0.93, 1))
    c1 = vmath(nt, 'MULTIPLY', base_in, mix_out(tint))
    c1 = vmath(nt, 'SCALE', c1.outputs[0])
    L.new(gain.outputs[0], c1.inputs['Scale'])
    col = c1.outputs[0]
    # ---- moss blob
    ms = sepv(A['tile_moss'])
    size = ms.outputs['X']
    cen = nnew(nt, 'ShaderNodeCombineXYZ', 'G6 moss centre')
    L.new(math_node(nt, 'MULTIPLY', ms.outputs['Y'], TL).outputs[0], cen.inputs['X'])
    L.new(math_node(nt, 'MULTIPLY', ms.outputs['Z'], TW).outputs[0], cen.inputs['Y'])
    dist = vmath(nt, 'DISTANCE', P.outputs['Vector'], cen.outputs['Vector'])
    pn = vmath(nt, 'ADD', P.outputs['Vector'])
    off = nnew(nt, 'ShaderNodeCombineXYZ', 'G6 noise off')
    L.new(math_node(nt, 'MULTIPLY', rnd, 31.0).outputs[0], off.inputs['X'])
    L.new(math_node(nt, 'MULTIPLY', rnd, 17.0).outputs[0], off.inputs['Y'])
    L.new(off.outputs['Vector'], pn.inputs[1])
    noi = nnew(nt, 'ShaderNodeTexNoise', 'G6 blob noise', noise_dimensions='3D')
    noi.inputs['Scale'].default_value = 14.0
    noi.inputs['Detail'].default_value = 1.0
    noi.inputs['Roughness'].default_value = 0.5
    L.new(pn.outputs[0], noi.inputs['Vector'])
    warp = math_node(nt, 'ADD', math_node(nt, 'MULTIPLY', noi.outputs['Fac'], 0.55).outputs[0], 0.72)      # 0.72 .. 1.27
    dw = math_node(nt, 'MULTIPLY', dist.outputs['Value'], warp.outputs[0])
    q = math_node(nt, 'DIVIDE', dw.outputs[0], math_node(nt, 'MAXIMUM', size, 0.0001).outputs[0])
    edge_m = smoothstep_node(nt, q.outputs[0], 0.70, 1.0)
    mask = math_node(nt, 'SUBTRACT', 1.0, edge_m.outputs[0])
    rim = smoothstep_node(nt, q.outputs[0], 0.38, 0.8)
    top = smoothstep_node(nt, q.outputs[0], 0.5, 0.0)              # 1 in the middle
    mlit = hex_lin('#5b5827')
    mdark = hex_lin('#2a2d1c')
    mhigh = hex_lin('#7a742f')
    mc = mix_rgb(nt, rim.outputs[0], mlit, mdark)
    mc = mix_rgb(nt, math_node(nt, 'MULTIPLY', top.outputs[0], 0.7).outputs[0], mix_out(mc), mhigh)
    col = mix_out(mix_rgb(nt, math_node(nt, 'MULTIPLY', mask.outputs[0], 0.95).outputs[0], col, mix_out(mc)))
    # ---- lichen flecks: small pale dots inside a soft round cluster
    ls = sepv(A['tile_lich'])
    lcen = nnew(nt, 'ShaderNodeCombineXYZ', 'G6 lichen centre')
    L.new(math_node(nt, 'MULTIPLY', ls.outputs['Y'], TL).outputs[0], lcen.inputs['X'])
    L.new(math_node(nt, 'MULTIPLY', ls.outputs['Z'], TW).outputs[0], lcen.inputs['Y'])
    ld = vmath(nt, 'DISTANCE', P.outputs['Vector'], lcen.outputs['Vector'])
    lq = math_node(nt, 'DIVIDE', ld.outputs['Value'], math_node(nt, 'MAXIMUM', ls.outputs['X'], 0.0001).outputs[0])
    lclu = math_node(nt, 'SUBTRACT', 1.0, smoothstep_node(nt, lq.outputs[0], 0.55, 1.0).outputs[0])
    vor = nnew(nt, 'ShaderNodeTexVoronoi', 'G6 lichen dots', voronoi_dimensions='3D', feature='F1')
    vor.inputs['Scale'].default_value = 24.0
    vor.inputs['Randomness'].default_value = 1.0
    L.new(pn.outputs[0], vor.inputs['Vector'])
    ldots = math_node(nt, 'SUBTRACT', 1.0, smoothstep_node(nt, vor.outputs['Distance'], 0.30, 0.50).outputs[0])
    lmask = math_node(nt, 'MULTIPLY', ldots.outputs[0], lclu.outputs[0])
    col = mix_out(mix_rgb(nt, math_node(nt, 'MULTIPLY', lmask.outputs[0], 0.88).outputs[0], col, hex_lin('#b8a47c')))
    # ---- drip stain from the lower tile end, a soft tapering tongue (u small = lower end)
    ds = sepv(A['tile_drip'])
    dlen = ds.outputs['X']
    dcv = math_node(nt, 'MULTIPLY', ds.outputs['Y'], TW)
    dv = math_node(nt, 'ABSOLUTE', math_node(nt, 'SUBTRACT', pv.outputs[0], dcv.outputs[0]).outputs[0])
    frac = math_node(nt, 'DIVIDE', pu.outputs[0], math_node(nt, 'MAXIMUM', dlen, 0.0001).outputs[0], clamp=True)
    wid = math_node(nt, 'MULTIPLY', math_node(nt, 'SUBTRACT', 1.0, math_node(nt, 'MULTIPLY', frac.outputs[0], 0.55).outputs[0]).outputs[0], 0.058)
    across = math_node(nt, 'SUBTRACT', 1.0, smoothstep_node(nt, math_node(nt, 'DIVIDE', dv.outputs[0], math_node(nt, 'MAXIMUM', wid.outputs[0], 0.0001).outputs[0]).outputs[0], 0.5, 1.0).outputs[0])
    along = math_node(nt, 'SUBTRACT', 1.0, smoothstep_node(nt, frac.outputs[0], 0.72, 1.0).outputs[0])
    dmask = math_node(nt, 'MULTIPLY', math_node(nt, 'MULTIPLY', across.outputs[0], along.outputs[0]).outputs[0], ds.outputs['Z'])
    has = math_node(nt, 'GREATER_THAN', dlen, 0.001)
    dmask = math_node(nt, 'MULTIPLY', dmask.outputs[0], has.outputs[0])
    col = mix_out(mix_rgb(nt, math_node(nt, 'MULTIPLY', dmask.outputs[0], 0.92).outputs[0], col, hex_lin('#26242f')))
    L.new(col, bsdf.inputs['Base Color'])
    if debug:
        if debug == 'masks':
            cmbd = nnew(nt, 'ShaderNodeCombineXYZ', 'G6 debug masks')
            for ax, mk in (('X', mask), ('Y', lmask), ('Z', dmask)):
                L.new(math_node(nt, 'ADD', math_node(nt, 'MULTIPLY', mk.outputs[0], 0.94).outputs[0], 0.04).outputs[0], cmbd.inputs[ax])
            for nm_ in ('Base Color', 'Specular IOR Level', 'Coat Weight', 'Metallic'):
                for l in list(bsdf.inputs[nm_].links):
                    nt.links.remove(l)
            bsdf.inputs['Specular IOR Level'].default_value = 0.0
            bsdf.inputs['Coat Weight'].default_value = 0.0
            bsdf.inputs['Metallic'].default_value = 0.0
            bsdf.inputs['Base Color'].default_value = (0, 0, 0, 1)
            L.new(cmbd.outputs['Vector'], bsdf.inputs['Emission Color'])
            bsdf.inputs['Emission Strength'].default_value = 1.0
            debug = None
    if debug:
        dd = {'moss': mask.outputs[0], 'lich': lmask.outputs[0], 'drip': dmask.outputs[0], 'tone': tone, 'moss_size': size, 'q': q.outputs[0]}
        g = dd[debug]
        cmbd = nnew(nt, 'ShaderNodeCombineXYZ', 'G6 debug')
        for ax in ('X', 'Y', 'Z'):
            L.new(g, cmbd.inputs[ax])
        L.new(cmbd.outputs['Vector'], bsdf.inputs['Base Color'])
        L.new(cmbd.outputs['Vector'], bsdf.inputs['Emission Color'])
        bsdf.inputs['Emission Strength'].default_value = 1.0
    # ---- roughness: moss is matt
    rmix = nnew(nt, 'ShaderNodeMix', 'G6 rough mix', data_type='FLOAT')
    L.new(mask.outputs[0], sid(rmix.inputs, 'Factor_Float'))
    L.new(rough_in, sid(rmix.inputs, 'A_Float'))
    sid(rmix.inputs, 'B_Float').default_value = 0.95
    L.new(rmix.outputs['Result'] if rmix.outputs['Result'].enabled else [o for o in rmix.outputs if o.enabled][0], bsdf.inputs['Roughness'])
    # ---- normal: glaze normal map (tangent space, UVMap) -> soft bump of the moss -> the scan's bump (weaker) -> kit
    if normal_img is not None:
        mp = nnew(nt, 'ShaderNodeMapping', 'G6 NM mapping')
        mp.inputs['Scale'].default_value = (1.0, TW / TL, 1.0)
        offv = nnew(nt, 'ShaderNodeCombineXYZ', 'G6 NM offset')
        L.new(math_node(nt, 'MULTIPLY', rnd, 7.31).outputs[0], offv.inputs['X'])
        L.new(math_node(nt, 'MULTIPLY', rnd, 3.17).outputs[0], offv.inputs['Y'])
        L.new(offv.outputs['Vector'], mp.inputs['Location'])
        L.new(uv.outputs['UV'], mp.inputs['Vector'])
        tx = nnew(nt, 'ShaderNodeTexImage', 'G6 NM image')
        tx.image = normal_img
        tx.interpolation = 'Cubic'
        tx.extension = 'REPEAT'
        L.new(mp.outputs['Vector'], tx.inputs['Vector'])
        nm = nnew(nt, 'ShaderNodeNormalMap', 'G6 NM', space='TANGENT', uv_map='UVMap')
        nm.inputs['Strength'].default_value = 0.9
        L.new(tx.outputs['Color'], nm.inputs['Color'])
        bm2 = nnew(nt, 'ShaderNodeBump', 'G6 moss bump')
        bm2.inputs['Strength'].default_value = 0.55
        bm2.inputs['Distance'].default_value = 0.012
        L.new(mask.outputs[0], bm2.inputs['Height'])
        L.new(nm.outputs['Normal'], bm2.inputs['Normal'])
        L.new(bm2.outputs['Normal'], bump.inputs['Normal'])
        bump.inputs['Strength'].default_value = 0.22
    return mat


def make_underlay_material():
    m = bpy.data.materials.new(PFX + 'underlay')
    m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = hex_lin('#1f1c1a')
    b.inputs['Roughness'].default_value = 0.92
    return m


def test_uv_reaches_instances():
    """step 0: do the evaluated instances carry the prototype copy's UV map? returns counts"""
    dg = bpy.context.evaluated_depsgraph_get()
    have = miss = 0
    for inst in dg.object_instances:
        if inst.is_instance and inst.parent and inst.parent.name == ROOF:
            try:
                ok = len(inst.object.data.uv_layers) > 0 and inst.object.data.uv_layers[0].name == 'UVMap'
            except Exception:
                ok = False
            have += ok
            miss += (not ok)
    return have, miss


def add_uv_test(mat):
    """debug: show the tile UV as colour (red = u along the tile, green = v across, blue = checker) so a close-up proves every tile has the same UV"""
    nt = mat.node_tree
    bsdf = [n for n in nt.nodes if n.bl_idname == 'ShaderNodeBsdfPrincipled'][0]
    uv = nnew(nt, 'ShaderNodeUVMap', 'G6 UV test', uv_map='UVMap')
    sep = nnew(nt, 'ShaderNodeSeparateXYZ', 'G6 uv test sep')
    nt.links.new(uv.outputs['UV'], sep.inputs['Vector'])
    chk = nnew(nt, 'ShaderNodeTexChecker', 'G6 checker')
    chk.inputs['Scale'].default_value = 8.0
    chk.inputs['Color1'].default_value = (1, 1, 1, 1)
    chk.inputs['Color2'].default_value = (0, 0, 0, 1)
    nt.links.new(uv.outputs['UV'], chk.inputs['Vector'])
    cmb = nnew(nt, 'ShaderNodeCombineXYZ', 'G6 uv test col')
    nt.links.new(sep.outputs['X'], cmb.inputs['X'])
    nt.links.new(sep.outputs['Y'], cmb.inputs['Y'])
    nt.links.new(chk.outputs['Fac'], cmb.inputs['Z'])
    nt.links.new(cmb.outputs['Vector'], bsdf.inputs['Base Color'])
    nt.links.new(cmb.outputs['Vector'], bsdf.inputs['Emission Color'])
    bsdf.inputs['Emission Strength'].default_value = 1.0
