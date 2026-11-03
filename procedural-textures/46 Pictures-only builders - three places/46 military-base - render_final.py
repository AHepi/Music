"""A military base at dusk: one muddy lane between barrack huts and bell tents,
a field gun parked in the lane, the last low sun at the far end.
Run:  python3 render_final.py WIDTH HEIGHT SAMPLES OUT.png
"""
import sys, math, random, time, os
import bpy, bmesh
import numpy as np
from mathutils import Matrix, Vector, Euler, noise

W = int(sys.argv[1]) if len(sys.argv) > 1 else 540
H = int(sys.argv[2]) if len(sys.argv) > 2 else 960
SAMPLES = int(sys.argv[3]) if len(sys.argv) > 3 else 32
OUT = sys.argv[4] if len(sys.argv) > 4 else "final.png"
HERE = os.path.dirname(os.path.abspath(__file__))

random.seed(7)
bpy.ops.preferences.addon_enable(module='cycles')
sc = bpy.context.scene
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o)

# ------------------------------------------------------------------ helpers
def hexc(h, a=1.0):
    h = h.lstrip('#')
    c = [int(h[i:i+2], 16) / 255 for i in (0, 2, 4)]
    c = [(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4) for x in c]
    return (c[0], c[1], c[2], a)

def nd(nt, t, inp=None, **props):
    n = nt.nodes.new(t)
    for k, v in props.items():
        setattr(n, k, v)
    for k, v in (inp or {}).items():
        s = n.inputs[k]
        if isinstance(v, bpy.types.NodeSocket):
            nt.links.new(v, s)
        else:
            s.default_value = v
    return n

def new_mat(name):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        if n.type != 'OUTPUT_MATERIAL':
            nt.nodes.remove(n)
    out = [n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL'][0]
    return m, nt, out

def ramp(nt, fac, stops):
    r = nd(nt, 'ShaderNodeValToRGB', {'Fac': fac})
    el = r.color_ramp.elements
    while len(el) > 1:
        el.remove(el[-1])
    el[0].position = stops[0][0]
    el[0].color = stops[0][1]
    for p, c in stops[1:]:
        e = el.new(p)
        e.color = c
    return r

def mix(nt, fac, a, b):
    m = nd(nt, 'ShaderNodeMixRGB', {'Fac': fac})
    for sock, v in ((m.inputs[1], a), (m.inputs[2], b)):
        if isinstance(v, bpy.types.NodeSocket):
            nt.links.new(v, sock)
        else:
            sock.default_value = v
    return m.outputs[0]

def mth(nt, op, a, b=None, clamp=False):
    n = nd(nt, 'ShaderNodeMath', operation=op, use_clamp=clamp)
    for i, v in enumerate((a, b)):
        if v is None:
            continue
        if isinstance(v, bpy.types.NodeSocket):
            nt.links.new(v, n.inputs[i])
        else:
            n.inputs[i].default_value = v
    return n.outputs[0]

def noise_tex(nt, vec, scale, detail=4, rough=0.55, dist=0.0):
    return nd(nt, 'ShaderNodeTexNoise', {'Vector': vec, 'Scale': scale, 'Detail': detail,
                                         'Roughness': rough, 'Distortion': dist}).outputs['Fac']

def principled(nt, out, color, rough, metal=0.0, normal=None, emit=None, emit_str=0.0, spec=0.5):
    p = nd(nt, 'ShaderNodeBsdfPrincipled', {'Base Color': color, 'Roughness': rough, 'Metallic': metal})
    p.inputs['Specular IOR Level'].default_value = spec
    if normal is not None:
        nt.links.new(normal, p.inputs['Normal'])
    if emit is not None:
        if isinstance(emit, bpy.types.NodeSocket):
            nt.links.new(emit, p.inputs['Emission Color'])
        else:
            p.inputs['Emission Color'].default_value = emit
        p.inputs['Emission Strength'].default_value = emit_str
    nt.links.new(p.outputs[0], out.inputs['Surface'])
    return p

def objcoord(nt):
    tc = nd(nt, 'ShaderNodeTexCoord')
    return tc.outputs['Object']

def sepxyz(nt, v):
    s = nd(nt, 'ShaderNodeSeparateXYZ', {'Vector': v})
    return s.outputs[0], s.outputs[1], s.outputs[2]

MATS = {}

def mud_splash(nt, color, z, height=0.9, wet='#1c1612'):
    """darken and brown the lower part of anything standing in the mud"""
    g = ramp(nt, mth(nt, 'DIVIDE', z, height, clamp=True),
             [(0.0, hexc(wet)), (0.5, hexc('#2c2118')), (1.0, (1, 1, 1, 1))])
    return nd(nt, 'ShaderNodeMixRGB', {'Fac': 1.0, 'Color1': color, 'Color2': g.outputs[0]}, blend_type='MULTIPLY').outputs[0]

def make_materials():
    # ---- mud
    m, nt, out = new_mat('mud'); MATS['mud'] = m
    c = objcoord(nt)
    x, y, z = sepxyz(nt, c)
    big = noise_tex(nt, c, 0.35, 3)
    mid = noise_tex(nt, c, 3.0, 5, 0.6)
    fine = nd(nt, 'ShaderNodeTexVoronoi', {'Vector': c, 'Scale': 16.0}).outputs['Distance']
    col = ramp(nt, big, [(0.30, hexc('#11161a')), (0.5, hexc('#2a2722')), (0.72, hexc('#6a4528'))])
    col2 = mix(nt, mth(nt, 'MULTIPLY', mid, 0.5), col.outputs[0], hexc('#4a463c'))
    wetmask = ramp(nt, z, [(-0.06, (1, 1, 1, 1)), (0.0, (1, 1, 1, 1)), (0.05, (0, 0, 0, 1))])
    col3 = mix(nt, mth(nt, 'MULTIPLY', wetmask.outputs[0], 0.8), col2, hexc('#0d0b0a'))
    clump = nd(nt, 'ShaderNodeTexVoronoi', {'Vector': c, 'Scale': 3.2, 'Randomness': 1.0}).outputs['Distance']
    col2 = mix(nt, mth(nt, 'MULTIPLY', clump, 0.55), col2, hexc('#6a3f22'))
    bumpv = mth(nt, 'ADD', mth(nt, 'ADD', mth(nt, 'MULTIPLY', fine, 0.6), mth(nt, 'MULTIPLY', mid, 0.8)), mth(nt, 'MULTIPLY', clump, 0.7))
    bn = nd(nt, 'ShaderNodeBump', {'Height': bumpv, 'Strength': 0.7, 'Distance': 0.05})
    rough = mth(nt, 'SUBTRACT', mth(nt, 'ADD', 0.62, mth(nt, 'MULTIPLY', mid, 0.35)), mth(nt, 'MULTIPLY', wetmask.outputs[0], 0.3))
    principled(nt, out, col3, rough, normal=bn.outputs[0], spec=0.45)

    # ---- water in ruts and puddles
    m, nt, out = new_mat('water'); MATS['water'] = m
    c = objcoord(nt)
    rip = noise_tex(nt, c, 4.0, 2)
    bn = nd(nt, 'ShaderNodeBump', {'Height': rip, 'Strength': 0.04, 'Distance': 0.01})
    p = principled(nt, out, hexc('#0d1b20'), 0.03, normal=bn.outputs[0], spec=0.9)
    p.inputs['IOR'].default_value = 1.4

    # ---- weathered boards (hut walls)
    m, nt, out = new_mat('boards'); MATS['boards'] = m
    c = objcoord(nt); x, y, z = sepxyz(nt, c)
    zz = mth(nt, 'MULTIPLY', z, 5.0)
    fl = mth(nt, 'FLOOR', zz)
    wn = nd(nt, 'ShaderNodeTexWhiteNoise', noise_dimensions='1D', ).outputs['Value']
    nt.links.new(fl, nt.nodes[-1].inputs['W'])
    seam = mth(nt, 'LESS_THAN', mth(nt, 'SUBTRACT', zz, fl), 0.07)
    grain = noise_tex(nt, nd(nt, 'ShaderNodeCombineXYZ', {'X': mth(nt, 'MULTIPLY', mth(nt, 'ADD', x, y), 1.5), 'Y': mth(nt, 'MULTIPLY', z, 0.5), 'Z': 0.0}).outputs[0], 6.0, 4, 0.6, 0.5)
    base = mix(nt, wn, hexc('#1a262c'), hexc('#2a231f'))
    base = mix(nt, mth(nt, 'MULTIPLY', grain, 0.8), base, hexc('#1c2426'))
    patch = ramp(nt, noise_tex(nt, c, 0.9, 3), [(0.40, (0, 0, 0, 1)), (0.62, (1, 1, 1, 1))])
    base = mix(nt, mth(nt, 'MULTIPLY', patch.outputs[0], 0.85), base, hexc('#6e4a2c'))
    base = mix(nt, mth(nt, 'MULTIPLY', seam, 0.9), base, hexc('#080a0b'))
    streak = noise_tex(nt, nd(nt, 'ShaderNodeCombineXYZ', {'X': mth(nt, 'MULTIPLY', mth(nt, 'ADD', x, y), 7.0), 'Y': 0.0, 'Z': mth(nt, 'MULTIPLY', z, 0.6)}).outputs[0], 2.5, 3, 0.6)
    base = mix(nt, mth(nt, 'MULTIPLY', ramp(nt, streak, [(0.45, (0, 0, 0, 1)), (0.65, (1, 1, 1, 1))]).outputs[0], 0.8), base, hexc('#0b0f11'))
    base = mud_splash(nt, base, z, 1.0)
    bn = nd(nt, 'ShaderNodeBump', {'Height': mth(nt, 'ADD', mth(nt, 'MULTIPLY', seam, -1.0), grain), 'Strength': 0.5, 'Distance': 0.03})
    principled(nt, out, base, 0.85, normal=bn.outputs[0], spec=0.12)

    # ---- corrugated iron roofs, rusted
    m, nt, out = new_mat('roof'); MATS['roof'] = m
    c = objcoord(nt); x, y, z = sepxyz(nt, c)
    corr = mth(nt, 'SINE', mth(nt, 'MULTIPLY', y, 42.0))
    rust = noise_tex(nt, c, 0.7, 5, 0.6, 0.4)
    rust2 = noise_tex(nt, c, 6.0, 5, 0.6)
    base = ramp(nt, mth(nt, 'ADD', rust, mth(nt, 'MULTIPLY', rust2, 0.25)),
                [(0.3, hexc('#2c3b3e')), (0.5, hexc('#5a3820')), (0.68, hexc('#8d4a22'))])
    bn = nd(nt, 'ShaderNodeBump', {'Height': mth(nt, 'ADD', corr, mth(nt, 'MULTIPLY', rust2, 0.8)), 'Strength': 0.12, 'Distance': 0.05})
    principled(nt, out, base.outputs[0], 0.7, metal=0.3, normal=bn.outputs[0], spec=0.4)

    # ---- dark wood (poles, crates, duckboards)
    m, nt, out = new_mat('wood'); MATS['wood'] = m
    c = objcoord(nt); x, y, z = sepxyz(nt, c)
    g = noise_tex(nt, nd(nt, 'ShaderNodeCombineXYZ', {'X': mth(nt, 'MULTIPLY', x, 2.0), 'Y': mth(nt, 'MULTIPLY', y, 2.0), 'Z': mth(nt, 'MULTIPLY', z, 0.4)}).outputs[0], 7.0, 4, 0.6)
    base = ramp(nt, g, [(0.3, hexc('#14110f')), (0.55, hexc('#2e241c')), (0.75, hexc('#473826'))])
    col = mud_splash(nt, base.outputs[0], z, 0.5)
    bn = nd(nt, 'ShaderNodeBump', {'Height': g, 'Strength': 0.4, 'Distance': 0.02})
    principled(nt, out, col, 0.72, normal=bn.outputs[0], spec=0.16)

    # ---- iron (gun, stove pipes, wire)
    m, nt, out = new_mat('iron'); MATS['iron'] = m
    c = objcoord(nt); x, y, z = sepxyz(nt, c)
    rust = noise_tex(nt, c, 5.0, 5, 0.6, 0.3)
    base = ramp(nt, rust, [(0.35, hexc('#1b2327')), (0.55, hexc('#3b3028')), (0.7, hexc('#7a3e1e'))])
    bn = nd(nt, 'ShaderNodeBump', {'Height': rust, 'Strength': 0.4, 'Distance': 0.01})
    principled(nt, out, base.outputs[0], 0.55, metal=0.6, normal=bn.outputs[0], spec=0.5)

    # ---- olive-grey gun paint
    m, nt, out = new_mat('gunpaint'); MATS['gunpaint'] = m
    c = objcoord(nt); x, y, z = sepxyz(nt, c)
    rust = noise_tex(nt, c, 4.0, 5, 0.6, 0.3)
    base = ramp(nt, rust, [(0.4, hexc('#2e3a38')), (0.6, hexc('#473b2c')), (0.72, hexc('#85461f'))])
    col = mud_splash(nt, base.outputs[0], z, 0.8)
    bn = nd(nt, 'ShaderNodeBump', {'Height': rust, 'Strength': 0.35, 'Distance': 0.01})
    principled(nt, out, col, 0.6, metal=0.3, normal=bn.outputs[0], spec=0.4)

    # ---- sandbags
    m, nt, out = new_mat('sack'); MATS['sack'] = m
    c = objcoord(nt); x, y, z = sepxyz(nt, c)
    n1 = noise_tex(nt, c, 3.0, 4)
    weave = nd(nt, 'ShaderNodeTexVoronoi', {'Vector': c, 'Scale': 90.0}).outputs['Distance']
    base = ramp(nt, n1, [(0.3, hexc('#2a2a24')), (0.55, hexc('#4a4535')), (0.75, hexc('#6a5d44'))])
    col = mud_splash(nt, base.outputs[0], z, 0.5)
    bn = nd(nt, 'ShaderNodeBump', {'Height': mth(nt, 'ADD', weave, n1), 'Strength': 0.7, 'Distance': 0.01})
    principled(nt, out, col, 0.9, normal=bn.outputs[0], spec=0.2)

    # ---- tents: three canvas states, lit from inside
    for name, st in (('tent_hot', 3.2), ('tent_dim', 0.9), ('tent_off', 0.0)):
        m, nt, out = new_mat(name); MATS[name] = m
        c = objcoord(nt); x, y, z = sepxyz(nt, c)
        n1 = noise_tex(nt, c, 2.5, 5, 0.6)
        base = ramp(nt, n1, [(0.3, hexc('#2c3532')), (0.55, hexc('#56553f')), (0.75, hexc('#6f6548'))])
        col = mud_splash(nt, base.outputs[0], z, 0.7)
        glowc = mix(nt, mth(nt, 'MULTIPLY', n1, 0.6), hexc('#ffa650'), hexc('#c9631e'))
        # glow strongest in the middle height, fading at the ground
        gz = ramp(nt, mth(nt, 'DIVIDE', z, 3.0, clamp=True), [(0.0, (0.4, 0.4, 0.4, 1)), (0.35, (1, 1, 1, 1)), (1.0, (0.15, 0.15, 0.15, 1))])
        bn = nd(nt, 'ShaderNodeBump', {'Height': n1, 'Strength': 0.4, 'Distance': 0.02})
        p = principled(nt, out, col, 0.85, normal=bn.outputs[0], spec=0.2)
        if st > 0:
            em = nd(nt, 'ShaderNodeMixRGB', {'Fac': 1.0, 'Color1': glowc, 'Color2': gz.outputs[0]}, blend_type='MULTIPLY').outputs[0]
            nt.links.new(em, p.inputs['Emission Color'])
            p.inputs['Emission Strength'].default_value = st

    m, nt, out = new_mat('brass'); MATS['brass'] = m
    c = objcoord(nt)
    n1 = noise_tex(nt, c, 25.0, 4)
    base = ramp(nt, n1, [(0.3, hexc('#6a4a1c')), (0.6, hexc('#b88a3a')), (0.8, hexc('#d9a850'))])
    principled(nt, out, base.outputs[0], 0.28, metal=1.0, spec=0.7)

    # ---- lit window glass, lamps, dark glass
    for name, st, col in (('glow_hot', 9.0, '#ffa850'), ('glow_dim', 3.0, '#e8883a'), ('lamp', 40.0, '#ffb25c'), ('doorglow', 5.0, '#ff9a40')):
        m, nt, out = new_mat(name); MATS[name] = m
        e = nd(nt, 'ShaderNodeEmission', {'Color': hexc(col), 'Strength': st})
        nt.links.new(e.outputs[0], out.inputs['Surface'])
    m, nt, out = new_mat('darkglass'); MATS['darkglass'] = m
    principled(nt, out, hexc('#0b1417'), 0.08, spec=0.8)
    m, nt, out = new_mat('darkhole'); MATS['darkhole'] = m
    principled(nt, out, hexc('#050709'), 0.9, spec=0.1)

    # ---- hills
    m, nt, out = new_mat('hill'); MATS['hill'] = m
    e = nd(nt, 'ShaderNodeBsdfDiffuse', {'Color': hexc('#10222d')})
    nt.links.new(e.outputs[0], out.inputs['Surface'])
    m, nt, out = new_mat('hill2'); MATS['hill2'] = m
    e = nd(nt, 'ShaderNodeBsdfDiffuse', {'Color': hexc('#1c3643')})
    nt.links.new(e.outputs[0], out.inputs['Surface'])

    # ---- haze
    m, nt, out = new_mat('haze'); MATS['haze'] = m
    v = nd(nt, 'ShaderNodeVolumePrincipled', {'Color': hexc('#7fa0b4'), 'Density': 0.0034, 'Anisotropy': 0.55})
    nt.links.new(v.outputs[0], out.inputs['Volume'])

make_materials()

# ------------------------------------------------------------------ builder
class Builder:
    def __init__(self):
        self.bm = {}
        self.T = Matrix.Identity(4)
    def get(self, m):
        if m not in self.bm:
            self.bm[m] = bmesh.new()
        return self.bm[m]
    def box(self, m, c, s, rz=0.0, rx=0.0, ry=0.0):
        mat = self.T @ Matrix.Translation(c) @ Euler((rx, ry, rz)).to_matrix().to_4x4() @ Matrix.Diagonal((s[0], s[1], s[2], 1))
        bmesh.ops.create_cube(self.get(m), size=1.0, matrix=mat, calc_uvs=False)
    def beam(self, m, p0, p1, w, h):
        p0 = Vector(p0); p1 = Vector(p1)
        d = p1 - p0
        L = d.length
        rot = Vector((0, 0, 1)).rotation_difference(d.normalized()).to_matrix().to_4x4()
        mat = self.T @ Matrix.Translation((p0 + p1) / 2) @ rot @ Matrix.Diagonal((w, h, L, 1))
        bmesh.ops.create_cube(self.get(m), size=1.0, matrix=mat, calc_uvs=False)
    def cyl(self, m, p0, p1, r0, r1=None, seg=12, cap=True):
        p0 = Vector(p0); p1 = Vector(p1)
        d = p1 - p0
        rot = Vector((0, 0, 1)).rotation_difference(d.normalized()).to_matrix().to_4x4()
        mat = self.T @ Matrix.Translation((p0 + p1) / 2) @ rot
        bmesh.ops.create_cone(self.get(m), cap_ends=cap, cap_tris=False, segments=seg, radius1=r0,
                              radius2=(r0 if r1 is None else r1), depth=d.length, matrix=mat, calc_uvs=False)
    def blob(self, m, c, s, rz=0.0, rx=0.0, ry=0.0, seg=8, rings=6):
        mat = self.T @ Matrix.Translation(c) @ Euler((rx, ry, rz)).to_matrix().to_4x4() @ Matrix.Diagonal((s[0], s[1], s[2], 1))
        bmesh.ops.create_uvsphere(self.get(m), u_segments=seg, v_segments=rings, radius=1.0, matrix=mat, calc_uvs=False)
    def poly(self, m, pts):
        bm = self.get(m)
        vs = [bm.verts.new(self.T @ Vector(p)) for p in pts]
        try:
            bm.faces.new(vs)
        except ValueError:
            pass
    def finish(self, smooth=()):
        objs = {}
        for key, bm in self.bm.items():
            bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
            me = bpy.data.meshes.new(key)
            bm.to_mesh(me)
            bm.free()
            for p in me.polygons:
                p.use_smooth = key in smooth
            ob = bpy.data.objects.new(key, me)
            sc.collection.objects.link(ob)
            ob.data.materials.append(MATS[key.split('#')[0]])
            objs[key] = ob
        return objs

B = Builder()

def with_T(T):
    B.T = T
def clear_T():
    B.T = Matrix.Identity(4)

# ------------------------------------------------------------------ ground
def ground():
    xs = sorted(set(list(np.linspace(-70, -9, 14)) + list(np.linspace(-9, -3.4, 18)) + list(np.linspace(-3.4, 3.4, 68)) +
                    list(np.linspace(3.4, 9, 18)) + list(np.linspace(9, 70, 14))))
    ys = []
    yy = -4.0
    while yy < 300:
        ys.append(yy)
        yy += 0.11 * (1 + (yy + 4) / 9.0)
    def zf(x, y):
        z = 0.0
        z += 0.045 * noise.noise((x * 0.8, y * 0.8, 1.3))
        z += 0.045 * noise.noise((x * 0.16, y * 0.10, 4.1))
        z += 0.02 * noise.noise((x * 3.0, y * 3.0, 7.7))
        p = noise.noise((x * 0.22 + 3, y * 0.16, 5.5)) + 0.45 * noise.noise((x * 0.9, y * 0.7, 2.2))
        if p > 0.42:
            z -= 0.16 * min(1.0, (p - 0.42) * 4.0)
        z += 0.03
        for (px_, py_, pr_) in ((1.5, 1.9, 1.0), (-1.1, 2.9, 0.75), (0.2, 0.2, 0.9)):
            dd = math.hypot(x - px_, (y - py_) * 0.8) / (pr_ * (1.0 + 0.3 * noise.noise((x * 1.7, y * 1.7, 3.3))))
            if dd < 1.0:
                z -= 0.22 * min(1.0, (1.0 - dd) * 3.0)
        lg = min(1.0, max(0.0, (y - 3.8) / 4.5)) * (1.0 - min(1.0, max(0.0, (y - 70.0) / 50.0)))
        wd = max(0.0, 1.0 - (abs(x - 0.2) / 2.7) ** 2)
        z -= 0.32 * lg * min(1.0, wd * 2.2) * (0.8 + 0.6 * noise.noise((x * 0.5, y * 0.18, 8.8)))
        for s in (-1, 1):
            xc = s * 1.0 + 0.22 * math.sin(y * 0.09 + s * 1.7) + 0.05 * math.sin(y * 0.7)
            d = (x - xc) / 0.26
            z -= 0.17 * math.exp(-d * d)
        z += 0.04 * math.exp(-(x / 1.5) ** 2) * (1.0 - min(1.0, max(0.0, (y - 3.0) / 3.0)) * 0.9)
        # lane edges are churned up
        e = max(0.0, abs(x) - 3.2)
        z += min(e, 2.0) * 0.07 * noise.noise((x * 0.9, y * 0.5, 9.1))
        return z
    bm = bmesh.new()
    rows = []
    for y in ys:
        row = [bm.verts.new((x, y, zf(x, y))) for x in xs]
        rows.append(row)
    for r in range(len(rows) - 1):
        for c in range(len(xs) - 1):
            bm.faces.new((rows[r][c], rows[r][c + 1], rows[r + 1][c + 1], rows[r + 1][c]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new('ground'); bm.to_mesh(me); bm.free()
    for p in me.polygons:
        p.use_smooth = True
    ob = bpy.data.objects.new('ground', me); sc.collection.objects.link(ob)
    ob.data.materials.append(MATS['mud'])
    # water
    bm = bmesh.new()
    vs = [bm.verts.new(p) for p in ((-70, -4, -0.075), (70, -4, -0.075), (70, 300, -0.075), (-70, 300, -0.075))]
    bm.faces.new(vs)
    me = bpy.data.meshes.new('water'); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new('water', me); sc.collection.objects.link(ob)
    ob.data.materials.append(MATS['water'])
    return zf

zf = ground()

# ------------------------------------------------------------------ huts
def prism(m, pts_uz, y0, y1, xs):
    """extrude an (across,height) profile along y"""
    n = len(pts_uz)
    a = [(u, y0, z) for u, z in pts_uz]
    b = [(u, y1, z) for u, z in pts_uz]
    B.poly(m, a)
    B.poly(m, list(reversed(b)))
    for i in range(n):
        j = (i + 1) % n
        B.poly(m, [a[i], a[j], b[j], b[i]])

def hut(s, xw, y0, L, D, hgt, rise, lit, door_lamp=False):
    """s=+1: lane lies toward +x of the wall (left-hand hut). Body extends away from the lane."""
    u0 = xw
    u1 = xw - s * D
    um = (u0 + u1) / 2
    prism('boards', [(u0, 0), (u1, 0), (u1, hgt), (um, hgt + rise), (u0, hgt)], y0, y0 + L, 0)
    # roof: two slabs with an overhang
    for ua, ub in ((u0, um), (u1, um)):
        d = Vector((ub - ua, 0, rise)).normalized()
        A = Vector((ua, 0, hgt)) - d * 0.45 + Vector((0, 0, 0.05))
        Bp = Vector((ub, 0, hgt + rise + 0.07))
        B.beam('roof', (A.x, y0 + L / 2, A.z), (Bp.x, y0 + L / 2, Bp.z), 0.07, L + 0.6)
        # beam() makes the long cross-section along local y; shift so y stays centred
    # ridge cap
    B.box('iron', (um, y0 + L / 2, hgt + rise + 0.1), (0.25, L + 0.6, 0.12))
    # eaves skirt (dark gutter line)
    # windows on the lane wall
    yo_list = [1.9, 4.4, 8.2, 10.7]
    zrows = [1.75] + ([4.4] if hgt > 5.0 else [])
    for ri, zrow in enumerate(zrows):
        for k, yo in enumerate(yo_list):
            cy = y0 + yo
            state = lit[(k + ri * 2) % 4]
            B.box('wood', (xw + s * 0.04, cy, zrow), (0.12, 1.05, 1.5))
            if state == 0:
                B.box('darkglass', (xw + s * 0.07, cy, zrow), (0.1, 0.85, 1.3))
            else:
                B.box('glow_hot' if state == 2 else 'glow_dim', (xw + s * 0.07, cy, zrow), (0.1, 0.85, 1.3))
                B.box('wood', (xw + s * 0.075, cy, zrow), (0.1, 0.05, 1.3))
                B.box('wood', (xw + s * 0.075, cy, zrow), (0.1, 0.85, 0.05))
            B.box('wood', (xw + s * 0.09, cy, zrow - 0.7), (0.18, 1.2, 0.06))  # sill
    # door
    dy = y0 + 6.3
    B.box('wood', (xw + s * 0.05, dy, 1.0), (0.12, 1.0, 2.0))
    B.box('darkhole', (xw + s * 0.12, dy, 1.0), (0.05, 0.8, 1.8))
    B.box('sack', (xw + s * 0.5, dy, 0.1), (0.9, 1.4, 0.2))  # step
    if door_lamp:
        B.box('wood', (xw + s * 0.2, dy + 0.62, 2.35), (0.35, 0.05, 0.05))
        B.blob('lamp', (xw + s * 0.38, dy + 0.62, 2.28), (0.07, 0.07, 0.10))
    # stove pipe
    px = um + s * 0.9
    py = y0 + L * 0.62
    B.cyl('iron', (px, py, hgt + rise * 0.4), (px, py, hgt + rise + 1.4), 0.10, 0.10, 8)
    B.cyl('iron', (px, py, hgt + rise + 1.4), (px, py, hgt + rise + 1.62), 0.2, 0.05, 8)

def build_huts():
    y = 3.0
    n = 0
    lamps = []
    while y < 125:
        L = 12.5 + random.uniform(-0.5, 0.8)
        hgt = 6.0 if n % 3 == 0 else random.choice([3.1, 3.3, 3.6, 4.4])
        lit = [random.choice([0, 1, 2, 2, 2, 1]) for _ in range(4)]
        lamp = (n % 2 == 0)
        xw = -4.1 + random.uniform(-0.1, 0.25)
        hut(+1, xw, y, L, 5.2, hgt, 1.2 + hgt * 0.12, lit, lamp)
        if lamp:
            lamps.append((xw + 0.38, y + 6.3 + 0.62, 2.28))
        y += L + random.uniform(2.2, 3.0)
        n += 1
    # right-hand blocks, behind the tent line
    y = 14.0
    n = 0
    while y < 125:
        L = 12.5 + random.uniform(-0.5, 0.8)
        hgt = random.choice([5.6, 6.2, 4.6, 6.0])
        lit = [random.choice([1, 2, 2, 1, 0]) for _ in range(4)]
        hut(-1, 10.8 + random.uniform(-0.2, 0.3), y, L, 5.2, hgt, 1.2 + hgt * 0.12, lit, False)
        y += L + random.uniform(2.2, 3.4)
        n += 1
    return lamps

hut_lamps = build_huts()

# ------------------------------------------------------------------ tents
def tent(x, y, r, state):
    key = {2: 'tent_hot', 1: 'tent_dim', 0: 'tent_off'}[state]
    B.cyl(key, (x, y, 0), (x, y, 1.0), r, r, 20, cap=False)
    B.cyl(key, (x, y, 1.0), (x, y, 3.2), r, 0.09, 20, cap=False)
    B.cyl('wood', (x, y, 3.1), (x, y, 3.75), 0.025, 0.025, 6)
    B.blob('iron', (x, y, 3.78), (0.06, 0.06, 0.06), seg=6, rings=4)
    # doorway facing the lane (-x)
    B.box('darkhole', (x - r + 0.01, y, 0.8), (0.12, 0.85, 1.6))
    if state == 2:
        B.box('doorglow', (x - r + 0.08, y, 0.75), (0.05, 0.62, 1.4))
    # guy ropes
    for a in range(0, 360, 45):
        ang = math.radians(a + 8)
        gx = x + math.cos(ang) * (r + 1.6)
        gy = y + math.sin(ang) * (r + 1.6)
        B.beam('wood', (x + math.cos(ang) * 0.5, y + math.sin(ang) * 0.5, 3.0), (gx, gy, 0.05), 0.014, 0.014)
        B.box('wood', (gx, gy, 0.15), (0.05, 0.05, 0.3))

def build_tents():
    y = 8.0
    out = []
    i = 0
    while y < 125:
        st = random.choice([2, 2, 1, 1, 0])
        x = 6.6 + random.uniform(-0.3, 0.4)
        tent(x, y, 2.4, st)
        if st == 2:
            out.append((x - 3.3, y, 0.9))
        y += 6.2 + random.uniform(0, 0.8)
        i += 1
    return out

tent_lights = build_tents()

# ------------------------------------------------------------------ poles and wires
wire_curves = []

def pole(x, y, h=9.0):
    B.beam('wood', (x, y, -0.2), (x + 0.04, y, h), 0.22, 0.22)
    B.box('wood', (x, y, h - 0.35), (0.14, 2.0, 0.12))
    B.box('wood', (x, y, h - 1.05), (0.14, 1.6, 0.11))
    B.beam('wood', (x, y - 0.7, h - 1.2), (x, y, h - 0.35), 0.07, 0.07)
    B.beam('wood', (x, y + 0.7, h - 1.2), (x, y, h - 0.35), 0.07, 0.07)
    for dy in (-0.9, -0.3, 0.3, 0.9):
        B.cyl('darkglass', (x, y + dy, h - 0.28), (x, y + dy, h - 0.12), 0.04, 0.03, 6)
    for dy in (-0.7, 0.0, 0.7):
        B.cyl('darkglass', (x, y + dy, h - 0.98), (x, y + dy, h - 0.84), 0.04, 0.03, 6)

def add_wire(pts):
    wire_curves.append(pts)

def build_poles():
    x = 3.4
    ys = [8.5 + 11.5 * k for k in range(11)]
    for y in ys:
        pole(x, y)
    h = 9.0
    for dy, dz in ((-0.9, -0.28), (-0.3, -0.28), (0.3, -0.28), (0.9, -0.28), (-0.7, -0.98), (0.0, -0.98), (0.7, -0.98)):
        for k in range(len(ys) - 1):
            p0 = Vector((x, ys[k] + dy, h + dz + 0.1))
            p1 = Vector((x, ys[k + 1] + dy, h + dz + 0.1))
            pts = []
            for t in np.linspace(0, 1, 9):
                p = p0.lerp(p1, t)
                p.z -= 0.55 * math.sin(math.pi * t)
                pts.append(p)
            add_wire(pts)

build_poles()

# ------------------------------------------------------------------ fence of barbed wire along the left of the lane
def build_fence():
    x = -3.3
    ys = [15.0 + 3.0 * k for k in range(0, 34)]
    for y in ys:
        B.beam('wood', (x, y, -0.05), (x, y, 1.15), 0.09, 0.09)
        B.box('wood', (x, y, 1.12), (0.12, 0.12, 0.05))
    for k in range(len(ys) - 1):
        for z in (0.35, 0.7, 1.05):
            pts = []
            p0 = Vector((x, ys[k], z)); p1 = Vector((x, ys[k + 1], z))
            for t in np.linspace(0, 1, 5):
                p = p0.lerp(p1, t); p.z -= 0.06 * math.sin(math.pi * t); pts.append(p)
            add_wire(pts)

build_fence()

# ------------------------------------------------------------------ gun
def spoked_wheel(cx, r=0.72, axle_x=0.0):
    # wheel in the y-z plane at x = cx, axle height r
    zc = r
    n = 28
    for i in range(n):
        a0 = 2 * math.pi * i / n
        a1 = 2 * math.pi * (i + 1) / n
        p0 = (cx, math.cos(a0) * r, zc + math.sin(a0) * r)
        p1 = (cx, math.cos(a1) * r, zc + math.sin(a1) * r)
        B.beam('iron', p0, p1, 0.09, 0.05)  # iron tyre, wide across the wheel
    for i in range(14):
        a = 2 * math.pi * i / 14
        B.beam('wood', (cx, math.cos(a) * 0.1, zc + math.sin(a) * 0.1), (cx, math.cos(a) * (r - 0.03), zc + math.sin(a) * (r - 0.03)), 0.05, 0.065)
    B.cyl('iron', (cx - 0.1, 0, zc), (cx + 0.1, 0, zc), 0.12, 0.12, 10)

def field_gun(x, y, yaw):
    T = Matrix.Translation((x, y, 0)) @ Matrix.Rotation(yaw, 4, 'Z') @ Matrix.Scale(1.35, 4)
    with_T(T)
    r = 0.72
    spoked_wheel(-0.86, r)
    spoked_wheel(0.86, r)
    B.cyl('iron', (-0.95, 0, r), (0.95, 0, r), 0.045, 0.045, 8)
    # trail: a heavy beam going back to the ground, with a spade plate
    B.beam('gunpaint', (0, 0.1, 0.75), (0, -2.3, 0.12), 0.15, 0.2)
    B.box('iron', (0, -2.35, 0.06), (0.30, 0.14, 0.12))
    B.beam('gunpaint', (0.14, 0.2, 0.8), (0.02, -1.5, 0.4), 0.05, 0.1)
    # carriage and cradle
    B.box('gunpaint', (0, 0.05, 0.98), (0.72, 0.5, 0.22))
    B.box('gunpaint', (0, 0.05, 1.2), (0.3, 0.9, 0.22))
    # barrel + recoil sleeve, raised a little
    T0 = B.T
    B.T = T0 @ Matrix.Translation((0, 0.1, 1.25)) @ Matrix.Rotation(math.radians(21), 4, 'X') @ Matrix.Translation((0, -0.1, -1.25))
    B.cyl('gunpaint', (0, -0.55, 1.28), (0, 0.9, 1.30), 0.145, 0.145, 14)
    B.cyl('iron', (0, 0.4, 1.29), (0, 2.5, 1.31), 0.085, 0.066, 14)
    B.cyl('iron', (0, 2.5, 1.31), (0, 2.58, 1.31), 0.085, 0.085, 14)
    B.cyl('iron', (0, -0.6, 1.28), (0, -0.78, 1.27), 0.08, 0.05, 10)
    B.T = T0
    # shield
    B.box('gunpaint', (0, 0.42, 1.45), (1.32, 0.035, 0.85))
    B.box('gunpaint', (0, 0.43, 0.99), (0.9, 0.03, 0.10))
    B.box('darkhole', (0, 0.445, 1.42), (0.30, 0.01, 0.28))
    # gun seats
    B.beam('iron', (0.66, 0.05, 0.95), (0.66, -0.5, 1.15), 0.025, 0.025)
    B.box('wood', (0.66, -0.55, 1.18), (0.3, 0.26, 0.04))
    # sights
    B.box('iron', (-0.3, 0.1, 1.5), (0.04, 0.04, 0.2))
    clear_T()

field_gun(0.25, 8.0, math.radians(-38))

# ------------------------------------------------------------------ sandbags
def sandbags(x0, y0, length, rows, rz=0.0, depth=2):
    k = 0
    for r in range(rows):
        off = 0.0 if r % 2 == 0 else 0.3
        n = int(length / 0.62)
        for i in range(n):
            for dpt in range(depth):
                yy = y0 + off + i * 0.62 + random.uniform(-0.03, 0.03)
                xx = x0 + dpt * 0.36 + random.uniform(-0.02, 0.02)
                zz = 0.14 + r * 0.22 + random.uniform(-0.01, 0.02)
                B.blob('sack', (xx, yy, zz), (0.18 + random.uniform(-0.01, 0.02), 0.33, 0.14), rz=random.uniform(-0.12, 0.12), seg=8, rings=6)

sandbags(-3.3, 6.5, 8.5, 4, depth=2)
sandbags(-3.3, 16.5, 6.0, 3, depth=2)

# ------------------------------------------------------------------ lanterns on posts, a helmet
lantern_lights = []
def lantern(x, y, h, watts):
    B.beam('wood', (x, y, -0.1), (x, y, h), 0.1, 0.1)
    B.box('wood', (x + 0.18, y, h - 0.02), (0.4, 0.05, 0.05))
    B.cyl('iron', (x + 0.34, y, h - 0.32), (x + 0.34, y, h - 0.02), 0.012, 0.012, 4)
    B.blob('lamp', (x + 0.34, y, h - 0.42), (0.085, 0.085, 0.12))
    B.cyl('iron', (x + 0.34, y, h - 0.30), (x + 0.34, y, h - 0.26), 0.11, 0.05, 8)
    lantern_lights.append((x + 0.34, y, h - 0.42, watts))

lantern(-2.35, 9.2, 2.3, 140)
for yy in (26.0, 44.0, 62.0, 84.0):
    lantern(-3.3, yy, 2.4, 30 * yy)

def helmet(x, y, z, rz=0.0):
    B.blob('iron', (x, y, z + 0.06), (0.14, 0.14, 0.095), rz=rz, seg=12, rings=6)
    B.cyl('iron', (x, y, z + 0.02), (x, y, z + 0.03), 0.22, 0.22, 14)

def debris():
    for i in range(9):
        x = random.uniform(-2.0, 3.0); y = random.uniform(2.6, 9.0)
        z = zf(x, y)
        B.box('wood', (x, y, z + 0.05), (0.16, random.uniform(0.9, 1.6), 0.035), rz=random.uniform(0.6, 2.5), rx=random.uniform(-0.1, 0.1))
    for i in range(10):
        x = random.uniform(-2.2, 3.2); y = random.uniform(2.4, 10.0)
        z = zf(x, y)
        sz = random.uniform(0.12, 0.26)
        B.blob('pebble', (x, y, z + sz * 0.15), (sz, sz * 0.8, sz * 0.6), rz=random.uniform(0, 3), seg=7, rings=5)
    # loose sandbag heap at the lower left
    for i in range(16):
        x = -1.9 + random.uniform(-0.55, 0.45); y = 3.7 + random.uniform(-0.6, 0.6)
        zz = 0.13 + 0.17 * random.choice([0, 0, 1, 1, 2]) * (1 - abs(x + 1.9) * 0.5)
        B.blob('sack', (x, y, zz), (0.17, 0.32, 0.13), rz=random.uniform(0, 3.1), seg=8, rings=6)
    # a broken crate
    B.box('wood', (1.9, 3.4, 0.18), (0.62, 0.42, 0.36), rz=0.5)
    B.box('wood', (2.15, 3.0, 0.07), (0.5, 0.12, 0.03), rz=1.2)
    B.cyl('wood', (2.6, 4.2, 0.0), (2.6, 4.2, 0.28), 0.17, 0.15, 12)
    B.cyl('iron', (2.6, 4.2, 0.27), (2.6, 4.2, 0.30), 0.18, 0.18, 12)

def shells(x, y, rz):
    # an open crate with brass shell cases standing in it
    B.box('wood', (x, y, 0.14), (0.9, 0.55, 0.28), rz=rz)
    for i in range(3):
        for j in range(2):
            lx = (i - 1) * 0.26; ly = (j - 0.5) * 0.26
            cx = x + lx * math.cos(rz) - ly * math.sin(rz)
            cy = y + lx * math.sin(rz) + ly * math.cos(rz)
            B.cyl('brass', (cx, cy, 0.2), (cx, cy, 0.62), 0.065, 0.065, 12)
            B.cyl('brass', (cx, cy, 0.62), (cx, cy, 0.82), 0.065, 0.02, 12)
            B.cyl('iron', (cx, cy, 0.62), (cx, cy, 0.64), 0.07, 0.07, 12)

shells(1.5, 3.7, 0.35)
# a hurricane lamp standing on the mud, throwing a pool of light
ground_lamps = [(0.62, 3.25)]
for gx, gy in ground_lamps:
    gz = zf(gx, gy)
    B.box('iron', (gx, gy, gz + 0.02), (0.2, 0.2, 0.04))
    B.cyl('iron', (gx, gy, gz + 0.04), (gx, gy, gz + 0.06), 0.1, 0.1, 10)
    B.blob('lamp', (gx, gy, gz + 0.17), (0.06, 0.06, 0.1))
    B.cyl('iron', (gx, gy, gz + 0.28), (gx, gy, gz + 0.34), 0.08, 0.03, 10)
    B.cyl('iron', (gx, gy, gz + 0.34), (gx, gy, gz + 0.40), 0.015, 0.015, 6)
    for k in range(4):
        a = k * math.pi / 2 + math.pi / 4
        B.beam('iron', (gx + math.cos(a) * 0.075, gy + math.sin(a) * 0.075, gz + 0.05), (gx + math.cos(a) * 0.06, gy + math.sin(a) * 0.06, gz + 0.28), 0.008, 0.008)
debris()
# planks lying in the dark puddle at the lower right
for i in range(6):
    B.box('wood', (1.4 + random.uniform(-0.7, 0.7), 1.9 + random.uniform(-0.5, 0.6), -0.045), (0.17, random.uniform(0.8, 1.4), 0.04), rz=random.uniform(0, 3.1), rx=random.uniform(-0.05, 0.05))
lantern(2.5, 7.4, 2.1, 150)
helmet(-2.9, 8.3, 0.99, 0.3)
helmet(-2.3, 5.2, 0.05, 1.0)

# ------------------------------------------------------------------ duckboards
def duckboards(x, y0, y1):
    B.beam('wood', (x - 0.38, y0, 0.03), (x - 0.38, y1, 0.03), 0.07, 0.06)
    B.beam('wood', (x + 0.38, y0, 0.03), (x + 0.38, y1, 0.03), 0.07, 0.06)
    y = y0
    while y < y1:
        B.box('wood', (x + random.uniform(-0.02, 0.02), y, 0.07), (0.9, 0.12, 0.035), rz=random.uniform(-0.04, 0.04))
        y += 0.22 + random.uniform(0, 0.03) * (1 + y / 6)

duckboards(-2.0, 2.4, 30)

# ------------------------------------------------------------------ crates, barrels, rifle stack, wire coil
def crate(x, y, z, rz, sx=0.62, sy=0.42, sz=0.36):
    B.box('wood', (x, y, z + sz / 2), (sx, sy, sz), rz=rz)
    B.box('iron', (x, y, z + sz / 2), (sx * 0.12, sy + 0.02, sz + 0.02), rz=rz)

def crates():
    base = Vector((2.9, 5.6, 0))
    spec = [(0, 0, 0.0, 0.2), (0.7, 0.1, 0.0, -0.15), (0.05, 0.05, 0.36, 0.1), (0.65, 0.12, 0.36, 0.3), (0.3, 0.1, 0.72, -0.1)]
    for dx, dy, z, rz in spec:
        crate(base.x + dx, base.y + dy, z, rz)
    # barrel
    B.cyl('wood', (3.6, 6.6, 0.0), (3.6, 6.6, 0.95), 0.32, 0.32, 14)
    for zz in (0.2, 0.75):
        B.cyl('iron', (3.6, 6.6, zz - 0.03), (3.6, 6.6, zz + 0.03), 0.335, 0.335, 14)

crates()

def rifle_stack(x, y):
    apex = Vector((x, y, 1.0))
    for k in range(4):
        a = math.radians(45 + 90 * k)
        base = Vector((x + math.cos(a) * 0.38, y + math.sin(a) * 0.38, 0.03))
        d = (apex - base).normalized()
        B.beam('wood', base, apex + d * 0.25, 0.045, 0.07)
        B.beam('iron', apex - d * 0.1 + d * 0.25, apex + d * 0.55, 0.022, 0.022)
        B.box('iron', base + Vector((0, 0, 0.0)), (0.07, 0.12, 0.02))
    B.cyl('wood', (x, y, 0.9), (x, y, 1.0), 0.05, 0.05, 6)

rifle_stack(-2.1, 4.3)

def helix(cx, cy, cz, r, length, turns, along='y'):
    pts = []
    n = int(turns * 14)
    for i in range(n + 1):
        t = i / n
        a = 2 * math.pi * turns * t
        pts.append((cx + math.cos(a) * r, cy + t * length, cz + math.sin(a) * r))
    add_wire(pts)

helix(2.3, 3.4, 0.5, 0.5, 4.8, 9)
helix(2.35, 3.4, 0.5, 0.42, 4.8, 9)

# ------------------------------------------------------------------ gate, watch box and tower at the far end
def far_end():
    gy = 132.0
    for sx in (-1, 1):
        B.beam('wood', (sx * 4.3, gy, -0.2), (sx * 4.3, gy, 4.6), 0.4, 0.4)
    B.box('wood', (0, gy, 4.6), (9.3, 0.35, 0.35))
    B.beam('wood', (-4.3, gy, 3.6), (-2.0, gy, 4.6), 0.18, 0.18)
    B.beam('wood', (4.3, gy, 3.6), (2.0, gy, 4.6), 0.18, 0.18)
    B.blob('lamp', (0, gy - 0.3, 4.2), (0.18, 0.18, 0.25))
    B.cyl('wood', (0, gy, 4.4), (0, gy, 4.6), 0.02, 0.02, 4)
    # barrier pole
    B.beam('iron', (-4.1, gy - 0.5, 1.1), (3.0, gy - 0.5, 1.4), 0.1, 0.1)
    # guard hut
    B.box('boards', (6.5, gy, 1.5), (3.2, 4.0, 3.0))
    B.box('roof', (6.5, gy, 3.2), (3.8, 4.6, 0.2))
    B.box('glow_hot', (4.88, gy - 0.4, 1.7), (0.1, 0.9, 1.0))
    B.box('wood', (4.88, gy - 0.4, 1.7), (0.12, 0.06, 1.0))
    # timber watch tower (headframe look) against the last light
    tx, ty = 0.3, 100.0
    Ht = 22.0
    base_h = 2.3
    taper = 0.5
    legs = [(-1, -1), (1, -1), (-1, 1), (1, 1)]
    def lp(lx, ly, z):
        f = 1 - (1 - taper) * z / Ht
        return (tx + lx * base_h * f, ty + ly * base_h * f, z)
    for lx, ly in legs:
        B.beam('wood', lp(lx, ly, 0), lp(lx, ly, Ht), 0.45, 0.45)
    levels = [0, 4.5, 9.0, 13.5, 18.0, Ht]
    for z in levels[1:]:
        for (ax, ay), (bx, by) in ((legs[0], legs[1]), (legs[1], legs[3]), (legs[3], legs[2]), (legs[2], legs[0])):
            B.beam('wood', lp(ax, ay, z), lp(bx, by, z), 0.28, 0.28)
    for z0, z1 in zip(levels[:-1], levels[1:]):
        for (ax, ay), (bx, by) in ((legs[0], legs[1]), (legs[1], legs[3]), (legs[3], legs[2]), (legs[2], legs[0])):
            B.beam('wood', lp(ax, ay, z0), lp(bx, by, z1), 0.2, 0.2)
            B.beam('wood', lp(bx, by, z0), lp(ax, ay, z1), 0.2, 0.2)
    # ladder up one face and a lit cabin on top
    B.box('boards', (tx, ty, Ht + 1.0), (3.4, 3.4, 2.0))
    B.box('roof', (tx, ty, Ht + 2.2), (4.4, 4.4, 0.35))
    B.box('wood', (tx, ty, Ht - 0.1), (4.2, 4.2, 0.25))
    B.box('glow_hot', (tx, ty - 1.72, Ht + 1.0), (2.2, 0.08, 1.0))
    B.box('wood', (tx, ty - 1.74, Ht + 1.0), (0.1, 0.1, 1.0))
    B.box('glow_dim', (tx + 1.72, ty, Ht + 1.0), (0.08, 1.4, 0.9))
    # searchlight on a rail
    B.cyl('iron', (tx + 1.6, ty - 2.0, Ht + 0.5), (tx + 2.3, ty - 2.3, Ht + 0.6), 0.32, 0.32, 12)
    B.box('wood', (tx, ty - 2.1, Ht + 0.25), (4.2, 0.1, 0.1))

far_end()

# ------------------------------------------------------------------ pebbles near the camera
def pebbles():
    for _ in range(700):
        x = random.gauss(0, 2.4)
        y = random.uniform(0.5, 26) ** 1.0
        if abs(x) > 6:
            continue
        z = zf(x, y)
        if z < -0.06:
            continue
        s = random.uniform(0.02, 0.07)
        B.blob('pebble', (x, y, z + s * 0.2), (s, s * random.uniform(0.7, 1.2), s * 0.6), rz=random.uniform(0, 3), seg=6, rings=4)
    for _ in range(26):
        x = random.uniform(-3.4, 3.4)
        y = random.uniform(1.2, 9)
        z = zf(x, y)
        if z < -0.05:
            continue
        s = random.uniform(0.07, 0.14)
        B.blob('pebble', (x, y, z + s * 0.2), (s, s * random.uniform(0.7, 1.2), s * 0.7), rz=random.uniform(0, 3), seg=7, rings=5)

m, nt, out = new_mat('pebble'); MATS['pebble'] = m
c = objcoord(nt)
n1 = noise_tex(nt, c, 30.0, 3)
base = ramp(nt, n1, [(0.3, hexc('#1f1c1a')), (0.55, hexc('#4a3a2c')), (0.75, hexc('#6b5238'))])
principled(nt, out, base.outputs[0], 0.55)
pebbles()

# ------------------------------------------------------------------ hills
def hills():
    for name, dist, h0, h1, mat in (('hillfar', 520, 26, 30, 'hill'), ('hillnear', 340, 12, 22, 'hill2')):
        bm = bmesh.new()
        xs = np.linspace(-700, 700, 140)
        tops = []
        for x in xs:
            h = h0 + h1 * (0.5 + 0.5 * noise.noise((x * 0.004 + dist, 0.5, 2.0))) + 0.35 * h1 * noise.noise((x * 0.02, dist, 1.0))
            tops.append(h)
        top = [bm.verts.new((x, dist, h)) for x, h in zip(xs, tops)]
        bot = [bm.verts.new((x, dist, -20)) for x in xs]
        top2 = [bm.verts.new((x, dist + 60, h)) for x, h in zip(xs, tops)]
        for i in range(len(xs) - 1):
            bm.faces.new((bot[i], bot[i + 1], top[i + 1], top[i]))
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
        ob = bpy.data.objects.new(name, me); sc.collection.objects.link(ob)
        ob.data.materials.append(MATS[mat])

hills()

objs = B.finish(smooth=('sack', 'tent_hot', 'tent_dim', 'tent_off', 'pebble'))

# ------------------------------------------------------------------ wires as curves
def make_wires():
    cu = bpy.data.curves.new('wires', 'CURVE')
    cu.dimensions = '3D'
    cu.bevel_depth = 0.011
    cu.bevel_resolution = 0
    cu.resolution_u = 2
    for pts in wire_curves:
        sp = cu.splines.new('POLY')
        sp.points.add(len(pts) - 1)
        for i, p in enumerate(pts):
            sp.points[i].co = (p[0], p[1], p[2], 1)
    ob = bpy.data.objects.new('wires', cu)
    sc.collection.objects.link(ob)
    ob.data.materials.append(MATS['iron'])

make_wires()

# ------------------------------------------------------------------ sky
def make_world():
    w = bpy.data.worlds.new('dusk')
    sc.world = w
    w.use_nodes = True
    nt = w.node_tree
    for n in list(nt.nodes):
        if n.type != 'OUTPUT_WORLD':
            nt.nodes.remove(n)
    out = [n for n in nt.nodes if n.type == 'OUTPUT_WORLD'][0]
    tc = nd(nt, 'ShaderNodeTexCoord')
    d = tc.outputs['Generated']
    dn = nd(nt, 'ShaderNodeVectorMath', {'Vector': d}, operation='NORMALIZE').outputs[0]
    x, y, z = sepxyz(nt, dn)
    zc = mth(nt, 'MAXIMUM', z, 0.0)
    sky = ramp(nt, zc, [(0.0, hexc('#eeaa5c')), (0.012, hexc('#c27a48')), (0.05, hexc('#4f7c88')), (0.14, hexc('#356070')),
                        (0.3, hexc('#1f4d62')), (0.6, hexc('#123348')), (1.0, hexc('#0b1e2b'))])
    # clouds: a flat layer seen in perspective
    den = mth(nt, 'ADD', zc, 0.18)
    u = mth(nt, 'DIVIDE', x, den)
    v = mth(nt, 'DIVIDE', y, den)
    cv = nd(nt, 'ShaderNodeCombineXYZ', {'X': mth(nt, 'MULTIPLY', u, 0.9), 'Y': mth(nt, 'MULTIPLY', v, 2.2), 'Z': 0.0}).outputs[0]
    cn = nd(nt, 'ShaderNodeTexNoise', {'Vector': cv, 'Scale': 1.05, 'Detail': 5.0, 'Roughness': 0.62, 'Distortion': 0.6}).outputs['Fac']
    dens = ramp(nt, cn, [(0.30, (0, 0, 0, 1)), (0.52, (1, 1, 1, 1))]).outputs[0]
    # clouds fade out at the very top and at the horizon so the glow shows under them
    dens = mth(nt, 'MULTIPLY', dens, mth(nt, 'SUBTRACT', 1.0, mth(nt, 'MULTIPLY', ramp(nt, zc, [(0.0, (1, 1, 1, 1)), (0.035, (0, 0, 0, 1))]).outputs[0], 0.9)))
    cloudcol = mix(nt, dens, sky.outputs[0], hexc('#091a24'))
    # lit lower edges of clouds
    edge = mth(nt, 'MULTIPLY', mth(nt, 'MULTIPLY', dens, mth(nt, 'SUBTRACT', 1.0, dens)), 4.0)
    glowband = ramp(nt, zc, [(0.0, (1, 1, 1, 1)), (0.1, (0.3, 0.3, 0.3, 1)), (0.3, (0.03, 0.03, 0.03, 1))]).outputs[0]
    amber = mix(nt, mth(nt, 'MULTIPLY', edge, glowband), cloudcol, hexc('#d98c4c'))
    # the sun itself is hidden behind the cloud; its glow is not
    sdir = Vector((0.07, 1.0, 0.09)).normalized()
    dot = nd(nt, 'ShaderNodeVectorMath', {'Vector': dn, 'Vector_001': sdir}, operation='DOT_PRODUCT').outputs['Value']
    g1 = mth(nt, 'POWER', mth(nt, 'MAXIMUM', dot, 0.0), 90.0)
    g2 = mth(nt, 'POWER', mth(nt, 'MAXIMUM', dot, 0.0), 16.0)
    glow = mth(nt, 'ADD', mth(nt, 'MULTIPLY', g1, 1.0), mth(nt, 'MULTIPLY', g2, 0.12))
    col = mix(nt, mth(nt, 'MULTIPLY', glow, 1.0, clamp=True), amber, hexc('#ffb868'))
    bg = nd(nt, 'ShaderNodeBackground', {'Color': col, 'Strength': 1.15})
    nt.links.new(bg.outputs[0], out.inputs['Surface'])
    return sdir

sdir = make_world()

# ------------------------------------------------------------------ lights
def make_lights():
    ld = bpy.data.lights.new('sun', 'SUN')
    ld.energy = 3.0
    ld.color = (1.0, 0.62, 0.30)
    ld.angle = math.radians(2.5)
    ob = bpy.data.objects.new('sun', ld)
    sc.collection.objects.link(ob)
    ob.rotation_euler = (-sdir).to_track_quat('-Z', 'Y').to_euler()
    # a cool fill from the opposite sky so shadows are blue and not black
    ld2 = bpy.data.lights.new('fill', 'SUN')
    ld2.energy = 0.6
    ld2.color = (0.45, 0.65, 0.9)
    ld2.angle = math.radians(40)
    ob2 = bpy.data.objects.new('fill', ld2)
    sc.collection.objects.link(ob2)
    ob2.rotation_euler = Vector((0.2, 0.5, -0.8)).to_track_quat('-Z', 'Y').to_euler()
    def pl(pos, watts, col=(1.0, 0.6, 0.28), r=0.15):
        l = bpy.data.lights.new('pl', 'POINT')
        l.energy = watts; l.color = col; l.shadow_soft_size = r
        o = bpy.data.objects.new('pl', l)
        sc.collection.objects.link(o)
        o.location = pos
    for p in hut_lamps[:6]:
        pl((p[0] + 0.3, p[1], p[2] - 0.1), 160)
    for p in hut_lamps[6:]:
        pl((p[0] + 0.3, p[1], p[2] - 0.1), 700)
    for p in tent_lights[:4]:
        pl(p, 120, (1.0, 0.55, 0.22), 0.5)
    for gx, gy in ground_lamps:
        pl((gx, gy, zf(gx, gy) + 0.2), 42, (1.0, 0.56, 0.24), 0.05)
    for lx, ly, lz, w in lantern_lights:
        pl((lx, ly, lz), w, (1.0, 0.58, 0.26), 0.12)
    pl((0.0, 126.0, 4.0), 900)
    pl((0.3, 98.0, 23.0), 1500, (1.0, 0.6, 0.3), 0.4)

make_lights()

# ------------------------------------------------------------------ haze cube
def haze():
    bpy.ops.mesh.primitive_cube_add(size=1.0)
    ob = bpy.context.active_object
    ob.name = 'haze'
    ob.scale = (240, 330, 40)
    ob.location = (0, 125, 12)
    ob.data.materials.append(MATS['haze'])
    ob.visible_shadow = False

haze()

def mist():
    m, nt, out = new_mat('mist'); MATS['mist'] = m
    tc = nd(nt, 'ShaderNodeTexCoord')
    x, y, z = sepxyz(nt, tc.outputs['Generated'])
    fall = mth(nt, 'POWER', mth(nt, 'SUBTRACT', 1.0, z, clamp=True), 2.5)
    v = nd(nt, 'ShaderNodeVolumePrincipled', {'Color': hexc('#9fb6c2'), 'Density': mth(nt, 'MULTIPLY', fall, 0.06), 'Anisotropy': 0.5})
    nt.links.new(v.outputs[0], out.inputs['Volume'])
    bpy.ops.mesh.primitive_cube_add(size=1.0)
    ob = bpy.context.active_object
    ob.name = 'mist'
    ob.scale = (40, 140, 3.2)
    ob.location = (0, 80, 1.6)
    ob.data.materials.append(m)
    ob.visible_shadow = False

mist()

# ------------------------------------------------------------------ camera
cam_d = bpy.data.cameras.new('cam')
cam_d.lens = 31
cam_d.sensor_width = 36
cam_d.sensor_fit = 'HORIZONTAL'
cam_d.shift_y = -0.14
cam_d.clip_end = 2000
cam = bpy.data.objects.new('cam', cam_d)
sc.collection.objects.link(cam)
cam.location = (0.15, 0.0, 1.7)
cam.rotation_euler = (math.radians(90.0), 0, 0)
sc.camera = cam

# ------------------------------------------------------------------ render
r = sc.render
r.engine = 'CYCLES'
r.resolution_x = W
r.resolution_y = H
r.resolution_percentage = 100
cy = sc.cycles
cy.device = 'CPU'
cy.samples = SAMPLES
cy.use_adaptive_sampling = True
cy.adaptive_threshold = 0.02
cy.use_denoising = True
cy.denoiser = 'OPENIMAGEDENOISE'
cy.max_bounces = 6
cy.diffuse_bounces = 3
cy.glossy_bounces = 4
cy.transmission_bounces = 2
cy.volume_bounces = 1
cy.sample_clamp_direct = 30
cy.sample_clamp_indirect = 8
cy.volume_step_rate = 2.0
cy.volume_max_steps = 64
cy.caustics_reflective = False
cy.caustics_refractive = False
sc.view_settings.view_transform = 'AgX' if 'AgX' in [i.identifier for i in sc.view_settings.bl_rna.properties['view_transform'].enum_items] else 'Standard'
sc.view_settings.look = 'None'
ng = bpy.data.node_groups.new('finish', 'CompositorNodeTree')
sc.compositing_node_group = ng
rl = ng.nodes.new('CompositorNodeRLayers')
ku = ng.nodes.new('CompositorNodeKuwahara')
ku.inputs['Type'].default_value = 'Anisotropic'
ku.inputs['Size'].default_value = max(2.0, 2.2 * W / 540.0)
ku.inputs['Sharpness'].default_value = 0.8
ku.inputs['Eccentricity'].default_value = 1.0
gl = ng.nodes.new('CompositorNodeGlare')
gl.inputs['Type'].default_value = 'Bloom'
gl.inputs['Threshold'].default_value = 1.2
gl.inputs['Strength'].default_value = 0.35
gl.inputs['Size'].default_value = 0.5
ng.interface.new_socket('Image', in_out='OUTPUT', socket_type='NodeSocketColor')
go = ng.nodes.new('NodeGroupOutput')
ng.links.new(rl.outputs['Image'], ku.inputs['Image'])
ng.links.new(ku.outputs['Image'], gl.inputs['Image'])
ng.links.new(gl.outputs['Image'], go.inputs[0])
r.use_compositing = True
r.image_settings.file_format = 'PNG'
r.image_settings.color_depth = '16'
raw = os.path.join(HERE, '_raw.png')
r.filepath = raw
t0 = time.time()
bpy.ops.render.render(write_still=True)
print('render seconds', round(time.time() - t0, 1))

# ------------------------------------------------------------------ finishing (numpy on the saved frame)
def blur(a, sigma):
    h, w = a.shape[:2]
    fy = np.fft.fftfreq(h)[:, None]
    fx = np.fft.rfftfreq(w)[None, :]
    g = np.exp(-2 * (math.pi ** 2) * sigma ** 2 * (fx ** 2 + fy ** 2))
    out = np.empty_like(a)
    for c in range(a.shape[2]):
        out[..., c] = np.fft.irfft2(np.fft.rfft2(a[..., c]) * g, s=(h, w))
    return out

img = bpy.data.images.load(raw)
img.colorspace_settings.name = 'Non-Color'
px = np.array(img.pixels[:], dtype=np.float32).reshape(H, W, 4)[..., :3]
px = np.clip(px, 0, 1)
bpy.data.images.remove(img)
try:
    os.remove(raw)
except OSError:
    pass
lin = px ** 2.2
scale = W / 540.0
# bloom: the warm lights spill a little into the air
lum = lin @ np.array([0.3, 0.5, 0.2], dtype=np.float32)
hot = lin * np.clip((lum[..., None] - 0.35) * 2.0, 0, 1)
bl = blur(hot, 4 * scale) * 0.35 + blur(hot, 16 * scale) * 0.35
lin = lin + bl
# grade: blue-black shadows lifted a touch, warm highlights
lum = lin @ np.array([0.3, 0.5, 0.2], dtype=np.float32)
sh = np.clip(1 - lum * 4, 0, 1)[..., None]
lin = lin + sh * np.array([0.002, 0.008, 0.016], dtype=np.float32)
# away from the light the picture goes blue-black; near the light it stays warm
lum = lin @ np.array([0.3, 0.5, 0.2], dtype=np.float32)
cw = np.clip(1 - lum / 0.14, 0, 1)[..., None] ** 1.3
lin = lin * (1 + cw * (np.array([0.76, 1.0, 1.30], dtype=np.float32) - 1))
hi = np.clip(lum * 2.0, 0, 1)[..., None]
lin = lin * (1 + hi * np.array([0.06, 0.0, -0.08], dtype=np.float32))
# vignette
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
rr = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H * 0.46) / (H / 2)) ** 2)
lin = lin * (1 - 0.42 * np.clip(rr - 0.35, 0, 1.2) ** 1.6)[..., None]
lin = np.clip(lin, 0, 1)
res = lin ** (1 / 2.2)
# grain, like paint on canvas
rng = np.random.default_rng(3)
res = res + rng.normal(0, 0.008, res.shape).astype(np.float32)
res = np.clip(res, 0, 1)

out_img = bpy.data.images.new('final', W, H, alpha=False)
out_img.colorspace_settings.name = 'Non-Color'
rgba = np.concatenate([res, np.ones((H, W, 1), dtype=np.float32)], axis=2)
out_img.pixels.foreach_set(rgba.ravel())
out_img.filepath_raw = os.path.abspath(OUT)
out_img.file_format = 'PNG'
out_img.save()
print('saved', OUT)
