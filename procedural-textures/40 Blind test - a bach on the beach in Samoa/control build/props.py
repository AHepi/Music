import bpy, bmesh, math, random
import numpy as np
from mathutils import Vector, Euler, Matrix
from lib import *
import terrain, plants
RAD = math.radians

def m_wood_weathered(name='driftwood', light=(0.42, 0.37, 0.30), dark=(0.20, 0.17, 0.14)):
    m = new_mat(name); nb = NB(m)
    obj = nb.coord('Object')
    n = nb.noise(nb.mapping(obj, (1, 1, 0.15)), 6, 6, 0.6, distort=0.4)
    c = nb.ramp(n.outputs['Fac'], [(0.3, (*dark, 1)), (0.7, (*light, 1))])
    p = nb.principled(c.outputs[0], 0.85, Normal=nb.bump(n.outputs['Fac'], 0.8, 0.05))
    nb.out(p.outputs[0]); return m

def m_canoe():
    m = new_mat('canoe_paint'); nb = NB(m)
    obj = nb.coord('Object')
    z = nb.sep(obj)[2]
    n = nb.noise(nb.mapping(obj, (3, 3, 3)), 5, 6, 0.65)
    blue = nb.ramp(n.outputs['Fac'], [(0.35, (0.01, 0.12, 0.30)), (0.7, (0.05, 0.22, 0.42))])
    chip = nb.ramp(nb.noise(nb.mapping(obj, (4, 4, 4)), 9, 6, 0.7).outputs['Fac'], [(0.58, (0, 0, 0)), (0.66, (1, 1, 1))])
    c = nb.mix(chip.outputs[0], blue.outputs[0], (0.35, 0.28, 0.2, 1))
    # white band near the top edge
    band = nb.ramp(z, [(0.0, (1, 1, 1)), (0.06, (0, 0, 0))])
    p = nb.principled(c, 0.5)
    nb.out(p.outputs[0]); return m

def make_canoe(base, heading_deg, L=3.9, coll=None):
    Mc = m_canoe()
    nu, nv = 24, 14
    V = []; F = []
    for i in range(nu + 1):
        u = i / nu
        w = 0.30 * (math.sin(math.pi * (0.04 + 0.92 * u)) ** 0.55)
        dep = 0.30 * (math.sin(math.pi * (0.04 + 0.92 * u)) ** 0.5) + 0.02
        zg = 0.42 + 0.55 * (abs(2 * u - 1) ** 3.2)
        for j in range(nv + 1):
            ph = -math.pi / 2 + math.pi * j / nv
            V.append((L * (u - 0.5), w * math.sin(ph) * (1.0), zg - dep * math.cos(ph) ** 0.8))
    for i in range(nu):
        for j in range(nv):
            a = i * (nv + 1) + j
            F.append((a, a + 1, a + nv + 2, a + nv + 1))
    ob = mesh_obj('canoe', V, F, Mc, coll, loc=(0, 0, 0))
    s = ob.modifiers.new('solid', 'SOLIDIFY'); s.thickness = 0.03; s.offset = -1
    # outrigger float and booms
    objs = [ob]
    Mw = m_wood_weathered('canoe_wood', (0.45, 0.30, 0.18), (0.25, 0.15, 0.08))
    for bx in (-0.7, 0.7):
        objs.append(cyl('boom', 0.025, 1.9, (bx, -1.0, 0.63), Mw, coll, rot=(math.pi / 2, 0, 0), seg=8))
    fl = sphere('float', 0.1, (0.0, -1.9, 0.30), Mc, coll, seg=16, ring=8, scale=(9.5, 1.0, 1.0))
    objs.append(fl)
    # seats
    for sx in (-0.5, 0.5):
        objs.append(box('seat', (0.12, 0.62, 0.03), (sx, 0, 0.5), Mw, coll))
    # a paddle
    objs.append(cyl('paddle', 0.015, 1.3, (0.15, -0.1, 0.5), Mw, coll, rot=(math.pi / 2, 0, 0.3), seg=6))
    root = bpy.data.objects.new('canoe_root', None); bpy.context.scene.collection.objects.link(root)
    for o in objs: o.parent = root
    # place: sit the hull on the sand with the keel slightly below ground, tilted slightly with the slope
    root.location = (base[0], base[1], terrain.ground(base[0], base[1]) - 0.22)
    root.rotation_euler = (RAD(-4), RAD(3), RAD(90 - heading_deg))
    return root

def make_log(base, length, r, heading_deg, seed, mat, coll=None):
    rnd = random.Random(seed)
    ns, nr = 14, 8
    V = []; F = []
    ph = rnd.random() * 10
    for i in range(ns + 1):
        s = i / ns
        cx = s * length - length / 2
        cy = 0.12 * math.sin(s * 3 + ph) * length * 0.2
        cz = 0.06 * math.sin(s * 4 + ph)
        rr = r * (1 - 0.35 * s) * (1 + 0.15 * math.sin(i * 2.3 + ph))
        for j in range(nr):
            a = 2 * math.pi * j / nr
            V.append((cx, cy + rr * math.cos(a), cz + rr * math.sin(a)))
    for i in range(ns):
        for j in range(nr):
            k = (j + 1) % nr
            F.append((i * nr + j, i * nr + k, (i + 1) * nr + k, (i + 1) * nr + j))
    ob = mesh_obj('log', V, F, mat, coll)
    ob.location = (base[0], base[1], terrain.ground(base[0], base[1]) + r * 0.7)
    ob.rotation_euler = (0, 0, RAD(90 - heading_deg))
    # branch stubs
    for k in range(3):
        s = rnd.uniform(0.2, 0.8)
        st = cyl('stub', r * 0.25, r * 1.6, (0, 0, 0), mat, coll, seg=6, r2=r * 0.12)
        st.parent = ob
        st.location = (s * length - length / 2, 0, r * 0.8)
        st.rotation_euler = (rnd.uniform(-0.8, 0.8), rnd.uniform(-0.5, 0.5), 0)
    return ob

def island(name, center, radius, height, seed, mat):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=5, radius=1.0)
    rnd = random.Random(seed)
    ph = [rnd.random() * 50 for _ in range(4)]
    for v in bm.verts:
        p = v.co.copy()
        if p.z < -0.15: v.co.z = -0.3 ; continue
        ridge = 0.5 + 0.5 * math.sin(p.x * 4.1 + ph[0]) * math.sin(p.y * 3.3 + ph[1])
        n = 0.18 * math.sin(p.x * 11 + ph[2]) * math.sin(p.y * 9 + ph[3]) + 0.08 * math.sin(p.x * 25 + p.y * 21 + ph[0])
        v.co.z = max(p.z, 0) * (0.65 + 0.5 * ridge + n) ** 1.0
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    for p in me.polygons: p.use_smooth = True
    ob = bpy.data.objects.new(name, me)
    ob.location = center; ob.scale = (radius, radius, height)
    bpy.context.scene.collection.objects.link(ob)
    me.materials.append(mat)
    return ob

# ---------------- surfboards ----------------
def make_surfboard(name, L, W, T, color, stripe, parent=None, loc=(0, 0, 0), rot=(0, 0, 0)):
    nu, nv = 20, 16
    V = []; F = []
    for i in range(nu + 1):
        u = i / nu
        w = W * (math.sin(math.pi * (0.02 + 0.96 * u)) ** 0.5) * (1 - 0.3 * max(0.0, u - 0.5))
        t = T * (math.sin(math.pi * (0.02 + 0.96 * u)) ** 0.45)
        for j in range(nv):
            th = 2 * math.pi * j / nv
            sn = math.sin(th)
            V.append((L * (u - 0.5), w * math.cos(th), t * sn * (1.0 if sn > 0 else 0.7) + 0.05 * (abs(2 * u - 1) ** 3) * 0.3))
    for i in range(nu):
        for j in range(nv):
            k = (j + 1) % nv
            F.append((i * nv + j, i * nv + k, (i + 1) * nv + k, (i + 1) * nv + j))
    m = new_mat(name + '_mat'); nb = NB(m)
    obj = nb.coord('Object')
    sx, sy, sz = nb.sep(obj)
    st = nb.ramp(nb.math('ABSOLUTE', sy), [(0.05, (1, 1, 1)), (0.06, (0, 0, 0))])
    st2 = nb.ramp(nb.math('ABSOLUTE', nb.math('SUBTRACT', sx, 0.1)), [(0.18, (1, 1, 1)), (0.19, (0, 0, 0))])
    c = nb.mix(st.outputs[0], (*color, 1), (*stripe, 1))
    c = nb.mix(st2.outputs[0], c, (*stripe, 1))
    p = nb.principled(c, 0.12, Coat_Weight=0.8)
    nb.out(p.outputs[0])
    ob = mesh_obj(name, V, F, m, loc=loc, rot=rot)
    if parent: ob.parent = parent
    return ob

# ---------------- laundry line ----------------
def m_cloth(name, a, b, kind):
    m = new_mat(name); nb = NB(m)
    obj = nb.coord('Object')
    if kind == 'stripes':
        w = nb.n('ShaderNodeTexWave'); w.wave_type = 'BANDS'; w.bands_direction = 'X'; w.wave_profile = 'SAW'
        w.inputs['Scale'].default_value = 5; w.inputs['Distortion'].default_value = 0.0
        nb.link(obj, w.inputs['Vector'])
        f = nb.ramp(w.outputs['Fac'], [(0.5, (0, 0, 0)), (0.51, (1, 1, 1))])
    elif kind == 'check':
        ck = nb.n('ShaderNodeTexChecker'); ck.inputs['Scale'].default_value = 6
        nb.link(obj, ck.inputs['Vector']); f = ck
        f = type('X', (), {'outputs': [ck.outputs['Fac']]})
    else:
        vo = nb.n('ShaderNodeTexVoronoi'); vo.inputs['Scale'].default_value = 9
        nb.link(obj, vo.inputs['Vector'])
        f = nb.ramp(vo.outputs['Distance'], [(0.12, (1, 1, 1)), (0.2, (0, 0, 0))])
    c = nb.mix(f.outputs[0], (*a, 1), (*b, 1))
    p = nb.principled(c, 0.85, Sheen_Weight=0.3)
    tr = nb.n('ShaderNodeBsdfTranslucent'); nb.link(c, tr.inputs['Color'])
    mx = nb.n('ShaderNodeMixShader'); mx.inputs[0].default_value = 0.3
    nb.link(p.outputs[0], mx.inputs[1]); nb.link(tr.outputs[0], mx.inputs[2])
    nb.out(mx.outputs[0]); return m

def make_laundry(p1, p2, coll=None):
    Mw = props_wood = m_wood_weathered('pole', (0.5, 0.40, 0.25), (0.25, 0.18, 0.10))
    P1 = Vector(p1); P2 = Vector(p2)
    g1 = terrain.ground(P1.x, P1.y); g2 = terrain.ground(P2.x, P2.y)
    for P, g, tl in ((P1, g1, 0.06), (P2, g2, -0.05)):
        cyl('pole', 0.035, 2.5, (P.x, P.y, g + 1.15), Mw, coll, rot=(0, tl, 0), seg=8)
    A = Vector((P1.x, P1.y, g1 + 2.3)); B = Vector((P2.x, P2.y, g2 + 2.3))
    # line
    nseg = 24
    pts = []
    for i in range(nseg + 1):
        t = i / nseg
        pts.append(A.lerp(B, t) + Vector((0, 0, -0.18 * 4 * t * (1 - t))))
    V = []; F = []
    for i, p in enumerate(pts):
        V.append((p.x - A.x, p.y - A.y, p.z - A.z))
    ln = bpy.data.meshes.new('line'); ln.from_pydata(V, [(i, i + 1) for i in range(nseg)], []); 
    lo = bpy.data.objects.new('line', ln); lo.location = A
    sc = bpy.context.scene; sc.collection.objects.link(lo)
    mod = lo.modifiers.new('skin', 'SKIN')
    for sv in ln.skin_vertices[0].data: sv.radius = (0.004, 0.004)
    lo.data.materials.append(simple_mat('rope', (0.1, 0.1, 0.1, 1), 0.6))
    specs = [((0.8, 0.05, 0.04), (0.95, 0.9, 0.8), 'stripes', 0.12, 1.15, 1.0),
             ((0.02, 0.2, 0.5), (0.9, 0.9, 0.95), 'dots', 0.40, 1.0, 0.85),
             ((0.95, 0.65, 0.05), (0.8, 0.2, 0.05), 'check', 0.66, 1.1, 0.95),
             ((0.05, 0.4, 0.2), (0.95, 0.95, 0.9), 'stripes', 0.86, 0.9, 0.9)]
    for k, (a, b, kind, t0, wd, ht) in enumerate(specs):
        Mc = m_cloth('cloth%d' % k, a, b, kind)
        L = (B - A).length * (wd / (B - A).length)
        nu, nv = 14, 8
        V = []; Fc = []
        d = (B - A).normalized()
        for i in range(nu + 1):
            u = i / nu
            tt = t0 + (wd / (B - A).length) * u * 0.9
            top = A.lerp(B, tt) + Vector((0, 0, -0.18 * 4 * tt * (1 - tt)))
            for j in range(nv + 1):
                v = j / nv
                fold = 0.05 * math.sin(u * 12 + k) * (0.3 + v)
                droop = -ht * v
                V.append((top.x - A.x + (-d.y) * fold, top.y - A.y + d.x * fold, top.z - A.z + droop * 1.0 - 0.1 * math.sin(u * 7 + k) * v * 0.3))
        for i in range(nu):
            for j in range(nv):
                a_ = i * (nv + 1) + j
                Fc.append((a_, a_ + nv + 1, a_ + nv + 2, a_ + 1))
        o = mesh_obj('cloth%d' % k, V, Fc, Mc, loc=tuple(A))
        o.modifiers.new('solid', 'SOLIDIFY').thickness = 0.004
