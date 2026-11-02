import bpy, bmesh, math, random
import numpy as np
from mathutils import Vector, Euler, Matrix
from lib import *
import terrain
RAD = math.radians

# ---------------- materials ----------------
def m_frond():
    m = new_mat('palm_frond'); nb = NB(m)
    A = nb.n('ShaderNodeAttribute', attribute_name='g'); A.attribute_type = 'GEOMETRY'
    sp = nb.n('ShaderNodeSeparateColor'); nb.link(A.outputs['Color'], sp.inputs[0])
    tip = nb.math('MULTIPLY', nb.math('POWER', sp.outputs[1], 3.0), 1.0)
    var = sp.outputs[2]
    rib = nb.math('GREATER_THAN', var, 1.5)
    c1 = nb.mix(nb.math('MULTIPLY', var, 0.9), (0.025, 0.20, 0.025, 1), (0.07, 0.30, 0.03, 1))
    c2 = nb.mix(nb.math('MULTIPLY', tip, 0.5), c1, (0.20, 0.30, 0.04, 1))
    c3 = nb.mix(rib, c2, (0.28, 0.30, 0.09, 1))
    pr = nb.principled(c3, 0.5)
    tr = nb.n('ShaderNodeBsdfTranslucent')
    tcol = nb.mix(rib, (0.13, 0.42, 0.04, 1), (0.2, 0.25, 0.05, 1))
    nb.link(tcol, tr.inputs['Color'])
    mx = nb.n('ShaderNodeMixShader'); mx.inputs[0].default_value = 0.45
    nb.link(pr.outputs[0], mx.inputs[1]); nb.link(tr.outputs[0], mx.inputs[2])
    nb.out(mx.outputs[0]); return m

def m_leafy(name='leafy', dark=(0.02, 0.09, 0.02), light=(0.08, 0.26, 0.04), scale=2.0, transl=0.4):
    m = new_mat(name); nb = NB(m)
    obj = nb.coord('Object')
    n = nb.noise(nb.mapping(obj, (1, 1, 1.4)), scale, 5, 0.6)
    n2 = nb.noise(obj, scale * 6, 4, 0.65)
    c = nb.ramp(n.outputs['Fac'], [(0.3, (*dark, 1)), (0.7, (*light, 1))])
    c = nb.mix(nb.math('MULTIPLY', n2.outputs['Fac'], 0.6), c.outputs[0], (*[x * 0.4 for x in dark], 1))
    pr = nb.principled(c, 0.55, Normal=nb.bump(n2.outputs['Fac'], 0.6, 0.15))
    tr = nb.n('ShaderNodeBsdfTranslucent'); nb.link(c, tr.inputs['Color'])
    mx = nb.n('ShaderNodeMixShader'); mx.inputs[0].default_value = transl
    nb.link(pr.outputs[0], mx.inputs[1]); nb.link(tr.outputs[0], mx.inputs[2])
    nb.out(mx.outputs[0]); return m

def m_bark():
    m = new_mat('palm_bark'); nb = NB(m)
    obj = nb.coord('Object')
    wv = nb.n('ShaderNodeTexWave'); wv.wave_type = 'BANDS'; wv.bands_direction = 'Z'; wv.wave_profile = 'SAW'
    wv.inputs['Scale'].default_value = 5.0; wv.inputs['Distortion'].default_value = 2.5; wv.inputs['Detail'].default_value = 2
    nb.link(obj, wv.inputs['Vector'])
    n = nb.noise(nb.mapping(obj, (6, 6, 1.5)), 8, 5, 0.6)
    c = nb.ramp(n.outputs['Fac'], [(0.3, (0.16, 0.12, 0.085)), (0.7, (0.34, 0.27, 0.19))])
    mul = nb.n('ShaderNodeMix'); mul.data_type = 'RGBA'; mul.blend_type = 'MULTIPLY'; mul.inputs[0].default_value = 1.0
    ring = nb.ramp(wv.outputs['Fac'], [(0.0, (0.45, 0.45, 0.45)), (0.35, (1, 1, 1))])
    nb.link(c.outputs[0], mul.inputs[6]); nb.link(ring.outputs[0], mul.inputs[7])
    bump = nb.bump(nb.math('ADD', wv.outputs['Fac'], n.outputs['Fac']), 0.9, 0.05)
    p = nb.principled(mul.outputs[2], 0.85, Normal=bump)
    nb.out(p.outputs[0]); return m

M = {}
def mats():
    if M: return M
    M['frond'] = m_frond(); M['bark'] = m_bark()
    M['tree'] = m_leafy('tree_canopy', (0.012, 0.07, 0.015), (0.07, 0.22, 0.035), 1.6, 0.35)
    M['tree2'] = m_leafy('tree_canopy2', (0.02, 0.09, 0.02), (0.14, 0.30, 0.04), 1.4, 0.4)
    M['banana'] = m_leafy('banana_leaf', (0.05, 0.20, 0.03), (0.20, 0.42, 0.05), 3.0, 0.55)
    M['shrub'] = m_leafy('shrub', (0.02, 0.10, 0.02), (0.07, 0.24, 0.04), 3.0, 0.3)
    M['trunk'] = simple_mat('trunk', (0.10, 0.07, 0.05, 1), 0.9)
    M['flower'] = simple_mat('hibiscus', (0.9, 0.025, 0.03, 1), 0.4, Subsurface_Weight=0.2)
    M['flower2'] = simple_mat('frangi', (1.0, 0.75, 0.55, 1), 0.4)
    M['coconut'] = simple_mat('coconut', (0.10, 0.17, 0.03, 1), 0.5)
    M['basalt'] = None
    return M

# ---------------- frond ----------------
def make_frond_mesh(name, L=4.2, a=0.35, b=0.65, nleaf=38, lmax=1.3, seed=1, ang_down=0.55):
    rnd = random.Random(seed)
    V = []; F = []; G = []
    def P(t): return np.array([L * t, 0.0, L * (a * t - b * t * t)])
    def Tg(t):
        d = np.array([L, 0.0, L * (a - 2 * b * t)]); return d / np.linalg.norm(d)
    def add(p, g, r):
        V.append(tuple(p)); G.append((0.0, g, r, 1.0)); return len(V) - 1
    # rib
    nr = 14; rr = rnd.random() * 0.3 + 1.6
    rib = []
    for i in range(nr + 1):
        t = i / nr
        w = 0.035 * (1 - 0.7 * t) + 0.01
        p = P(t)
        rib.append((add(p + np.array([0, -w, 0]), 0, rr), add(p + np.array([0, w, 0]), 0, rr)))
    for i in range(nr):
        F.append((rib[i][0], rib[i + 1][0], rib[i + 1][1], rib[i][1]))
    for i in range(nleaf):
        t = 0.08 + 0.9 * (i + rnd.random() * 0.3) / nleaf
        O = P(t); T = Tg(t)
        for s in (-1, 1):
            ln = lmax * (math.sin(math.pi * min(1, 0.12 + 0.88 * t)) ** 0.6) * (1.0 - 0.45 * t) * (0.85 + 0.3 * rnd.random())
            ln = max(ln, 0.12)
            D = np.array([T[0] * 0.5, s * 1.0, T[2] * 0.5 - ang_down * (0.8 + 0.4 * rnd.random())])
            D /= np.linalg.norm(D)
            wd = 0.085 * (0.8 + 0.4 * rnd.random())
            r = rnd.random()
            b0 = add(O - T * wd * 0.5, 0.0, r); b1 = add(O + T * wd * 0.5, 0.0, r)
            M0 = O + D * ln * 0.5 + np.array([0, 0, -0.05 * ln])
            m0 = add(M0 - T * wd * 0.55, 0.5, r); m1 = add(M0 + T * wd * 0.55, 0.5, r)
            tipp = O + D * ln + np.array([0, 0, -0.3 * ln]) + T * 0.12 * ln
            tp = add(tipp, 1.0, r)
            F.append((b0, b1, m1, m0)); F.append((m0, m1, tp))
    me = bpy.data.meshes.new(name)
    me.from_pydata(V, [], F); me.update()
    ca = me.color_attributes.new('g', 'FLOAT_COLOR', 'POINT')
    ca.data.foreach_set('color', np.array(G, dtype=np.float32).ravel())
    me.materials.append(mats()['frond'])
    return me

FRONDS = []
def frond_pool():
    if not FRONDS:
        for k in range(5):
            FRONDS.append(make_frond_mesh('frond%d' % k, L=3.6 + 0.3 * k, a=0.30 + 0.05 * k, b=0.55 + 0.06 * k, seed=k + 3, ang_down=0.45 + 0.08 * k))
    return FRONDS

def make_palm(base, H, lean_az_deg, lean, seed, nfr=15, scale=1.0, coll=None, ripe=True):
    rnd = random.Random(seed)
    M_ = mats()
    ns = 36; nr = 12
    az = RAD(lean_az_deg)
    lx, ly = math.sin(az), math.cos(az)
    pts = []
    for i in range(ns + 1):
        s = i / ns
        off = lean * (s ** 1.7) + 0.15 * math.sin(s * 5 + seed)
        x = base[0] + lx * off + 0.2 * math.sin(s * 3 + seed) * -ly * 0.5
        y = base[1] + ly * off + 0.2 * math.sin(s * 3 + seed) * lx * 0.5
        pts.append(np.array([x, y, base[2] - 0.2 + s * H]))
    V = []; Fc = []
    for i, p in enumerate(pts):
        s = i / ns
        r = (0.145 + 0.045 * (1 - s) + 0.18 * math.exp(-s * H / 0.6)) * scale
        r *= 1 + 0.03 * math.sin(i * 1.7)
        for j in range(nr):
            a = 2 * math.pi * j / nr
            V.append((p[0] + r * math.cos(a), p[1] + r * math.sin(a), p[2]))
    for i in range(ns):
        for j in range(nr):
            k = (j + 1) % nr
            Fc.append((i * nr + j, i * nr + k, (i + 1) * nr + k, (i + 1) * nr + j))
    # object coords: put origin at base so the ring texture uses Z up from base
    ob = mesh_obj('palm_trunk', [(v[0] - base[0], v[1] - base[1], v[2] - base[2]) for v in V], Fc, M_['bark'], coll, loc=(base[0], base[1], base[2]))
    top = pts[-1]
    pool = frond_pool()
    crown = []
    for k in range(nfr):
        azf = rnd.random() * 2 * math.pi
        ring = k / nfr
        tilt = RAD(-50 + 95 * ring ** 0.8 + rnd.uniform(-8, 8))   # negative = up
        o = bpy.data.objects.new('frond', pool[rnd.randrange(len(pool))])
        o.location = (top[0], top[1], top[2] - 0.05)
        o.rotation_euler = Euler((rnd.uniform(-0.12, 0.12), tilt, azf), 'ZYX')
        o.rotation_euler = Euler((0, 0, 0))
        # rotate: first tilt about Y, then azimuth about Z
        mat = Matrix.Rotation(azf, 4, 'Z') @ Matrix.Rotation(tilt, 4, 'Y') @ Matrix.Rotation(rnd.uniform(-0.15, 0.15), 4, 'X')
        o.rotation_euler = mat.to_euler()
        sc = scale * rnd.uniform(0.85, 1.15)
        o.scale = (sc, sc, sc)
        (coll or bpy.context.scene.collection).objects.link(o)
    # coconuts
    if ripe:
        for k in range(rnd.randint(3, 6)):
            a = rnd.random() * 6.28
            cn = sphere('coconut', 0.11 * scale, (top[0] + 0.22 * math.cos(a), top[1] + 0.22 * math.sin(a), top[2] - 0.25 - rnd.random() * 0.2), M_['coconut'], coll, seg=10, ring=8, scale=(1, 1, 1.15))
    return ob

# ---------------- tree blobs ----------------
def make_blob(name, center, r, mat, seed, squash=0.75, subdiv=3, rough=0.35, coll=None):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=subdiv, radius=1.0)
    rnd = random.Random(seed)
    ph = [rnd.random() * 100 for _ in range(3)]
    for v in bm.verts:
        p = v.co
        n = (math.sin(p.x * 2.7 + ph[0]) * math.sin(p.y * 3.1 + ph[1]) + math.sin(p.z * 3.7 + ph[2]) * math.sin(p.x * 4.3 + ph[1]) * 0.7)
        n += 0.5 * math.sin(p.x * 9 + p.y * 8 + ph[2]) * math.sin(p.z * 8.5 + ph[0])
        v.co = p * (1 + rough * n * 0.5)
        v.co.z *= squash
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    for p in me.polygons: p.use_smooth = True
    ob = bpy.data.objects.new(name, me)
    ob.location = center; ob.scale = (r, r, r)
    ob.rotation_euler = (0, 0, rnd.random() * 6.28)
    (coll or bpy.context.scene.collection).objects.link(ob)
    me.materials.append(mat)
    return ob

def make_tree(base, h, r, seed, coll=None):
    rnd = random.Random(seed)
    M_ = mats()
    cyl('trunk', 0.16 * (r / 3), h * 0.75, (base[0], base[1], base[2] + h * 0.35), M_['trunk'], coll, seg=8, r2=0.09 * (r / 3))
    for k in range(rnd.randint(3, 5)):
        ang = rnd.random() * 6.28; dd = rnd.random() * r * 0.55
        make_blob('canopy', (base[0] + math.cos(ang) * dd, base[1] + math.sin(ang) * dd, base[2] + h + rnd.uniform(-0.5, 1.0) * r * 0.25),
                  r * rnd.uniform(0.65, 1.0), M_['tree'] if rnd.random() < 0.65 else M_['tree2'], seed * 10 + k, 0.7, 3, 0.4, coll)

# ---------------- banana / big leaf plants ----------------
def make_leaf_mesh(name, L=2.2, W=0.7, seed=0):
    rnd = random.Random(seed)
    nu, nv = 10, 6
    V = []; F = []
    for i in range(nu + 1):
        u = i / nu
        for j in range(nv + 1):
            v = j / nv - 0.5   # -0.5..0.5
            wid = W * math.sin(math.pi * (0.1 + 0.85 * u)) ** 0.7 if u > 0 else 0.03
            x = L * u
            y = v * wid
            z = (0.9 * L * (0.35 * u - 0.6 * u * u) + 0.9 * abs(v) * wid * 0.9 - abs(v) * 0 + 0.04 * math.sin(u * 14 + j) * abs(v) * wid * 3)
            V.append((x, y, z))
    for i in range(nu):
        for j in range(nv):
            a = i * (nv + 1) + j
            F.append((a, a + nv + 1, a + nv + 2, a + 1))
    me = bpy.data.meshes.new(name); me.from_pydata(V, [], F); me.update()
    for p in me.polygons: p.use_smooth = True
    me.materials.append(mats()['banana'])
    return me

LEAVES = []
def make_banana(base, seed, scale=1.0, nl=8, coll=None):
    rnd = random.Random(seed)
    if not LEAVES:
        for k in range(4): LEAVES.append(make_leaf_mesh('bleaf%d' % k, 2.4 + 0.2 * k, 0.75, k))
    hgt = rnd.uniform(1.4, 2.4) * scale
    cyl('pseudostem', 0.12 * scale, hgt, (base[0], base[1], base[2] + hgt / 2), mats()['banana'], coll, seg=8, r2=0.08 * scale)
    for k in range(nl):
        o = bpy.data.objects.new('bleaf', LEAVES[rnd.randrange(4)])
        o.location = (base[0], base[1], base[2] + hgt * rnd.uniform(0.85, 1.0))
        mat = Matrix.Rotation(rnd.random() * 6.28, 4, 'Z') @ Matrix.Rotation(RAD(rnd.uniform(-55, 5)), 4, 'Y')
        o.rotation_euler = mat.to_euler()
        s = scale * rnd.uniform(0.8, 1.1); o.scale = (s, s, s)
        (coll or bpy.context.scene.collection).objects.link(o)

# ---------------- shrubs with flowers ----------------
def make_shrub(base, r, seed, flowers=True, coll=None):
    rnd = random.Random(seed)
    M_ = mats()
    for k in range(rnd.randint(3, 5)):
        ang = rnd.random() * 6.28; dd = rnd.random() * r * 0.6
        c = (base[0] + math.cos(ang) * dd, base[1] + math.sin(ang) * dd, base[2] + r * 0.45 + rnd.random() * 0.2)
        make_blob('shrub', c, r * rnd.uniform(0.55, 0.9), M_['shrub'], seed * 7 + k, 0.8, 2, 0.4, coll)
        if flowers:
            for q in range(rnd.randint(2, 5)):
                a = rnd.random() * 6.28; el = rnd.uniform(0.2, 1.2)
                rr = r * 0.8
                fp = (c[0] + math.cos(a) * math.cos(el) * rr, c[1] + math.sin(a) * math.cos(el) * rr, c[2] + math.sin(el) * rr * 0.8)
                sphere('flower', 0.055, fp, M_['flower'], coll, seg=8, ring=6, scale=(1, 1, 0.55))

# ---------------- grass tufts ----------------
def grass_field(name, pts, mat, hmin=0.14, hmax=0.34, blades=5, seed=3, coll=None):
    rnd = np.random.RandomState(seed)
    n = len(pts)
    V = np.zeros((n * blades * 3, 3)); G = np.zeros((n * blades * 3, 4), dtype=np.float32)
    F = np.arange(n * blades * 3).reshape(-1, 3)
    for b in range(blades):
        ang = rnd.rand(n) * 6.28
        h = rnd.uniform(hmin, hmax, n) * (0.6 + 0.8 * rnd.rand(n))
        off = rnd.uniform(0.0, 0.09, n)
        bx = pts[:, 0] + np.cos(ang) * off; by = pts[:, 1] + np.sin(ang) * off
        bend = rnd.uniform(0.05, 0.2, n) * h * 3
        dirang = rnd.rand(n) * 6.28
        w = 0.011
        base_idx = (np.arange(n) * blades + b) * 3
        tx = -np.sin(dirang) * w; ty = np.cos(dirang) * w
        V[base_idx] = np.stack([bx - tx, by - ty, pts[:, 2]], 1)
        V[base_idx + 1] = np.stack([bx + tx, by + ty, pts[:, 2]], 1)
        V[base_idx + 2] = np.stack([bx + np.cos(dirang) * bend, by + np.sin(dirang) * bend, pts[:, 2] + h], 1)
        r = rnd.rand(n)
        for q, gv in ((0, 0.0), (1, 0.0), (2, 1.0)):
            G[base_idx + q] = np.stack([r, np.full(n, gv), r, np.ones(n)], 1)
    me = bpy.data.meshes.new(name)
    me.from_pydata(V.tolist(), [], F.tolist()); me.update()
    ca = me.color_attributes.new('g', 'FLOAT_COLOR', 'POINT')
    ca.data.foreach_set('color', G.ravel())
    ob = bpy.data.objects.new(name, me)
    (coll or bpy.context.scene.collection).objects.link(ob)
    me.materials.append(mat)
    return ob

def m_grass(c0=(0.04, 0.16, 0.02), c1=(0.28, 0.40, 0.08)):
    m = new_mat('grass_blades'); nb = NB(m)
    A = nb.n('ShaderNodeAttribute', attribute_name='g'); A.attribute_type = 'GEOMETRY'
    sp = nb.n('ShaderNodeSeparateColor'); nb.link(A.outputs['Color'], sp.inputs[0])
    obj = nb.coord('Object')
    pos = nb.n('ShaderNodeNewGeometry')
    n = nb.noise(nb.mapping(pos.outputs['Position'], (1, 1, 1)), 0.5, 3, 0.5)
    base = nb.mix(n.outputs['Fac'], (*c0, 1), (c0[0] * 1.5, c0[1] * 1.3, c0[2] * 1.3, 1))
    col = nb.mix(nb.math('MULTIPLY', sp.outputs[1], nb.math('MULTIPLY', sp.outputs[2], 0.8)), base, (*c1, 1))
    pr = nb.principled(col, 0.6)
    tr = nb.n('ShaderNodeBsdfTranslucent'); nb.link(col, tr.inputs['Color'])
    mx = nb.n('ShaderNodeMixShader'); mx.inputs[0].default_value = 0.4
    nb.link(pr.outputs[0], mx.inputs[1]); nb.link(tr.outputs[0], mx.inputs[2])
    nb.out(mx.outputs[0]); return m

# ---------------- rocks ----------------
def m_basalt():
    m = new_mat('basalt'); nb = NB(m)
    obj = nb.coord('Object')
    n = nb.noise(nb.mapping(obj, (2, 2, 2)), 3, 6, 0.6)
    c = nb.ramp(n.outputs['Fac'], [(0.3, (0.012, 0.012, 0.014)), (0.7, (0.06, 0.055, 0.05))])
    n2 = nb.noise(obj, 25, 5, 0.7)
    wet = nb.n('ShaderNodeNewGeometry')
    p = nb.principled(c.outputs[0], 0.55, Normal=nb.bump(n2.outputs['Fac'], 0.8, 0.05))
    nb.out(p.outputs[0]); return m

def make_rock(loc, r, seed, mat, squash=0.6, coll=None):
    return make_blob('rock', loc, r, mat, seed, squash, 3, 0.55, coll)
