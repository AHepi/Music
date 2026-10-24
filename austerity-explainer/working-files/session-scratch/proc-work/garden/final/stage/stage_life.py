# What this does (plain words): "stage_life" is builder 2 (life) of the Japanese garden plan. It works on the ALREADY-OPEN courtyard scene
# (astra-work/out/courtyard_final.blend, possibly after stage_shapes) and changes only living things, the pond and the ground's shading:
#   1 maple      leaves 5-12 cm wide, 7 lobes, 5 shapes instanced with geometry nodes (about 56,000), colours deep red to orange to yellow-green and brown,
#                crown in layers with windows, dark inner mass in layers, woody twigs
#   2 ground     terrain and (real look) pebbles smooth-shaded; moss at the feet of stones, moss drifts on damp ground, tufts, pebble fringe by the
#                add-on's LIVE scatter (patched copy), keep-clear path, mottled moss colours
#   3 pond       see-through water (transmission, IOR 1.33, tint by depth), silt bed 0.32 m down with pebbles, lily stems, uneven lily pads, iris clumps
#   4 pine       flat needle pads in dark blue-green on the old limbs, small layered pads on new short limbs
#   5 shrubs     clipped round shrubs in groups of 2, 3 and 5, kept out of the lantern's line of sight
#   6 bamboo     two inside-out culms fixed, per-culm colours (clumps and fence), fewer smaller mixed-colour fallen leaves (none on the gravel)
# Use (inside Blender, scene already open):   import stage_life; report = stage_life.apply({'look': 'real'})      # or 'painted'
#   options: look 'real'|'painted'; steps (list from: maple ground pond pine shrubs bamboo; default all); seed (int); quick (True = about 6,000 leaves);
#            scatter (False = skip the add-on's live scatter); addon (folder of the PATCHED add-on copy; default ./addon_copy next to this file);
#            smooth_ground (default True: the ground is terrain, smooth-shaded in both looks; False keeps it flat-shaded in the painted look)
# Needs next to this file: astra_loader.py (unchanged copy) and addon_copy/ (the 0.2.1 add-on with the 3-line Blender 5.2 patch, 3.4 MB). Without them the
#   live scatter is skipped and everything else still runs. Safe to run twice (it removes what an earlier run made and rebuilds).
# Rules kept: every new object has garden_owner = 'life' and garden_role, and sits in collection "G2 life" (hidden source banks in "Life / ... sources").
#   Objects whose own materials must NOT be replaced by the surfaces stage also carry garden_keep_materials = 1. Nothing owned by another builder is
#   renamed, deleted or reshaped. Metres; x across, y away from the camera, z up. Blender 5.2.
import bpy, bmesh, math, os, sys, json, hashlib, random
import numpy as np
from mathutils import Vector, Matrix, Euler
from mathutils.bvhtree import BVHTree

sys.dont_write_bytecode = True
OWNER = 'life'
HERE = os.path.dirname(os.path.abspath(__file__))
ALL_STEPS = ['maple', 'ground', 'pond', 'pine', 'shrubs', 'bamboo']
WATER_Z = -0.12


# ------------------------------------------------------------------------------------------------ report and small helpers
class Stage:
    def __init__(self, options):
        o = dict(look='real', steps=None, addon=os.path.join(HERE, 'addon_copy'), seed=2026, quick=False, scatter=True)
        o.update(options or {})
        if o['look'] not in ('real', 'painted'):
            raise ValueError("look must be 'real' or 'painted'")
        self.o = o
        self.look = o['look']
        self.real = self.look == 'real'
        self.steps = list(o['steps'] or ALL_STEPS)
        self.seed = int(o['seed'])
        self.created, self.changed, self.deleted, self.notes, self.numbers = [], [], [], [], {}
        self.col = None
        self._bvh = None

    def say(self, text):
        self.notes.append(text)
        print('[life] ' + text, flush=True)

    # collections -----------------------------------------------------------------------------------------------
    def collection(self):
        if self.col is None:
            c = bpy.data.collections.get('G2 life')
            if c is None:
                c = bpy.data.collections.new('G2 life')
            if c.name not in bpy.context.scene.collection.children:
                bpy.context.scene.collection.children.link(c)
            self.col = c
        return self.col

    def tag(self, ob, role, keep_materials=False, extra=None):
        ob['garden_owner'] = OWNER
        ob['garden_role'] = role
        ob['garden_look'] = self.look
        if keep_materials:
            ob['garden_keep_materials'] = 1
        for k, v in (extra or {}).items():
            ob[k] = v
        return ob

    def new_object(self, name, data, role, keep_materials=False, collection=None):
        ob = bpy.data.objects.new(name, data)
        (collection or self.collection()).objects.link(ob)
        self.tag(ob, role, keep_materials)
        ob['life_created'] = 1
        self.created.append(name)
        return ob

    # ground ----------------------------------------------------------------------------------------------------
    def ground_bvh(self):
        if self._bvh is None:
            g = bpy.data.objects['Astra / Courtyard receiving ground']
            dg = bpy.context.evaluated_depsgraph_get()
            ev = g.evaluated_get(dg)
            me = ev.to_mesh()
            me.transform(g.matrix_world)
            me.calc_loop_triangles()
            vs = [v.co.copy() for v in me.vertices]
            fs = [tuple(t.vertices) for t in me.loop_triangles]
            self._bvh = BVHTree.FromPolygons(vs, fs, all_triangles=True)
            ev.to_mesh_clear()
        return self._bvh

    def ground_z(self, x, y):
        hit = self.ground_bvh().ray_cast(Vector((x, y, 30.0)), Vector((0, 0, -1)))
        return hit[0].z if hit[0] is not None else 0.0


def material(name, build=None):
    """Get or create a node material; build(m, nodes, links) is called on a cleared tree."""
    m = bpy.data.materials.get(name)
    if m is None:
        m = bpy.data.materials.new(name)
    m.use_nodes = True
    if build is not None:
        nt = m.node_tree
        nt.nodes.clear()
        build(m, nt.nodes, nt.links)
    return m


def principled_out(nodes, links, **vals):
    b = nodes.new('ShaderNodeBsdfPrincipled')
    for k, v in vals.items():
        key = k.replace('_', ' ')
        if key in b.inputs:
            b.inputs[key].default_value = v
    out = nodes.new('ShaderNodeOutputMaterial')
    links.new(b.outputs['BSDF'], out.inputs['Surface'])
    return b, out


def mesh_from_arrays(name, V, F, smooth=False, colors=None, mat=None, flat_sharp=False):
    """V (n,3) float array, F (m,k) int array of polygons with the same corner count (3 or 4). colors: (m,4) per face."""
    V = np.asarray(V, dtype=np.float32)
    F = np.asarray(F, dtype=np.int32)
    me = bpy.data.meshes.new(name)
    me.vertices.add(len(V))
    me.vertices.foreach_set('co', V.ravel())
    k = F.shape[1]
    me.polygons.add(len(F))
    me.loops.add(len(F) * k)
    me.loops.foreach_set('vertex_index', F.ravel())
    me.polygons.foreach_set('loop_start', np.arange(0, len(F) * k, k, dtype=np.int32))
    me.update(calc_edges=True)
    me.validate()
    me.polygons.foreach_set('use_smooth', np.full(len(F), bool(smooth)))
    if colors is not None:
        layer = me.color_attributes.new('Col', 'FLOAT_COLOR', 'CORNER')
        c = np.asarray(colors, dtype=np.float32)
        if c.ndim == 2 and c.shape[0] == len(F):
            c = np.repeat(c, k, axis=0)
        layer.data.foreach_set('color', c.ravel())
    if mat is not None:
        me.materials.append(mat)
    return me


def rotation_to_euler(normal, spin, ref=np.array([0.0, 0.0, 1.0])):
    """Matrix with local +Z along `normal`, then spun about it; returns an XYZ Euler as an array (n,3). Vectorised."""
    n = normal / np.linalg.norm(normal, axis=1, keepdims=True)
    a = np.where(np.abs(n[:, 2:3]) > 0.95, np.array([[1.0, 0.0, 0.0]]), np.array([[0.0, 0.0, 1.0]]))
    x = np.cross(a, n)
    x /= np.linalg.norm(x, axis=1, keepdims=True)
    y = np.cross(n, x)
    c, s = np.cos(spin)[:, None], np.sin(spin)[:, None]
    xs = x * c + y * s
    ys = -x * s + y * c
    R = np.stack([xs, ys, n], axis=2)          # columns are the new axes
    # XYZ Euler from rotation matrix (Blender: R = Rz * Ry * Rx)
    sy = -R[:, 2, 0]
    ey = np.arcsin(np.clip(sy, -1, 1))
    cy = np.cos(ey)
    ex = np.where(cy > 1e-6, np.arctan2(R[:, 2, 1], R[:, 2, 2]), np.arctan2(-R[:, 1, 2], R[:, 1, 1]))
    ez = np.where(cy > 1e-6, np.arctan2(R[:, 1, 0], R[:, 0, 0]), 0.0)
    return np.stack([ex, ey, ez], axis=1)


def point_cloud_object(st, name, P, attrs, role, material_obj=None, keep=False):
    """A vertices-only mesh with POINT attributes: attrs = {name: (type, array)} type FLOAT|INT|FLOAT_VECTOR."""
    me = bpy.data.meshes.new(name)
    me.vertices.add(len(P))
    me.vertices.foreach_set('co', np.asarray(P, dtype=np.float32).ravel())
    me.update()
    for k, (typ, arr) in attrs.items():
        a = me.attributes.new(name=k, type=typ, domain='POINT')
        arr = np.asarray(arr)
        if typ == 'FLOAT_VECTOR':
            a.data.foreach_set('vector', arr.astype(np.float32).ravel())
        elif typ == 'INT':
            a.data.foreach_set('value', arr.astype(np.int32).ravel())
        else:
            a.data.foreach_set('value', arr.astype(np.float32).ravel())
    return me


def smooth_noise(P, seed, freq=1.0, octaves=3):
    """A cheap smooth 3D noise in [-1, 1] at points P (n,3): sums of random plane waves."""
    r = np.random.default_rng(seed)
    out = np.zeros(len(P))
    amp = 1.0
    tot = 0.0
    for o in range(octaves):
        for _ in range(4):
            d = r.normal(size=3)
            d /= np.linalg.norm(d)
            out += amp * np.sin(P @ d * freq * (2.0 ** o) * 2.1 + r.uniform(0, 6.283))
            tot += amp
        amp *= 0.5
    return out / tot * 1.6


def remove_object_and_data(name, st=None):
    ob = bpy.data.objects.get(name)
    if ob is None:
        return
    data = ob.data
    bpy.data.objects.remove(ob, do_unlink=True)
    if data is not None and data.users == 0:
        if isinstance(data, bpy.types.Mesh):
            bpy.data.meshes.remove(data)
        elif isinstance(data, bpy.types.Curve):
            bpy.data.curves.remove(data)
    if st:
        st.deleted.append(name)


def remove_previous():
    """Idempotent re-run: remove what an earlier run of this stage created (objects tagged garden_owner=life that are NOT original)."""
    gone = []
    for ob in list(bpy.data.objects):
        if ob.get('garden_owner') == OWNER and ob.get('life_created') == 1:
            gone.append(ob.name)
            data = ob.data
            bpy.data.objects.remove(ob, do_unlink=True)
            if data is not None and data.users == 0:
                if isinstance(data, bpy.types.Mesh):
                    bpy.data.meshes.remove(data)
                elif isinstance(data, bpy.types.Curve):
                    bpy.data.curves.remove(data)
    for g in list(bpy.data.node_groups):
        if (g.name.startswith('Life / ') or g.name.startswith('Astra / Life / ')) and g.users == 0:
            bpy.data.node_groups.remove(g)
    return gone


# ------------------------------------------------------------------------------------------------ 1. MAPLE
# leaf colour stops (linear RGB): deep red -> red -> red-orange -> orange -> yellow-orange -> yellow-green -> brown
LEAF_STOPS = [(0.00, (0.17, 0.006, 0.010)), (0.16, (0.42, 0.018, 0.014)), (0.34, (0.72, 0.055, 0.016)),
              (0.55, (0.90, 0.17, 0.026)), (0.72, (0.92, 0.38, 0.045)), (0.86, (0.42, 0.46, 0.06)), (1.00, (0.20, 0.09, 0.03))]


def leaf_mesh_arrays(look, variant, nlobes):
    """One maple leaf in its own frame: base at the origin, centre lobe along +Y, unit lobe length 1, in the XY plane.
    Returns vertices (n,3) and triangles (m,3). Real: serrated, cupped. Painted: each lobe two flat folded planes, no serration."""
    rng = np.random.default_rng(100 + variant * 7 + (0 if look == 'real' else 500))
    spread = math.radians(236 if nlobes >= 7 else 190)
    angs = np.linspace(-spread / 2, spread / 2, nlobes)
    delta = angs[1] - angs[0]
    t = np.abs(angs) / (spread / 2)
    L = (1.0 - 0.40 * t ** 1.6) * (1 + rng.uniform(-0.06, 0.06, nlobes))
    if look == 'real':
        seq = [(-0.32, 0.52), (-0.17, 0.78), (0.0, 1.0), (0.17, 0.78), (0.32, 0.52)]
        jit_a, jit_r = 0.02, 0.06
    else:
        seq = [(-0.28, 0.55), (0.0, 1.0), (0.28, 0.55)]
        jit_a, jit_r = 0.04, 0.12
    pts, tip = [], []                                        # outline in order of polar angle: (angle, radius), is_tip
    pts.append((angs[0] - 0.5 * delta, 0.30 * L[0])); tip.append(False)
    for k in range(nlobes):
        for f, fr in seq:
            pts.append((angs[k] + (f + rng.uniform(-jit_a, jit_a)) * delta, fr * L[k] * (1 + rng.uniform(-jit_r, jit_r))))
            tip.append(f == 0.0)
        nxt = L[k + 1] if k + 1 < nlobes else L[k]
        pts.append((angs[k] + 0.5 * delta, 0.30 * (L[k] + nxt) / 2)); tip.append(False)
    P = [(0.0, 0.0, 0.0)] + [(math.sin(a) * r, math.cos(a) * r, 0.0) for a, r in pts]
    P = np.array(P)
    tip = np.array([False] + tip)
    r = np.hypot(P[:, 0], P[:, 1])
    if look == 'real':
        # cup the blade (edges curl down); the veins stay a little higher so the leaf reads as a shallow dish
        P[:, 2] = -0.16 * r ** 2 + np.where(tip, 0.035, 0.0)
    else:
        # flat planes: the vein of each lobe (its tip) is raised and the margins dropped, so each lobe folds into two flat facets
        P[:, 2] = -0.07 * r + np.where(tip, 0.10, 0.0)
    n = len(P) - 1
    F = [(0, i, i + 1) for i in range(1, n)]                 # fan from the base; the base notch stays open like a real leaf
    sb = len(P)
    P = np.vstack([P, [(-0.025, -0.02, 0.0), (0.025, -0.02, 0.0), (0.0, -0.42, -0.05)]])   # a short stalk
    F.append((sb, sb + 1, 0))
    F.append((sb, sb + 2, sb + 1))
    return P.astype(np.float32), np.array(F, dtype=np.int32)


def leaf_material(st, name='Maple leaves'):
    real = st.real

    def build(m, nodes, links):
        att = nodes.new('ShaderNodeAttribute'); att.attribute_type = 'INSTANCER'; att.attribute_name = 'leaf_hue'
        tone = nodes.new('ShaderNodeAttribute'); tone.attribute_type = 'INSTANCER'; tone.attribute_name = 'leaf_tone'
        ramp = nodes.new('ShaderNodeValToRGB')
        cr = ramp.color_ramp
        cr.interpolation = 'LINEAR' if real else 'CONSTANT'
        # the default ramp has two stops; build the rest
        while len(cr.elements) > 1:
            cr.elements.remove(cr.elements[-1])
        stops = LEAF_STOPS
        cr.elements[0].position = stops[0][0]; cr.elements[0].color = (*stops[0][1], 1)
        for pos, col in stops[1:]:
            e = cr.elements.new(pos); e.color = (*col, 1)
        links.new(att.outputs['Fac'], ramp.inputs['Fac'])
        mul = nodes.new('ShaderNodeMix'); mul.data_type = 'RGBA'; mul.blend_type = 'MULTIPLY'
        mul.inputs['Factor'].default_value = 1.0
        links.new(ramp.outputs['Color'], mul.inputs[6])
        tcol = nodes.new('ShaderNodeCombineColor')
        for i in range(3):
            links.new(tone.outputs['Fac'], tcol.inputs[i])
        links.new(tcol.outputs['Color'], mul.inputs[7])
        b, out = principled_out(nodes, links, Roughness=0.5 if real else 0.8)
        b.inputs['Emission Strength'].default_value = 0.05
        links.new(mul.outputs[2], b.inputs['Base Color'])
        links.new(mul.outputs[2], b.inputs['Emission Color'])
        tr = nodes.new('ShaderNodeBsdfTranslucent')
        links.new(mul.outputs[2], tr.inputs['Color'])
        mix = nodes.new('ShaderNodeMixShader'); mix.inputs['Fac'].default_value = 0.55 if real else 0.35
        links.new(b.outputs['BSDF'], mix.inputs[1]); links.new(tr.outputs['BSDF'], mix.inputs[2])
        links.new(mix.outputs['Shader'], out.inputs['Surface'])
    m = material(name, build)
    m.use_backface_culling = False
    m.diffuse_color = (0.8, 0.14, 0.03, 1.0)          # viewport / Workbench colour only
    return m


def crown_tiers(real):
    """(cx, cy, cz, rx, ry) relative to the trunk base; built from the old five clusters, each split into stacked tiers."""
    base = [(1.7, -0.3, 3.15, 1.7, 1.5), (3.0, -0.7, 2.55, 1.2, 1.1), (0.0, 0.9, 3.4, 1.3, 1.1), (2.9, 1.0, 3.2, 1.0, 0.9), (0.9, -0.9, 2.3, 1.1, 0.9)]
    plan = {0: [(-0.45, 1.0), (0.0, 0.84), (0.45, 0.58)], 1: [(-0.2, 1.0), (0.22, 0.68)], 2: [(-0.28, 1.0), (0.18, 0.7)],
            3: [(-0.2, 1.0), (0.2, 0.66)], 4: [(-0.2, 1.0), (0.22, 0.7)]}
    tiers = []
    rng = np.random.default_rng(31)
    for i, (cx, cy, cz, rx, ry) in enumerate(base):
        for dz, sc in plan[i]:
            tiers.append((cx + rng.uniform(-0.12, 0.12), cy + rng.uniform(-0.12, 0.12), cz + dz, rx * sc * 0.97, ry * sc * 0.97))
    # small satellite pads near the outer tips so the outline is not a stack of clean discs
    for (cx, cy, cz, r) in [(3.65, -0.8, 2.3, 0.5), (3.9, 0.9, 2.85, 0.45), (-0.8, 1.5, 3.0, 0.5), (1.5, -1.5, 2.6, 0.45), (-0.4, 0.0, 2.75, 0.42)]:
        tiers.append((cx, cy, cz, r, r * 0.9))
    return tiers


def sample_crown(st, MX, MY, mz, n_total, wmin, wmax, rng):
    """Leaf centres, normals, colours for the layered crown. Returns dict of numpy arrays (world space)."""
    tiers = crown_tiers(st.real)
    areas = np.array([t[3] * t[4] for t in tiers])
    counts = np.maximum(max(40, n_total // 90), (n_total * areas / areas.sum()).astype(int))
    P, N, U, T, KIND, SIZE, TIERIDX = [], [], [], [], [], [], []
    for ti, ((cx, cy, cz, rx, ry), n) in enumerate(zip(tiers, counts)):
        th_t = 0.30 + 0.06 * rng.uniform()
        tilt = math.radians(rng.uniform(8, 17)); az = rng.uniform(0, math.tau)
        droop = 0.26 * (rx + ry) / 3.0
        ph = rng.uniform(0, 6.3, 3)
        holes = [(rng.uniform(0.25, 0.7), rng.uniform(0, math.tau), rng.uniform(0.15, 0.27)) for _ in range(1 + (ti % 3))]
        got = 0
        pts = []
        while got < n:
            m = int(n * 1.8)
            rho = np.sqrt(rng.uniform(0, 1, m)); th = rng.uniform(0, math.tau, m)
            edge = 1 + 0.20 * np.sin(2 * th + ph[0]) + 0.12 * np.sin(3 * th + ph[1]) + 0.07 * np.sin(5 * th + ph[2])
            rho_e = rho / edge
            keep = (rho_e <= 1.0) & (rng.uniform(0, 1, m) < np.clip(1 - rho_e ** 3, 0, None) ** 0.5 * 0.85 + 0.15)
            x = rho * np.cos(th) * rx; y = rho * np.sin(th) * ry
            for hr, hth, hrad in holes:
                hx = hr * math.cos(hth) * rx; hy = hr * math.sin(hth) * ry
                keep &= np.hypot(x - hx, y - hy) > hrad
            keep &= np.hypot(x, y) > 0.0
            sel = np.where(keep)[0][: n - got]
            pts.append((x[sel], y[sel], rho_e[sel], th[sel]))
            got += len(sel)
        x = np.concatenate([p[0] for p in pts]); y = np.concatenate([p[1] for p in pts]); rho = np.concatenate([p[2] for p in pts]); th = np.concatenate([p[3] for p in pts])
        h = 0.14
        z = h * (1 - rho ** 2) - droop * rho ** 3 + rng.normal(0, th_t * 0.30, len(x))
        # surface slope for the normal
        dzdr = -2 * h * rho - 3 * droop * rho ** 2
        nx = -dzdr * np.cos(th) / max(rx, 0.3); ny = -dzdr * np.sin(th) / max(ry, 0.3)
        nrm = np.stack([nx, ny, np.ones_like(nx)], axis=1)
        # tilt the whole tier
        ca, sa = math.cos(az), math.sin(az)
        axis = np.array([-sa, ca, 0.0])
        K = np.array([[0, -axis[2], axis[1]], [axis[2], 0, -axis[0]], [-axis[1], axis[0], 0]])
        R = np.eye(3) + math.sin(tilt) * K + (1 - math.cos(tilt)) * (K @ K)
        loc = np.stack([x, y, z], axis=1) @ R.T
        nrm = nrm @ R.T
        rnd = rng.normal(size=nrm.shape)
        wr = 0.50 + 0.25 * rho[:, None]
        nrm = nrm / np.linalg.norm(nrm, axis=1, keepdims=True) * (1 - wr) + rnd / np.linalg.norm(rnd, axis=1, keepdims=True) * wr
        world = loc + np.array([MX + cx, MY + cy, mz + cz])
        P.append(world); N.append(nrm)
        # colour parameter: more orange towards the outside, the top and the sun side (the sun is to the left, -x), blotchy by branch, plus per-leaf scatter
        low = smooth_noise(world, 5, 0.55, 2)
        sun = np.clip(0.5 - (world[:, 0] - (MX + 1.7)) / 5.0, 0, 1)
        u = 0.10 + 0.30 * rho + 0.14 * sun + 0.50 * low + 0.10 * (z - z.mean()) / 0.3
        if st.real:
            u = u + rng.normal(0, 0.13, len(u))
            # a few yellow-green near the outer top and a few brown
            r = rng.uniform(0, 1, len(u))
            u = np.where((r < 0.045) & (rho > 0.55), rng.uniform(0.80, 0.90, len(u)), u)
            u = np.where(r > 0.955, rng.uniform(0.96, 1.0, len(u)), u)
            u = np.clip(u, 0.0, 0.99)
            tone = np.clip(rng.normal(1.0, 0.17, len(u)), 0.62, 1.35)
        else:
            # painted: five broad colour passages (deep red, red, red-orange, orange, yellow-orange), laid by region (branch groups), not leaf by leaf
            sc_ = 0.50 + 0.55 * low + 0.20 * (rho - 0.5) + 0.12 * (sun - 0.5)
            lvl = np.clip(np.floor(sc_ * 5.0), 0, 4).astype(int)
            u = np.array([0.04, 0.19, 0.36, 0.56, 0.73])[lvl] + 0.012
            r = rng.uniform(0, 1, len(u))
            u = np.where((r < 0.02) & (rho > 0.6), 0.87, u)
            tone = np.clip(rng.normal(1.0, 0.04, len(u)), 0.9, 1.1)
        U.append(u); T.append(tone)
        w = np.clip(np.exp(rng.normal(math.log((wmin + wmax) / 2), 0.28, len(x))), wmin, wmax)
        SIZE.append(w); TIERIDX.append(np.full(len(x), ti))
    return {k: np.concatenate(v) for k, v in dict(P=P, N=N, U=U, T=T, SIZE=SIZE, TIER=TIERIDX).items()}, tiers


def build_gn_instancer(st, name, collection, extra_inputs=True):
    """Life / <name>: Instance on Points of the leaf sources, using leaf_kind, leaf_rot, leaf_scale, leaf_rank (thinning)."""
    g = bpy.data.node_groups.get(name)
    if g is not None:
        bpy.data.node_groups.remove(g)
    g = bpy.data.node_groups.new(name, 'GeometryNodeTree')
    g.interface.new_socket('Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
    g.interface.new_socket('Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
    dens = g.interface.new_socket('Density', in_out='INPUT', socket_type='NodeSocketFloat')
    dens.default_value = 1.0; dens.min_value = 0.0; dens.max_value = 1.0
    n = g.nodes
    inp = n.new('NodeGroupInput'); out = n.new('NodeGroupOutput')
    ci = n.new('GeometryNodeCollectionInfo'); ci.transform_space = 'RELATIVE'
    ci.inputs['Collection'].default_value = collection
    ci.inputs['Separate Children'].default_value = True; ci.inputs['Reset Children'].default_value = True
    iop = n.new('GeometryNodeInstanceOnPoints'); iop.inputs['Pick Instance'].default_value = True

    def named(attr, typ):
        a = n.new('GeometryNodeInputNamedAttribute'); a.data_type = typ; a.inputs['Name'].default_value = attr
        return a.outputs['Attribute']
    cmp_ = n.new('FunctionNodeCompare'); cmp_.data_type = 'FLOAT'; cmp_.operation = 'LESS_EQUAL'
    g.links.new(named('leaf_rank', 'FLOAT'), cmp_.inputs['A']); g.links.new(inp.outputs['Density'], cmp_.inputs['B'])
    g.links.new(inp.outputs['Geometry'], iop.inputs['Points'])
    g.links.new(cmp_.outputs['Result'], iop.inputs['Selection'])
    g.links.new(ci.outputs['Instances'], iop.inputs['Instance'])
    g.links.new(named('leaf_kind', 'INT'), iop.inputs['Instance Index'])
    g.links.new(named('leaf_rot', 'FLOAT_VECTOR'), iop.inputs['Rotation'])
    g.links.new(named('leaf_scale', 'FLOAT_VECTOR'), iop.inputs['Scale'])
    g.links.new(iop.outputs['Instances'], out.inputs['Geometry'])
    for i, nd in enumerate(n):
        nd.location = ((i % 5) * 240, -(i // 5) * 200)
    return g


def leaf_sources(st, prefix, nkinds=5):
    """Hidden source meshes in an unlinked collection, one per leaf shape. Returns (collection, [objects], unit width)."""
    cname = 'Life / ' + prefix + ' leaf sources'
    old = bpy.data.collections.get(cname)
    if old is not None:
        for o in list(old.objects):
            d = o.data
            bpy.data.objects.remove(o, do_unlink=True)
            if d and d.users == 0:
                bpy.data.meshes.remove(d)
        bpy.data.collections.remove(old)
    col = bpy.data.collections.new(cname)
    mat = leaf_material(st)
    objs = []
    width = 0
    for k in range(nkinds):
        nl = 5 if k == nkinds - 1 else 7
        V, F = leaf_mesh_arrays(st.look, k, nl)
        me = mesh_from_arrays(f'{prefix} leaf shape {k}', V, F, smooth=st.real, mat=mat)
        ob = bpy.data.objects.new(f'{prefix} leaf source {k}', me)
        col.objects.link(ob)
        ob['garden_owner'] = OWNER; ob['garden_role'] = 'leaf'; ob['life_created'] = 1
        objs.append(ob)
        width = max(width, float(V[:, 0].max() - V[:, 0].min()))
        st.created.append(ob.name)
    return col, objs, width


def build_maple(st, ctx=None):
    sc = bpy.context.scene
    tr = bpy.data.objects['Maple trunk']
    p0 = tr.data.splines[0].points[0].co
    MX, MY, mz = p0.x, p0.y, p0.z + 0.1
    rng = np.random.default_rng(st.seed + 11)
    quick = st.o.get('quick')
    if st.real:
        n_total, wmin, wmax = (6000 if quick else 56000), 0.055, 0.125
    else:
        n_total, wmin, wmax = (4000 if quick else 48000), 0.08, 0.14
    # 1. leaf sources + instancer
    col, objs, unit_width = leaf_sources(st, 'Maple')
    data, tiers = sample_crown(st, MX, MY, mz, n_total, wmin, wmax, rng)
    n = len(data['P'])
    scale = (data['SIZE'] / unit_width)
    spin = rng.uniform(0, math.tau, n)
    eul = rotation_to_euler(data['N'], spin)
    attrs = {'leaf_kind': ('INT', rng.integers(0, len(objs), n)), 'leaf_rot': ('FLOAT_VECTOR', eul),
             'leaf_scale': ('FLOAT_VECTOR', np.stack([scale, scale, scale], axis=1)), 'leaf_hue': ('FLOAT', data['U']),
             'leaf_tone': ('FLOAT', data['T']), 'leaf_rank': ('FLOAT', rng.uniform(0, 1, n))}
    me = point_cloud_object(st, 'Maple leaves', data['P'], attrs, 'leaf')
    ob = bpy.data.objects['Maple leaves']
    old = ob.data
    me.materials.append(old.materials[0] if len(old.materials) else leaf_material(st))
    ob.data = me
    if old.users == 0:
        bpy.data.meshes.remove(old)
    for m in list(ob.modifiers):
        ob.modifiers.remove(m)
    g = build_gn_instancer(st, 'Life / maple leaf instancer', col)
    md = ob.modifiers.new('Life / maple leaves', 'NODES'); md.node_group = g
    st.tag(ob, 'leaf'); st.changed.append('Maple leaves')
    st.numbers['maple_leaves'] = n
    wd = data['SIZE']
    st.numbers['maple_leaf_width_cm'] = (round(float(wd.min()) * 100, 1), round(float(np.median(wd)) * 100, 1), round(float(wd.max()) * 100, 1))
    st.numbers['maple_leaf_unique_triangles'] = sum(len(o.data.polygons) for o in objs)
    st.numbers['maple_leaf_kinds'] = len(objs)
    # 2. inner mass: dark layered lenses, one under each tier, replacing the old blobs
    build_inner_mass(st, MX, MY, mz, tiers, rng)
    # 3. woody scaffold: twigs from the old branches up to each tier
    build_scaffold(st, MX, MY, mz, tiers, rng)
    # 4. materials: recolour the inner mass
    return dict(MX=MX, MY=MY, mz=mz, tiers=tiers)


def build_inner_mass(st, MX, MY, mz, tiers, rng):
    V_all, F_all, C_all = [], [], []
    off = 0
    for ti, (cx, cy, cz, rx, ry) in enumerate(tiers):
        if rx < 0.6:
            continue
        # a flat lens: 3 rings of vertices, lumpy; painted: fewer, flatter, unequal planes
        nring = 9 if st.real else 7
        rings = [0.0, 0.45, 0.8]
        verts = [(0.0, 0.0, 0.10)]
        for r_i, rr in enumerate(rings[1:], start=1):
            for k in range(nring):
                a = (k + rng.uniform(-0.25, 0.25)) * math.tau / nring
                rad = rr * (0.8 + rng.uniform(-0.12, 0.12))
                verts.append((math.cos(a) * rx * 0.78 * rad, math.sin(a) * ry * 0.78 * rad, 0.10 - 0.16 * rr ** 2 + rng.uniform(-0.03, 0.03)))
        # bottom centre
        verts.append((0.0, 0.0, -0.16))
        V = np.array(verts, dtype=np.float32)
        nv = len(V)
        F = []
        for k in range(nring):
            k2 = (k + 1) % nring
            F.append((0, 1 + k, 1 + k2))
            a0, a1, b0, b1 = 1 + k, 1 + k2, 1 + nring + k, 1 + nring + k2
            F.append((a0, b0, b1)); F.append((a0, b1, a1))
            F.append((nv - 1, 1 + nring + k2, 1 + nring + k))
        F = np.array(F, dtype=np.int32)
        # tier tilt (a gentle random dip) and translation
        tilt = rng.uniform(-0.2, 0.2, 2)
        V[:, 2] += V[:, 0] * tilt[0] * 0.3 + V[:, 1] * tilt[1] * 0.3
        V += np.array([MX + cx, MY + cy, mz + cz - 0.05], dtype=np.float32)
        V_all.append(V); F_all.append(F + off); off += len(V)
        # per face colour: dark red-brown, a bit lighter towards the top
        zc = V[F].mean(axis=1)[:, 2]
        t = np.clip((zc - zc.min()) / max(1e-4, np.ptp(zc)), 0, 1)[:, None] * 0.6 + rng.uniform(0, 0.25, (len(F), 1))
        a, b = np.array([0.07, 0.008, 0.006]), np.array([0.26, 0.03, 0.015])
        C_all.append(np.concatenate([a + (b - a) * np.clip(t, 0, 1), np.ones((len(F), 1))], axis=1))
    V = np.concatenate(V_all); F = np.concatenate(F_all); C = np.concatenate(C_all)
    ob = bpy.data.objects['Maple inner mass']
    old = ob.data
    me = mesh_from_arrays('Maple inner mass', V, F, smooth=False, colors=C)
    me.materials.append(old.materials[0])
    ob.data = me
    if old.users == 0:
        bpy.data.meshes.remove(old)
    st.tag(ob, 'leaf'); st.changed.append('Maple inner mass')
    st.numbers['maple_inner_mass_faces'] = len(F)


def curve_object(st, name, points, r0, r1, mat, role='bark'):
    cu = bpy.data.curves.new(name, 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = 1.0; cu.bevel_resolution = 2 if not st.real else 3; cu.use_fill_caps = True
    sp = cu.splines.new('POLY'); sp.points.add(len(points) - 1)
    for i, (p, pt) in enumerate(zip(points, sp.points)):
        pt.co = (*p, 1.0); pt.radius = r0 + (r1 - r0) * i / max(1, len(points) - 1)
    cu.materials.append(mat)
    return st.new_object(name, cu, role)


def build_scaffold(st, MX, MY, mz, tiers, rng):
    bark = bpy.data.materials['Bark']
    # joints on the existing limbs (relative offsets): trunk top and the three old branches
    joints = [(1.15, -0.10, 2.55), (1.7, 0.15, 3.2), (1.5, -0.65, 2.1), (2.5, -0.8, 2.4), (0.4, 0.7, 2.9), (3.0, 1.1, 3.25), (0.55, -0.2, 1.7), (2.0, 0.7, 3.0)]
    made = 0
    for ti, (cx, cy, cz, rx, ry) in enumerate(tiers):
        if (rx < 0.6 and ti < len(tiers) - 5) or (ti % 2 == 1 and made >= 6 and rx >= 0.6):
            continue
        j = min(joints, key=lambda a: (a[0] - cx) ** 2 + (a[1] - cy) ** 2 + (a[2] - cz) ** 2 * 0.5)
        a = np.array(j); b = np.array([cx, cy, cz - 0.08])
        mid = (a + b) / 2 + np.array([rng.uniform(-0.12, 0.12), rng.uniform(-0.12, 0.12), 0.10])
        pts = [tuple(np.array((MX, MY, mz)) + q) for q in (a, mid, b)]
        curve_object(st, 'Maple branch.' + format(3 + made, '03d'), pts, 0.045, 0.012, bark)
        made += 1
    st.numbers['maple_scaffold_twigs'] = made


# ------------------------------------------------------------------------------------------------ entry point
def _snapshot_names():
    return (sorted(o.name for o in bpy.data.objects), sorted(m.name for m in bpy.data.materials))


def apply(options=None):
    """Run the life stage on the open scene. Returns a report dict (also printed in short)."""
    st = Stage(options)
    _STAGE_REF['st'] = st
    before_o, before_m = _snapshot_names()
    gone = remove_previous()
    if gone:
        st.say(f're-run: removed {len(gone)} objects from an earlier run of this stage')
    ctx = {}
    for nm, role in [('Maple trunk', 'bark'), ('Maple branch', 'bark'), ('Maple branch.001', 'bark'), ('Maple branch.002', 'bark'), ('Pine trunk', 'bark'),
                     ('Pine limb', 'bark'), ('Pine limb.001', 'bark'), ('Pine limb.002', 'bark'), ('Pine limb.003', 'bark'), ('Pine limb.004', 'bark'),
                     ('Bamboo leaves', 'leaf'), ('Lotus blossoms', 'growth')]:
        o = bpy.data.objects.get(nm)
        if o is not None:
            st.tag(o, role)
    for step in ALL_STEPS:
        if step not in st.steps:
            continue
        fn = globals().get('build_' + step)
        if fn is None:
            st.say(f'step {step}: not available in this version')
            continue
        st.say(f'step {step} ({st.look})')
        ctx[step] = fn(st, ctx)
    after_o, after_m = _snapshot_names()
    rep = dict(look=st.look, steps=st.steps, created=st.created, changed=st.changed, deleted=st.deleted,
               objects_before=len(before_o), objects_after=len(after_o),
               objects_added=sorted(set(after_o) - set(before_o)), objects_removed=sorted(set(before_o) - set(after_o)),
               materials_added=sorted(set(after_m) - set(before_m)), materials_removed=sorted(set(before_m) - set(after_m)),
               numbers=st.numbers, notes=st.notes)
    print('[life] REPORT ' + json.dumps({k: (v if k != 'notes' else len(v)) for k, v in rep.items() if k in ('look', 'steps', 'objects_before', 'objects_after', 'numbers')}, default=str))
    def short(names, n=40):
        return ', '.join(names[:n]) + (f' ... (+{len(names) - n} more)' if len(names) > n else '')
    print(f"[life] created {len(st.created)}: {short(st.created)}")
    print(f"[life] changed {len(st.changed)}: {short(st.changed)}")
    print(f"[life] deleted {len(st.deleted)}: {short(st.deleted)}")
    return rep


# ------------------------------------------------------------------------------------------------ 2. GROUND COVER
def _hull(points):
    pts = sorted(set((round(x, 4), round(y, 4)) for x, y in points))
    if len(pts) < 3:
        return pts

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lo = []
    for p in pts:
        while len(lo) >= 2 and cross(lo[-2], lo[-1], p) <= 0:
            lo.pop()
        lo.append(p)
    up = []
    for p in reversed(pts):
        while len(up) >= 2 and cross(up[-2], up[-1], p) <= 0:
            up.pop()
        up.append(p)
    return lo[:-1] + up[:-1]


def world_vertices(ob):
    dg = bpy.context.evaluated_depsgraph_get()
    ev = ob.evaluated_get(dg)
    me = ev.to_mesh()
    V = np.array([tuple(v.co) for v in me.vertices], dtype=np.float64).reshape(-1, 3)
    ev.to_mesh_clear()
    if len(V) == 0:
        return V
    M = np.array(ob.matrix_world)
    return V @ M[:3, :3].T + M[:3, 3]


def foot_print(st, ob):
    """(centre xy, hull xy list) of a stone where it meets the ground: vertices from just under to 0.28 m over the ground at its centre."""
    V = world_vertices(ob)
    if len(V) == 0:
        return None
    c = V[:, :2].mean(axis=0)
    g = st.ground_z(c[0], c[1])
    sel = V[(V[:, 2] > g - 0.04) & (V[:, 2] < g + 0.28)]
    if len(sel) < 4:
        sel = V[V[:, 2] < V[:, 2].min() + 0.4 * max(1e-3, np.ptp(V[:, 2]))]
    h = _hull([(p[0], p[1]) for p in sel])
    if len(h) < 3:
        return None
    hc = np.mean(np.array(h), axis=0)
    return hc, h


def perimeter_samples(hull, centre, offset, spacing, rng):
    """Points along the hull outline pushed outward by `offset` (can be negative); returns (points (n,2), outward normals (n,2))."""
    H = np.array(hull)
    out = []
    nor = []
    n = len(H)
    for i in range(n):
        a, b = H[i], H[(i + 1) % n]
        seg = b - a
        L = np.hypot(*seg)
        if L < 1e-6:
            continue
        k = max(1, int(L / spacing))
        for j in range(k):
            t = (j + rng.uniform(0.15, 0.85)) / k
            p = a + seg * t
            d = p - centre
            dn = d / max(1e-6, np.hypot(*d))
            out.append(p + dn * offset(rng) if callable(offset) else p + dn * offset)
            nor.append(dn)
    return np.array(out).reshape(-1, 2), np.array(nor).reshape(-1, 2)


def dist_to_polyline(p, line):
    best = 1e9
    for a, b in zip(line, line[1:]):
        ab = b - a
        t = np.clip(np.dot(p - a, ab) / max(1e-9, np.dot(ab, ab)), 0, 1)
        best = min(best, float(np.hypot(*(p - (a + t * ab)))))
    return best


def scene_context(st):
    """Positions read live from the open scene (after the shapes stage): stones, path, gravel court, hall, pond centre."""
    import re
    ctx = {}
    objs = [o for o in bpy.data.objects if o.type == 'MESH' and not o.hide_render]

    def pick(pattern):
        return sorted([o for o in objs if re.match(pattern, o.name)], key=lambda o: o.name)
    ctx['rocks'] = pick(r'^Rock \d+$')
    ctx['gravel_rocks'] = pick(r'^Gravel rock \d+$')
    ctx['pond_stones'] = pick(r'^Pond edge stone \d+$')
    ctx['steps'] = pick(r'^Stepping stone \d+$')
    ctx['others'] = [o for o in objs if o.name in ('Lantern base', 'Water basin', 'Veranda step, lower')]
    # path through the stepping stones (their order is the walking order)
    pts = []
    for o in sorted(ctx['steps'], key=lambda o: int(o.name.split()[-1])):
        V = world_vertices(o)
        if len(V):
            pts.append(V[:, :2].mean(axis=0))
    ctx['path'] = [np.array(p) for p in pts]
    g = bpy.data.objects.get('Raked gravel court')
    if g is not None:
        V = world_vertices(g)
        ctx['gravel'] = (float(V[:, 0].min()), float(V[:, 1].min()), float(V[:, 0].max()), float(V[:, 1].max()))
    else:
        ctx['gravel'] = (0.9, -5.9, 9.1, 1.9)
    ctx['hall'] = (-5.3, 4.5, 5.7, 11.0)
    return ctx


def in_rect(x, y, r, margin=0.0):
    return r[0] - margin < x < r[2] + margin and r[1] - margin < y < r[3] + margin


def _unit_dome(st, variant, rng, kind):
    """Moss cushion / pebble source geometry: returns (V, F) arrays with the bottom near z=0."""
    bm = bmesh.new()
    sub = 2 if (st.real and kind == 'moss') else 1
    lumps = [(0.0, 0.0, 1.0)]
    if kind == 'moss' and st.real:
        for _ in range(3 + variant % 3):
            a = rng.uniform(0, math.tau)
            lumps.append((math.cos(a) * rng.uniform(0.40, 0.75), math.sin(a) * rng.uniform(0.40, 0.75), rng.uniform(0.34, 0.62)))
    for (ox, oy, rs) in lumps:
        ret = bmesh.ops.create_icosphere(bm, subdivisions=sub, radius=rs)
        for v in ret['verts']:
            v.co.x += ox; v.co.y += oy
    # keep the upper half only
    bm.verts.ensure_lookup_table()
    drop = [v for v in bm.verts if v.co.z < -0.02]
    bmesh.ops.delete(bm, geom=drop, context='VERTS')
    for v in bm.verts:
        jit = 0.14 if (kind == 'moss' and st.real) else (0.20 if not st.real else 0.10)
        v.co.x += rng.uniform(-jit, jit) * 0.5; v.co.y += rng.uniform(-jit, jit) * 0.5; v.co.z += rng.uniform(-jit, jit) * 0.4
        v.co.z *= 0.8 if kind == 'moss' else (0.55 + rng.uniform(-0.1, 0.1))
        if kind == 'pebble':
            v.co.x *= 1.0 + 0.2 * rng.uniform(-1, 1); v.co.y *= 0.8 + 0.2 * rng.uniform(-1, 1)
    bm.faces.ensure_lookup_table()
    V = np.array([tuple(v.co) for v in bm.verts], dtype=np.float32)
    V[:, 2] -= V[:, 2].min()                      # bottom at z = 0 (the add-on wants the support origin at the bottom)
    idx = {v: i for i, v in enumerate(bm.verts)}
    F = [tuple(idx[v] for v in f.verts) for f in bm.faces if len(f.verts) == 3]
    bm.free()
    return V, np.array(F, dtype=np.int32)


def _tuft_arrays(st, variant, rng):
    nb = (12 if st.real else 7) + variant % 3
    V, F = [], []
    for b in range(nb):
        a = rng.uniform(0, math.tau)
        lean = rng.uniform(0.15, 0.55)
        h = rng.uniform(0.65, 1.0)
        w = 0.05 if st.real else 0.07
        d = np.array([math.cos(a), math.sin(a)])
        side = np.array([-d[1], d[0]])
        segs = 3 if st.real else 2
        prev = None
        for s in range(segs + 1):
            t = s / segs
            c = d * (0.05 + lean * t ** 1.6 * h * 0.8)
            z = h * t - (0.18 * h * t ** 3 if st.real else 0)
            ww = w * (1 - t) ** 0.8 if s < segs else 0
            base = len(V)
            if s < segs:
                V.append((c[0] + side[0] * ww, c[1] + side[1] * ww, z)); V.append((c[0] - side[0] * ww, c[1] - side[1] * ww, z))
            else:
                V.append((c[0], c[1], z))
            if prev is not None:
                pa, pb = prev
                if s < segs:
                    F.append((pa, pb, base + 1)); F.append((pa, base + 1, base))
                else:
                    F.append((pa, pb, base))
            prev = (base, base + 1)
    return np.array(V, dtype=np.float32), np.array(F, dtype=np.int32)


def moss_materials(st):
    """Recolour the four moss tone materials (this stage owns them): mottled, yellow-green to deep green to olive-brown."""
    tones = {0: ((0.016, 0.042, 0.012), (0.034, 0.075, 0.020)), 1: ((0.060, 0.098, 0.022), (0.115, 0.165, 0.034)),
             2: ((0.060, 0.062, 0.020), (0.105, 0.088, 0.028)), 3: ((0.026, 0.066, 0.020), (0.052, 0.110, 0.030))}
    out = []
    for i, (A, B) in tones.items():
        def build(m, nodes, links, A=A, B=B):
            tc = nodes.new('ShaderNodeTexCoord')
            no = nodes.new('ShaderNodeTexNoise'); no.inputs['Scale'].default_value = 9.0; no.inputs['Detail'].default_value = 3.0
            links.new(tc.outputs['Object'] if False else tc.outputs['Generated'], no.inputs['Vector'])
            ramp = nodes.new('ShaderNodeValToRGB')
            ramp.color_ramp.elements[0].position = 0.30; ramp.color_ramp.elements[0].color = (*A, 1)
            ramp.color_ramp.elements[1].position = 0.70; ramp.color_ramp.elements[1].color = (*B, 1)
            if not st.real:
                ramp.color_ramp.interpolation = 'CONSTANT'
            links.new(no.outputs['Fac'], ramp.inputs['Fac'])
            b, out_ = principled_out(nodes, links, Roughness=0.93 if st.real else 0.95)
            if st.real:
                b.inputs['Sheen Weight'].default_value = 0.28; b.inputs['Sheen Roughness'].default_value = 0.45
                b.inputs['Sheen Tint'].default_value = (0.55, 0.75, 0.45, 1)
                fine = nodes.new('ShaderNodeTexVoronoi'); fine.inputs['Scale'].default_value = 140.0
                links.new(tc.outputs['Generated'], fine.inputs['Vector'])
                bump = nodes.new('ShaderNodeBump'); bump.inputs['Strength'].default_value = 0.35; bump.inputs['Distance'].default_value = 0.004
                links.new(fine.outputs['Distance'], bump.inputs['Height']); links.new(bump.outputs['Normal'], b.inputs['Normal'])
            links.new(ramp.outputs['Color'], b.inputs['Base Color'])
        m = material(f'Astra / moss tone {i}', build)
        m.diffuse_color = (*A, 1)
        out.append(m.name)
    return out


def tuft_material(st):
    def build(m, nodes, links):
        tc = nodes.new('ShaderNodeTexCoord')
        sep = nodes.new('ShaderNodeSeparateXYZ'); links.new(tc.outputs['Generated'], sep.inputs['Vector'])
        ramp = nodes.new('ShaderNodeValToRGB')
        ramp.color_ramp.elements[0].position = 0.0; ramp.color_ramp.elements[0].color = (0.016, 0.040, 0.010, 1)
        e = ramp.color_ramp.elements.new(0.6); e.color = (0.065, 0.12, 0.022, 1)
        e = ramp.color_ramp.elements.new(1.0); e.color = (0.17, 0.20, 0.04, 1)
        if not st.real:
            ramp.color_ramp.interpolation = 'CONSTANT'
        links.new(sep.outputs['Z'], ramp.inputs['Fac'])
        b, out_ = principled_out(nodes, links, Roughness=0.6)
        links.new(ramp.outputs['Color'], b.inputs['Base Color'])
        tr = nodes.new('ShaderNodeBsdfTranslucent'); links.new(ramp.outputs['Color'], tr.inputs['Color'])
        mix = nodes.new('ShaderNodeMixShader'); mix.inputs['Fac'].default_value = 0.25
        links.new(b.outputs['BSDF'], mix.inputs[1]); links.new(tr.outputs['BSDF'], mix.inputs[2])
        links.new(mix.outputs['Shader'], out_.inputs['Surface'])
    m = material('Life / tuft', build)
    m.use_backface_culling = False
    m.diffuse_color = (0.12, 0.2, 0.03, 1)
    return m


def make_bank(st, name, kind, nvar, materials):
    """A hidden collection of source meshes for the live scatter (identity transforms, bottoms at z = 0, no parents)."""
    old = bpy.data.collections.get(name)
    if old is not None:
        for o in list(old.objects):
            d = o.data
            bpy.data.objects.remove(o, do_unlink=True)
            if d and d.users == 0:
                bpy.data.meshes.remove(d)
        bpy.data.collections.remove(old)
    col = bpy.data.collections.new(name)
    st.collection().children.link(col)
    col.hide_render = True
    rng = np.random.default_rng(st.seed + {'moss': 1, 'tuft': 2, 'pebble': 3}.get(kind, 4))
    for v in range(nvar):
        if kind == 'tuft':
            V, F = _tuft_arrays(st, v, rng)
        else:
            V, F = _unit_dome(st, v, rng, kind)
        me = mesh_from_arrays(f'{name} {v}', V, F, smooth=st.real and kind != 'tuft')
        me.materials.append(materials[v % len(materials)])
        ob = bpy.data.objects.new(f'{name} {v}', me)
        col.objects.link(ob)
        ob.hide_render = True
        ob['garden_owner'] = OWNER; ob['garden_role'] = 'growth'; ob['life_created'] = 1; ob['garden_keep_materials'] = 1
        st.created.append(ob.name)
    return col


def make_records(prefix, pts, scales, rots, traffics, habitats, contacts):
    return [dict(id=f'{prefix}:{i}', x=float(p[0]), y=float(p[1]), scale=[float(s) for s in sc], rot=[float(r) for r in ro],
                 traffic=float(t), habitat=float(h), contact=float(c))
            for i, (p, sc, ro, t, h, c) in enumerate(zip(pts, scales, rots, traffics, habitats, contacts))]


def expected_kept(st, host, controls):
    """Expected instance count of a native scatter from its own retained records and the receiver surface (for the count check)."""
    contract = json.loads(host['astra_native_contract'])
    kind = contract['kind']
    recs = json.loads(host['astra_records'])
    radii = [min(1.0, 1.0) for _ in recs]
    total = 0.0
    for r, fr in zip(recs, [a.value for a in host.data.attributes['astra_footprint_radius'].data]):
        chance = min(r['habitat'] + r['contact'] * controls['Contact Influence'], 1.0) * controls['Density']
        z = st.ground_z(r['x'], r['y']) - (0.012 if kind == 'pebble' else 0.018)
        # the node tests the ray hit position (before the embed offset)
        hz = st.ground_z(r['x'], r['y'])
        dz = hz - controls['Waterline']
        ok = (r['traffic'] - fr) > controls['Traffic Width'] and dz > -0.015
        if kind != 'pebble':
            ok = ok and dz < controls['Damp Reach']
        total += min(chance, 1.0) * (1.0 if ok else 0.0)
    return total, len(recs)


def count_instances(host):
    dg = bpy.context.evaluated_depsgraph_get()
    gs = host.evaluated_get(dg).evaluated_geometry()
    ipc = gs.instances_pointcloud()
    return 0 if ipc is None else len(ipc.points)


STORE_SHIP = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/garden/life/ship'


def load_addon(st):
    folder = st.o['addon']
    if not os.path.isdir(folder):
        for alt in (os.path.join(STORE_SHIP, 'addon_copy'), '/home/user/Music/japanese-courtyard/addon_copy'):
            if os.path.isdir(alt):
                folder = alt
                break
        else:
            return None
    sys.dont_write_bytecode = True
    for place in (HERE, STORE_SHIP):
        if os.path.exists(os.path.join(place, 'astra_loader.py')) and place not in sys.path:
            sys.path.insert(0, place)                # astra_loader.py (an unchanged copy of the project's loader) lives next to this file
    try:
        from astra_loader import load_astra, apply_blender_52_shim
        api = load_astra(folder)
        apply_blender_52_shim(api)
        return api
    except Exception as exc:
        st.say('add-on could not be loaded (' + repr(exc)[:120] + '): live scatter skipped')
        return None


def build_ground(st, ctx=None):
    rng = np.random.default_rng(st.seed + 21)
    scene = scene_context(st)
    ground = bpy.data.objects['Astra / Courtyard receiving ground']
    # 1. smooth shading of terrain and (real look) pebbles
    me = ground.data
    smooth_ground = bool(st.o.get('smooth_ground', True)) or st.real
    me.polygons.foreach_set('use_smooth', np.full(len(me.polygons), smooth_ground))
    me.update()
    st.changed.append(ground.name)
    peb = bpy.data.objects['Astra / pebbles grouped bodies']
    peb.data.polygons.foreach_set('use_smooth', np.full(len(peb.data.polygons), st.real))
    peb.data.update()
    st.changed.append(peb.name)
    st.tag(ground, 'ground.earth'); st.tag(peb, 'ground.earth', keep_materials=False)
    moss_mats = moss_materials(st)
    st.changed.extend(moss_mats)
    bpy.data.objects['Astra / moss grouped bodies'].data.polygons.foreach_set('use_smooth', np.full(len(bpy.data.objects['Astra / moss grouped bodies'].data.polygons), st.real))
    st.changed.append('Astra / moss grouped bodies')
    api = load_addon(st) if st.o.get('scatter', True) else None
    if api is None:
        st.say('live scatter not run (no add-on)')
        return {}
    mats = [bpy.data.materials[f'Astra / moss tone {i}'] for i in (0, 1, 2, 3)]
    moss_bank = make_bank(st, 'Life / moss sources', 'moss', 6, [mats[0], mats[1], mats[2], mats[3], mats[1], mats[2]])
    tuft_bank = make_bank(st, 'Life / tuft sources', 'tuft', 4, [tuft_material(st)])
    peb_mats = [bpy.data.materials[f'Astra / pebbles tone {i}'] for i in range(4)]
    peb_bank = make_bank(st, 'Life / pebble sources', 'pebble', 6, peb_mats)
    bpy.context.view_layer.update()
    path = scene['path']
    gx0, gy0, gx1, gy1 = scene['gravel']
    hall = scene['hall']
    water = WATER_Z
    results = {}

    def traffic_of(p):
        return dist_to_polyline(np.array(p), path) if len(path) > 1 else 9.0

    def allowed(x, y, collar=False):
        if in_rect(x, y, hall):
            return False
        if in_rect(x, y, (gx0, gy0, gx1, gy1), margin=-0.05) and not collar:
            return False
        return -11.0 < x < 11.0 and -8.0 < y < 12.0

    # ---- A. moss collars at the feet of stones --------------------------------------------------------------
    pts, sc, ro, tr, hab, con = [], [], [], [], [], []
    stones = [(o, 'rock') for o in scene['rocks']] + [(o, 'grock') for o in scene['gravel_rocks']] + [(o, 'pond') for o in scene['pond_stones']] + \
             [(o, 'step') for o in scene['steps']] + [(o, 'other') for o in scene['others']]
    n_by = {}
    for o, cls in stones:
        fp = foot_print(st, o)
        if fp is None:
            continue
        c, hull = fp
        if cls == 'grock':
            spacing, off, rad = 0.05, (lambda r: r.uniform(-0.03, 0.05)), (0.05, 0.10)       # a tight collar slightly above the gravel
        elif cls == 'step':
            spacing, off, rad = 0.11, (lambda r: r.uniform(0.0, 0.10)), (0.05, 0.10)
        elif cls == 'pond':
            spacing, off, rad = 0.06, (lambda r: r.uniform(-0.04, 0.06)), (0.06, 0.12)
        else:
            spacing, off, rad = 0.055, (lambda r: r.uniform(-0.04, 0.07)), (0.07, 0.15)
        P, Nn = perimeter_samples(hull, c, off, spacing, rng)
        for p in P:
            if not allowed(p[0], p[1], collar=(cls == 'grock')):
                continue
            r = rng.uniform(*rad)
            pts.append(p); sc.append((r * rng.uniform(0.85, 1.25), r * rng.uniform(0.85, 1.25), r * rng.uniform(0.7, 1.1) * (1.5 if cls == 'grock' else 1.0)))
            ro.append((0, 0, rng.uniform(0, math.tau))); tr.append(traffic_of(p))
            hab.append(0.25 if cls in ('step',) else 0.45); con.append(0.9 if cls != 'step' else 0.5)
        n_by[cls] = n_by.get(cls, 0) + len(P)
    # ---- B. damp edges: a few broad irregular drifts (dense overlapping cushions, soft edge, quiet middle), not polka dots --------
    mx, my = -6.7, 1.3
    cand = np.column_stack([rng.uniform(-8.2, 1.4, 9000), rng.uniform(-2.6, 4.6, 9000)])

    def habitat_at(x, y):
        z = st.ground_z(x, y)
        dz = z - water
        h = 0.0
        if -0.03 < dz < 0.30:
            h = max(h, 0.9 * (1 - dz / 0.30) ** 0.8)
        d = math.hypot(x - mx, y - my)
        if d < 2.4:
            h = max(h, 0.7 * (1 - d / 2.4))
        return h
    scored = []
    for p in cand[:4500]:
        x, y = float(p[0]), float(p[1])
        if allowed(x, y):
            h = habitat_at(x, y)
            if h > 0.35:
                scored.append((h + rng.uniform(0, 0.25), x, y))
    scored.sort(reverse=True)
    centres = []
    for sco, x, y in scored:
        if all(math.hypot(x - cx, y - cy) > 1.5 for _, cx, cy in centres):
            centres.append((sco, x, y))
        if len(centres) >= (9 if st.real else 8):
            break
    n_patch = 0
    for sco, cx, cy in centres:
        a_ax = rng.uniform(0.55, 1.15) * (0.7 + 0.5 * min(1.0, sco)); b_ax = a_ax * rng.uniform(0.45, 0.8); ang = rng.uniform(0, math.pi)
        n = int(math.pi * a_ax * b_ax * (60 if st.real else 30))
        for _ in range(n):
            rr = math.sqrt(rng.uniform(0, 1)); th = rng.uniform(0, math.tau)
            lx, ly = rr * math.cos(th) * a_ax, rr * math.sin(th) * b_ax
            x = cx + lx * math.cos(ang) - ly * math.sin(ang); y = cy + lx * math.sin(ang) + ly * math.cos(ang)
            if not allowed(x, y):
                continue
            hv = habitat_at(x, y)
            falloff = np.clip(1.15 - rr ** 2.2, 0.0, 1.0)
            habv = float(np.clip(hv * 1.1, 0, 1)) * float(falloff)
            if habv < 0.1:
                continue
            r = rng.uniform(0.08, 0.16) if st.real else rng.uniform(0.11, 0.2)
            pts.append(np.array([x, y])); sc.append((r * rng.uniform(0.85, 1.3), r * rng.uniform(0.85, 1.3), r * rng.uniform(0.55, 0.95)))
            ro.append((0, 0, rng.uniform(0, math.tau))); tr.append(traffic_of((x, y))); hab.append(habv); con.append(0.0)
        n_patch += 1
    st.numbers['moss_drifts'] = n_patch
    recs = make_records('moss', pts, sc, ro, tr, hab, con)
    ctrl = dict(Density=1.0, **{'Traffic Width': 0.575, 'Waterline': water, 'Damp Reach': 100.0, 'Contact Influence': 0.6, 'Seed': 521})
    host = api.create_native_scatter('Life / moss at feet and damp edges', recs, moss_bank, ground, st.collection(), 'moss', controls=ctrl, footprint_check=True)
    st.tag(host, 'growth', keep_materials=True); host['life_created'] = 1; st.created.append(host.name)
    results['moss'] = (host, ctrl)
    # ---- C. tufts: pond bank, beside stones (second ring), maple root ------------------------------------------
    pts, sc, ro, tr, hab, con = [], [], [], [], [], []
    for o, cls in stones:
        if cls == 'step':
            continue
        fp = foot_print(st, o)
        if fp is None:
            continue
        c, hull = fp
        P, Nn = perimeter_samples(hull, c, (lambda r: r.uniform(0.10, 0.30)), 0.55, rng)
        for p in P:
            if allowed(p[0], p[1]) and rng.uniform() < 0.6:
                h = rng.uniform(0.10, 0.22)
                pts.append(p); sc.append((h * rng.uniform(0.9, 1.4), h * rng.uniform(0.9, 1.4), h)); ro.append((0, 0, rng.uniform(0, math.tau)))
                tr.append(traffic_of(p)); hab.append(0.5); con.append(0.5)
    clumps_n = 0
    for p in cand[:6000]:
        x, y = float(p[0]), float(p[1])
        if not allowed(x, y):
            continue
        dz = st.ground_z(x, y) - water
        if 0.0 < dz < 0.22 and rng.uniform() < 0.012:               # a clump: three to six tufts close together
            clumps_n += 1
            for _ in range(int(rng.integers(3, 7))):
                a2 = rng.uniform(0, math.tau); d2 = rng.uniform(0.02, 0.22)
                x2, y2 = x + math.cos(a2) * d2, y + math.sin(a2) * d2
                if not allowed(x2, y2):
                    continue
                h = rng.uniform(0.10, 0.22)
                pts.append(np.array([x2, y2])); sc.append((h * rng.uniform(0.9, 1.4), h * rng.uniform(0.9, 1.4), h)); ro.append((0, 0, rng.uniform(0, math.tau)))
                tr.append(traffic_of((x2, y2))); hab.append(0.7); con.append(0.0)
    st.numbers['tuft_clumps_on_bank'] = clumps_n
    recs = make_records('tuft', pts, sc, ro, tr, hab, con)
    ctrl = dict(Density=1.0, **{'Traffic Width': 0.575, 'Waterline': water, 'Damp Reach': 1.5, 'Contact Influence': 0.6, 'Seed': 733})
    host = api.create_native_scatter('Life / tufts', recs, tuft_bank, ground, st.collection(), 'tuft', controls=ctrl, footprint_check=True)
    st.tag(host, 'growth', keep_materials=True); host['life_created'] = 1; st.created.append(host.name)
    results['tuft'] = (host, ctrl)
    # ---- D. pebble fringe: the left and front gravel edges and the pond shore ----------------------------------------
    pts, sc, ro, tr, hab, con = [], [], [], [], [], []
    for k in range(260):                          # left edge of the court (the pond and path side)
        y = rng.uniform(gy0 + 0.2, gy1 - 0.1)
        x = gx0 - rng.uniform(0.02, 0.22)
        pts.append(np.array([x, y]))
    for k in range(90):                            # near edge of the court
        x = rng.uniform(gx0 + 0.2, gx1 - 0.2)
        y = gy0 - rng.uniform(0.02, 0.2)
        pts.append(np.array([x, y]))
    n_edge = len(pts)
    for p in cand[:9000]:
        x, y = float(p[0]), float(p[1])
        dz = st.ground_z(x, y) - water
        if allowed(x, y) and 0.0 < dz < 0.10 and rng.uniform() < 0.28:
            pts.append(np.array([x, y]))
    for p in pts:
        s = rng.uniform(0.5, 1.5) * 0.04
        sc.append((s * rng.uniform(0.8, 1.3), s * rng.uniform(0.8, 1.3), s * rng.uniform(0.6, 1.0))); ro.append((0, 0, rng.uniform(0, math.tau)))
        tr.append(traffic_of(p)); hab.append(0.8); con.append(0.2)
    recs = make_records('pebble', pts, sc, ro, tr, hab, con)
    ctrl = dict(Density=1.0, **{'Traffic Width': 0.575, 'Waterline': water, 'Damp Reach': 1.0, 'Contact Influence': 0.6, 'Seed': 307})
    host = api.create_native_scatter('Life / pebble fringe', recs, peb_bank, ground, st.collection(), 'pebble', controls=ctrl, footprint_check=True)
    st.tag(host, 'ground.earth', keep_materials=True); host['life_created'] = 1; st.created.append(host.name)
    results['pebble'] = (host, ctrl)
    bpy.context.view_layer.update()
    for key, (host, ctrl) in results.items():
        exp, nrec = expected_kept(st, host, ctrl)
        got = count_instances(host)
        contract = json.loads(host['astra_native_contract'])
        st.numbers['scatter_' + key] = dict(candidates=contract['candidate_count'], retained_after_footprint=contract['retained_candidates'],
                                            expected_kept=round(exp, 1), instances=got, within_12pct=bool(abs(got - exp) <= 0.12 * max(exp, 1.0)))
    st.numbers['moss_collar_perimeter_samples'] = n_by
    return results


# ------------------------------------------------------------------------------------------------ 3. POND
POND_C = (-3.0, 1.0)


def scene_hit_name(x, y, z0=8.0):
    """Name of the first evaluated object a vertical ray meets at (x, y), or None."""
    dg = bpy.context.evaluated_depsgraph_get()
    ok, loc, nrm, idx, ob, mat = bpy.context.scene.ray_cast(dg, Vector((x, y, z0)), Vector((0, 0, -1)))
    return (ob.name if ok else None), (loc.z if ok else None)


CANOPY = ('Maple ', 'Pine ', 'Bamboo ')


def clear_at(x, y, ground_ok=('Astra / Courtyard receiving ground', 'Pond water', 'Life / pond bed')):
    """True when nothing solid stands on this spot: the first thing a ray from high above meets is the ground, the water, the bed or a tree
    canopy (leaves hang above the ground, so they do not count), and a ray from 0.6 m over the ground meets the ground itself."""
    hn, _ = scene_hit_name(x, y)
    if hn is not None and hn not in ground_ok and not hn.startswith(CANOPY):
        return False
    gz = max(st_ground_z(x, y), WATER_Z)
    hn2, _ = scene_hit_name(x, y, gz + 0.6)
    return hn2 is None or hn2 in ground_ok


_STAGE_REF = {}


def st_ground_z(x, y):
    return _STAGE_REF['st'].ground_z(x, y)


def water_material(st):
    real = st.real

    def build(m, nodes, links):
        att = nodes.new('ShaderNodeAttribute'); att.attribute_type = 'GEOMETRY'; att.attribute_name = 'depth'
        mr = nodes.new('ShaderNodeMapRange'); mr.inputs['From Min'].default_value = 0.0; mr.inputs['From Max'].default_value = 0.46
        links.new(att.outputs['Fac'], mr.inputs['Value'])
        ramp = nodes.new('ShaderNodeValToRGB')
        cr = ramp.color_ramp
        stops = [(0.0, (0.90, 0.98, 0.94)), (0.30, (0.58, 0.82, 0.76)), (0.62, (0.30, 0.60, 0.57)), (1.0, (0.16, 0.42, 0.42))]
        while len(cr.elements) > 1:
            cr.elements.remove(cr.elements[-1])
        cr.elements[0].position = stops[0][0]; cr.elements[0].color = (*stops[0][1], 1)
        for pos, col in stops[1:]:
            e = cr.elements.new(pos); e.color = (*col, 1)
        if not real:
            cr.interpolation = 'CONSTANT'                     # three flat passes of colour: shallow, middle, deep
        links.new(mr.outputs['Result'], ramp.inputs['Fac'])
        b, out = principled_out(nodes, links, Roughness=0.03 if real else 0.05, IOR=1.33)
        b.inputs['Transmission Weight'].default_value = 1.0
        b.inputs['Specular IOR Level'].default_value = 0.55
        links.new(ramp.outputs['Color'], b.inputs['Base Color'])
        # ripples: a soft bump (kept from the old water) so reflections stay crisp but not mirror-flat
        tc = nodes.new('ShaderNodeTexCoord'); wn = nodes.new('ShaderNodeTexNoise')
        wn.inputs['Scale'].default_value = 6.0; wn.inputs['Detail'].default_value = 2.0
        links.new(tc.outputs['Object'], wn.inputs['Vector'])
        bump = nodes.new('ShaderNodeBump'); bump.inputs['Strength'].default_value = 0.035 if real else 0.0; bump.inputs['Distance'].default_value = 0.03
        links.new(wn.outputs['Fac'], bump.inputs['Height']); links.new(bump.outputs['Normal'], b.inputs['Normal'])
        # shadow rays pass through (Cycles treats refractive glass as opaque for shadows, which would leave the bed unlit)
        lp = nodes.new('ShaderNodeLightPath'); tp = nodes.new('ShaderNodeBsdfTransparent')
        mix = nodes.new('ShaderNodeMixShader')
        links.new(lp.outputs['Is Shadow Ray'], mix.inputs['Fac']); links.new(b.outputs['BSDF'], mix.inputs[1]); links.new(tp.outputs['BSDF'], mix.inputs[2])
        links.new(mix.outputs['Shader'], out.inputs['Surface'])
    m = material('Pond water', build)
    m.diffuse_color = (0.05, 0.18, 0.18, 1)
    return m


def bed_material(st):
    def build(m, nodes, links):
        tc = nodes.new('ShaderNodeTexCoord')
        no = nodes.new('ShaderNodeTexNoise'); no.inputs['Scale'].default_value = 3.0; no.inputs['Detail'].default_value = 4.0
        links.new(tc.outputs['Object'], no.inputs['Vector'])
        ramp = nodes.new('ShaderNodeValToRGB')
        ramp.color_ramp.elements[0].position = 0.35; ramp.color_ramp.elements[0].color = (0.075, 0.068, 0.050, 1)
        ramp.color_ramp.elements[1].position = 0.65; ramp.color_ramp.elements[1].color = (0.150, 0.130, 0.095, 1)
        if not st.real:
            ramp.color_ramp.interpolation = 'CONSTANT'
        links.new(no.outputs['Fac'], ramp.inputs['Fac'])
        b, out = principled_out(nodes, links, Roughness=0.9)
        links.new(ramp.outputs['Color'], b.inputs['Base Color'])
    m = material('Life / pond bed', build)
    m.diffuse_color = (0.05, 0.045, 0.035, 1)
    return m


def stem_material(st):
    def build(m, nodes, links):
        b, out = principled_out(nodes, links, Base_Color=(0.05, 0.11, 0.03, 1), Roughness=0.6)
    return material('Life / lily stem', build)


def iris_material(st):
    def build(m, nodes, links):
        tc = nodes.new('ShaderNodeTexCoord')
        sep = nodes.new('ShaderNodeSeparateXYZ'); links.new(tc.outputs['Generated'], sep.inputs['Vector'])
        ramp = nodes.new('ShaderNodeValToRGB')
        ramp.color_ramp.elements[0].position = 0.0; ramp.color_ramp.elements[0].color = (0.04, 0.09, 0.02, 1)
        e = ramp.color_ramp.elements.new(0.7); e.color = (0.11, 0.24, 0.035, 1)
        e = ramp.color_ramp.elements.new(1.0); e.color = (0.22, 0.30, 0.05, 1)
        if not st.real:
            ramp.color_ramp.interpolation = 'CONSTANT'
        links.new(sep.outputs['Z'], ramp.inputs['Fac'])
        b, out = principled_out(nodes, links, Roughness=0.55)
        links.new(ramp.outputs['Color'], b.inputs['Base Color'])
        tr = nodes.new('ShaderNodeBsdfTranslucent'); links.new(ramp.outputs['Color'], tr.inputs['Color'])
        mix = nodes.new('ShaderNodeMixShader'); mix.inputs['Fac'].default_value = 0.35
        links.new(b.outputs['BSDF'], mix.inputs[1]); links.new(tr.outputs['BSDF'], mix.inputs[2]); links.new(mix.outputs['Shader'], out.inputs['Surface'])
    m = material('Life / iris blade', build)
    m.use_backface_culling = False
    m.diffuse_color = (0.12, 0.24, 0.04, 1)
    return m


def replace_mesh(ob, me, keep_material=True):
    old = ob.data
    if keep_material and len(old.materials):
        for m in old.materials:
            me.materials.append(m)
    ob.data = me
    if old.users == 0:
        bpy.data.meshes.remove(old)


def build_pond(st, ctx=None):
    rng = np.random.default_rng(st.seed + 31)
    step = 0.15
    x0, x1, y0, y1 = POND_C[0] - 4.3, POND_C[0] + 4.3, POND_C[1] - 3.3, POND_C[1] + 3.3
    xs = np.arange(x0, x1 + 1e-6, step); ys = np.arange(y0, y1 + 1e-6, step)
    nx, ny = len(xs), len(ys)
    gz = np.array([[st.ground_z(x, y) for x in xs] for y in ys])            # (ny, nx)
    draw = WATER_Z - gz
    faces = []
    keep_v = {}
    for j in range(ny - 1):
        for i in range(nx - 1):
            if max(draw[j, i], draw[j, i + 1], draw[j + 1, i], draw[j + 1, i + 1]) > 0.0:
                faces.append((j * nx + i, j * nx + i + 1, (j + 1) * nx + i + 1, (j + 1) * nx + i))
    used = sorted(set(v for f in faces for v in f))
    remap = {v: k for k, v in enumerate(used)}
    V = np.array([(xs[v % nx], ys[v // nx], WATER_Z) for v in used], dtype=np.float32)
    depth = np.array([max(0.0, draw[v // nx, v % nx]) for v in used], dtype=np.float32)
    F = np.array([[remap[v] for v in f] for f in faces], dtype=np.int32)
    me = mesh_from_arrays('Pond water', V, F, smooth=False)
    a = me.attributes.new('depth', 'FLOAT', 'POINT')
    a.data.foreach_set('value', depth)
    wm = water_material(st)
    me.materials.append(wm)
    ob = bpy.data.objects['Pond water']
    old = ob.data
    ob.data = me
    if old.users == 0:
        bpy.data.meshes.remove(old)
    st.tag(ob, 'water'); st.changed.append('Pond water'); st.changed.append('material Pond water')
    st.numbers['pond_water_faces'] = len(F)
    st.numbers['pond_depth_max_m'] = round(float(depth.max()), 3)
    # ---- the bed: a silt plane 0.32 m below the water, level with the ground where the bank rises above it ------------------
    bstep = 0.1
    bxs = np.arange(x0, x1 + 1e-6, bstep); bys = np.arange(y0, y1 + 1e-6, bstep)
    bnx, bny = len(bxs), len(bys)
    bed_level = WATER_Z - 0.32
    BG = np.array([[st.ground_z(x, y) for x in bxs] for y in bys])
    PX, PY = np.meshgrid(bxs, bys)
    pts = np.stack([PX.ravel(), PY.ravel(), np.zeros(PX.size)], axis=1)
    undulate = 0.025 * smooth_noise(pts, 77, 0.9, 3).reshape(bny, bnx)
    BZ = np.maximum(bed_level + undulate, BG) - 0.004                         # under the ground wherever the ground is higher
    # drop cells that lie entirely under the ground (nothing to see)
    bf = []
    for j in range(bny - 1):
        for i in range(bnx - 1):
            c = [(j, i), (j, i + 1), (j + 1, i + 1), (j + 1, i)]
            if any(BG[q] < (bed_level + undulate[q]) - 0.004 for q in c):
                bf.append(tuple(q[0] * bnx + q[1] for q in c))
    bused = sorted(set(v for f in bf for v in f)); bre = {v: k for k, v in enumerate(bused)}
    BV = np.array([(bxs[v % bnx], bys[v // bnx], BZ[v // bnx, v % bnx]) for v in bused], dtype=np.float32)
    BF = np.array([[bre[v] for v in f] for f in bf], dtype=np.int32)
    bme = mesh_from_arrays('Life / pond bed', BV, BF, smooth=st.real)
    bme.materials.append(bed_material(st))
    bed = st.new_object('Life / pond bed', bme, 'water', keep_materials=True)
    st.numbers['pond_bed_faces'] = len(BF)

    def bed_z(x, y):
        i = int(np.clip(round((x - x0) / bstep), 0, bnx - 1)); j = int(np.clip(round((y - y0) / bstep), 0, bny - 1))
        return float(BZ[j, i])
    # ---- pebbles on the bed (real stones laid in, denser near the shore) --------------------------------------------------
    rng_p = np.random.default_rng(st.seed + 32)
    peb_mats = [bpy.data.materials[f'Astra / pebbles tone {i}'] for i in range(4)]
    srcV, srcF = [], []
    for v in range(6):
        V0, F0 = _unit_dome(st, v, rng_p, 'pebble')
        srcV.append(V0); srcF.append(F0)
    allV, allF, matidx = [], [], []
    off = 0
    n_try = 0
    placed = 0
    placed_xy = []
    target = 650 if st.real else 360
    while placed < target and n_try < 30000:
        n_try += 1
        x = rng_p.uniform(x0, x1); y = rng_p.uniform(y0, y1)
        d = WATER_Z - st.ground_z(x, y)
        if d < 0.04:
            continue
        zb = bed_z(x, y)
        gzb = st.ground_z(x, y)
        # density falls with depth: shallow edge full, the middle sparse
        if rng_p.uniform() > np.clip(1.2 - d / 0.5, 0.18, 1.0):
            continue
        k = int(rng_p.integers(0, 6))
        s = rng_p.uniform(0.025, 0.07) * (1.0 if st.real else 1.25)
        if any(math.hypot(x - qx, y - qy) < 1.1 * (s + qs) for qx, qy, qs in placed_xy[-400:]):
            continue                                                           # stones lie beside each other, not through each other
        placed_xy.append((x, y, s))
        sc = np.array([s * rng_p.uniform(0.8, 1.4), s * rng_p.uniform(0.8, 1.4), s * rng_p.uniform(0.6, 1.0)])
        th = rng_p.uniform(0, math.tau)
        R = np.array([[math.cos(th), -math.sin(th), 0], [math.sin(th), math.cos(th), 0], [0, 0, 1]])
        top = max(zb, gzb)
        Vp = (srcV[k] * sc) @ R.T + np.array([x, y, top - 0.012])
        allV.append(Vp); allF.append(srcF[k] + off); off += len(Vp); matidx.append(np.full(len(srcF[k]), int(rng_p.integers(0, 4))))
        placed += 1
    if allV:
        PV = np.concatenate(allV); PF = np.concatenate(allF); PM = np.concatenate(matidx)
        pme = mesh_from_arrays('Life / pond pebbles', PV, PF, smooth=st.real)
        for m in peb_mats:
            pme.materials.append(m)
        pme.polygons.foreach_set('material_index', PM.astype(np.int32))
        pme.update()
        pebs = st.new_object('Life / pond pebbles', pme, 'ground.earth', keep_materials=True)
        st.numbers['pond_pebbles'] = placed
    # ---- lily pads: same places, uneven outlines, a slight upturned rim; plus a few small extras --------------------------
    pads_ob = bpy.data.objects['Lily pads']
    pm = pads_ob.data
    P0 = np.array([tuple(v.co) for v in pm.vertices]).reshape(-1, 3)
    centres = []
    if len(P0) % 19 == 0 and len(P0) >= 19:
        for k in range(len(P0) // 19):
            c = P0[19 * k]
            r = float(np.mean(np.hypot(P0[19 * k + 1:19 * k + 19, 0] - c[0], P0[19 * k + 1:19 * k + 19, 1] - c[1])))
            centres.append((c[0], c[1], r))
    if not centres:                                    # fallback after a re-run: islands of the current mesh are not needed, use stored centres
        centres = [tuple(c) for c in json.loads(pads_ob.get('life_pad_centres', '[]'))]
    extras = []
    for (cx, cy, r) in list(centres):
        if rng.uniform() < 0.5:
            for _ in range(2):
                a = rng.uniform(0, math.tau); dd = rng.uniform(0.28, 0.5)
                extras.append((cx + math.cos(a) * dd, cy + math.sin(a) * dd, rng.uniform(0.06, 0.1)))
    good = []
    for (x, y, r) in extras:
        hn, _ = scene_hit_name(x, y)
        if (hn in ('Pond water', 'Life / pond bed', 'Astra / Courtyard receiving ground') or (hn or '').startswith(CANOPY)) and WATER_Z - st.ground_z(x, y) > 0.2 \
                and clear_at(x, y) and all(math.hypot(x - a, y - b) > 0.35 + r for a, b, _ in centres):
            good.append((x, y, r))
    pads_ob['life_pad_centres'] = json.dumps([list(map(float, c)) for c in centres])
    allc = centres + good[:8]
    V, F, C = [], [], []
    off = 0
    for (cx, cy, r) in allc:
        notch = rng.uniform(0, math.tau)
        n = 20 if st.real else 9
        ph = rng.uniform(0, 6.3, 3)
        ring = []
        for k in range(n):
            a = notch + 0.30 + k * (math.tau - 0.60) / (n - 1)
            wob = 1 + 0.13 * math.sin(2 * a + ph[0]) + 0.08 * math.sin(3 * a + ph[1]) + (rng.uniform(-0.10, 0.10) if not st.real else 0.0)
            ring.append((a, r * wob))
        base = off
        zc = WATER_Z + 0.004
        V.append((cx, cy, zc)); off += 1
        if st.real:
            inner = []
            for a, rad in ring:
                V.append((cx + math.cos(a) * rad * 0.55, cy + math.sin(a) * rad * 0.55, zc + 0.001)); inner.append(off); off += 1
            outer = []
            for a, rad in ring:
                V.append((cx + math.cos(a) * rad, cy + math.sin(a) * rad, zc + 0.008 + 0.01 * (rad / r - 0.6))); outer.append(off); off += 1
            for k in range(n - 1):
                F.append((base, inner[k], inner[k + 1]))
                F.append((inner[k], outer[k], outer[k + 1])); F.append((inner[k], outer[k + 1], inner[k + 1]))
        else:
            ids = []
            for k, (a, rad) in enumerate(ring):
                V.append((cx + math.cos(a) * rad, cy + math.sin(a) * rad, zc + (0.006 if k % 3 == 0 else 0.0))); ids.append(off); off += 1
            for k in range(n - 1):
                F.append((base, ids[k], ids[k + 1]))
    V = np.array(V, dtype=np.float32); F = np.array(F, dtype=np.int32)
    nme = mesh_from_arrays('Lily pads', V, F, smooth=False, mat=None)
    for m in pm.materials:
        nme.materials.append(m)
    pads_ob.data = nme
    if pm.users == 0:
        bpy.data.meshes.remove(pm)
    st.tag(pads_ob, 'growth', keep_materials=True); st.changed.append('Lily pads')
    st.numbers['lily_pads'] = len(allc)
    # ---- lily stems down to the bed --------------------------------------------------------------------------------------------
    sV, sF = [], []
    so = 0
    for (cx, cy, r) in allc:
        zb = bed_z(cx, cy)
        if zb > WATER_Z - 0.05:
            continue
        sides = 4
        segs = 4
        sway = np.array([rng.uniform(-0.05, 0.05), rng.uniform(-0.05, 0.05)])
        for sgi in range(segs + 1):
            t = sgi / segs
            z = WATER_Z + 0.0 - t * (WATER_Z - zb)
            c = np.array([cx, cy]) + sway * math.sin(t * math.pi)
            rad = 0.006 * (1 - 0.3 * t)
            for q in range(sides):
                a = q * math.tau / sides
                sV.append((c[0] + math.cos(a) * rad, c[1] + math.sin(a) * rad, z))
        for sgi in range(segs):
            for q in range(sides):
                q2 = (q + 1) % sides
                a0 = so + sgi * sides + q; a1 = so + sgi * sides + q2; b0 = a0 + sides; b1 = a1 + sides
                sF.append((a0, a1, b1, b0))
        so += (segs + 1) * sides
    if sV:
        sme = mesh_from_arrays('Life / lily stems', np.array(sV), np.array(sF), smooth=False)
        sme.materials.append(stem_material(st))
        st.new_object('Life / lily stems', sme, 'growth', keep_materials=True)
    # ---- iris / sweet-flag clumps near the bridge landings -----------------------------------------------------------------------
    piers = [bpy.data.objects.get(f'Bridge pier {i}') for i in range(4)]
    land = []
    for p in (piers[0], piers[3]):
        if p is not None:
            Vp = world_vertices(p)
            land.append(Vp[:, :2].mean(axis=0))
    iV, iF = [], []
    io = 0
    clumps = []
    tries = 0
    while len(clumps) < (7 if st.real else 5) and tries < 4000 and land:
        tries += 1
        L0 = land[rng.integers(0, len(land))]
        x, y = L0[0] + rng.normal(0, 1.1), L0[1] + rng.normal(0, 1.1)
        gzv = st.ground_z(x, y)
        if not (-0.17 < gzv - WATER_Z < 0.06):
            continue
        if not clear_at(x, y):
            continue
        if any(math.hypot(x - a, y - b) < 0.9 for a, b in clumps):
            continue
        clumps.append((x, y))
    for (x, y) in clumps:
        z0 = max(st.ground_z(x, y), WATER_Z - 0.05) - 0.02
        nb = int(rng.integers(10, 17))
        for _ in range(nb):
            a = rng.uniform(0, math.tau); lean = rng.uniform(0.05, 0.28); hgt = rng.uniform(0.28, 0.62); w = rng.uniform(0.010, 0.017)
            d = np.array([math.cos(a), math.sin(a)]); sd = np.array([-d[1], d[0]])
            base_xy = np.array([x, y]) + d * rng.uniform(0, 0.1)
            segs = 3
            prev = None
            for s in range(segs + 1):
                t = s / segs
                c = base_xy + d * lean * hgt * t ** 1.7
                z = z0 + hgt * t - (0.04 * t ** 3)
                ww = w * (1 - t) ** 0.7 if s < segs else 0.0
                b = len(iV)
                if s < segs:
                    iV.append((c[0] + sd[0] * ww, c[1] + sd[1] * ww, z)); iV.append((c[0] - sd[0] * ww, c[1] - sd[1] * ww, z))
                else:
                    iV.append((c[0], c[1], z))
                if prev is not None:
                    pa, pb = prev
                    if s < segs:
                        iF.append((pa, pb, b + 1)); iF.append((pa, b + 1, b))
                    else:
                        iF.append((pa, pb, b))
                prev = (b, b + 1)
    if iV:
        ime = mesh_from_arrays('Life / iris clumps', np.array(iV), np.array(iF), smooth=False)
        ime.materials.append(iris_material(st))
        st.new_object('Life / iris clumps', ime, 'growth', keep_materials=True)
    st.numbers['iris_clumps'] = len(clumps)
    return dict(bed_level=bed_level)


# ------------------------------------------------------------------------------------------------ 4. PINE
def pine_material(st):
    def build(m, nodes, links):
        vc = nodes.new('ShaderNodeVertexColor'); vc.layer_name = 'Col'
        b, out = principled_out(nodes, links, Roughness=0.7)
        b.inputs['Emission Strength'].default_value = 0.03
        links.new(vc.outputs['Color'], b.inputs['Base Color']); links.new(vc.outputs['Color'], b.inputs['Emission Color'])
        if st.real:
            tr = nodes.new('ShaderNodeBsdfTranslucent'); links.new(vc.outputs['Color'], tr.inputs['Color'])
            mix = nodes.new('ShaderNodeMixShader'); mix.inputs['Fac'].default_value = 0.25
            links.new(b.outputs['BSDF'], mix.inputs[1]); links.new(tr.outputs['BSDF'], mix.inputs[2]); links.new(mix.outputs['Shader'], out.inputs['Surface'])
    m = material('Pine needles', build)
    m.use_backface_culling = False
    m.diffuse_color = (0.03, 0.10, 0.05, 1)
    return m


def pine_pad(st, centre, radius, rng, thick=0.24):
    """One flat needle pad: ragged outline, three rings on top, a sloping side and a dark underside; unequal flat planes."""
    n = 18 if st.real else 12
    ph = rng.uniform(0, 6.3, 3)
    ang = np.array([(k + rng.uniform(-0.22, 0.22)) * math.tau / n for k in range(n)])
    edge = 1 + 0.16 * np.sin(2 * ang + ph[0]) + 0.10 * np.sin(3 * ang + ph[1]) + rng.uniform(-0.08, 0.08, n)
    rings = [0.0, 0.52, 0.84, 1.0]
    V = [(0.0, 0.0, thick * 0.55)]
    for ri in (1, 2, 3):
        rr = rings[ri]
        for k in range(n):
            rad = radius * rr * edge[k] * (1 + rng.uniform(-0.05, 0.05))
            z = thick * (0.55 - 0.45 * rr ** 2) + rng.uniform(-0.035, 0.035)
            V.append((math.cos(ang[k]) * rad, math.sin(ang[k]) * rad * 0.92, z))
    rim_top = 1 + 3 * 0 + 0
    for k in range(n):                       # lower rim (sloping side), then the underside centre
        rad = radius * edge[k] * 0.86
        V.append((math.cos(ang[k]) * rad, math.sin(ang[k]) * rad * 0.92, -thick * 0.45 + rng.uniform(-0.03, 0.03)))
    V.append((0.0, 0.0, -thick * 0.70))
    V = np.array(V, dtype=np.float32)
    top0, r1, r2, r3, low, bot = 0, 1, 1 + n, 1 + 2 * n, 1 + 3 * n, 1 + 4 * n
    F, role = [], []
    for k in range(n):
        k2 = (k + 1) % n
        F.append((top0, r1 + k, r1 + k2)); role.append('top')
        F.append((r1 + k, r2 + k, r2 + k2)); role.append('top'); F.append((r1 + k, r2 + k2, r1 + k2)); role.append('top')
        F.append((r2 + k, r3 + k, r3 + k2)); role.append('top'); F.append((r2 + k, r3 + k2, r2 + k2)); role.append('top')
        F.append((r3 + k, low + k, low + k2)); role.append('side'); F.append((r3 + k, low + k2, r3 + k2)); role.append('side')
        F.append((bot, low + k2, low + k)); role.append('under')
    V += np.array(centre, dtype=np.float32)
    F = np.array(F, dtype=np.int32)
    return V, F, role


def needle_fringe(st, centre, radius, rng, count):
    """Spiky needle tufts (three thin triangles each) along the rim and over the top, for the real look."""
    V, F = [], []
    for _ in range(count):
        rr = math.sqrt(rng.uniform(0.35, 1.05)); a = rng.uniform(0, math.tau)
        p = np.array([centre[0] + math.cos(a) * radius * rr, centre[1] + math.sin(a) * radius * rr * 0.92, centre[2] + 0.12 * (1 - rr ** 2) + 0.02])
        ln = rng.uniform(0.07, 0.15)
        out = np.array([math.cos(a), math.sin(a), 0.0])
        for q in range(3):
            aa = rng.uniform(0, math.tau)
            d = out * rng.uniform(0.3, 0.8) + np.array([math.cos(aa) * 0.5, math.sin(aa) * 0.5, rng.uniform(0.3, 0.9)])
            d = d / np.linalg.norm(d) * ln
            side = np.cross(d, [0, 0, 1.0]); side = side / (np.linalg.norm(side) + 1e-9) * 0.006
            b = len(V)
            V.extend([p + side, p - side, p + d]); F.append((b, b + 1, b + 2))
    return np.array(V, dtype=np.float32).reshape(-1, 3), np.array(F, dtype=np.int32).reshape(-1, 3)


def build_pine(st, ctx=None):
    rng = np.random.default_rng(st.seed + 41)
    mat = pine_material(st)
    tr = bpy.data.objects['Pine trunk']
    base = tr.data.splines[0].points[0].co
    anchors = []
    for nm in ('Pine limb', 'Pine limb.001', 'Pine limb.002', 'Pine limb.003', 'Pine limb.004'):
        ob = bpy.data.objects.get(nm)
        if ob is not None:
            pts = ob.data.splines[0].points
            anchors.append(np.array([pts[-1].co.x, pts[-1].co.y, pts[-1].co.z]))
    radii = [0.95, 0.85, 0.9, 0.7, 0.75]
    allV, allF, allC = [], [], []
    off = 0
    pads = []
    for i, a in enumerate(anchors):
        pads.append((a + np.array([0, 0, 0.10]), radii[i % 5] * (1.05 if st.real else 1.0)))
    # layered: a smaller pad above and behind three of the big ones, carried by a short new limb
    sat = []
    for i in (0, 2, 4):
        if i < len(pads):
            c, r = pads[i]
            sat.append((c + np.array([rng.uniform(-0.25, 0.25), rng.uniform(0.1, 0.3), 0.36]), r * 0.5))
    bark = bpy.data.materials['Bark']
    made_limbs = 0
    for (c, r), (src_c, src_r) in zip(sat, [pads[i] for i in (0, 2, 4) if i < len(pads)]):
        curve_object(st, 'Pine limb.' + format(5 + made_limbs, '03d'), [tuple(src_c - np.array([0, 0, 0.03])), tuple((src_c + c) / 2 + np.array([0.04, 0, -0.02])), tuple(c - np.array([0, 0, 0.08]))], 0.028, 0.014, bark)
        made_limbs += 1
    cols = {'top': ((0.020, 0.075, 0.045), (0.060, 0.150, 0.075)), 'side': ((0.012, 0.040, 0.030), (0.030, 0.085, 0.050)), 'under': ((0.006, 0.020, 0.016), (0.014, 0.040, 0.026))}
    needle_n = 0
    for (c, r) in pads + sat:
        V, F, role = pine_pad(st, c, r, rng)
        C = np.zeros((len(F), 4))
        for fi, rl in enumerate(role):
            a, b = np.array(cols[rl][0]), np.array(cols[rl][1])
            C[fi, :3] = a + (b - a) * rng.uniform(0, 1)
            C[fi, 3] = 1
        allV.append(V); allF.append(F + off); allC.append(C); off += len(V)
        if st.real:
            nv, nf = needle_fringe(st, c, r, rng, int(120 * r * r + 40))
            if len(nv):
                allV.append(nv); allF.append(nf + off); off += len(nv)
                cc = np.zeros((len(nf), 4)); cc[:, :3] = np.array(cols['top'][1]) * rng.uniform(0.5, 1.1, (len(nf), 1)); cc[:, 3] = 1
                allC.append(cc); needle_n += len(nf)
    V = np.concatenate(allV); F = np.concatenate(allF); C = np.concatenate(allC)
    ob = bpy.data.objects['Pine pads']
    me = mesh_from_arrays('Pine pads', V, F, smooth=False, colors=C)
    me.materials.append(mat)
    old = ob.data
    ob.data = me
    if old.users == 0:
        bpy.data.meshes.remove(old)
    st.tag(ob, 'leaf'); st.changed.append('Pine pads')
    st.numbers['pine_pads'] = len(pads) + len(sat)
    st.numbers['pine_pad_faces'] = len(F)
    return dict(pads=pads, sat=sat)


# ------------------------------------------------------------------------------------------------ 5. SHRUBS
def shrub_material(st):
    def build(m, nodes, links):
        tc = nodes.new('ShaderNodeTexCoord')
        vor = nodes.new('ShaderNodeTexVoronoi'); vor.inputs['Scale'].default_value = 26.0 if st.real else 5.0
        links.new(tc.outputs['Object'], vor.inputs['Vector'])
        ramp = nodes.new('ShaderNodeValToRGB')
        ramp.color_ramp.elements[0].position = 0.25; ramp.color_ramp.elements[0].color = (0.016, 0.050, 0.020, 1)
        ramp.color_ramp.elements[1].position = 0.85; ramp.color_ramp.elements[1].color = (0.060, 0.135, 0.040, 1)
        if not st.real:
            ramp.color_ramp.interpolation = 'CONSTANT'
        links.new(vor.outputs['Distance'], ramp.inputs['Fac'])
        b, out = principled_out(nodes, links, Roughness=0.62)
        links.new(ramp.outputs['Color'], b.inputs['Base Color'])
        if st.real:
            bump = nodes.new('ShaderNodeBump'); bump.inputs['Strength'].default_value = 0.6; bump.inputs['Distance'].default_value = 0.01
            links.new(vor.outputs['Distance'], bump.inputs['Height']); links.new(bump.outputs['Normal'], b.inputs['Normal'])
    m = material('Life / shrub', build)
    m.diffuse_color = (0.04, 0.10, 0.03, 1)
    return m


def build_shrubs(st, ctx=None):
    rng = np.random.default_rng(st.seed + 51)
    sc = scene_context(st)
    gx0, gy0, gx1, gy1 = sc['gravel']
    stones = sc['rocks'] + sc['gravel_rocks'] + sc['pond_stones'] + sc['steps'] + sc['others']
    for nm in ('Lantern post', 'Lantern gallery', 'Lantern firebox', 'Lantern cap', 'Bridge pier 0', 'Bridge pier 3'):
        o = bpy.data.objects.get(nm)
        if o is not None:
            stones.append(o)
    foots = []
    for o in stones:
        fp = foot_print(st, o)
        if fp is not None:
            c, h = fp
            rad = max(np.hypot(*(np.array(p) - c)) for p in h)
            foots.append((c, rad))
    placed = []

    def free(x, y, r):
        z = st.ground_z(x, y)
        if z < WATER_Z + 0.08:
            return False
        if in_rect(x, y, (gx0, gy0, gx1, gy1), margin=0.15) or in_rect(x, y, sc['hall'], margin=0.2):
            return False
        for c, rad in foots:
            if math.hypot(x - c[0], y - c[1]) < rad + r * 0.8:
                return False
        for (px, py, pr) in placed:
            if math.hypot(x - px, y - py) < (pr + r) * 0.7:
                return False
        if len(sc['path']) > 1 and dist_to_polyline(np.array([x, y]), sc['path']) < 0.55 + r * 0.5:
            return False
        if not clear_at(x, y, ground_ok=('Astra / Courtyard receiving ground',)):
            return False
        # gentle slope only
        e = 0.2
        if abs(st.ground_z(x + e, y) - st.ground_z(x - e, y)) > 0.25 or abs(st.ground_z(x, y + e) - st.ground_z(x, y - e)) > 0.25:
            return False
        return True
    groups = []
    lb = bpy.data.objects.get('Lantern base')
    Lc = world_vertices(lb)[:, :2].mean(axis=0) if lb is not None else np.array([0.95, 1.1])
    groups.append(('lantern', Lc, 3, 1.1))
    r3 = sc['rocks']
    if len(r3) >= 4:
        c0 = foot_print(st, r3[3])[0]; c1 = foot_print(st, r3[0])[0]
        groups.append(('rocks A', (c0 + c1) / 2 + np.array([0.0, 0.5]), 2, 0.9))
        c2 = foot_print(st, r3[1])[0]; c3 = foot_print(st, r3[2])[0]
        groups.append(('rocks B', (c2 + c3) / 2 + np.array([0.0, 0.7]), 3, 1.0))
    pt = bpy.data.objects['Pine trunk'].data.splines[0].points[0].co
    groups.append(('pine', np.array([pt.x, pt.y]), 5, 1.5))
    shrubs = []
    for name, c, n, spread in groups:
        got = 0
        for _ in range(400):
            if got >= n:
                break
            r = rng.uniform(0.17, 0.36)                          # radius of the clipped dome
            ang = rng.uniform(0, math.tau); d = rng.uniform(0.35, spread)
            x, y = c[0] + math.cos(ang) * d, c[1] + math.sin(ang) * d
            if free(x, y, r):
                shrubs.append((x, y, r, name)); placed.append((x, y, r)); got += 1
        st.numbers['shrubs_' + name.replace(' ', '_')] = got
    V, F = [], []
    off = 0
    for (x, y, r, name) in shrubs:
        bm = bmesh.new()
        sub = 3 if st.real else 2
        bmesh.ops.create_icosphere(bm, subdivisions=sub, radius=1.0)
        bm.verts.ensure_lookup_table()
        seed = rng.uniform(0, 100)
        for v in bm.verts:
            if st.real:
                jit = 0.05 * math.sin(v.co.x * 5 + seed) * math.cos(v.co.y * 4.3 + seed * 1.3) + 0.03 * math.sin(v.co.z * 7 + seed)
                v.co *= (1 + jit)
            else:
                jit = rng.uniform(-0.12, 0.12)
                v.co *= (1 + jit)
        bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.z < -0.12], context='VERTS')
        for v in bm.verts:
            v.co.x *= r * 1.0; v.co.y *= r * 1.05; v.co.z = (v.co.z + 0.12) * r * 0.78
        bm.faces.ensure_lookup_table()
        idx = {v: i for i, v in enumerate(bm.verts)}
        Vs = np.array([tuple(v.co) for v in bm.verts]) + np.array([x, y, st.ground_z(x, y) - 0.04])
        Fs = np.array([[idx[v] for v in f.verts] for f in bm.faces if len(f.verts) == 3])
        bm.free()
        V.append(Vs); F.append(Fs + off); off += len(Vs)
    if V:
        V = np.concatenate(V); F = np.concatenate(F)
        me = mesh_from_arrays('Life / shrubs', V, F, smooth=st.real)
        me.materials.append(shrub_material(st))
        ob = st.new_object('Life / shrubs', me, 'growth', keep_materials=True)
        # line of sight from the hero camera to the lantern's lit window: the shrubs must not be in the way
        cam = bpy.context.scene.camera
        win = bpy.data.objects.get('Lantern window glow')
        if cam is not None and win is not None:
            Vw = world_vertices(win)
            target = Vector(tuple(Vw.mean(axis=0)))
            dg = bpy.context.evaluated_depsgraph_get()
            origin = cam.matrix_world.translation
            direction = (target - origin).normalized()
            dist = (target - origin).length
            bvh = BVHTree.FromObject(ob, dg)
            hit = bvh.ray_cast(origin, direction, dist - 0.05)
            st.numbers['shrubs_block_lantern_window'] = hit[0] is not None
        st.numbers['shrubs'] = len(shrubs)
        st.numbers['shrub_faces'] = len(F)
    return {}


# ------------------------------------------------------------------------------------------------ 6. BAMBOO AND LITTER
def _islands(bm):
    seen = set()
    out = []
    for f in bm.faces:
        if f.index in seen:
            continue
        seen.add(f.index)
        stack = [f]
        isl = []
        while stack:
            c = stack.pop()
            isl.append(c)
            for e in c.edges:
                for g in e.link_faces:
                    if g.index not in seen:
                        seen.add(g.index)
                        stack.append(g)
        out.append(isl)
    return out


def _signed_volume(isl):
    vol = 0.0
    for f in isl:
        vs = [v.co for v in f.verts]
        for i in range(1, len(vs) - 1):
            vol += vs[0].dot(vs[i].cross(vs[i + 1])) / 6.0
    return vol


def bamboo_palette(kind):
    if kind == 'fence':
        return [((0.50, 0.46, 0.18), 3), ((0.42, 0.45, 0.15), 3), ((0.36, 0.33, 0.13), 2), ((0.30, 0.38, 0.11), 2), ((0.55, 0.50, 0.26), 1)]
    return [((0.13, 0.25, 0.04), 3), ((0.28, 0.38, 0.07), 3), ((0.19, 0.24, 0.055), 2), ((0.40, 0.36, 0.13), 1), ((0.20, 0.28, 0.10), 2)]


def build_bamboo(st, ctx=None):
    rng = np.random.default_rng(st.seed + 61)
    fixed = {}
    # recolour material: culm colour from the 'Col' colour attribute, broken up by the old noise as a brightness variation
    def build(m, nodes, links):
        vc = nodes.new('ShaderNodeVertexColor'); vc.layer_name = 'Col'
        tc = nodes.new('ShaderNodeTexCoord'); mp = nodes.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (4, 4, 0.5)
        links.new(tc.outputs['Object'], mp.inputs['Vector'])
        no = nodes.new('ShaderNodeTexNoise'); no.inputs['Scale'].default_value = 3.0; no.inputs['Detail'].default_value = 4.0
        links.new(mp.outputs['Vector'], no.inputs['Vector'])
        mr = nodes.new('ShaderNodeMapRange'); mr.inputs['To Min'].default_value = 0.8; mr.inputs['To Max'].default_value = 1.18
        links.new(no.outputs['Fac'], mr.inputs['Value'])
        mul = nodes.new('ShaderNodeMix'); mul.data_type = 'RGBA'; mul.blend_type = 'MULTIPLY'; mul.inputs['Factor'].default_value = 1.0
        links.new(vc.outputs['Color'], mul.inputs[6])
        cc = nodes.new('ShaderNodeCombineColor')
        for i in range(3):
            links.new(mr.outputs['Result'], cc.inputs[i])
        links.new(cc.outputs['Color'], mul.inputs[7])
        b, out = principled_out(nodes, links, Roughness=0.4)
        links.new(mul.outputs[2], b.inputs['Base Color'])
        fine = nodes.new('ShaderNodeTexNoise'); fine.inputs['Scale'].default_value = 18.0
        links.new(mp.outputs['Vector'], fine.inputs['Vector'])
        bump = nodes.new('ShaderNodeBump'); bump.inputs['Strength'].default_value = 0.1; bump.inputs['Distance'].default_value = 0.02
        links.new(fine.outputs['Fac'], bump.inputs['Height']); links.new(bump.outputs['Normal'], b.inputs['Normal'])
    m = material('Bamboo stalk', build)
    m.diffuse_color = (0.3, 0.38, 0.08, 1)
    st.changed.append('material Bamboo stalk')
    for name, kind in (('Bamboo stalks', 'clump'), ('Bamboo fence', 'fence')):
        ob = bpy.data.objects[name]
        bm = bmesh.new(); bm.from_mesh(ob.data); bm.faces.ensure_lookup_table()
        isl = _islands(bm)
        flipped = 0
        for f_list in isl:
            if _signed_volume(f_list) < 0:
                bmesh.ops.reverse_faces(bm, faces=f_list)
                flipped += 1
        fixed[name] = flipped
        # one colour per culm: islands share a tone by where they stand (culms are ~0.1 m apart on the fence, ~0.15 m in the clumps)
        pal = bamboo_palette(kind)
        w = np.array([p[1] for p in pal], dtype=float); w /= w.sum()
        tone_of = {}
        col = bm.loops.layers.float_color.get('Col') or bm.loops.layers.float_color.new('Col')
        for f_list in isl:
            cen = np.mean([tuple(f.calc_center_median()) for f in f_list], axis=0)
            zspan = max(v.co.z for f in f_list for v in f.verts) - min(v.co.z for f in f_list for v in f.verts)
            if kind == 'fence':
                key = (int(round(cen[1] / 0.085)),) if zspan > 0.5 else ('r', int(round(cen[2] / 0.2)), int(round(cen[1] / 3.0)))
            else:
                key = (int(round(cen[0] / 0.13)), int(round(cen[1] / 0.13)))
            if key not in tone_of:
                k = rng.choice(len(pal), p=w)
                tone_of[key] = np.array(pal[k][0]) * rng.uniform(0.85, 1.15)
            c = tone_of[key].copy()
            if zspan < 0.03:                                          # a node ring: browner and a little darker
                c = c * np.array([1.05, 0.85, 0.6]) * 0.85
            if kind == 'fence' and zspan < 0.4 and zspan >= 0.03 and abs(cen[2]) < 3:  # rails and posts: darker, browner
                c = c * np.array([0.7, 0.62, 0.5])
            for f in f_list:
                for lp in f.loops:
                    lp[col] = (float(c[0]), float(c[1]), float(c[2]), 1.0)
        bm.to_mesh(ob.data)
        bm.free()
        ob.data.update()
        st.tag(ob, 'growth', keep_materials=True)
        st.changed.append(name)
    st.numbers['bamboo_inside_out_pieces_flipped'] = dict(fixed)
    # ---- fallen leaves: fewer, smaller, mixed colours, under the maple and along the moss edge, none on the gravel -------------
    sc = scene_context(st)
    gx0, gy0, gx1, gy1 = sc['gravel']
    tr = bpy.data.objects['Maple trunk'].data.splines[0].points[0].co
    MX, MY = tr.x, tr.y
    leaf_V, leaf_F = leaf_mesh_arrays(st.look, 0, 7)
    n_leaves = 84
    V, F, C = [], [], []
    off = 0
    pal = [((0.55, 0.06, 0.03), 0.30), ((0.85, 0.25, 0.04), 0.28), ((0.80, 0.52, 0.07), 0.14), ((0.30, 0.13, 0.05), 0.20), ((0.40, 0.42, 0.06), 0.08)]
    pw = np.array([p[1] for p in pal]); pw /= pw.sum()
    got = 0
    tries = 0
    on_water = 0
    while got < n_leaves and tries < 6000:
        tries += 1
        r = rng.uniform()
        if r < 0.55:                                                     # under the maple
            x = MX + 1.7 + rng.normal(0, 1.5); y = MY - 0.3 + rng.normal(0, 1.2)
        elif r < 0.85:                                                   # along the moss edge of the pond
            a = rng.uniform(0, math.tau); x = POND_C[0] + math.cos(a) * rng.uniform(3.2, 4.6); y = POND_C[1] + math.sin(a) * rng.uniform(2.5, 3.5)
        else:                                                            # a few on the path side
            x = rng.uniform(-1.5, 2.8); y = rng.uniform(-3.5, 2.5)
        if in_rect(x, y, (gx0, gy0, gx1, gy1), margin=0.05) or in_rect(x, y, sc['hall'], margin=0.0):
            continue
        if not clear_at(x, y):
            continue
        z = max(st.ground_z(x, y), WATER_Z) + (0.006 if st.ground_z(x, y) > WATER_Z else 0.01)
        if st.ground_z(x, y) < WATER_Z:
            if on_water >= 9:
                continue
            on_water += 1
        s = rng.uniform(0.028, 0.045)
        th = rng.uniform(0, math.tau)
        R = np.array([[math.cos(th), -math.sin(th), 0], [math.sin(th), math.cos(th), 0], [0, 0, 1]])
        tilt = rng.normal(0, 0.12, 2)
        Rx = np.array([[1, 0, 0], [0, math.cos(tilt[0]), -math.sin(tilt[0])], [0, math.sin(tilt[0]), math.cos(tilt[0])]])
        Vl = (leaf_V * s) @ (R @ Rx).T + np.array([x, y, z])
        V.append(Vl); F.append(leaf_F + off); off += len(Vl)
        k = rng.choice(len(pal), p=pw)
        c = np.array(pal[k][0]) * rng.uniform(0.8, 1.15)
        C.append(np.concatenate([np.tile(c, (len(leaf_F), 1)), np.ones((len(leaf_F), 1))], axis=1))
        got += 1
    ob = bpy.data.objects['Fallen leaves']
    me = mesh_from_arrays('Fallen leaves', np.concatenate(V), np.concatenate(F), smooth=False, colors=np.concatenate(C))
    me.materials.append(bpy.data.materials['Fallen leaves'])
    old = ob.data
    ob.data = me
    if old.users == 0:
        bpy.data.meshes.remove(old)
    fm = bpy.data.materials['Fallen leaves']
    b = fm.node_tree.nodes.get('Principled BSDF')
    if b:
        b.inputs['Emission Strength'].default_value = 0.03
    st.tag(ob, 'leaf'); st.changed.append('Fallen leaves')
    st.numbers['fallen_leaves'] = got
    st.numbers['fallen_leaves_on_water'] = on_water
    return {}
