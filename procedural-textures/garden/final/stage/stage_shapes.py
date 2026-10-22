# What this does (plain words): "stage_shapes" is builder 1 of the Japanese garden plan. It works on the ALREADY OPEN courtyard scene
# (astra-work/out/courtyard_final.blend, never saved over) and, in the plan's priority order:
#   1 repairs (bridge piers + stringers, corner boards, veranda steps, wall caps, plinth/deck z-fight, plaster inset, shoji bars, roof carried)
#   2 lantern rebuilt as one carved six-sided lantern with a hollow lit firebox      3 rocks, pond-edge stones, stepping stones: more unequal planes, buried
#   4 raked gravel court re-made (12 cm rake lines, rings round the rocks, kerb)       5 stepping stones re-laid in a zigzag
#   6 walls: slightly battered, real overhanging tile cap seated on the wall           7 water-basin set     8 shore stones
# It changes ONLY geometry and where parts sit (never materials of existing objects, never lights, world, camera, hills, plants, water).
# Use (inside Blender, scene already open):   import stage_shapes; report = stage_shapes.apply({'look': 'real'})   # or 'painted'
#   options: look 'real'|'painted' (only the rock treatment differs), seed (int), steps (list of step names, default all),
#            rake_period (m, default 0.12; adjusted by under 1 mm to fit the mesh), cells_per_period (mesh squares per rake line, 5), rake_height (m peak to trough, 0.015),
#            fix_open_room (default False: lowers the unowned 'Open room back' plane onto the floor), force (run again on a scene that already has our objects)
# Every new object gets garden_owner = 'shapes' and garden_role, sits in collection 'G1 shapes' and has one 'GARDEN placeholder <role>' material.
import math
import random
import time

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Quaternion, Vector, noise
from mathutils.bvhtree import BVHTree

OWNER = 'shapes'
STEPS = ['repairs', 'lantern', 'rocks', 'gravel', 'stepping', 'walls', 'basin', 'shore']
LOG = []


def say(text):
    LOG.append(text)
    print('[shapes] ' + text, flush=True)


# ------------------------------------------------------------------------------------------------ small helpers
def smoothstep(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def collection(name):
    col = bpy.data.collections.get(name)
    if col is None:
        col = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(col)
    return col


def placeholder_material(role):
    """One plain grey-brown stand-in per role; builder 3 (surfaces) replaces it. Real nodes so every renderer shows the same plain colour."""
    name = 'GARDEN placeholder ' + role
    mat = bpy.data.materials.get(name)
    if mat is None:
        mat = bpy.data.materials.new(name)
        col = {'stone.natural': (0.36, 0.35, 0.32, 1), 'stone.dressed': (0.40, 0.40, 0.38, 1), 'timber.frame': (0.13, 0.08, 0.05, 1),
               'timber.deck': (0.30, 0.20, 0.14, 1), 'wall.cap': (0.03, 0.03, 0.035, 1), 'ground.gravel': (0.62, 0.60, 0.55, 1),
               'glow': (1.0, 0.6, 0.2, 1), 'growth': (0.2, 0.3, 0.08, 1), 'water': (0.03, 0.06, 0.06, 1)}.get(role, (0.5, 0.5, 0.5, 1))
        mat.diffuse_color = col
        b = mat.node_tree.nodes.get('Principled BSDF') if mat.node_tree else None
        if b is not None:
            b.inputs['Base Color'].default_value = col
            b.inputs['Roughness'].default_value = 0.9
    return mat


def tag(obj, role):
    obj['garden_owner'] = OWNER
    obj['garden_role'] = role
    return obj


def new_object(name, bm, role, material=None, smooth=False, parent_col=None):
    """A new mesh object from a bmesh, tagged for the weathering/surface stages and put in collection G1 shapes."""
    old = bpy.data.objects.get(name)
    if old is not None:                       # re-run safe: replace our own earlier object
        if old.get('garden_owner') == OWNER:
            bpy.data.objects.remove(old, do_unlink=True)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = smooth
    me.materials.append(material or placeholder_material(role))
    ob = bpy.data.objects.new(name, me)
    (parent_col or collection('G1 shapes')).objects.link(ob)
    return tag(ob, role)


def eval_mesh(obj, dg=None):
    dg = dg or bpy.context.evaluated_depsgraph_get()
    ev = obj.evaluated_get(dg)
    me = ev.to_mesh()
    return ev, me


def world_points(obj, dg=None):
    """All evaluated vertices of an object in world space as an (n,3) numpy array."""
    ev, me = eval_mesh(obj, dg)
    n = len(me.vertices)
    co = np.empty(n * 3, np.float64)
    me.vertices.foreach_get('co', co)
    ev.to_mesh_clear()
    co = co.reshape(-1, 3)
    m = np.array(obj.matrix_world)
    return co @ m[:3, :3].T + m[:3, 3]


def bbox(obj, dg=None):
    p = world_points(obj, dg)
    return p.min(axis=0), p.max(axis=0)


class Ground:
    """Ray-cast height of the receiving ground (not ours; read only)."""
    def __init__(self):
        dg = bpy.context.evaluated_depsgraph_get()
        self.obj = bpy.data.objects['Astra / Courtyard receiving ground']
        self.bvh = BVHTree.FromObject(self.obj, dg)

    def z(self, x, y, default=0.0):
        hit = self.bvh.ray_cast(Vector((x, y, 20.0)), Vector((0, 0, -1)))
        return hit[0].z if hit[0] is not None else default


def box_into(bm, center, size, rot=None):
    """Closed box (8 verts) centred at center, size (sx,sy,sz), optional 3x3/4x4 rotation. Returns the bmesh verts."""
    ret = bmesh.ops.create_cube(bm, size=1.0)
    m = Matrix.Translation(center) @ (rot.to_4x4() if rot is not None else Matrix.Identity(4)) @ Matrix.Diagonal((size[0], size[1], size[2], 1))
    bmesh.ops.transform(bm, matrix=m, verts=ret['verts'])
    return ret['verts']


def set_geometry(obj, bm, keep_materials=True, rest=True):
    """Replace an existing object's mesh by a bmesh (same mesh datablock, so material slots stay). Removes the add-on's geometry-nodes/bevel
    modifiers (their result is what we just baked) and keeps the custom attribute CT_rest (the stone material's coordinate) equal to the position."""
    me = obj.data
    mats = [m for m in me.materials]
    for m in list(obj.modifiers):
        obj.modifiers.remove(m)
    bm.to_mesh(me)
    bm.free()
    me.update()
    if keep_materials and not len(me.materials):
        for m in mats:
            me.materials.append(m)
    if rest:
        write_rest(me)
    return obj


def write_rest(me):
    """The add-on's stone materials read a point attribute called CT_rest as their texture coordinate. The add-on stores it normalised: x and y about
    -0.5..0.5, z 0..1 (position divided by the stone's size), so the pattern scales with the stone. Keep that convention for the reshaped mesh."""
    n = len(me.vertices)
    if n == 0:
        return
    co = np.empty(n * 3, np.float32)
    me.vertices.foreach_get('co', co)
    co = co.reshape(-1, 3)
    lo = co.min(axis=0)
    size = np.maximum(co.max(axis=0) - lo, 1e-6)
    rest = np.stack([co[:, 0] / size[0], co[:, 1] / size[1], (co[:, 2] - lo[2]) / size[2]], axis=1).astype(np.float32)
    att = me.attributes.get('CT_rest')
    if att is None:
        att = me.attributes.new('CT_rest', 'FLOAT_VECTOR', 'POINT')
    att.data.foreach_set('vector', rest.ravel())


def baked_bmesh(obj, dg=None):
    """The object's evaluated geometry (modifiers applied) as a new bmesh in the object's local space."""
    ev, me = eval_mesh(obj, dg)
    bm = bmesh.new()
    bm.from_mesh(me)
    ev.to_mesh_clear()
    return bm


# ------------------------------------------------------------------------------------------------ rock engine (planes cut off a solid)
def _boundary_loops(edges):
    """Group boundary edges into connected loops of vertices."""
    edges = list(edges)
    left = set(edges)
    loops = []
    while left:
        e = left.pop()
        grp = [e]
        stack = [e]
        while stack:
            cur = stack.pop()
            for v in cur.verts:
                for e2 in v.link_edges:
                    if e2 in left:
                        left.discard(e2)
                        grp.append(e2)
                        stack.append(e2)
        loops.append(grp)
    return loops


def cut_planes(bm, rng, target_faces, depth_rel, size, min_nz=-0.25, base_z=0.0, top_bias=0.0, max_loss=0.2, protect_base=0.04):
    """Chisel flat facets until the solid has about `target_faces` faces. Each cut: pick a random direction n (never pointing down under the base),
    sort the vertices by how far they reach along n, and put a plane between the k-th and (k+1)-th farthest vertex (k = 1..4), so exactly k corners
    are cut off and one new flat facet appears. Facets come out as polygons of very different sizes; a cap is never deeper than depth_rel[1] x size.
    The bottom (z < base_z + protect_base) is never cut. Stops at target_faces or when `max_loss` of the volume is gone. Returns the number of cuts."""
    made = 0
    vol0 = abs(bm.calc_volume())
    tries = 0
    ks = [1] * 9 + [2] * 5 + [3] * 3 + [4] * 2
    while len(bm.faces) < target_faces and tries < target_faces * 40:
        tries += 1
        if rng.random() < top_bias:
            n = Vector((rng.uniform(-0.5, 0.5), rng.uniform(-0.5, 0.5), 1.0)).normalized()
        else:
            n = Vector((rng.gauss(0, 1), rng.gauss(0, 1), rng.gauss(0, 1))).normalized()
        if n.z < min_nz:
            continue
        verts = sorted(bm.verts, key=lambda w: -w.co.dot(n))
        k = rng.choice(ks)
        h = [w.co.dot(n) for w in verts[:k + 2]]
        if verts[0].co.z < base_z + protect_base:
            continue
        gap = h[k - 1] - h[k]
        if gap < 0.004 * size:
            continue
        u = rng.uniform(0.2, 0.9)
        c = h[k - 1] - u * gap
        depth = h[0] - c
        if depth > depth_rel[1] * size or depth < depth_rel[0] * size:
            continue
        p = n * c
        if any(w.co.z < base_z + protect_base * 0.5 for w in verts[:k]):
            continue
        geom = bm.verts[:] + bm.edges[:] + bm.faces[:]
        bmesh.ops.bisect_plane(bm, geom=geom, dist=1e-6, plane_co=p, plane_no=n, clear_outer=True, clear_inner=False)
        bm.edges.ensure_lookup_table()
        boundary = [e for e in bm.edges if e.is_boundary]
        for loop in _boundary_loops(boundary):
            if len(loop) >= 3:
                bmesh.ops.contextual_create(bm, geom=loop)
        made += 1
        if abs(bm.calc_volume()) < (1.0 - max_loss) * vol0:
            break
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    return made


def clean(bm, dist=0.003):
    bmesh.ops.dissolve_degenerate(bm, dist=dist, edges=bm.edges[:])
    bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=dist * 0.3)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])


def wear_edges(bm, rng, width, min_angle=22.0, min_len=0.04):
    """Painted look: a narrow flat chamfer along the real edges (worn arris), no rounding."""
    bm.edges.ensure_lookup_table()
    edges = []
    for e in bm.edges:
        if len(e.link_faces) != 2 or e.calc_length() < min_len:
            continue
        ang = math.degrees(e.calc_face_angle(0.0))
        if ang > min_angle:
            edges.append(e)
    if not edges:
        return 0
    bmesh.ops.bevel(bm, geom=edges, offset=width, offset_type='OFFSET', segments=1, profile=0.5, affect='EDGES', clamp_overlap=True)
    return len(edges)


def soften_real(bm, rng, size, noise_amp, crease_angle=38.0, seed=0, levels=2):
    """Real look: bevel + Catmull-Clark smoothing that keeps only the big creases, then fine rock noise. Returns a new bmesh."""
    bm.edges.ensure_lookup_table()
    # small bevel on all convex edges first so subdivision does not collapse the corners
    es = [e for e in bm.edges if len(e.link_faces) == 2 and e.calc_length() > 0.03]
    if es:
        bmesh.ops.bevel(bm, geom=es, offset=min(0.02, size * 0.025), offset_type='OFFSET', segments=1, profile=0.5, affect='EDGES', clamp_overlap=True)
    me = bpy.data.meshes.new('tmp_rock')
    bm.to_mesh(me)
    bm.free()
    # creases on the large-angle edges
    cr = me.attributes.new('crease_edge', 'FLOAT', 'EDGE')
    vals = np.zeros(len(me.edges), np.float32)
    bm2 = bmesh.new()
    bm2.from_mesh(me)
    bm2.edges.ensure_lookup_table()
    for i, e in enumerate(bm2.edges):
        if len(e.link_faces) == 2 and e.calc_length() > 0.04:
            ang = math.degrees(e.calc_face_angle(0.0))
            vals[i] = 0.9 if ang > crease_angle else (0.35 if ang > 24 else 0.0)
    bm2.free()
    cr.data.foreach_set('value', vals)
    tmp = bpy.data.objects.new('tmp_rock', me)
    bpy.context.scene.collection.objects.link(tmp)
    sub = tmp.modifiers.new('sub', 'SUBSURF')
    sub.levels = levels
    sub.render_levels = levels
    sub.use_creases = True
    dg = bpy.context.evaluated_depsgraph_get()
    ev = tmp.evaluated_get(dg)
    em = ev.to_mesh()
    out = bmesh.new()
    out.from_mesh(em)
    ev.to_mesh_clear()
    bpy.context.scene.collection.objects.unlink(tmp)
    bpy.data.objects.remove(tmp)
    bpy.data.meshes.remove(me)
    out.verts.ensure_lookup_table()
    out.normal_update()
    off = Vector((rng.uniform(-50, 50), rng.uniform(-50, 50), rng.uniform(-50, 50)))
    f1 = 1.0 / max(0.12, size * 0.35)
    for v in out.verts:
        if v.co.z < 0.03:
            continue
        p = (v.co + off) * f1
        n1 = noise.fractal(p, 0.6, 2.0, 3, noise_basis='PERLIN_ORIGINAL')
        n2 = noise.noise(v.co * 10.0 + off, noise_basis='PERLIN_ORIGINAL')
        v.co += v.normal * (noise_amp * (n1 * 1.0 + 0.2 * n2))
    out.normal_update()
    return out


def stone_footprint_radius(bm):
    xs = [v.co.x for v in bm.verts]
    ys = [v.co.y for v in bm.verts]
    zs = [v.co.z for v in bm.verts]
    return (max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs))


def reshape_stone(obj, rng, look, target_faces, flat_top=False, depth_rel=(0.003, 0.08), dg=None, wear=1.0):
    """Bake the add-on stone and give it more, unequal planes. look 'painted': flat facets + narrow worn chamfers, flat shading, no smoothing.
    look 'real': facets softened and weathered, smooth shading with the big creases kept. Returns (L,W,H) of the new local bbox."""
    bm = baked_bmesh(obj, dg)
    sx, sy, sz = stone_footprint_radius(bm)
    size = (sx * sy * sz) ** (1 / 3)
    if look == 'real':
        target_faces = int(target_faces * 0.6)
    if flat_top:
        # keep a wide flat top: flatten the very top first, then cut mostly at the sides
        top = max(v.co.z for v in bm.verts)
        bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], dist=1e-6, plane_co=(0, 0, top - 0.004), plane_no=(0, 0, 1),
                               clear_outer=True, clear_inner=False)
        bm.edges.ensure_lookup_table()
        for loop in _boundary_loops([e for e in bm.edges if e.is_boundary]):
            if len(loop) >= 3:
                bmesh.ops.contextual_create(bm, geom=loop)
    cut_planes(bm, rng, target_faces, depth_rel, size, top_bias=0.0, min_nz=(0.05 if flat_top else -0.25), protect_base=0.04)
    clean(bm, dist=0.003)
    if look == 'painted':
        wear_edges(bm, rng, width=rng.uniform(0.007, 0.014) * wear * (0.5 + size), min_angle=24.0)
        clean(bm, dist=0.002)
        for f in bm.faces:
            f.smooth = False
    else:
        bm = soften_real(bm, rng, size, noise_amp=0.010 * (0.5 + size) * (0.5 if flat_top else 1.0), seed=rng.randrange(10 ** 6))
        for f in bm.faces:
            f.smooth = True
    sx, sy, sz = stone_footprint_radius(bm)
    set_geometry(obj, bm)
    obj['garden_shape_baked'] = look
    return sx, sy, sz


# ------------------------------------------------------------------------------------------------ context
class Ctx:
    def __init__(self, options):
        self.opt = options or {}
        self.look = self.opt.get('look', 'real')
        if self.look not in ('real', 'painted'):
            raise ValueError("options['look'] must be 'real' or 'painted'")
        self.seed = int(self.opt.get('seed', 4242))
        self.rng = random.Random(self.seed)
        self.ground = Ground()
        self.created = []
        self.changed = []
        self.notes = {}

    def sub_rng(self, name):
        return random.Random(self.seed * 7919 + sum(ord(c) * (i + 1) for i, c in enumerate(name)))


def obj_or_none(name):
    return bpy.data.objects.get(name)


def world_zrange(obj):
    p = world_points(obj)
    return float(p[:, 2].min()), float(p[:, 2].max()), p


def reseat_z(obj, ctx, bury=None, top_above=None, margin=0.03):
    """Move a stone straight up/down so that (a) `bury` of its height is under the ground at its centre, or (b) its top is `top_above` over the
    highest ground under it; and in both cases the bottom is below the lowest ground under its footprint (no gaps)."""
    zmin, zmax, p = world_zrange(obj)
    H = zmax - zmin
    low = p[p[:, 2] < zmin + 0.3 * H]
    gz = np.array([ctx.ground.z(x, y) for x, y in low[::max(1, len(low) // 40), :2]])
    g_c = ctx.ground.z(float(p[:, 0].mean()), float(p[:, 1].mean()))
    if bury is not None:
        target_bottom = min(g_c - bury * H, float(gz.min()) - margin)
        dz = target_bottom - zmin
    else:
        target_top = float(gz.max()) + top_above
        dz = target_top - zmax
        zmin2 = zmin + dz
        if zmin2 > float(gz.min()) - margin:
            dz -= zmin2 - (float(gz.min()) - margin)
    obj.location.z += dz
    return dz


def nudge_group(ctx, names, max_move=0.5, passes=40, gap=0.55, fixed=()):
    """Small push-aparts so stones do not sit on top of each other (never more than max_move from where they were)."""
    info = {}
    for n in names:
        ob = bpy.data.objects[n]
        p = world_points(ob)
        info[n] = dict(c=np.array([p[:, 0].mean(), p[:, 1].mean()]), r=0.25 * (np.ptp(p[:, 0]) + np.ptp(p[:, 1])), c0=np.array([p[:, 0].mean(), p[:, 1].mean()]))
    for _ in range(passes):
        for i, a in enumerate(names):
            for b in names[i + 1:]:
                d = info[b]['c'] - info[a]['c']
                dist = float(np.hypot(*d)) + 1e-9
                want = (info[a]['r'] + info[b]['r']) * gap
                if dist < want:
                    push = (want - dist) * 0.5 * d / dist
                    if a not in fixed:
                        info[a]['c'] = info[a]['c'] - push
                    if b not in fixed:
                        info[b]['c'] = info[b]['c'] + push
        for n in names:
            off = info[n]['c'] - info[n]['c0']
            L = float(np.hypot(*off))
            if L > max_move:
                info[n]['c'] = info[n]['c0'] + off * max_move / L
    moved = {}
    for n in names:
        off = info[n]['c'] - info[n]['c0']
        if float(np.hypot(*off)) > 0.01:
            ob = bpy.data.objects[n]
            ob.location.x += off[0]
            ob.location.y += off[1]
            moved[n] = round(float(np.hypot(*off)), 2)
    bpy.context.view_layer.update()
    return moved



def bake_scaled(ob, sc):
    """Apply the add-on's modifiers once (bake), scale the baked solid by the vector sc about its base centre, keep material slots."""
    bm = baked_bmesh(ob, bpy.context.evaluated_depsgraph_get())
    bmesh.ops.scale(bm, vec=sc, verts=bm.verts[:])
    tmpme = bpy.data.meshes.new('tmp')
    bm.to_mesh(tmpme)
    bm.free()
    for m in list(ob.modifiers):
        ob.modifiers.remove(m)
    oldme = ob.data
    mats = list(oldme.materials)
    name = ob.name
    ob.data = tmpme
    for m in mats:
        tmpme.materials.append(m)
    bpy.data.meshes.remove(oldme)
    tmpme.name = name


def width_ratio(ob, ground):
    """(top width / base width) of the part standing out of the ground: widest xy extent in the top quarter over the bottom quarter of the visible height."""
    p = world_points(ob)
    gz = ground.z(float(p[:, 0].mean()), float(p[:, 1].mean()))
    zt = float(p[:, 2].max())
    vis = zt - gz
    if vis < 0.05:
        return 0.0, vis

    def w(lo, hi):
        q = p[(p[:, 2] >= lo) & (p[:, 2] <= hi)]
        return float(np.hypot(np.ptp(q[:, 0]), np.ptp(q[:, 1]))) if len(q) >= 3 else 0.0
    base = w(gz - 0.05, gz + 0.3 * vis)
    top = w(zt - 0.3 * vis, zt)
    return (top / base if base > 0 else 0.0), vis


def taper_if_needed(ob, ctx, limit=0.97):
    """No stone wider at the top than at the base: if it is, lean its upper half in (a gentle taper, repeated up to 3 times)."""
    r0, _ = width_ratio(ob, ctx.ground)
    n = 0
    r = r0
    while r > limit and n < 3:
        me = ob.data
        co = np.empty(len(me.vertices) * 3, np.float32)
        me.vertices.foreach_get('co', co)
        co = co.reshape(-1, 3)
        zmax = float(co[:, 2].max())
        zmid = 0.35 * zmax
        t = np.clip((co[:, 2] - zmid) / max(zmax - zmid, 1e-6), 0, 1)
        sc = 1.0 - 0.16 * t
        cx, cy = float(co[:, 0].mean()), float(co[:, 1].mean())
        co[:, 0] = cx + (co[:, 0] - cx) * sc
        co[:, 1] = cy + (co[:, 1] - cy) * sc
        me.vertices.foreach_set('co', co.ravel())
        me.update()
        write_rest(me)
        bpy.context.view_layer.update()
        r, _ = width_ratio(ob, ctx.ground)
        n += 1
    return r0, r


def step_rocks(ctx):
    look = ctx.look
    rocks = [f'Rock {i}' for i in range(5)] + [f'Gravel rock {i}' for i in range(3)]
    pond = [f'Pond edge stone {i}' for i in range(15)]
    rocks = [n for n in rocks if obj_or_none(n)]
    pond = [n for n in pond if obj_or_none(n)]
    moved = nudge_group(ctx, [n for n in rocks if n.startswith('Rock')] + pond, max_move=0.5, gap=0.62)
    say(f'rocks: nudged {len(moved)} stones (metres): {moved}')
    dg = bpy.context.evaluated_depsgraph_get()
    report = {}
    for n in rocks + pond:
        ob = bpy.data.objects[n]
        rng = ctx.sub_rng(n)
        # change yaw by up to ~14 degrees and size by up to 15 percent (decided before baking so it is part of the shape)
        yaw = rng.uniform(-0.25, 0.25)
        sc = Vector((rng.uniform(0.9, 1.12), rng.uniform(0.9, 1.12), rng.uniform(0.94, 1.1)))
        ob.rotation_mode = 'QUATERNION'
        ob.rotation_quaternion = Quaternion((0, 0, 1), yaw) @ ob.rotation_quaternion
        bpy.context.view_layer.update()
        cuts = 150 if n.startswith('Rock') else (120 if n.startswith('Gravel') else 105)
        bake_scaled(ob, sc)
        reshape_stone(ob, rng, look, cuts)
        tag(ob, 'stone.natural')
        if not n.startswith('Pond'):                       # pond-edge stones are already about half buried (55 percent) on the bank; the rocks were 22 percent
            reseat_z(ob, ctx, bury=0.34)
        bpy.context.view_layer.update()
        zmin, zmax, p = world_zrange(ob)
        g_c = ctx.ground.z(float(p[:, 0].mean()), float(p[:, 1].mean()))
        r0, r1 = taper_if_needed(ob, ctx)
        bpy.context.view_layer.update()
        zmin, zmax, p = world_zrange(ob)
        report[n] = dict(faces=len(ob.data.polygons), H=round(zmax - zmin, 2), buried=round((g_c - zmin) / (zmax - zmin), 2), top_over_base=(round(r0, 2), round(r1, 2)))
        ctx.changed.append(n)
    say('rocks: ' + ', '.join(f"{k} {v['faces']}f buried {int(v['buried'] * 100)}% top/base {v['top_over_base']}" for k, v in report.items()))
    ctx.notes['rocks'] = report



# ------------------------------------------------------------------------------------------------ step 1: repairs
def mesh_components(bm):
    seen = set()
    comps = []
    for v in bm.verts:
        if v.index in seen:
            continue
        stack = [v]
        comp = []
        while stack:
            a = stack.pop()
            if a.index in seen:
                continue
            seen.add(a.index)
            comp.append(a)
            for e in a.link_edges:
                stack.append(e.other_vert(a))
        comps.append(comp)
    return comps


def world_bvh(objs):
    verts, tris = [], []
    dg = bpy.context.evaluated_depsgraph_get()
    for ob in objs:
        ev = ob.evaluated_get(dg)
        me = ev.to_mesh()
        me.calc_loop_triangles()
        off = len(verts)
        verts += [ob.matrix_world @ v.co for v in me.vertices]
        tris += [tuple(off + i for i in t.vertices) for t in me.loop_triangles]
        ev.to_mesh_clear()
    return BVHTree.FromPolygons(verts, tris)


def roof_rows():
    """Lowest z of the roof tiles for each row of tiles (y rounded to 0.1 m): {y: zmin}. Read from the instanced tiles of 'Hall roof'."""
    dg = bpy.context.evaluated_depsgraph_get()
    roof = bpy.data.objects['Hall roof']
    rows = {}
    for inst in dg.object_instances:
        if inst.is_instance and inst.parent and inst.parent.original == roof:
            m = inst.matrix_world
            bb = [m @ Vector(c) for c in inst.object.bound_box]
            key = round(sum(b.y for b in bb) / 8, 1)
            rows[key] = min(rows.get(key, 99.0), min(b.z for b in bb))
    return rows


def bridge_numbers():
    """Measured gaps: pier top to whatever carries it (deck underside or stringer), like the add-on audit."""
    runs = [bpy.data.objects.get(f'Astra / varied planks.00{i}') for i in range(3, 8)]
    carriers = [o for o in runs if o] + [bpy.data.objects[n] for n in ('Bridge stringers',) if n in bpy.data.objects]
    bvh = world_bvh(carriers)
    out = {}
    for i in range(4):
        ob = bpy.data.objects[f'Bridge pier {i}']
        p = world_points(ob)
        top = float(p[:, 2].max())
        topv = p[p[:, 2] > top - 0.01]
        gaps = []
        for x, y, _ in topv[:: max(1, len(topv) // 24)]:
            hit = bvh.ray_cast(Vector((x, y, top - 0.02)), Vector((0, 0, 1)), 2.0)
            if hit[0] is not None:
                gaps.append(hit[0].z - top)
        out[f'pier {i}'] = None if not gaps else round(min(gaps), 3)
    return out


def snap_pier(obj, z_top):
    """Bake the add-on stone and make its top a flat plane at world z_top (cut down or stretched up), keeping the bottom where it is."""
    bm = baked_bmesh(obj)
    off = obj.location.z                       # piers are only turned about z, so world z = local z + object z
    top_local = z_top - off
    cur = max(v.co.z for v in bm.verts)
    if cur > top_local:
        bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], dist=1e-6, plane_co=(0, 0, top_local), plane_no=(0, 0, 1),
                               clear_outer=True, clear_inner=False)
        bm.edges.ensure_lookup_table()
        for loop in _boundary_loops([e for e in bm.edges if e.is_boundary]):
            if len(loop) >= 3:
                bmesh.ops.contextual_create(bm, geom=loop)
    else:
        for v in bm.verts:
            if v.co.z > cur - 0.05:
                v.co.z = top_local
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    for f in bm.faces:
        f.smooth = False
    set_geometry(obj, bm)
    tag(obj, 'stone.dressed')
    obj['garden_shape_baked'] = 'pier'


def clip_landing_boards(obj, strips, margin=0.0):
    """Trim the boards of a landing square so none sticks out of the corridor made by the two bridge runs (strips = [(A,B,halfwidth,ext)] in world xy)."""
    mw = obj.matrix_world
    inv = mw.inverted()
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.verts.ensure_lookup_table()

    def allowed(wx, wy):
        for (ax, ay), (bx, by), hw, ext in strips:
            dx, dy = bx - ax, by - ay
            L = math.hypot(dx, dy)
            ux, uy = dx / L, dy / L
            t = (wx - ax) * ux + (wy - ay) * uy
            s = -(wx - ax) * uy + (wy - ay) * ux
            if -ext <= t <= L + ext and abs(s) <= hw + margin:
                return True
        return False

    trimmed = 0
    removed = 0
    dead = []
    for comp in mesh_components(bm):
        xs = [v.co.x for v in comp]
        ys = [v.co.y for v in comp]
        yc = 0.5 * (min(ys) + max(ys))
        zc = 0.5 * (min(v.co.z for v in comp) + max(v.co.z for v in comp))
        x0, x1 = min(xs), max(xs)
        samples = np.linspace(x0, x1, int((x1 - x0) / 0.01) + 1)
        ok = [allowed(*(mw @ Vector((x, yc, zc)))[:2]) for x in samples]
        if not any(ok):
            dead.extend(comp)
            removed += 1
            continue
        # keep the contiguous allowed run that contains the allowed sample nearest the middle
        mid = min((abs(x), k) for k, x in enumerate(samples) if ok[k])[1]
        lo = mid
        while lo > 0 and ok[lo - 1]:
            lo -= 1
        hi = mid
        while hi < len(samples) - 1 and ok[hi + 1]:
            hi += 1
        nx0, nx1 = samples[lo], samples[hi]
        changed = False
        for v in comp:
            if v.co.x > nx1 + 1e-6:
                v.co.x = nx1
                changed = True
            elif v.co.x < nx0 - 1e-6:
                v.co.x = nx0
                changed = True
        trimmed += 1 if changed else 0
    if dead:
        bmesh.ops.delete(bm, geom=dead, context='VERTS')
    bm.to_mesh(obj.data)
    bm.free()
    obj.data.update()
    return trimmed, removed


def repair_bridge(ctx):
    nodes = [(-0.55, -0.6), (-2.0, 1.0), (-3.9, 0.15), (-5.95, 1.55)]
    before = bridge_numbers()
    runs = [bpy.data.objects[f'Astra / varied planks.00{i}'] for i in range(3, 6)]
    unders = []
    for ob in runs:
        p = world_points(ob)
        unders.append(float(p[:, 2].min()))
    # stringers: two beams under every run
    STR_H, STR_W = 0.09, 0.07
    bm = bmesh.new()
    for j, (a, b) in enumerate(zip(nodes, nodes[1:])):
        d = Vector((b[0] - a[0], b[1] - a[1], 0))
        L = d.length
        d.normalize()
        perp = Vector((-d.y, d.x, 0))
        yaw = math.atan2(d.y, d.x)
        rot = Matrix.Rotation(yaw, 3, 'Z')
        mid = Vector(((a[0] + b[0]) / 2, (a[1] + b[1]) / 2, 0))
        ztop = unders[j] + 0.004
        for s in (-0.2, 0.2):
            c = mid + perp * s
            c.z = ztop - STR_H / 2
            box_into(bm, c, (L + 0.44, STR_W, STR_H), rot)
    new_object('Bridge stringers', bm, 'timber.frame')
    bpy.context.view_layer.update()
    # piers: top plane just under the stringers they carry
    for i in range(4):
        inc = [j for j in (i - 1, i) if 0 <= j <= 2]
        z_top = max(unders[j] - STR_H for j in inc) + 0.004
        snap_pier(bpy.data.objects[f'Bridge pier {i}'], z_top)
        ctx.changed.append(f'Bridge pier {i}')
    # corner boards: trim the two landing squares to the width of the runs
    strips = [(nodes[j], nodes[j + 1], 0.525, 0.275) for j in range(3)]
    res = {}
    for n in ('Astra / varied planks.006', 'Astra / varied planks.007'):
        res[n] = clip_landing_boards(bpy.data.objects[n], strips, margin=0.01)
        ctx.changed.append(n)
    bpy.context.view_layer.update()
    after = bridge_numbers()
    ctx.created.append('Bridge stringers')
    say(f'repair bridge: pier gap to what carries it before {before} after {after} (m, negative = overlap); 6 stringers added; landing boards (trimmed, removed) {res}')
    ctx.notes['bridge_gap_before_after'] = (before, after)


def repair_steps(ctx):
    g = ctx.ground
    deck_top = 0.56
    up = bpy.data.objects['Veranda step']
    lo = bpy.data.objects['Veranda step, lower']
    before = {}
    for ob in (up, lo):
        p = world_points(ob)
        before[ob.name] = (round(float(p[:, 2].min()) - g.z(float(p[:, 0].mean()), float(p[:, 1].mean())), 3), round(float(p[:, 2].max()), 3))
    plinth_front = 4.70

    def rebuild(ob, top_z, back_y, width_scale=1.0):
        bm = baked_bmesh(ob)
        zs = [v.co.z for v in bm.verts]
        H0 = max(zs)
        # world z of the stone's base: sit 4 cm into the ground
        base_world = g.z(ob.location.x, ob.location.y) - 0.04
        Hn = top_z - base_world
        for v in bm.verts:
            v.co.z *= Hn / H0
            v.co.x *= width_scale
        ys = [v.co.y for v in bm.verts]
        set_geometry(ob, bm)
        ob.location.z = base_world
        ob.location.y += back_y - (ob.location.y + max(ys))
        tag(ob, 'stone.dressed')
    rebuild(up, 0.36, plinth_front + 0.02)
    p = world_points(up)
    front_up = float(p[:, 1].min())
    rebuild(lo, 0.17, front_up + 0.04, width_scale=1.45)
    bpy.context.view_layer.update()
    after = {}
    for ob in (up, lo):
        p = world_points(ob)
        after[ob.name] = (round(float(p[:, 2].min()) - g.z(float(p[:, 0].mean()), float(p[:, 1].mean())), 3), round(float(p[:, 2].max()), 3))
        ctx.changed.append(ob.name)
    say(f'repair steps: (lowest point over ground, top z) before {before} after {after}; upper step back now 2 cm into the plinth, deck top 0.56')
    ctx.notes['steps_before_after'] = (before, after)


def repair_caps(ctx):
    """Wall caps: seat the floating pieces down onto the wall tops (this is also what the 'walls' step rebuilds properly)."""
    out = {}
    for base in ('Back wall, left', 'Back wall, right', 'Right wall behind hall'):
        cap = bpy.data.objects.get(base + ' cap')
        wall = bpy.data.objects.get(base)
        if cap is None or wall is None or cap.get('garden_shape_baked') == 'cap':
            continue
        top = float(world_points(wall)[:, 2].max())
        bm = bmesh.new()
        bm.from_mesh(cap.data)
        comps = mesh_components(bm)
        zmins = [min(v.co.z for v in c) for c in comps]
        low = min(zmins)
        gap_before = round(sorted(zmins)[1] - top, 3) if len(zmins) > 1 else 0.0
        shift = None
        for c, z in zip(comps, zmins):
            if z > top + 0.01:
                shift = (z - top) if shift is None else shift
        if shift is not None:
            for c, z in zip(comps, zmins):
                if z > top + 0.01:
                    for v in c:
                        v.co.z -= shift
        bm.to_mesh(cap.data)
        bm.free()
        out[cap.name] = (gap_before, round(shift or 0.0, 3))
        tag(cap, 'wall.cap')
        ctx.changed.append(cap.name)
    say(f'repair caps: (gap before, moved down) {out}')


def repair_deck_and_plinth(ctx):
    n = 0
    for name in ('Astra / Planked run controls', 'Astra / Planked run controls.001', 'Astra / Planked run controls.002'):
        ob = bpy.data.objects.get(name)
        if ob is not None and not ob.get('garden_raised'):
            ob.location.z += 0.01
            ob['garden_raised'] = 1
            ctx.changed.append(name)
            n += 1
    for name in ('Astra / varied planks', 'Astra / varied planks.001', 'Astra / varied planks.002'):
        if name in bpy.data.objects:
            ctx.changed.append(name)
            tag(bpy.data.objects[name], 'timber.deck')
    pl = bpy.data.objects.get('Stone plinth')
    k = 0
    if pl is not None:
        for v in pl.data.vertices:
            if abs(v.co.x + 5.25) < 1e-4:
                v.co.x = -5.26
                k += 1
            elif abs(v.co.x - 5.65) < 1e-4:
                v.co.x = 5.66
                k += 1
        pl.data.update()
        tag(pl, 'stone.dressed')
        ctx.changed.append(pl.name)
    say(f'repair deck: {n} veranda plank runs raised 1 cm so their top is no longer in the plinth top plane, plinth made 1 cm longer at both ends ({k} corner points) so the plank ends no longer share its end planes (the coplanar faces)')


def repair_plaster(ctx):
    ob = bpy.data.objects['Hall plaster']
    me = ob.data
    n_top = n_bot = 0
    for v in me.vertices:
        if abs(v.co.z - 3.0) < 1e-4:
            v.co.z = 2.996
            n_top += 1
        elif abs(v.co.z - 0.55) < 1e-4:
            v.co.z = 0.547
            n_bot += 1
    me.update()
    tag(ob, 'wall.plaster')
    ctx.changed.append(ob.name)
    say(f'repair plaster: {n_top} top and {n_bot} bottom corner points of the hall plaster moved 4 mm and 3 mm so the plaster no longer shares planes with the posts')


def repair_shoji(ctx):
    """Shoji bars: the 368 coplanar faces came from rails and upright bars that end 1 mm from each other's planes. Rails keep touching the posts, become
    22 percent shallower and the top and bottom rails sit 3 mm in; the outermost upright bars move 2 mm inward so no face lies within 1 mm of another's plane."""
    ob = bpy.data.objects.get('Shoji bars')
    if ob is None or ob.get('garden_shoji_fixed'):
        return
    ob['garden_shoji_fixed'] = 1
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    comps = mesh_components(bm)
    rails, uprights = [], []
    for comp in comps:
        xs = [v.co.x for v in comp]
        zs = [v.co.z for v in comp]
        (rails if ((max(xs) - min(xs)) > 0.1 and (max(zs) - min(zs)) < 0.05) else uprights).append(comp)
    ends = [(min(v.co.x for v in c), max(v.co.x for v in c)) for c in rails]
    for comp in rails:
        ys = [v.co.y for v in comp]
        zs = [v.co.z for v in comp]
        yc = 0.5 * (min(ys) + max(ys))
        top_rail = max(zs) > 2.19
        bot_rail = min(zs) < 0.69
        for v in comp:
            v.co.y = yc + (v.co.y - yc) * 0.78
            if top_rail:
                v.co.z -= 0.003
            if bot_rail:
                v.co.z += 0.003
    moved = 0
    for comp in uprights:
        x0, x1 = min(v.co.x for v in comp), max(v.co.x for v in comp)
        dx = 0.0
        if any(abs(x0 - e0) < 0.0015 for e0, _ in ends):
            dx = 0.002
        elif any(abs(x1 - e1) < 0.0015 for _, e1 in ends):
            dx = -0.002
        if dx:
            for v in comp:
                v.co.x += dx
            moved += 1
    bm.to_mesh(ob.data)
    bm.free()
    ob.data.update()
    ctx.changed.append(ob.name)
    say(f'repair shoji: {len(rails)} rails made 22 percent shallower (top/bottom rails 3 mm in), {moved} outer upright bars moved 2 mm inward so no face lies within 1 mm of another bar\'s plane')


def repair_roof_frame(ctx):
    rows = roof_rows()
    front = sorted([(y, z) for y, z in rows.items() if y <= 7.2 + 1e-6])
    back = sorted([(y, z) for y, z in rows.items() if y >= 7.2 - 1e-6], reverse=True)
    posts_x = [-4.85, -2.325, 0.2, 2.725, 5.25]
    bm = bmesh.new()
    RW, RD = 0.06, 0.09

    def rafter(x, prof):
        top = [(x, y, z + 0.008) for y, z in prof]
        stations = []
        for (px, py, pz) in top:
            stations.append([bm.verts.new((px - RW / 2, py, pz)), bm.verts.new((px + RW / 2, py, pz)),
                             bm.verts.new((px + RW / 2, py, pz - RD)), bm.verts.new((px - RW / 2, py, pz - RD))])
        for a, b in zip(stations, stations[1:]):
            for k in range(4):
                k2 = (k + 1) % 4
                bm.faces.new((a[k], a[k2], b[k2], b[k]))
        bm.faces.new(list(reversed(stations[0])))
        bm.faces.new(stations[-1])

    xs = np.arange(-5.45, 5.95, 0.56)
    full = front + [(y, z) for y, z in sorted(back) if y > 7.2 + 1e-6]       # one continuous rafter over the ridge: front eave -> ridge -> back eave
    for x in xs:
        rafter(float(x), full)
    z_ridge = rows[7.2]
    # ridge beam, eave purlins, tie beams and king posts (all hidden under the tiles / inside the roof)
    box_into(bm, (0.2, 7.2, z_ridge - 0.05), (11.4, 0.16, 0.14))
    z51 = np.interp(5.85, [y for y, _ in front], [z for _, z in front])
    z96 = np.interp(9.7, [y for y, _ in sorted(back)], [z for _, z in sorted(back)])
    p1_lo, p1_hi = 3.235, z51 - RD + 0.012
    box_into(bm, (0.2, 5.85, 0.5 * (p1_lo + p1_hi)), (11.4, 0.14, p1_hi - p1_lo))
    p2_lo, p2_hi = 3.148, z96 - RD + 0.012
    box_into(bm, (0.2, 9.7, 0.5 * (p2_lo + p2_hi)), (11.4, 0.12, max(0.06, p2_hi - p2_lo)))
    for px in posts_x:
        box_into(bm, (px, 8.25, 3.07), (0.12, 3.75, 0.14))                    # tie beam from the front post row (y 6.4) to the rear posts (y 10.1)
        box_into(bm, (px, 7.2, 0.5 * (3.14 + z_ridge - 0.05) ), (0.13, 0.13, (z_ridge - 0.05) - 3.14 + 0.02))      # king post
    new_object('Roof carrying frame', bm, 'timber.frame')
    ctx.created.append('Roof carrying frame')
    # how close the roof now is to something that carries it
    bpy.context.view_layer.update()
    say(f'repair roof: hidden frame added (ridge beam, 2 purlins, {len(xs)} rafters, 5 tie beams, 5 king posts); tile rows used: {len(rows)}')


def repair_beams(ctx):
    """'Hall beams': the three deck-edge posts stop 4 cm under the eave beam they carry; raise their tops 5 mm into the beam."""
    ob = bpy.data.objects.get('Hall beams')
    if ob is None:
        return
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    n = 0
    for comp in mesh_components(bm):
        xs = [v.co.x for v in comp]
        ys = [v.co.y for v in comp]
        zs = [v.co.z for v in comp]
        if abs((max(xs) - min(xs)) - 0.19) < 0.01 and abs((max(ys) - min(ys)) - 0.19) < 0.01 and abs(max(zs) - 3.0) < 1e-3:
            for v in comp:
                if v.co.z > 2.9:
                    v.co.z = 3.045
            n += 1
    bm.to_mesh(ob.data)
    bm.free()
    ob.data.update()
    tag(ob, 'timber.frame')
    ctx.changed.append(ob.name)
    say(f'repair beams: {n} deck-edge posts raised 4.5 cm so they touch the eave beam above them (they stopped 4 cm short)')


def repair_open_room(ctx):
    """'Open room back' (the dim plane seen through the open shoji leaf) hung 12 cm above the floor; lower its bottom edge onto the floor."""
    ob = bpy.data.objects.get('Open room back')
    if ob is None or ob.get('garden_shape_baked'):
        return
    n = 0
    for v in ob.data.vertices:
        if abs(v.co.z - 0.67) < 1e-3:
            v.co.z = 0.548
            n += 1
    ob.data.update()
    ob['garden_shape_baked'] = 'floor'
    tag(ob, 'glow')
    ctx.changed.append(ob.name)
    say(f'repair open room: {n} bottom points of the dim back plane lowered from z 0.67 to the floor (0.548) so it no longer hangs in the air')


def step_repairs(ctx):
    repair_bridge(ctx)
    repair_steps(ctx)
    repair_caps(ctx)
    repair_deck_and_plinth(ctx)
    repair_plaster(ctx)
    repair_shoji(ctx)
    repair_beams(ctx)
    if ctx.opt.get('fix_open_room'):          # not in anybody's ownership list, so off unless asked for
        repair_open_room(ctx)
    repair_roof_frame(ctx)



# ------------------------------------------------------------------------------------------------ step 2: the lantern
def loft_rings(bm, rings, sides=6, yaw=0.0, center=(0.0, 0.0), radius_mode=False):
    """A solid built from rings [(r, z), ...] bottom to top, each ring a regular `sides`-gon (r = apothem, or circumradius when radius_mode), closed at both
    ends. Two rings with the same z make a flat shoulder. Returns the list of ring vertex lists."""
    cx, cy = center
    out = []
    for r, z in rings:
        rc = r if radius_mode else r / math.cos(math.pi / sides)
        out.append([bm.verts.new((cx + rc * math.cos(yaw + (k + 0.5) * math.tau / sides), cy + rc * math.sin(yaw + (k + 0.5) * math.tau / sides), z))
                    for k in range(sides)])
    for a, b in zip(out, out[1:]):
        for k in range(sides):
            k2 = (k + 1) % sides
            bm.faces.new((a[k], a[k2], b[k2], b[k]))
    bm.faces.new(list(reversed(out[0])))
    bm.faces.new(out[-1])
    return out


def boolean_difference(base_bm, cutter_bms):
    """base minus the cutters (exact solver), returns a new bmesh; temporary objects are removed again."""
    scn = bpy.context.scene
    objs = []

    def mk(bm, name):
        me = bpy.data.meshes.new(name)
        bm.to_mesh(me)
        ob = bpy.data.objects.new(name, me)
        scn.collection.objects.link(ob)
        objs.append(ob)
        return ob
    base = mk(base_bm, 'tmp_bool_base')
    for k, cb in enumerate(cutter_bms):
        c = mk(cb, f'tmp_bool_cut{k}')
        m = base.modifiers.new(f'b{k}', 'BOOLEAN')
        m.operation = 'DIFFERENCE'
        m.object = c
        m.solver = 'EXACT'
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    ev = base.evaluated_get(dg)
    me = ev.to_mesh()
    out = bmesh.new()
    out.from_mesh(me)
    ev.to_mesh_clear()
    for ob in objs:
        me = ob.data
        scn.collection.objects.unlink(ob)
        bpy.data.objects.remove(ob)
        bpy.data.meshes.remove(me)
    return out


def curled_roof(bm, rings, yaw, center, sides=6):
    """Hexagonal roof: rings = [(r_mid, r_corner, z_mid, z_corner)], bottom to top; 2*sides points per ring (flat centres and corners alternate)."""
    cx, cy = center
    built = []
    for r_mid, r_cor, z_mid, z_cor in rings:
        pts = []
        for k in range(sides):
            a_mid = yaw + k * math.tau / sides                      # direction of the flat's centre
            a_cor = a_mid + math.pi / sides                         # direction of the corner after it
            pts.append(bm.verts.new((cx + r_mid * math.cos(a_mid), cy + r_mid * math.sin(a_mid), z_mid)))
            pts.append(bm.verts.new((cx + r_cor * math.cos(a_cor), cy + r_cor * math.sin(a_cor), z_cor)))
        built.append(pts)
    n = 2 * sides
    for a, b in zip(built, built[1:]):
        for k in range(n):
            k2 = (k + 1) % n
            bm.faces.new((a[k], a[k2], b[k2], b[k]))
    bm.faces.new(list(reversed(built[0])))
    bm.faces.new(built[-1])


def step_lantern(ctx):
    LX, LY = 0.95, 1.1
    z0 = ctx.ground.z(LX, LY)
    yaw = math.radians(47.5)                       # flats face the hero camera and the veranda view (see the plan)
    names = ['Lantern base', 'Lantern post', 'Lantern gallery', 'Lantern firebox', 'Lantern cap', 'Lantern finial', 'Lantern window glow']
    old = {n: bpy.data.objects[n] for n in names}
    before = {n: world_points(old[n]) for n in names}

    def place(name, bm, rest=True, role='stone.dressed', smooth=False):
        ob = old[name]
        zmin = min(v.co.z for v in bm.verts)
        for v in bm.verts:
            v.co.x -= LX
            v.co.y -= LY
            v.co.z -= zmin
        for f in bm.faces:
            f.smooth = smooth
        for m in list(ob.modifiers):
            ob.modifiers.remove(m)
        ob.rotation_mode = 'QUATERNION'
        ob.rotation_quaternion = Quaternion()
        ob.scale = (1, 1, 1)
        ob.location = (LX, LY, zmin)
        set_geometry(ob, bm, rest=rest and ('CT_rest' in ob.data.attributes or ob.get('ct_component') == 'stone'))
        tag(ob, role)
        ob['garden_shape_baked'] = 'lantern'
        ctx.changed.append(name)

    # base (kiso): a low hexagonal slab and a smaller step on it
    bm = bmesh.new()
    loft_rings(bm, [(0.36, z0 - 0.05), (0.36, z0 + 0.09), (0.29, z0 + 0.09), (0.275, z0 + 0.17)], yaw=yaw, center=(LX, LY))
    place('Lantern base', bm)
    top_base = z0 + 0.17
    # post (sao): thick, slightly tapering, with a ring (takenotsu) at about 55 cm
    zb = top_base - 0.005
    bm = bmesh.new()
    loft_rings(bm, [(0.125, zb), (0.115, zb + 0.34), (0.15, zb + 0.35), (0.15, zb + 0.41), (0.115, zb + 0.42), (0.105, 0.955 + z0)], yaw=yaw, center=(LX, LY))
    place('Lantern post', bm)
    # gallery (nakadai): inverted-lotus flare under a hexagonal plate with a seat for the firebox
    zg = z0 + 0.95
    bm = bmesh.new()
    loft_rings(bm, [(0.10, zg), (0.20, zg + 0.05), (0.32, zg + 0.10), (0.34, zg + 0.115), (0.34, zg + 0.17), (0.31, zg + 0.18), (0.25, zg + 0.185), (0.25, zg + 0.235)],
               yaw=yaw, center=(LX, LY))
    place('Lantern gallery', bm)
    # firebox (hibukuro): hexagonal, hollow, an opening in two opposite flats
    zf = z0 + 1.18
    H = 0.38
    outer = bmesh.new()
    loft_rings(outer, [(0.215, zf), (0.215, zf + H)], yaw=yaw, center=(LX, LY))
    cav = bmesh.new()
    loft_rings(cav, [(0.168, zf + 0.055), (0.168, zf + H - 0.055)], yaw=yaw, center=(LX, LY))
    cutters = [cav]
    for k in (0, 3):
        ang = yaw + k * math.pi / 3
        n = Vector((math.cos(ang), math.sin(ang), 0))
        t = Vector((-n.y, n.x, 0))
        c = bmesh.new()
        rot = Matrix(((n.x, t.x, 0), (n.y, t.y, 0), (0, 0, 1)))
        box_into(c, Vector((LX, LY, zf + 0.20)) + n * 0.17, (0.30, 0.17, 0.19), rot)
        cutters.append(c)
    bm = boolean_difference(outer, cutters)
    outer.free()
    place('Lantern firebox', bm)
    # cap (kasa): hexagonal roof, corners curled up, thick lip, stepped top for the finial
    zc = zf + H - 0.005
    bm = bmesh.new()
    curled_roof(bm, [(0.20, 0.23, zc, zc), (0.31, 0.36, zc + 0.02, zc + 0.025), (0.47, 0.62, zc + 0.055, zc + 0.085), (0.47, 0.62, zc + 0.10, zc + 0.16),
                     (0.31, 0.40, zc + 0.18, zc + 0.215), (0.17, 0.20, zc + 0.245, zc + 0.265), (0.10, 0.115, zc + 0.275, zc + 0.275)], yaw=yaw, center=(LX, LY))
    place('Lantern cap', bm)
    zt = zc + 0.275
    # finial (hoju): collar, lotus bowl, onion jewel, point
    bm = bmesh.new()
    loft_rings(bm, [(0.075, zt - 0.012), (0.095, zt + 0.0), (0.095, zt + 0.02), (0.05, zt + 0.03), (0.065, zt + 0.05), (0.08, zt + 0.08), (0.075, zt + 0.115),
                    (0.05, zt + 0.15), (0.025, zt + 0.18), (0.006, zt + 0.205)], sides=10, yaw=yaw, center=(LX, LY), radius_mode=True)
    place('Lantern finial', bm, rest=False)
    # glow box: sits on the cavity floor, passes through both openings and stands 3 cm proud of the outside faces
    bm = bmesh.new()
    n = Vector((math.cos(yaw), math.sin(yaw), 0))
    t = Vector((-n.y, n.x, 0))
    rot = Matrix(((n.x, t.x, 0), (n.y, t.y, 0), (0, 0, 1)))
    box_into(bm, Vector((LX, LY, zf + 0.055 - 0.003 + 0.095)), (2 * 0.215 + 0.06, 0.145, 0.19), rot)
    place('Lantern window glow', bm, rest=False, role='glow')
    bpy.context.view_layer.update()
    after = {n: world_points(old[n]) for n in names}
    rep = {n: (round(float(after[n][:, 2].min()), 3), round(float(after[n][:, 2].max()), 3)) for n in names}
    say(f'lantern rebuilt (hexagonal, yaw 47.5 deg, hollow firebox with 2 openings, curled roof, finial); part z ranges: {rep}')
    ctx.notes['lantern_z'] = rep



# ------------------------------------------------------------------------------------------------ step 4: the raked gravel court
def hull_2d(points):
    pts = sorted(set((round(float(x), 4), round(float(y), 4)) for x, y in points))
    if len(pts) < 3:
        return pts

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lower = []
    for q in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], q) <= 0:
            lower.pop()
        lower.append(q)
    upper = []
    for q in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], q) <= 0:
            upper.pop()
        upper.append(q)
    return lower[:-1] + upper[:-1]


def dist_to_polygon(X, Y, poly):
    """Distance from points to a convex polygon (counter-clockwise list of (x,y)); 0 or negative inside."""
    n = len(poly)
    best = np.full(X.shape, 1e9)
    inside = np.ones(X.shape, bool)
    for k in range(n):
        ax, ay = poly[k]
        bx, by = poly[(k + 1) % n]
        dx, dy = bx - ax, by - ay
        L2 = dx * dx + dy * dy + 1e-12
        t = np.clip(((X - ax) * dx + (Y - ay) * dy) / L2, 0, 1)
        d = np.hypot(X - ax - t * dx, Y - ay - t * dy)
        best = np.minimum(best, d)
        inside &= ((X - ax) * dy - (Y - ay) * dx) >= 0          # left of every edge (counter-clockwise polygon)
    return np.where(inside, -best, best)


def dist_to_polyline(X, Y, pts):
    best = np.full(X.shape, 1e9)
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        dx, dy = bx - ax, by - ay
        L2 = dx * dx + dy * dy
        t = np.clip(((X - ax) * dx + (Y - ay) * dy) / L2, 0, 1)
        best = np.minimum(best, np.hypot(X - ax - t * dx, Y - ay - t * dy))
    return best


STEP_PATH = [(4.3, -5.6), (3.2, -3.1), (2.4, -1.0), (2.0, 0.9), (2.2, 2.8)]
COURT = (0.9, 9.1, -5.9, 1.9)            # x0, x1, y0, y1 of the raked court


def smooth01(t):
    t = np.clip(t, 0, 1)
    return t * t * (3 - 2 * t)


def step_gravel(ctx):
    period = float(ctx.opt.get('rake_period', 0.12))
    rake_h = float(ctx.opt.get('rake_height', 0.015))
    per_period = int(ctx.opt.get('cells_per_period', 5))              # mesh squares across one rake line (the plan asks for at least 4)
    obj = bpy.data.objects['Raked gravel court']
    old_faces = len(obj.data.polygons)
    x0, x1, y0, y1 = COURT
    nx = int(round((x1 - x0) / (period / per_period)))
    period = (x1 - x0) / nx * per_period                             # make the period fit the mesh exactly, so every line is sampled the same way
    cell = (x1 - x0) / nx
    ny = int(round((y1 - y0) / cell))
    xs = x0 + (np.arange(nx + 1)) * (x1 - x0) / nx
    ys = y0 + (np.arange(ny + 1)) * (y1 - y0) / ny
    X, Y = np.meshgrid(xs, ys)
    # rock footprints at the gravel: convex hull of everything within 25 cm over the gravel surface
    polys = []
    for n in ('Gravel rock 0', 'Gravel rock 1', 'Gravel rock 2'):
        ob = bpy.data.objects.get(n)
        if ob is None:
            continue
        p = world_points(ob)
        low = p[(p[:, 2] > 0.0) & (p[:, 2] < 0.3)]
        if len(low) < 6:
            low = p
        polys.append(hull_2d(low[:, :2]))
    d_rock = np.full(X.shape, 1e9)
    for poly in polys:
        d_rock = np.minimum(d_rock, dist_to_polygon(X, Y, poly))
    n_rings = 4
    d_ring = (n_rings + 0.5) * period
    ring_zone = d_rock < d_ring
    # straight lines (ridges run away from the camera, along y) with a few millimetres of wobble
    wob = 0.003 * np.sin(Y * 2 * math.pi / 0.9 + 0.7) + 0.002 * np.sin(Y * 2 * math.pi / 0.37 + 2.1)
    phase_line = (X - x0 + wob) / period
    phase_ring = d_rock / period + 0.25
    phase = np.where(ring_zone, phase_ring, phase_line)
    u = phase - np.floor(phase)
    dd = np.minimum(np.abs(u - 0.4), 1.0 - np.abs(u - 0.4))             # crest on the 3rd node of every 5, so every line has the same profile
    crest = np.clip(1.0 - 2.0 * dd, 0, 1) ** 1.35                        # pointed crest, broad flat-ish trough
    # a flat seam where the rings meet the straight lines (reads as the short cross-lines at the ends of the lines)
    seam = smooth01(np.abs(d_rock - d_ring) / 0.035)
    # keep the stepping-stone corridor flat, fade out at the court edge, no ridge under the rocks
    path = dist_to_polyline(X, Y, STEP_PATH)
    keep = smooth01((path - 0.5) / 0.25)
    edge = smooth01(np.minimum.reduce([X - x0, x1 - X, Y - y0, y1 - Y]) / 0.03)
    under_rock = smooth01((d_rock - 0.025) / 0.03)
    grain = 0.0012 * (np.sin(X * 83.0 + Y * 37.0) * np.sin(X * 29.0 - Y * 71.0))
    amp = rake_h
    Z = 0.02 + amp * crest * seam * keep * edge * under_rock * (1.0 + 0.04 * np.sin(Y * 11.0 + X * 3.0)) + grain * keep * edge
    verts = np.stack([X.ravel(), Y.ravel(), Z.ravel()], axis=1)
    idx = np.arange((nx + 1) * (ny + 1)).reshape(ny + 1, nx + 1)
    faces = np.stack([idx[:-1, :-1].ravel(), idx[:-1, 1:].ravel(), idx[1:, 1:].ravel(), idx[1:, :-1].ravel()], axis=1)
    me = bpy.data.meshes.new('Raked gravel court')
    me.vertices.add(len(verts))
    me.vertices.foreach_set('co', verts.astype(np.float32).ravel())
    me.loops.add(len(faces) * 4)
    me.loops.foreach_set('vertex_index', faces.ravel())
    me.polygons.add(len(faces))
    me.polygons.foreach_set('loop_start', np.arange(len(faces)) * 4)
    me.polygons.foreach_set('loop_total', np.full(len(faces), 4))
    me.update()
    me.validate()
    for pol in me.polygons:
        pol.use_smooth = True
    mats = list(obj.data.materials)
    oldme = obj.data
    obj.data = me
    for m in mats:
        me.materials.append(m)
    bpy.data.meshes.remove(oldme)
    me.name = 'Raked gravel court'
    tag(obj, 'ground.gravel')
    ctx.changed.append(obj.name)
    ridges = int((x1 - x0) / period)
    say(f'gravel: mesh {nx}x{ny} cells of {cell * 100:.1f} cm = {len(faces)} faces (was {old_faces}); rake lines every {period * 100:.0f} cm, {rake_h * 100:.1f} cm high, '
        f'about {ridges} lines across, {n_rings} rings round each of {len(polys)} rocks, flat corridor for the stepping stones')
    gravel_kerb(ctx)


def gravel_kerb(ctx):
    """Low stone kerb on the pond, front and hall sides of the court (open where the path crosses), low timber edge on the fence side."""
    look = ctx.look
    rng = random.Random(ctx.seed + 77)
    x0, x1, y0, y1 = COURT
    g = ctx.ground
    lantern = Vector((0.95, 1.1))
    bm = bmesh.new()
    n_stone = 0

    def near_path(px, py):
        return float(dist_to_polyline(np.array([px]), np.array([py]), STEP_PATH)[0]) < 0.62

    def edge_run(fixed, lo, hi, axis):
        nonlocal n_stone
        t = lo
        while t < hi - 0.05:
            L = rng.uniform(0.28, 0.5)
            L = min(L, hi - t)
            W = rng.uniform(0.10, 0.14)
            Hh = rng.uniform(0.06, 0.08)
            c = t + L / 2
            out = W / 2 + 0.004
            px, py = (fixed - out if axis == 'x' and fixed == x0 else fixed + out if axis == 'x' else c,
                      c if axis == 'x' else (fixed - out if fixed == y0 else fixed + out))
            skip = near_path(px, py) or (Vector((px, py)) - lantern).length < 0.52
            t += L + rng.uniform(0.008, 0.02)
            if skip:
                continue
            zb = g.z(px, py) - 0.035
            zt = 0.02 + 0.045 + rng.uniform(-0.006, 0.01)
            yaw = rng.uniform(-0.06, 0.06) + (math.pi / 2 if axis == 'x' else 0.0)
            vs = box_into(bm, (px, py, 0.5 * (zb + zt)), (L, W, zt - zb), Matrix.Rotation(yaw, 3, 'Z'))
            # irregular top: lift/drop the four top corners by a few millimetres
            for v in vs:
                if v.co.z > 0.5 * (zb + zt):
                    v.co.z += rng.uniform(-0.006, 0.006)
            n_stone += 1
    edge_run(x0, y0, y1, 'x')
    edge_run(y0, x0, x1, 'y')
    edge_run(y1, x0, x1, 'y')
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    bm.edges.ensure_lookup_table()
    es = [e for e in bm.edges if len(e.link_faces) == 2 and e.calc_length() > 0.03]
    if look == 'painted':
        bmesh.ops.bevel(bm, geom=es, offset=0.007, segments=1, profile=0.5, affect='EDGES', clamp_overlap=True)
    else:
        bmesh.ops.bevel(bm, geom=es, offset=0.009, segments=2, profile=0.5, affect='EDGES', clamp_overlap=True)
    ob = new_object('Gravel kerb', bm, 'stone.natural', smooth=(look == 'real'))
    if look == 'real':
        for e in ob.data.edges:
            e.use_edge_sharp = False
    ctx.created.append(ob.name)
    # timber edge along the fence side
    bm = bmesh.new()
    fx = x1 + 0.0375
    t = y0
    nb = 0
    while t < y1 - 0.05:
        L = min(rng.uniform(1.1, 1.6), y1 - t)
        zbot = g.z(fx, t + L / 2) - 0.02
        box_into(bm, (fx, t + L / 2, 0.5 * (zbot + 0.085)), (0.075, L - 0.008, 0.085 - zbot))
        t += L + 0.008
        nb += 1
    ob2 = new_object('Gravel timber edge', bm, 'timber.frame')
    ctx.created.append(ob2.name)
    say(f'gravel edge: {n_stone} kerb stones on the pond, front and hall sides (open where the path crosses, at the lantern), {nb} timber boards on the fence side')



# ------------------------------------------------------------------------------------------------ step 5: stepping stones
def path_point(s_len):
    """Point and unit direction on STEP_PATH at arc length s_len."""
    acc = 0.0
    for (ax, ay), (bx, by) in zip(STEP_PATH, STEP_PATH[1:]):
        L = math.hypot(bx - ax, by - ay)
        if s_len <= acc + L or (bx, by) == STEP_PATH[-1]:
            t = (s_len - acc) / L
            return Vector((ax + (bx - ax) * t, ay + (by - ay) * t)), Vector(((bx - ax) / L, (by - ay) / L))
        acc += L
    return Vector(STEP_PATH[-1]), Vector((0, 1))


def step_stepping(ctx):
    rng = random.Random(ctx.seed + 5)
    pitches = [0.5, 1.5, 2.55, 3.5, 4.45, 5.6, 6.65, 7.7]           # arc length of each stone's centre along the corridor (uneven, 0.95-1.15 m apart)
    offsets = [0.12, -0.2, 0.0, 0.22, -0.16, 0.2, -0.12, 0.1]        # sideways zigzag, metres
    sizes = [(0.66, 0.56), (0.7, 0.6), (0.98, 0.78), (0.64, 0.55), (0.72, 0.6), (0.62, 0.52), (0.7, 0.58), (0.76, 0.62)]    # index 2 is the big one at the turn
    out = []
    for i in range(8):
        ob = obj_or_none(f'Stepping stone {i}')
        if ob is None:
            continue
        c, d = path_point(pitches[i])
        perp = Vector((-d.y, d.x))
        pos = c + perp * offsets[i]
        L, W = sizes[i]
        yaw = math.atan2(d.y, d.x) + rng.uniform(-0.45, 0.45)
        bm = baked_bmesh(ob)
        sx, sy, sz = stone_footprint_radius(bm)
        bake_scaled(ob, Vector((L / sx, W / sy, 0.16 / sz)))
        reshape_stone(ob, ctx.sub_rng(ob.name), ctx.look, 70, flat_top=True, depth_rel=(0.004, 0.09), wear=0.8)
        ob.rotation_mode = 'QUATERNION'
        ob.rotation_quaternion = Quaternion((0, 0, 1), yaw)
        ob.location.x, ob.location.y = pos.x, pos.y
        bpy.context.view_layer.update()
        reseat_z(ob, ctx, top_above=rng.uniform(0.032, 0.058))
        bpy.context.view_layer.update()
        tag(ob, 'stone.natural')
        p = world_points(ob)
        gz = ctx.ground.z(pos.x, pos.y)
        out.append((ob.name, round(float(p[:, 2].max()) - gz, 3)))
        ctx.changed.append(ob.name)
    # check the 10 cm gap rule between neighbours (distance between footprints)
    hulls = [hull_2d(world_points(bpy.data.objects[f'Stepping stone {i}'])[:, :2]) for i in range(8) if obj_or_none(f'Stepping stone {i}')]
    gaps = []
    for a, b in zip(hulls, hulls[1:]):
        pa = np.array(a)
        d = dist_to_polygon(pa[:, 0], pa[:, 1], b)
        pb = np.array(b)
        d2 = dist_to_polygon(pb[:, 0], pb[:, 1], a)
        gaps.append(round(float(min(d.min(), d2.min())), 2))
    say(f'stepping stones re-laid in a zigzag (offsets {offsets}); top above ground (m): {out}; gaps between neighbours (m): {gaps}')
    ctx.notes['stepping'] = dict(tops=out, gaps=gaps)


# ------------------------------------------------------------------------------------------------ step 6: walls
def battered_wall(ob, axis, a0, a1, c, thickness, height, front_sign, batter_deg=3.5, sink=0.15):
    """Rebuild a plaster wall as a slightly battered box: top thickness `thickness` about the line `c` (axis 'x' = wall runs along x at y=c, 'y' = along y at x=c),
    wider at the base by `batter_deg` on both faces. a0..a1 = extent along the wall. Bottom sinks `sink` below z=0."""
    t = math.tan(math.radians(batter_deg))
    h = height
    off_top = thickness / 2
    off_bot = off_top + (h + sink) * t
    bm = bmesh.new()

    def P(a, off, z):
        return (a, c + off, z) if axis == 'x' else (c + off, a, z)
    ring_b = [bm.verts.new(P(a0, -off_bot, -sink)), bm.verts.new(P(a1, -off_bot, -sink)), bm.verts.new(P(a1, off_bot, -sink)), bm.verts.new(P(a0, off_bot, -sink))]
    ring_t = [bm.verts.new(P(a0, -off_top, h)), bm.verts.new(P(a1, -off_top, h)), bm.verts.new(P(a1, off_top, h)), bm.verts.new(P(a0, off_top, h))]
    for k in range(4):
        k2 = (k + 1) % 4
        bm.faces.new((ring_b[k], ring_b[k2], ring_t[k2], ring_t[k]))
    bm.faces.new(list(reversed(ring_b)))
    bm.faces.new(ring_t)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    me = ob.data
    bm.to_mesh(me)
    bm.free()
    me.update()
    for p in me.polygons:
        p.use_smooth = False
    return off_bot


def tile_cap(cap_ob, axis, a0, a1, c, z_top, wall_thickness):
    """A real wall cap: tiled gable on a base slab that overhangs the wall by 10 cm each side, eave strips, and a ridge row of half-round tiles; sits 1 cm into the wall."""
    over = 0.10
    hw = wall_thickness / 2 + over
    zb = z_top - 0.01
    prof = [(-hw, 0.0), (hw, 0.0), (hw, 0.05), (0.0, 0.05 + 0.095), (-hw, 0.05)]        # across the wall: (offset, height over zb)
    bm = bmesh.new()
    A0, A1 = a0 - 0.05, a1 + 0.05

    def P(a, off, z):
        return (a, c + off, z) if axis == 'x' else (c + off, a, z)
    vs0 = [bm.verts.new(P(A0, o, zb + h)) for o, h in prof]
    vs1 = [bm.verts.new(P(A1, o, zb + h)) for o, h in prof]
    n = len(prof)
    for k in range(n):
        k2 = (k + 1) % n
        bm.faces.new((vs0[k], vs1[k], vs1[k2], vs0[k2]))
    bm.faces.new(list(reversed(vs0)))
    bm.faces.new(vs1)
    # eave strips (the lower tile edge) on both sides
    for sgn in (-1, 1):
        o = sgn * (hw - 0.02)
        a_c = (A0 + A1) / 2
        ln = A1 - A0
        size = (ln, 0.04, 0.035) if axis == 'x' else (0.04, ln, 0.035)
        centre = (a_c, c + o, zb + 0.05 + 0.012) if axis == 'x' else (c + o, a_c, zb + 0.05 + 0.012)
        box_into(bm, centre, size)
    # ridge: half-round tiles 17 cm long with a 5 mm gap
    t = A0 + 0.02
    ridge_z = zb + 0.05 + 0.095
    while t < A1 - 0.1:
        Ltile = min(0.17, A1 - 0.02 - t)
        segs = 6
        ring = []
        for k in range(segs + 1):
            ang = math.pi * k / segs
            ring.append((0.06 * math.cos(ang), 0.06 * math.sin(ang)))
        v0 = [bm.verts.new(P(t, o, ridge_z - 0.012 + h)) for o, h in ring]
        v1 = [bm.verts.new(P(t + Ltile, o, ridge_z - 0.012 + h)) for o, h in ring]
        for k in range(segs):
            bm.faces.new((v0[k], v0[k + 1], v1[k + 1], v1[k]))
        bm.faces.new(list(reversed(v0)))
        bm.faces.new(v1)
        t += Ltile + 0.005
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    me = cap_ob.data
    bm.to_mesh(me)
    bm.free()
    me.update()
    for p in me.polygons:
        p.use_smooth = False
    cap_ob['garden_shape_baked'] = 'cap'


def step_walls(ctx):
    specs = [('Back wall, left', 'x', -10.4, -5.2, 10.5, 0.3, 2.1), ('Back wall, right', 'x', 5.6, 10.4, 10.5, 0.3, 2.1), ('Right wall behind hall', 'y', 1.4, 10.5, 10.4, 0.3, 2.2)]
    info = {}
    for name, axis, a0, a1, c, th, h in specs:
        wall = obj_or_none(name)
        cap = obj_or_none(name + ' cap')
        if wall is None:
            continue
        before = bbox(wall)
        off_bot = battered_wall(wall, axis, a0, a1, c, th, h, -1, batter_deg=3.5)
        tag(wall, 'wall.plaster')
        ctx.changed.append(name)
        if cap is not None:
            tile_cap(cap, axis, a0, a1, c, h, th)
            tag(cap, 'wall.cap')
            ctx.changed.append(cap.name)
        info[name] = dict(foot_thickness=round(2 * off_bot, 3), top_thickness=th)
    bpy.context.view_layer.update()
    gap = {}
    for name, *_ in specs:
        cap = obj_or_none(name + ' cap')
        wall = obj_or_none(name)
        if cap is None or wall is None:
            continue
        wt = float(world_points(wall)[:, 2].max())
        cb = world_points(cap)
        gap[cap.name] = round(float(cb[:, 2].min()) - wt, 3)
    say(f'walls: 3 walls rebuilt slightly battered (3.5 degrees each face; thickness top 0.30 m, foot {[v["foot_thickness"] for v in info.values()]}), garden face stays one flat plane; '
        f'tiled caps (gable, eave strips, half-round ridge tiles, 10 cm overhang) sit 1 cm into the wall: lowest cap point minus wall top = {gap}')
    ctx.notes['walls'] = info



# ------------------------------------------------------------------------------------------------ small natural stones (basin set, shore)
def rock_blob(rng, L, W, H, look, faces=60, flat_top=False, n_pts=18):
    """A new stone from scratch: convex hull of random points on an ellipsoid, then chiselled facets (painted) or softened (real). Bottom at z = 0.
    Returns a bmesh."""
    bm = bmesh.new()
    pts = []
    for _ in range(n_pts):
        v = Vector((rng.gauss(0, 1), rng.gauss(0, 1), rng.gauss(0, 1))).normalized()
        r = rng.uniform(0.86, 1.0)
        pts.append(bm.verts.new((v.x * L / 2 * r, v.y * W / 2 * r, v.z * H / 2 * r)))
    res = bmesh.ops.convex_hull(bm, input=pts, use_existing_faces=False)
    loose = [v for v in bm.verts if not v.link_faces]
    if loose:
        bmesh.ops.delete(bm, geom=loose, context='VERTS')
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    zmin = min(v.co.z for v in bm.verts)
    for v in bm.verts:
        v.co.z -= zmin
    size = (L * W * H) ** (1 / 3)
    if flat_top:
        top = max(v.co.z for v in bm.verts)
        bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], dist=1e-6, plane_co=(0, 0, top - 0.12 * H), plane_no=(0, 0, 1),
                               clear_outer=True, clear_inner=False)
        bm.edges.ensure_lookup_table()
        for loop in _boundary_loops([e for e in bm.edges if e.is_boundary]):
            if len(loop) >= 3:
                bmesh.ops.contextual_create(bm, geom=loop)
    cut_planes(bm, rng, faces, (0.003, 0.09), size, protect_base=0.0, min_nz=-0.6)
    clean(bm, dist=0.0015)
    if look == 'painted':
        wear_edges(bm, rng, width=0.004 + 0.01 * size, min_angle=26.0, min_len=0.02)
        clean(bm, dist=0.001)
        for f in bm.faces:
            f.smooth = False
    else:
        bm = soften_real(bm, rng, size, noise_amp=0.012 * size, seed=0, levels=1)
        for f in bm.faces:
            f.smooth = True
    stray = [v for v in bm.verts if not v.link_faces]
    if stray:
        bmesh.ops.delete(bm, geom=stray, context='VERTS')
    zmin = min(v.co.z for v in bm.verts)
    zmax = max(v.co.z for v in bm.verts)
    for v in bm.verts:
        v.co.z = (v.co.z - zmin) / max(zmax - zmin, 1e-6)           # unit height, bottom at 0
    return bm


def copy_into(dst, src, matrix):
    """Append a copy of bmesh src (transformed by matrix) to bmesh dst."""
    vmap = {}
    for v in src.verts:
        vmap[v] = dst.verts.new(matrix @ v.co)
    for f in src.faces:
        nf = dst.faces.new([vmap[v] for v in f.verts])
        nf.smooth = f.smooth


def pond_radius(x, y):
    """About 1.0 on the pond's edge, below 1 in the water (the same outline the original build script used)."""
    cx, cy, A, B, rot = -3.0, 1.0, 3.3, 2.5, math.radians(10)
    dx, dy = x - cx, y - cy
    u = dx * math.cos(-rot) - dy * math.sin(-rot)
    v = dx * math.sin(-rot) + dy * math.cos(-rot)
    th = math.atan2(v / B, u / A)
    wob = 1 + 0.10 * math.sin(3 * th + 0.8) + 0.06 * math.sin(5 * th + 2.1) + 0.04 * math.sin(2 * th)
    return math.hypot(u / A, v / B) / wob


# ------------------------------------------------------------------------------------------------ step 7: the water-basin set
def step_basin(ctx):
    rng = random.Random(ctx.seed + 9)
    look = ctx.look
    g = ctx.ground
    BX, BY = 4.4, 4.0
    gz = g.z(BX, BY)
    basin = bpy.data.objects['Water basin']
    water = bpy.data.objects['Basin water']
    # 1) the basin stone gets a real bowl (it was a solid block with the water buried in it)
    bm = baked_bmesh(basin)
    top_local = max(v.co.z for v in bm.verts)
    loc = basin.location.copy()
    rot = basin.rotation_quaternion.copy()
    bowl_r = 0.2
    cut = bmesh.new()
    bmesh.ops.create_cone(cut, cap_ends=True, cap_tris=False, segments=12, radius1=bowl_r, radius2=bowl_r, depth=0.30,
                          matrix=Matrix.Translation((0, 0, top_local - 0.13 + 0.15)))
    bm2 = boolean_difference(bm, [cut])
    cut.free()
    for f in bm2.faces:
        f.smooth = False
    set_geometry(basin, bm2)
    tag(basin, 'stone.dressed')
    ctx.changed.append(basin.name)
    bpy.context.view_layer.update()
    pw = world_points(basin)
    top_w = float(pw[:, 2].max())
    bowl_floor = top_w - 0.13
    # 2) the water: a disc filling the bowl up to 4 cm under the rim (a few mm wider than the bowl so no slit shows, bottom inside the floor)
    bmw = bmesh.new()
    cx, cy = float(pw[:, 0].mean()), float(pw[:, 1].mean())
    bmesh.ops.create_cone(bmw, cap_ends=True, cap_tris=False, segments=12, radius1=bowl_r + 0.004, radius2=bowl_r + 0.004, depth=(top_w - 0.04) - (bowl_floor - 0.01),
                          matrix=Matrix.Translation((cx, cy, 0.5 * ((top_w - 0.04) + (bowl_floor - 0.01)))))
    for m in list(water.modifiers):
        water.modifiers.remove(m)
    water.rotation_mode = 'QUATERNION'
    water.rotation_quaternion = Quaternion()
    water.location = (0, 0, 0)
    bmw.to_mesh(water.data)
    bmw.free()
    water.data.update()
    for pgn in water.data.polygons:
        pgn.use_smooth = False
    tag(water, 'water')
    ctx.changed.append(water.name)
    created = []
    # 3) stones around it: front stone (low, flat), candle stone (right), bucket stone (left)
    def put_stone(name, cx, cy, L, W, H, top_above, yaw, role='stone.dressed', faces=45, flat=True):
        bmx = rock_blob(rng, L, W, H, look, faces=faces, flat_top=flat)
        for v in bmx.verts:
            v.co.z *= H
        ob = new_object(name, bmx, role, smooth=(look == 'real'))
        ob.rotation_mode = 'QUATERNION'
        ob.rotation_quaternion = Quaternion((0, 0, 1), yaw)
        ob.location = (cx, cy, 0)
        bpy.context.view_layer.update()
        reseat_z(ob, ctx, top_above=top_above, margin=0.02)
        ctx.created.append(name)
        return ob
    put_stone('Basin front stone', BX - 0.02, BY - 0.58, 0.52, 0.34, 0.22, 0.075, 0.1)
    put_stone('Basin candle stone', BX + 0.62, BY - 0.02, 0.28, 0.27, 0.34, 0.24, 0.5, faces=40)
    put_stone('Basin bucket stone', BX - 0.62, BY + 0.0, 0.32, 0.3, 0.26, 0.15, -0.4, faces=40)
    # 4) drain pebbles round the foot of the basin and the front stone
    protos = [rock_blob(rng, 1.0, rng.uniform(0.7, 1.0), rng.uniform(0.5, 0.75), look, faces=26, n_pts=12) for _ in range(5)]
    bmp = bmesh.new()
    n = 0
    tries = 0
    placed = []
    while n < 150 and tries < 1200:
        tries += 1
        a = rng.uniform(0, math.tau)
        r = rng.uniform(0.34, 0.74)
        px, py = BX + r * math.cos(a) * 1.1, BY + r * math.sin(a) * 0.95
        if py > BY + 0.45:
            continue
        # keep off the three stones
        if math.hypot(px - (BX + 0.62), py - BY) < 0.21 or math.hypot(px - (BX - 0.62), py - BY) < 0.23 or (abs(px - BX) < 0.3 and abs(py - (BY - 0.58)) < 0.22):
            continue
        sz = rng.uniform(0.04, 0.085)
        if any(math.hypot(px - qx, py - qy) < 0.55 * (sz + qs) for qx, qy, qs in placed):
            continue
        placed.append((px, py, sz))
        zz = g.z(px, py) - 0.006 + rng.uniform(-0.004, 0.004)
        mtx = Matrix.Translation((px, py, zz)) @ Matrix.Rotation(rng.uniform(0, math.tau), 4, 'Z') @ Matrix.Diagonal((sz, sz * rng.uniform(0.8, 1.0), sz * rng.uniform(0.55, 0.8), 1))
        copy_into(bmp, rng.choice(protos), mtx)
        n += 1
    for pr in protos:
        pr.free()
    pob = new_object('Basin drain pebbles', bmp, 'stone.natural', smooth=(look == 'real'))
    ctx.created.append(pob.name)
    # 5) bamboo spout on a post behind the basin, and a ladle across the rim (existing bamboo material, nothing new)
    bamboo = bpy.data.materials.get('Bamboo stalk') or placeholder_material('growth')
    bm = bmesh.new()
    zpost = g.z(BX, BY + 0.62)
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=8, radius1=0.032, radius2=0.032, depth=0.78 + 0.05,
                          matrix=Matrix.Translation((BX, BY + 0.62, zpost - 0.05 + 0.415)))
    spout_z = top_w + 0.22
    a = Vector((BX, BY + 0.64, spout_z + 0.03))
    b = Vector((BX, BY + 0.14, spout_z - 0.045))
    d = b - a
    rotq = Vector((0, 0, 1)).rotation_difference(d.normalized()).to_matrix().to_4x4()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=8, radius1=0.025, radius2=0.025, depth=d.length, matrix=Matrix.Translation((a + b) / 2) @ rotq)
    sp = new_object('Basin bamboo spout', bm, 'growth', material=bamboo)
    ctx.created.append(sp.name)
    bm = bmesh.new()
    bvh_b = world_bvh([basin])
    rim = []
    for tt in np.linspace(0.0, 1.0, 14):
        px = (BX - 0.17) + tt * 0.44
        py = (BY - 0.12) + tt * 0.12
        hit = bvh_b.ray_cast(Vector((px, py, top_w + 0.5)), Vector((0, 0, -1)))
        if hit[0] is not None:
            rim.append(hit[0].z)
    lad_z = (max(rim) if rim else top_w) + 0.011 - 0.003
    hv = Vector((BX - 0.17, BY - 0.12, lad_z))
    hv2 = Vector((BX + 0.27, BY + 0.0, lad_z))
    dh = hv2 - hv
    rq = Vector((0, 0, 1)).rotation_difference(dh.normalized()).to_matrix().to_4x4()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=6, radius1=0.011, radius2=0.011, depth=dh.length, matrix=Matrix.Translation((hv + hv2) / 2) @ rq)
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=8, radius1=0.045, radius2=0.04, depth=0.075, matrix=Matrix.Translation((hv.x - 0.015, hv.y - 0.005, lad_z + 0.03)))
    ld = new_object('Basin ladle', bm, 'growth', material=bamboo)
    ctx.created.append(ld.name)
    say(f'basin set: bowl cut into the basin stone (water 4 cm under the rim), front stone, candle stone (right), bucket stone (left), {n} drain pebbles, bamboo spout on a post, ladle')


# ------------------------------------------------------------------------------------------------ step 8: shore stones
def step_shore(ctx):
    rng = random.Random(ctx.seed + 31)
    look = ctx.look
    g = ctx.ground
    water_z = -0.12
    existing = []
    for ob in bpy.data.objects:
        if ob.name.startswith(('Pond edge stone', 'Rock ', 'Bridge pier', 'Lantern base')) and ob.type == 'MESH':
            p = world_points(ob)
            existing.append((float(p[:, 0].mean()), float(p[:, 1].mean()), 0.25 * (np.ptp(p[:, 0]) + np.ptp(p[:, 1]))))
    protos = [rock_blob(rng, 1.0, rng.uniform(0.7, 1.0), rng.uniform(0.5, 0.8), look, faces=34, n_pts=12) for _ in range(6)]
    angles = np.linspace(0, math.tau, 72, endpoint=False)
    cand = []
    for th in angles:
        # walk out from the pond centre along th to the shoreline (where the bank rises through the water level)
        x, y = -3.0, 1.0
        dx, dy = math.cos(th), math.sin(th)
        for k in range(500):
            x += dx * 0.02
            y += dy * 0.02
            if g.z(x, y) >= water_z + 0.02 and pond_radius(x, y) > 0.8:
                break
        room = min(math.hypot(x - ex, y - ey) - er for ex, ey, er in existing)
        cand.append((room, th, x, y, g.z(x, y)))
    cand.sort(reverse=True)
    chosen = []
    for room, th, x, y, gzv in cand:
        if all(abs(math.remainder(th - o[0], math.tau)) > 0.5 for o in chosen):
            chosen.append((th, x, y, gzv))
        if len(chosen) >= 5:
            break
    bm = bmesh.new()
    n = 0
    for th, x, y, gzv in chosen:
        k = rng.randint(3, 5)
        for j in range(k):
            ox = x + rng.uniform(-0.32, 0.32)
            oy = y + rng.uniform(-0.32, 0.32)
            if not (0.7 <= pond_radius(ox, oy) <= 1.12) or min(math.hypot(ox - ex, oy - ey) - er for ex, ey, er in existing) < 0.0:
                continue
            Lx = rng.uniform(0.11, 0.3)
            sz = Lx * rng.uniform(0.6, 1.0)
            gzz = g.z(ox, oy)
            top = max(water_z, gzz) + rng.uniform(0.045, 0.13)           # always clearly over the water line or the bank under it
            bottom = gzz - 0.04
            hh = max(top - bottom, 0.07)
            proto = rng.choice(protos)
            mtx = (Matrix.Translation((ox, oy, bottom)) @ Matrix.Rotation(rng.uniform(0, math.tau), 4, 'Z') @ Matrix.Diagonal((Lx, Lx * rng.uniform(0.7, 1.0), hh, 1)))
            copy_into(bm, proto, mtx)
            n += 1
    for pr in protos:
        pr.free()
    ob = new_object('Shore stones', bm, 'stone.natural', smooth=(look == 'real'))
    ctx.created.append(ob.name)
    say(f'shore: {len(chosen)} groups, {n} small stones set into the water line (tops 4 to 13 cm over the water), one object')


def apply(options=None):
    t0 = time.time()
    ctx = Ctx(options)
    if any(o.get('garden_owner') == OWNER for o in bpy.data.objects) and not ctx.opt.get('force'):
        say('this scene already carries stage_shapes objects: nothing done (the stage is meant to run once on the starting file; pass {"force": True} to run again)')
        return {'look': ctx.look, 'changed': [], 'created': [], 'notes': {'skipped': True}, 'log': LOG}
    steps = ctx.opt.get('steps') or STEPS
    for s in steps:
        t = time.time()
        fn = globals().get('step_' + s)
        if fn is None:
            say(f'unknown step {s}')
            continue
        fn(ctx)
        say(f'step {s} done in {time.time() - t:.1f} s')
    changed = sorted(set(ctx.changed))
    created = sorted(set(ctx.created))
    say(f'REPORT created ({len(created)}): {created}')
    say(f'REPORT changed ({len(changed)}): {changed}')
    say('REPORT deleted (0): none (this stage deletes nothing; the add-on modifiers of the stones it reshaped are baked into their meshes)')
    say(f'stage_shapes done in {time.time() - t0:.1f} s, look={ctx.look}')
    return {'look': ctx.look, 'changed': changed, 'created': created, 'deleted': [], 'notes': ctx.notes, 'log': LOG}
