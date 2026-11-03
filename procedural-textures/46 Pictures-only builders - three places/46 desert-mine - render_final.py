#!/usr/bin/env python3
# A mine in the desert, built in Blender and drawn in the look of the reference pictures.
# Run:  python3 render_final.py WIDTH HEIGHT SAMPLES OUT.png
import bpy, bmesh, math, random, sys, os, time
import numpy as np
from mathutils import Vector, Matrix, noise as mnoise

args = sys.argv[1:]
W = int(args[0]) if len(args) > 0 else 540
H = int(args[1]) if len(args) > 1 else 960
SAMPLES = int(args[2]) if len(args) > 2 else 64
OUT = args[3] if len(args) > 3 else os.path.join(os.path.dirname(os.path.abspath(__file__)), 'final.png')
HERE = os.path.dirname(os.path.abspath(__file__))
T0 = time.time()
random.seed(7)
np.random.seed(7)

# ----------------------------------------------------------------- helpers
def lin(c, k=1.0):
    c = c.lstrip('#')
    r, g, b = [int(c[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    f = lambda v: (v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4) * k
    return (f(r), f(g), f(b), 1.0)

def sstep(a, b, x):
    t = np.clip((np.asarray(x, dtype=float) - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)

def _h(ix, iy, seed):
    n = (ix * 374761393 + iy * 668265263 + seed * 982451653) & 0xffffffff
    n = ((n ^ (n >> 13)) * 1274126177) & 0xffffffff
    n = n ^ (n >> 16)
    return (n & 0xffff) / 65535.0

def vnoise(x, y, seed):
    xi = np.floor(x).astype(np.int64); yi = np.floor(y).astype(np.int64)
    xf = x - xi; yf = y - yi
    u = xf * xf * (3 - 2 * xf); v = yf * yf * (3 - 2 * yf)
    a = _h(xi, yi, seed); b = _h(xi + 1, yi, seed)
    c = _h(xi, yi + 1, seed); d = _h(xi + 1, yi + 1, seed)
    return a + (b - a) * u + (c - a) * v + (a - b - c + d) * u * v

def fbm(x, y, octv, seed):
    s = 0.0; amp = 0.5; tot = 0.0
    for o in range(octv):
        s = s + amp * vnoise(x, y, seed + o * 17)
        tot += amp; amp *= 0.5; x = x * 2.03 + 11.1; y = y * 2.03 + 5.3
    return s / tot

# ------------------------------------------------------------------ scene
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.samples = SAMPLES
scene.cycles.use_denoising = True
try:
    scene.cycles.denoiser = 'OPENIMAGEDENOISE'
except Exception:
    pass
scene.cycles.max_bounces = 6
scene.cycles.diffuse_bounces = 3
scene.cycles.glossy_bounces = 4
scene.cycles.transmission_bounces = 2
scene.cycles.sample_clamp_indirect = 6.0
scene.render.resolution_x = W
scene.render.resolution_y = H
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.render.image_settings.color_depth = '16'
scene.cycles.use_adaptive_sampling = True
scene.cycles.adaptive_threshold = 0.02
vt = scene.view_settings
try:
    vt.view_transform = 'AgX'
except Exception:
    vt.view_transform = 'Standard'
try:
    vt.look = 'AgX - Punchy'
except Exception:
    pass
vt.exposure = float(os.environ.get('EXPO', '0.0'))

# the sun: low, behind and to the left of the mine, just outside the frame
SUN = Vector((-0.40, 0.90, 0.20)).normalized()
HAZE_K = float(os.environ.get('HAZEK', '0.0046'))
COOL_HAZE = lin('#46666f', 0.46)
WARM_HAZE = lin('#d09058', 0.62)
WARM_SKY = lin('#e0983e', 0.50)

# ---------------------------------------------------------------- materials
class MB:
    def __init__(self, name):
        self.m = bpy.data.materials.new(name)
        self.m.use_nodes = True
        self.nt = self.m.node_tree
        self.nt.nodes.clear()
        self.n = self.nt.nodes
        self.l = self.nt.links
    def node(self, t, **kw):
        nd = self.n.new(t)
        for k, v in kw.items():
            setattr(nd, k, v)
        return nd
    def put(self, sock, val):
        if isinstance(val, bpy.types.NodeSocket):
            self.l.new(val, sock)
        elif isinstance(val, str):
            sock.default_value = lin(val)
        else:
            sock.default_value = val
    def ins(self, nd, **kw):
        for k, v in kw.items():
            self.put(nd.inputs[k.replace('_', ' ')], v)
        return nd
    def coord(self):
        if not hasattr(self, '_tc'):
            self._tc = self.node('ShaderNodeTexCoord')
        return self._tc.outputs['Object']
    def noise(self, scale, detail=4, rough=0.55, vec=None, dist=0.0):
        nd = self.node('ShaderNodeTexNoise')
        nd.noise_dimensions = '3D'
        self.put(nd.inputs['Vector'], vec if vec is not None else self.coord())
        nd.inputs['Scale'].default_value = scale
        nd.inputs['Detail'].default_value = detail
        nd.inputs['Roughness'].default_value = rough
        nd.inputs['Distortion'].default_value = dist
        return nd.outputs['Fac']
    def voronoi(self, scale, vec=None, out='Distance'):
        nd = self.node('ShaderNodeTexVoronoi')
        self.put(nd.inputs['Vector'], vec if vec is not None else self.coord())
        nd.inputs['Scale'].default_value = scale
        return nd.outputs[out]
    def ramp(self, fac, stops):
        nd = self.node('ShaderNodeValToRGB')
        cr = nd.color_ramp
        while len(cr.elements) > len(stops):
            cr.elements.remove(cr.elements[-1])
        while len(cr.elements) < len(stops):
            cr.elements.new(0.5)
        for e, (p, c) in zip(cr.elements, stops):
            e.position = p
            e.color = lin(c) if isinstance(c, str) else c
        self.put(nd.inputs['Fac'], fac)
        return nd.outputs['Color']
    def mix(self, fac, a, b, blend='MIX'):
        nd = self.node('ShaderNodeMixRGB', blend_type=blend)
        self.put(nd.inputs['Fac'], fac)
        self.put(nd.inputs['Color1'], lin(a) if isinstance(a, str) else a)
        self.put(nd.inputs['Color2'], lin(b) if isinstance(b, str) else b)
        return nd.outputs['Color']
    def math(self, op, a, b=0.0, clamp=False):
        nd = self.node('ShaderNodeMath', operation=op)
        nd.use_clamp = clamp
        self.put(nd.inputs[0], a)
        self.put(nd.inputs[1], b)
        return nd.outputs[0]
    def sep(self, vec):
        nd = self.node('ShaderNodeSeparateXYZ')
        self.put(nd.inputs[0], vec)
        return nd.outputs['X'], nd.outputs['Y'], nd.outputs['Z']
    def bump(self, height, strength=0.5, dist=0.1):
        nd = self.node('ShaderNodeBump')
        nd.inputs['Strength'].default_value = strength
        nd.inputs['Distance'].default_value = dist
        self.put(nd.inputs['Height'], height)
        return nd.outputs['Normal']
    def principled(self, color, rough=0.8, metal=0.0, normal=None, emit=None, emit_strength=0.0, spec=0.35, ior=1.45):
        p = self.node('ShaderNodeBsdfPrincipled')
        self.put(p.inputs['Base Color'], color)
        self.put(p.inputs['Roughness'], rough)
        self.put(p.inputs['Metallic'], metal)
        try:
            self.put(p.inputs['Specular IOR Level'], spec)
        except Exception:
            pass
        p.inputs['IOR'].default_value = ior
        if normal is not None:
            self.put(p.inputs['Normal'], normal)
        if emit is not None:
            self.put(p.inputs['Emission Color'], emit)
            p.inputs['Emission Strength'].default_value = emit_strength
        return p.outputs['BSDF']
    def finish(self, surf, haze=True):
        out = self.node('ShaderNodeOutputMaterial')
        if not haze:
            self.l.new(surf, out.inputs['Surface'])
            return self.m
        cd = self.node('ShaderNodeCameraData')
        mul = self.math('MULTIPLY', cd.outputs['View Distance'], -HAZE_K)
        pw = self.math('POWER', 2.71828, mul)
        fac = self.math('SUBTRACT', 1.0, pw, clamp=True)
        geo = self.node('ShaderNodeNewGeometry')
        dt = self.node('ShaderNodeVectorMath', operation='DOT_PRODUCT')
        self.l.new(geo.outputs['Incoming'], dt.inputs[0])
        dt.inputs[1].default_value = (-SUN.x, -SUN.y, -SUN.z)
        mx = self.math('MAXIMUM', dt.outputs['Value'], 0.0)
        w = self.math('POWER', mx, 5.0)
        hz = self.mix(w, COOL_HAZE, WARM_HAZE)
        em = self.node('ShaderNodeEmission')
        self.put(em.inputs['Color'], hz)
        em.inputs['Strength'].default_value = 1.0
        ms = self.node('ShaderNodeMixShader')
        self.put(ms.inputs['Fac'], fac)
        self.l.new(surf, ms.inputs[1])
        self.l.new(em.outputs['Emission'], ms.inputs[2])
        self.l.new(ms.outputs['Shader'], out.inputs['Surface'])
        return self.m

def mat_ground():
    mb = MB('ground')
    big = mb.noise(0.35, 5, 0.6)
    mid = mb.noise(3.0, 5, 0.6)
    fine = mb.noise(38.0, 3, 0.7)
    peb = mb.voronoi(26.0)
    at = mb.node('ShaderNodeAttribute'); at.attribute_name = 'mask'
    r, g, b_ = mb.sep(at.outputs['Color'])
    sand = mb.ramp(mid, [(0.0, '#20150f'), (0.45, '#35231a'), (0.7, '#4a3220'), (1.0, '#5b3f26')])
    sand = mb.mix(fine, sand, '#5b4231', 'MULTIPLY') if False else sand
    sand2 = mb.mix(mb.ramp(fine, [(0.3, '#ffffff'), (0.7, '#b8a58f')]), sand, '#3e2c22', 'MULTIPLY')
    gravel = mb.ramp(peb, [(0.0, '#1b130f'), (0.5, '#33241b'), (1.0, '#4a3425')])
    gmask = mb.ramp(mb.noise(0.45, 4, 0.6), [(0.36, '#000000'), (0.55, '#ffffff')])
    sand2 = mb.mix(mb.math('MULTIPLY', mb.sep(gmask)[0], 0.85), sand2, gravel)
    # ballast / ore dust near the rails: dark brown-black
    ballast = mb.ramp(peb, [(0.0, '#1a1410'), (0.5, '#3a2c22'), (1.0, '#4f3d2e')])
    col = mb.mix(mb.math('MULTIPLY', r, 0.9, clamp=True), sand2, ballast)
    # mud: dark, wet
    col = mb.mix(mb.math('MULTIPLY', g, 0.85, clamp=True), col, '#2a1d17')
    # high rock: strata bands in rust, ochre and slate
    cx, cy, cz = mb.sep(mb.coord())
    wob = mb.noise(0.05, 3, 0.5)
    band = mb.math('SINE', mb.math('ADD', mb.math('MULTIPLY', cz, 0.55), mb.math('MULTIPLY', wob, 9.0)))
    band2 = mb.math('SINE', mb.math('ADD', mb.math('MULTIPLY', cz, 1.9), mb.math('MULTIPLY', wob, 14.0)))
    strata = mb.ramp(mb.math('ADD', mb.math('ADD', mb.math('MULTIPLY', band, 0.5), mb.math('MULTIPLY', band2, 0.22)), 0.5),
                     [(0.0, '#5a4741'), (0.35, '#7b5640'), (0.6, '#a2724a'), (0.85, '#8a6a4c'), (1.0, '#b88a5a')])
    col = mb.mix(b_, col, strata)
    bump = mb.bump(mb.math('ADD', mb.math('MULTIPLY', fine, 0.4), mb.math('MULTIPLY', mb.math('SUBTRACT', 1.0, peb), 0.45)), 0.6, 0.05)
    bsdf = mb.principled(col, rough=mb.math('SUBTRACT', 0.92, mb.math('MULTIPLY', g, 0.72)), normal=bump, spec=0.25)
    return mb.finish(bsdf)

def mat_rock(tint=None):
    mb = MB('rock')
    n1 = mb.noise(4.5, 5, 0.6)
    n2 = mb.noise(30.0, 3, 0.6)
    col = mb.ramp(n1, [(0.0, '#2b1e18'), (0.35, '#4a3024'), (0.65, '#6a4630'), (1.0, '#85583a')])
    col = mb.mix(mb.ramp(n2, [(0.3, '#ffffff'), (0.75, '#a89888')]), col, '#2b211b', 'MULTIPLY')
    if tint:
        col = mb.mix(mb.ramp(mb.noise(2.2, 3, 0.5), [(0.55, '#000000'), (0.62, '#ffffff')]), col, tint)
    bump = mb.bump(mb.math('ADD', n1, n2), 0.8, 0.04)
    return mb.finish(mb.principled(col, rough=0.9, normal=bump, spec=0.3))

def mat_timber(light=False):
    mb = MB('timber')
    v = mb.coord()
    x, y, z = mb.sep(v)
    # grain: noise stretched along the beam (we do not know the beam direction, so use all three)
    gv = mb.node('ShaderNodeMapping')
    mb.put(gv.inputs['Vector'], v)
    gv.inputs['Scale'].default_value = (14.0, 14.0, 3.0)
    grain = mb.noise(1.0, 4, 0.6, vec=gv.outputs['Vector'])
    big = mb.noise(0.8, 3, 0.5)
    base = mb.ramp(grain, [(0.0, '#14100d'), (0.45, '#2b211a'), (0.7, '#463629'), (1.0, '#5e4a38')])
    gray = mb.ramp(big, [(0.3, '#ffffff'), (0.8, '#a9a69a')])
    col = mb.mix(gray, base, base, 'MULTIPLY') if False else mb.mix(mb.ramp(big, [(0.2, '#ffffff'), (0.8, '#b9b4a8')]), '#000000', '#000000') if False else base
    col = mb.mix(mb.ramp(big, [(0.25, '#000000'), (0.85, '#ffffff')]), base, '#6f6a62' if light else '#4a4640', 'MULTIPLY') if False else base
    bump = mb.bump(grain, 0.7, 0.03)
    return mb.finish(mb.principled(col, rough=0.88, normal=bump, spec=0.25))

def mat_iron(rust_amount=0.6):
    mb = MB('iron')
    n1 = mb.noise(6.0, 5, 0.6)
    n2 = mb.noise(40.0, 3, 0.6)
    rust = mb.ramp(n1, [(0.0, '#2a1710'), (0.4, '#5c2f17'), (0.65, '#8f4a1f'), (1.0, '#b66a2c')])
    dark = mb.mix(mb.ramp(n2, [(0.2, '#ffffff'), (0.8, '#9c8f86')]), '#1c1816', '#1c1816')
    col = mb.mix(mb.ramp(mb.noise(2.0, 4, 0.55), [(0.35, '#000000'), (0.6, '#ffffff')]), '#1d1917', rust)
    bump = mb.bump(mb.math('ADD', n1, n2), 0.6, 0.02)
    bsdf = mb.principled(col, rough=0.62, metal=0.55, normal=bump, spec=0.5)
    return mb.finish(bsdf)

def mat_tin():
    mb = MB('tin')
    n1 = mb.noise(3.0, 5, 0.6)
    n2 = mb.noise(14.0, 3, 0.6)
    streak = mb.node('ShaderNodeMapping')
    mb.put(streak.inputs['Vector'], mb.coord())
    streak.inputs['Scale'].default_value = (1.5, 1.5, 0.35)
    st = mb.noise(1.0, 4, 0.6, vec=streak.outputs['Vector'])
    col = mb.ramp(st, [(0.0, '#3a3a3a'), (0.4, '#6f6a60'), (0.55, '#8a5a35'), (0.8, '#5a2e1a'), (1.0, '#3a1d12')])
    bump = mb.bump(n2, 0.4, 0.02)
    bsdf = mb.principled(col, rough=0.5, metal=0.7, normal=bump, spec=0.5)
    return mb.finish(bsdf)

def mat_brick():
    mb = MB('brick')
    geo = mb.node('ShaderNodeNewGeometry')
    nx, ny, nz = mb.sep(geo.outputs['Normal'])
    ax = mb.math('GREATER_THAN', mb.math('ABSOLUTE', nx), 0.5)
    px, py, pz = mb.sep(mb.coord())
    # coordinates for walls facing y: (x, z); for walls facing x: (y, z)
    hor = mb.math('ADD', mb.math('MULTIPLY', px, mb.math('SUBTRACT', 1.0, ax)), mb.math('MULTIPLY', py, ax))
    vc = mb.node('ShaderNodeCombineXYZ')
    mb.put(vc.inputs['X'], hor); mb.put(vc.inputs['Y'], pz)
    br = mb.node('ShaderNodeTexBrick')
    br.inputs['Color1'].default_value = lin('#7a3a24')
    br.inputs['Color2'].default_value = lin('#a05a38')
    br.inputs['Mortar'].default_value = lin('#6b6258')
    br.inputs['Scale'].default_value = 3.6
    br.inputs['Mortar Size'].default_value = 0.025
    br.inputs['Mortar Smooth'].default_value = 0.1
    br.inputs['Bias'].default_value = 0.0
    br.inputs['Brick Width'].default_value = 0.5
    br.inputs['Row Height'].default_value = 0.2
    mb.l.new(vc.outputs['Vector'], br.inputs['Vector'])
    soot = mb.noise(1.6, 5, 0.6)
    col = mb.mix(mb.ramp(soot, [(0.35, '#ffffff'), (0.75, '#4a3b36')]), br.outputs['Color'], '#2a211e', 'MULTIPLY') if False else br.outputs['Color']
    col = mb.mix(mb.ramp(soot, [(0.3, '#000000'), (0.8, '#ffffff')]), col, '#2b201c')
    bump = mb.bump(br.outputs['Fac'], 0.5, 0.03)
    return mb.finish(mb.principled(col, rough=0.85, normal=bump, spec=0.3))

def mat_glow(strength=14.0, color='#ffb066'):
    mb = MB('glow')
    flick = mb.noise(9.0, 2, 0.5)
    c = mb.mix(flick, color, '#ff9a48')
    bsdf = mb.principled('#2a1a10', rough=0.5, emit=c, emit_strength=strength)
    return mb.finish(bsdf, haze=True)

def mat_water():
    mb = MB('water')
    rip = mb.noise(14.0, 3, 0.5)
    bump = mb.bump(rip, 0.05, 0.02)
    col = mb.mix(mb.noise(0.5, 3, 0.5), '#0a1417', '#10161a')
    bsdf = mb.principled(col, rough=0.035, normal=bump, spec=0.5, ior=1.33)
    return mb.finish(bsdf)

def mat_grass():
    mb = MB('grass')
    n = mb.noise(7.0, 2, 0.5)
    col = mb.ramp(n, [(0.0, '#6b5a2e'), (0.5, '#a58a48'), (1.0, '#cfae66')])
    d = mb.principled(col, rough=0.8, spec=0.1)
    tr = mb.node('ShaderNodeBsdfTranslucent')
    mb.put(tr.inputs['Color'], mb.mix(n, '#a47e3c', '#c59c52'))
    ms = mb.node('ShaderNodeMixShader')
    ms.inputs['Fac'].default_value = 0.5
    mb.l.new(d, ms.inputs[1]); mb.l.new(tr.outputs['BSDF'], ms.inputs[2])
    return mb.finish(ms.outputs['Shader'])

def mat_shrub():
    mb = MB('shrub')
    n = mb.noise(9.0, 2, 0.5)
    col = mb.ramp(n, [(0.0, '#2a3225'), (0.5, '#4a5638'), (1.0, '#6f7447')])
    d = mb.principled(col, rough=0.85, spec=0.1)
    tr = mb.node('ShaderNodeBsdfTranslucent')
    mb.put(tr.inputs['Color'], mb.mix(n, '#7d7a44', '#a99655'))
    ms = mb.node('ShaderNodeMixShader')
    ms.inputs['Fac'].default_value = 0.4
    mb.l.new(d, ms.inputs[1]); mb.l.new(tr.outputs['BSDF'], ms.inputs[2])
    return mb.finish(ms.outputs['Shader'])

def mat_cactus():
    mb = MB('cactus')
    n = mb.noise(25.0, 3, 0.6)
    col = mb.ramp(mb.noise(1.5, 3, 0.5), [(0.0, '#101f19'), (0.6, '#1b3328'), (1.0, '#24412f')])
    bump = mb.bump(n, 0.5, 0.01)
    return mb.finish(mb.principled(col, rough=0.62, normal=bump, spec=0.5))

def mat_plain(color, rough=0.9, metal=0.0):
    mb = MB('plain')
    return mb.finish(mb.principled(color, rough=rough, metal=metal))

MAT = {}
def build_materials():
    MAT['ground'] = mat_ground()
    MAT['rock'] = mat_rock()
    MAT['ore'] = mat_rock('#3c6a5a')
    MAT['timber'] = mat_timber()
    MAT['iron'] = mat_iron()
    MAT['tin'] = mat_tin()
    MAT['brick'] = mat_brick()
    MAT['glow'] = mat_glow(5.5)
    MAT['glow_hot'] = mat_glow(11.0, '#ff9a40')
    MAT['water'] = mat_water()
    MAT['grass'] = mat_grass()
    MAT['dark'] = mat_plain('#120e0c', 0.9)
    MAT['cactus'] = mat_cactus()
    MAT['shrub'] = mat_shrub()

# ---------------------------------------------------------------- mesh builder
class Mesher:
    def __init__(self):
        self.v = []
        self.f = []
    def quad(self, a, b, c, d):
        n = len(self.v)
        self.v.extend([tuple(a), tuple(b), tuple(c), tuple(d)])
        self.f.append((n, n + 1, n + 2, n + 3))
    def tri(self, a, b, c):
        n = len(self.v)
        self.v.extend([tuple(a), tuple(b), tuple(c)])
        self.f.append((n, n + 1, n + 2))
    def beam(self, p0, p1, w, h, up=(0, 0, 1)):
        p0 = Vector(p0); p1 = Vector(p1)
        a = p1 - p0
        L = a.length
        if L < 1e-6:
            return
        an = a / L
        u = an.cross(Vector(up))
        if u.length < 1e-4:
            u = an.cross(Vector((1, 0, 0)))
        u.normalize()
        vv = u.cross(an)
        c = []
        for p in (p0, p1):
            for su, sv in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
                c.append(p + u * (su * w / 2) + vv * (sv * h / 2))
        self.quad(c[0], c[1], c[2], c[3])
        self.quad(c[7], c[6], c[5], c[4])
        self.quad(c[0], c[4], c[5], c[1])
        self.quad(c[1], c[5], c[6], c[2])
        self.quad(c[2], c[6], c[7], c[3])
        self.quad(c[3], c[7], c[4], c[0])
    def box(self, center, size, rotz=0.0):
        cx, cy, cz = center
        sx, sy, sz = size
        R = Matrix.Rotation(rotz, 3, 'Z')
        pts = []
        for i in (-1, 1):
            for j in (-1, 1):
                for k in (-1, 1):
                    pts.append(Vector((cx, cy, cz)) + R @ Vector((i * sx / 2, j * sy / 2, k * sz / 2)))
        # index: i,j,k loops -> idx = (i>0)*4+(j>0)*2+(k>0)
        q = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
        for a, b, c, d in q:
            self.quad(pts[a], pts[b], pts[c], pts[d])
    def cyl(self, p0, p1, r0, r1=None, seg=14, caps=True):
        p0 = Vector(p0); p1 = Vector(p1)
        r1 = r0 if r1 is None else r1
        a = (p1 - p0); L = a.length
        an = a / L
        u = an.cross(Vector((0, 0, 1)))
        if u.length < 1e-4:
            u = an.cross(Vector((1, 0, 0)))
        u.normalize()
        vv = u.cross(an)
        ring0 = []; ring1 = []
        for i in range(seg):
            t = 2 * math.pi * i / seg
            d = u * math.cos(t) + vv * math.sin(t)
            ring0.append(p0 + d * r0); ring1.append(p1 + d * r1)
        for i in range(seg):
            j = (i + 1) % seg
            self.quad(ring0[i], ring0[j], ring1[j], ring1[i])
        if caps:
            for i in range(seg):
                j = (i + 1) % seg
                self.tri(p0, ring0[j], ring0[i])
                self.tri(p1, ring1[i], ring1[j])
    def build(self, name, matkey, smooth=False):
        me = bpy.data.meshes.new(name)
        me.from_pydata(self.v, [], self.f)
        me.update()
        if smooth:
            for p in me.polygons:
                p.use_smooth = True
        ob = bpy.data.objects.new(name, me)
        bpy.context.scene.collection.objects.link(ob)
        ob.data.materials.append(MAT[matkey])
        return ob

MESH = {}
def M(key):
    if key not in MESH:
        MESH[key] = Mesher()
    return MESH[key]

# ----------------------------------------------------------------- terrain
def track_x(y):
    return 3.0 * sstep(4, 54, y) - 0.5 * np.sin(sstep(0, 30, y) * math.pi)

def road_x(y):
    return -4.6 - 5.5 * sstep(18, 46, y)

MESAS = [  # cx, cy, rx, ry, height, seed
    (-95, 430, 150, 75, 56, 1),
    (105, 330, 48, 34, 58, 2),
    (-330, 520, 120, 60, 50, 3),
    (40, 760, 300, 70, 95, 4),
    (330, 560, 110, 70, 70, 5),
    (-20, 205, 150, 40, 7, 6),
    (125, 215, 70, 30, 12, 7),
    (-170, 250, 60, 36, 16, 8),
]
PUDDLES = [  # cx, cy, ax, ay, depth   (y is measured ahead of the camera, CAMY below)
    (-1.6, 20.5, 0.8, 1.6, 0.10),
    (1.7, 24.0, 0.8, 1.8, 0.10),
    (-1.5, 28.5, 0.8, 2.4, 0.10),
    (-5.2, 33.0, 1.5, 3.0, 0.10),
    (-4.7, 25.0, 0.9, 2.2, 0.09),
    (-0.2, 38.0, 1.0, 2.6, 0.09),
    (5.6, 36.0, 1.3, 2.6, 0.10),
    (-3.2, 43.5, 1.8, 3.4, 0.10),
    (-8.0, 40.0, 2.0, 3.4, 0.10),
]

def puddle_r(theta, k):
    return 1 + 0.16 * np.sin(theta * 2 + k) + 0.10 * np.sin(theta * 3 + 2 * k) + 0.06 * np.sin(theta * 5 + 3 * k)

PUD_BASE = {}

def ground_h(x, y, with_masks=False, puddles=True):
    h = 0.55 * (fbm(x / 24, y / 24, 3, 1) - 0.5)
    h += 0.20 * (fbm(x / 4.5, y / 4.5, 3, 2) - 0.5)
    h += 0.05 * (fbm(x / 0.9, y / 0.9, 2, 3) - 0.5)
    # shallow dry wash across the foreground
    # mine compound platform
    ox = np.maximum(np.abs(x - 2.0) - 22.0, 0); oy = np.maximum(np.abs(y - 56) - 17.0, 0)
    od = np.sqrt(ox * ox + oy * oy)
    plat = 1 - sstep(0, 7, od)
    h = h * (1 - plat) + (0.1 + 0.05 * fbm(x / 3, y / 3, 2, 9)) * plat
    # track bed
    dt = np.abs(x - track_x(y))
    bed = (1 - sstep(1.0, 2.6, dt)) * sstep(-6, -1, y)
    bedz = 0.12 + 0.008 * np.minimum(y, 60) + 0.025 * (fbm(x * 3, y * 3, 2, 5) - 0.5)
    h = h * (1 - bed) + bedz * bed
    # wagon road with two ruts
    rc = road_x(y)
    dr = np.abs(x - rc)
    roadm = (1 - sstep(0.8, 2.2, dr)) * sstep(8, 14, y) * (1 - sstep(60, 66, y))
    rut = (np.exp(-((dr - 0.72) / 0.2) ** 2)) * sstep(8, 14, y) * (1 - sstep(60, 66, y))
    h = h - 0.10 * rut - 0.03 * roadm
    # waste dump: a flat-topped fan of rock behind the mine
    rr = np.hypot(x - 26, (y - 88) * 0.8)
    dump = np.minimum(8.5, (22 - rr) * 0.6) * (rr < 22) * (0.85 + 0.3 * fbm(x / 4, y / 4, 3, 21))
    h = h + np.maximum(dump, 0)
    # mesas and buttes
    for cx, cy, rx, ry, ht, sd in MESAS:
        u = (x - cx) / rx; v = (y - cy) / ry
        d = (np.abs(u) ** 3.0 + np.abs(v) ** 3.0) ** (1 / 3.0)
        d = d + 0.16 * (fbm(u * 2.5 + sd, v * 2.5, 4, sd) - 0.5) + 0.05 * (fbm(u * 9, v * 9, 3, sd + 9) - 0.5)
        t = np.clip((1.45 - d) / 0.6, 0, 1)
        prof = 0.30 * sstep(0, 0.62, t) + 0.70 * sstep(0.58, 0.82, t)
        # a ledge in the cliff
        prof = prof + 0.04 * np.sin(t * 22) * sstep(0.5, 0.7, t) * (1 - sstep(0.85, 1.0, t))
        top = 1 + 0.015 * (fbm(u * 6, v * 6, 3, sd + 3) - 0.5)
        h = h + ht * prof * top
    # puddles
    mask_g = np.zeros_like(x)
    for (cx, cy, ax, ay, dep), pk in zip(PUDDLES if puddles else [], range(len(PUDDLES))):
        u = (x - cx) / ax; v = (y - cy) / ay
        th = np.arctan2(v, u)
        r = np.hypot(u, v) / puddle_r(th, pk * 1.7)
        base = bedz_at(cx, cy)
        z = np.where(r < 1, base - dep * (1 - r * r), base)
        w = 1 - sstep(1.0, 1.7, r)
        h = h * (1 - w) + z * w
        mask_g = np.maximum(mask_g, 1 - sstep(0.9, 1.9, r))
    if with_masks:
        track_m = (1 - sstep(0.6, 2.3, dt)) * sstep(-6, -1, y) * (1 - sstep(62, 70, y))
        hi = sstep(1.8, 5.5, h)
        mud = np.maximum(mask_g * 0.95, rut * 0.8)
        mud = np.maximum(mud, 0.5 * roadm * fbm(x * 2, y * 2, 2, 31))
        # wet patches left behind by the storm, mostly near the camera and along the wash
        wet = sstep(0.55, 0.68, fbm(x / 2.6 + 3.0, y / 2.6, 3, 41)) * (1 - sstep(CAMY + 28, CAMY + 40, y)) * (1 - 0.9 * track_m)
        mud = np.maximum(mud, 0.75 * wet)
        return h, np.stack([track_m, mud, hi], axis=-1)
    return h

def bedz_at(cx, cy):
    # the unflattened height at a puddle centre: take the local terrain with puddles left out
    key = (round(float(cx), 2), round(float(cy), 2))
    if key not in PUD_BASE:
        PUD_BASE[key] = float(ground_h(np.array([cx], dtype=float), np.array([cy], dtype=float), puddles=False)[0])
    return PUD_BASE[key]

CAMY = 14.0

def axis(maxv, fine=0.12, growth=0.015):
    pos = [0.0]; v = 0.0
    while v < maxv:
        v += max(fine, growth * v)
        pos.append(v)
    return np.array(pos)

def build_terrain():
    ya = axis(1600); yb = axis(5)
    ys = CAMY + np.concatenate([-yb[::-1][:-1], ya])
    xa = axis(1300)
    xs = np.concatenate([-xa[::-1][:-1], xa])
    X, Y = np.meshgrid(xs, ys)
    Z, MK = ground_h(X, Y, with_masks=True)
    ny, nx = X.shape
    me = bpy.data.meshes.new('terrain')
    nv = nx * ny
    me.vertices.add(nv)
    co = np.stack([X, Y, Z], axis=-1).reshape(-1, 3).astype(np.float32)
    me.vertices.foreach_set('co', co.ravel())
    idx = np.arange(nv).reshape(ny, nx)
    q = np.stack([idx[:-1, :-1], idx[:-1, 1:], idx[1:, 1:], idx[1:, :-1]], axis=-1).reshape(-1, 4)
    nf = q.shape[0]
    me.loops.add(nf * 4)
    me.polygons.add(nf)
    me.polygons.foreach_set('loop_start', (np.arange(nf) * 4).astype(np.int32))
    me.polygons.foreach_set('loop_total', np.full(nf, 4, dtype=np.int32))
    me.loops.foreach_set('vertex_index', q.ravel().astype(np.int32))
    me.polygons.foreach_set('use_smooth', np.ones(nf, dtype=bool))
    me.update(calc_edges=True)
    ca = me.color_attributes.new('mask', 'FLOAT_COLOR', 'POINT')
    rgba = np.concatenate([MK.reshape(-1, 3), np.ones((nv, 1))], axis=1).astype(np.float32)
    ca.data.foreach_set('color', rgba.ravel())
    ob = bpy.data.objects.new('terrain', me)
    scene.collection.objects.link(ob)
    ob.data.materials.append(MAT['ground'])
    print('terrain verts', nv, 'time', round(time.time() - T0, 1))
    return ob

def gh(x, y):
    return float(ground_h(np.array([x], dtype=float), np.array([y], dtype=float))[0])

def add_puddle_water():
    mk = Mesher()
    for (cx, cy, ax, ay, dep), pk in zip(PUDDLES, range(len(PUDDLES))):
        base = bedz_at(cx, cy)
        z = base - dep * (1 - 0.8 ** 2) + 0.004
        pts = []
        for i in range(48):
            th = 2 * math.pi * i / 48
            r = 0.8 * puddle_r(th, pk * 1.7)
            pts.append((cx + ax * r * math.cos(th), cy + ay * r * math.sin(th), z))
        for i in range(48):
            mk.tri((cx, cy, z), pts[i], pts[(i + 1) % 48])
    mk.build('water', 'water')

# ------------------------------------------------------------------ camera and light
def setup_camera():
    cam = bpy.data.cameras.new('cam')
    cam.lens = float(os.environ.get('LENS', '34'))
    cam.sensor_fit = 'VERTICAL'
    cam.sensor_height = 36
    cam.shift_y = float(os.environ.get('SHIFTY', '0.08'))
    cam.clip_start = 0.1
    cam.clip_end = 6000
    ob = bpy.data.objects.new('cam', cam)
    scene.collection.objects.link(ob)
    ob.location = (-0.3, CAMY, 1.65)
    ob.rotation_euler = (math.radians(90), 0, 0)
    scene.camera = ob

def setup_world():
    w = bpy.data.worlds.new('sky')
    scene.world = w
    w.use_nodes = True
    nt = w.node_tree
    nt.nodes.clear()
    mb = MB.__new__(MB)
    mb.m = None; mb.nt = nt; mb.n = nt.nodes; mb.l = nt.links
    tc = mb.node('ShaderNodeTexCoord')
    d = tc.outputs['Generated']
    dx, dy, dz = mb.sep(d)
    e = mb.math('MAXIMUM', dz, 0.0)
    dt = mb.node('ShaderNodeVectorMath', operation='DOT_PRODUCT')
    mb.l.new(d, dt.inputs[0])
    dt.inputs[1].default_value = (SUN.x, SUN.y, SUN.z)
    wsun = mb.math('POWER', mb.math('MAXIMUM', dt.outputs['Value'], 0.0), 5.0)
    # vertical gradient: horizon matches the haze, then teal, then deep blue
    grad = mb.ramp(mb.math('POWER', e, 0.55), [
        (0.0, lin('#6e8c8a', 0.50)), (0.12, lin('#6f9696', 0.50)), (0.30, lin('#4d737c', 0.44)),
        (0.55, lin('#2b4b57', 0.36)), (1.0, lin('#13303c', 0.28))])
    # warm glow, thickest at the horizon on the sun side
    glowfac = mb.math('MULTIPLY', wsun, mb.math('SUBTRACT', 1.0, mb.ramp(e, [(0.0, '#000000'), (0.35, '#ffffff')])) if False else
                      mb.math('SUBTRACT', 1.0, mb.math('MINIMUM', mb.math('MULTIPLY', e, 3.2), 1.0)))
    sky = mb.mix(glowfac, grad, WARM_SKY)
    # streaky cloud banks: stretched sideways, dark slate with amber undersides toward the sun
    sc = mb.node('ShaderNodeMapping')
    mb.l.new(d, sc.inputs['Vector'])
    sc.inputs['Scale'].default_value = (2.2, 2.2, 8.0)
    cl = mb.noise(1.0, 5, 0.58, vec=sc.outputs['Vector'], dist=0.6)
    cmask = mb.ramp(cl, [(0.44, '#000000'), (0.64, '#ffffff')])
    cm, _, _ = mb.sep(cmask)
    band = mb.math('MULTIPLY', mb.math('MINIMUM', mb.math('MULTIPLY', e, 14.0), 1.0),
                   mb.math('SUBTRACT', 1.0, mb.math('MINIMUM', mb.math('MULTIPLY', mb.math('MAXIMUM', mb.math('SUBTRACT', e, 0.6), 0.0), 2.5), 1.0)))
    cfac = mb.math('MULTIPLY', cm, band)
    warmc = mb.math('MULTIPLY', mb.math('MINIMUM', mb.math('MULTIPLY', wsun, 1.8), 1.0),
                    mb.math('SUBTRACT', 1.0, mb.math('MINIMUM', mb.math('MULTIPLY', e, 3.4), 1.0)))
    ccol = mb.mix(warmc, lin('#3a5662', 0.50), lin('#d28a4a', 0.7))
    sky = mb.mix(mb.math('MULTIPLY', cfac, 0.9), sky, ccol)
    bg = mb.node('ShaderNodeBackground')
    lp = mb.node('ShaderNodeLightPath')
    fill = mb.math('ADD', 1.0, mb.math('MULTIPLY', mb.math('SUBTRACT', 1.0, lp.outputs['Is Camera Ray']), float(os.environ.get('FILL', '0.9'))))
    mb.l.new(mb.math('MULTIPLY', fill, float(os.environ.get('WORLD', '3.0'))), bg.inputs['Strength'])
    mb.l.new(sky, bg.inputs['Color'])
    out = mb.node('ShaderNodeOutputWorld')
    mb.l.new(bg.outputs['Background'], out.inputs['Surface'])

def add_dust():
    # a box of dusty air around the whole mine: the low sun shows itself in it
    me = bpy.data.meshes.new('dust')
    x0, x1, y0, y1, z0, z1 = -90, 90, CAMY - 2, CAMY + 190, -1, 46
    v = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0), (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
    f = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    me.from_pydata(v, [], f)
    ob = bpy.data.objects.new('dust', me)
    scene.collection.objects.link(ob)
    m = bpy.data.materials.new('dustvol')
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    pv = nt.nodes.new('ShaderNodeVolumeScatter')
    pv.inputs['Color'].default_value = (1.0, 0.82, 0.62, 1.0)
    pv.inputs['Anisotropy'].default_value = 0.72
    # thicker low down and toward the sun, thinner higher up; a little drift in it
    tc = nt.nodes.new('ShaderNodeTexCoord')
    nz = nt.nodes.new('ShaderNodeTexNoise')
    nz.inputs['Scale'].default_value = 0.035
    nz.inputs['Detail'].default_value = 3
    nt.links.new(tc.outputs['Object'], nz.inputs['Vector'])
    sp = nt.nodes.new('ShaderNodeSeparateXYZ')
    nt.links.new(tc.outputs['Object'], sp.inputs[0])
    hz = nt.nodes.new('ShaderNodeMath'); hz.operation = 'MULTIPLY'; hz.inputs[1].default_value = -0.07
    nt.links.new(sp.outputs['Z'], hz.inputs[0])
    ex = nt.nodes.new('ShaderNodeMath'); ex.operation = 'POWER'; ex.inputs[0].default_value = 2.71828
    nt.links.new(hz.outputs[0], ex.inputs[1])
    dn = nt.nodes.new('ShaderNodeMath'); dn.operation = 'MULTIPLY'; dn.inputs[1].default_value = float(os.environ.get('DUST', '0.0075'))
    nt.links.new(ex.outputs[0], dn.inputs[0])
    dn2 = nt.nodes.new('ShaderNodeMath'); dn2.operation = 'MULTIPLY'
    nt.links.new(dn.outputs[0], dn2.inputs[0])
    nt.links.new(nz.outputs['Fac'], dn2.inputs[1])
    mm = nt.nodes.new('ShaderNodeMath'); mm.operation = 'MULTIPLY'; mm.inputs[1].default_value = 1.6
    nt.links.new(dn2.outputs[0], mm.inputs[0])
    nt.links.new(mm.outputs[0], pv.inputs['Density'])
    nt.links.new(pv.outputs['Volume'], out.inputs['Volume'])
    ob.data.materials.append(m)
    ob.visible_shadow = True
    scene.cycles.volume_step_rate = 1.0
    scene.cycles.volume_max_steps = 256
    scene.cycles.volume_bounces = 1

def add_sun():
    ld = bpy.data.lights.new('sun', 'SUN')
    ld.energy = float(os.environ.get('SUNE', '4.5'))
    ld.color = (1.0, 0.52, 0.20)
    ld.angle = math.radians(1.2)
    ob = bpy.data.objects.new('sun', ld)
    scene.collection.objects.link(ob)
    ob.rotation_euler = SUN.to_track_quat('Z', 'Y').to_euler()

def add_point(loc, power, color=(1.0, 0.62, 0.3), radius=0.25):
    ld = bpy.data.lights.new('lamp', 'POINT')
    ld.energy = power
    ld.color = color
    ld.shadow_soft_size = radius
    ob = bpy.data.objects.new('lamp', ld)
    scene.collection.objects.link(ob)
    ob.location = loc
    return ob


# ================================================================== the mine itself
MESH_MAT = {'shrub': 'shrub', 'cactus': 'cactus', 'timber': 'timber', 'iron': 'iron', 'tin': 'tin', 'brick': 'brick', 'glow': 'glow', 'glow_hot': 'glow_hot',
            'dark': 'dark', 'grass': 'grass'}
SMOOTH_KEYS = {'cactus'}
LIGHTS = []   # (location, power, colour, radius)

def mk_xf(origin, rotz, scale=1.0):
    R = Matrix.Rotation(rotz, 3, 'Z')
    o = Vector(origin)
    return lambda p: o + R @ (Vector(p) * scale)

def lerp(a, b, t):
    return a + (b - a) * t

def hexa(mk, c):
    # c: 8 points, bottom 0..3 (ccw), top 4..7
    mk.quad(c[0], c[3], c[2], c[1]); mk.quad(c[4], c[5], c[6], c[7])
    for i in range(4):
        j = (i + 1) % 4
        mk.quad(c[i], c[j], c[j + 4], c[i + 4])

def frustum(mk, xf, hb, ht, zb, zt):
    # square-ish tapered block; hb, ht = (hx,hy) half sizes at bottom and top
    bot = [(-hb[0], -hb[1], zb), (hb[0], -hb[1], zb), (hb[0], hb[1], zb), (-hb[0], hb[1], zb)]
    top = [(-ht[0], -ht[1], zt), (ht[0], -ht[1], zt), (ht[0], ht[1], zt), (-ht[0], ht[1], zt)]
    hexa(mk, [xf(p) for p in bot + top])

def ribbed_panel(mk, a0, a1, b0, b1, rib=0.11, amp=0.035):
    # a0->a1 is the eave edge, b0->b1 the ridge edge (world points); corrugated sheet
    a0, a1, b0, b1 = map(Vector, (a0, a1, b0, b1))
    n = max(2, int((a1 - a0).length / rib))
    nrm = (a1 - a0).cross(b0 - a0).normalized()
    if nrm.z < 0:
        nrm = -nrm
    pts = []
    for i in range(2 * n + 1):
        t = i / (2 * n)
        off = nrm * (amp if i % 2 else 0.0)
        pts.append((a0.lerp(a1, t) + off, b0.lerp(b1, t) + off))
    for i in range(2 * n):
        mk.quad(pts[i][0], pts[i + 1][0], pts[i + 1][1], pts[i][1])
    # thin edge so the sheet has a thickness
    return

def gable_roof(xf, hx, hy, ze, zr, over=0.35):
    tin = M('tin')
    # two slopes of corrugated iron; ridge along local X
    for sgn in (-1, 1):
        a0 = xf((-hx - over, sgn * (hy + over), ze)); a1 = xf((hx + over, sgn * (hy + over), ze))
        b0 = xf((-hx - over, 0, zr)); b1 = xf((hx + over, 0, zr))
        if sgn < 0:
            ribbed_panel(tin, a0, a1, b0, b1)
        else:
            ribbed_panel(tin, a1, a0, b1, b0)
    # ridge cap and eave boards in timber
    t = M('timber')
    t.beam(xf((-hx - over, 0, zr + 0.03)), xf((hx + over, 0, zr + 0.03)), 0.18, 0.07)
    for sgn in (-1, 1):
        t.beam(xf((-hx - over, sgn * (hy + over), ze - 0.05)), xf((hx + over, sgn * (hy + over), ze - 0.05)), 0.07, 0.14)

def window(xf, cx, cz, w, h, y, key='glow', frame=0.07):
    g = M(key); t = M('timber')
    g.beam(xf((cx - w / 2, y, cz)), xf((cx + w / 2, y, cz)), 0.0 + 0.04, h)   # thin lit pane (beam: width along y... see below)
    # frame
    t.beam(xf((cx - w / 2 - frame / 2, y - 0.03, cz)), xf((cx - w / 2 - frame / 2, y - 0.03, cz)), 0.01, 0.01)
    for sx in (-1, 1):
        t.beam(xf((cx + sx * (w / 2 + frame / 2), y - 0.03, cz - h / 2 - frame)), xf((cx + sx * (w / 2 + frame / 2), y - 0.03, cz + h / 2 + frame)), frame, 0.1)
    for sz in (-1, 1):
        t.beam(xf((cx - w / 2 - frame, y - 0.03, cz + sz * (h / 2 + frame / 2))), xf((cx + w / 2 + frame, y - 0.03, cz + sz * (h / 2 + frame / 2))), frame, 0.1, up=(0, 1, 0))
    t.beam(xf((cx, y - 0.04, cz - h / 2)), xf((cx, y - 0.04, cz + h / 2)), 0.035, 0.07)
    t.beam(xf((cx - w / 2, y - 0.04, cz)), xf((cx + w / 2, y - 0.04, cz)), 0.035, 0.07, up=(0, 1, 0))

def lit_pane(xf, cx, cz, w, h, y, key='glow'):
    g = M(key)
    g.quad(xf((cx - w / 2, y, cz - h / 2)), xf((cx + w / 2, y, cz - h / 2)), xf((cx + w / 2, y, cz + h / 2)), xf((cx - w / 2, y, cz + h / 2)))

def window_frame(xf, cx, cz, w, h, y, frame=0.08):
    t = M('timber')
    lit_pane(xf, cx, cz, w, h, y - 0.0)
    for sx in (-1, 1):
        t.beam(xf((cx + sx * (w / 2 + frame / 2), y - 0.05, cz - h / 2 - frame)), xf((cx + sx * (w / 2 + frame / 2), y - 0.05, cz + h / 2 + frame)), 0.1, 0.1)
    for sz in (-1, 1):
        t.beam(xf((cx - w / 2 - frame, y - 0.05, cz + sz * (h / 2 + frame / 2))), xf((cx + w / 2 + frame, y - 0.05, cz + sz * (h / 2 + frame / 2))), 0.1, 0.1)
    # muntins
    t.beam(xf((cx, y - 0.06, cz - h / 2)), xf((cx, y - 0.06, cz + h / 2)), 0.05, 0.05)
    t.beam(xf((cx - w / 2, y - 0.06, cz)), xf((cx + w / 2, y - 0.06, cz)), 0.05, 0.05)

# ---------------------------------------------------------------- headframe
def headframe(origin, rot):
    xf = mk_xf(origin, rot, 1.28)
    t = M('timber'); ir = M('iron')
    Z = 12.8
    hx = lambda z: lerp(3.0, 0.85, z / Z)
    hy = lambda z: lerp(2.4, 1.15, z / Z)
    corners = lambda z: [(-hx(z), -hy(z), z), (hx(z), -hy(z), z), (hx(z), hy(z), z), (-hx(z), hy(z), z)]
    for sx in (-1, 1):
        for sy in (-1, 1):
            t.beam(xf((sx * hx(-0.4), sy * hy(-0.4), -0.4)), xf((sx * hx(Z), sy * hy(Z), Z + 0.2)), 0.42, 0.42)
    levels = [0.9, 3.8, 6.7, 9.6, Z]
    for z in levels:
        c = corners(z)
        for i in range(4):
            t.beam(xf(c[i]), xf(c[(i + 1) % 4]), 0.24, 0.24)
    for z0, z1 in zip(levels[:-1], levels[1:]):
        c0 = corners(z0); c1 = corners(z1)
        for i in range(4):
            j = (i + 1) % 4
            t.beam(xf(c0[i]), xf(c1[j]), 0.17, 0.17)
            t.beam(xf(c0[j]), xf(c1[i]), 0.17, 0.17)
    # back stay legs: heavy timber from top deck down toward the hoist side
    for sy in (-1, 1):
        t.beam(xf((-hx(Z) + 0.1, sy * hy(Z), Z)), xf((-8.5, sy * 1.7, 0.0)), 0.3, 0.3)
        t.beam(xf((-5.5, sy * 1.6, 2.2)), xf((-6.6, sy * 1.65, 0.1)), 0.2, 0.2)
    for xx in (-3.2, -5.0, -6.8):
        t.beam(xf((xx, -1.7, 0.9)), xf((xx, 1.7, 0.9)), 0.17, 0.2, up=(1, 0, 0)) if False else None
    # sheave deck and bearings
    for sy in (-1, 1):
        t.beam(xf((-1.1, sy * 1.5, Z + 0.1)), xf((1.1, sy * 1.5, Z + 0.1)), 0.3, 0.3)
        t.beam(xf((-0.9, sy * 1.35, Z + 0.1)), xf((0.0, sy * 1.35, Z + 1.7)), 0.2, 0.2)
        t.beam(xf((0.9, sy * 1.35, Z + 0.1)), xf((0.0, sy * 1.35, Z + 1.7)), 0.2, 0.2)
    zc = Z + 1.6
    ir.cyl(xf((0, -1.9, zc)), xf((0, 1.9, zc)), 0.09, seg=10)
    R = 1.75
    for yy in (-0.85, 0.85):
        n = 30
        for i in range(n):
            a0 = 2 * math.pi * i / n; a1 = 2 * math.pi * (i + 1) / n
            ir.beam(xf((R * math.cos(a0), yy, zc + R * math.sin(a0))), xf((R * math.cos(a1), yy, zc + R * math.sin(a1))), 0.2, 0.14, up=(0, 1, 0))
        for i in range(12):
            a = 2 * math.pi * i / 12
            ir.beam(xf((0, yy, zc)), xf(((R - 0.05) * math.cos(a), yy, zc + (R - 0.05) * math.sin(a))), 0.07, 0.09, up=(0, 1, 0))
        ir.cyl(xf((0, yy - 0.12, zc)), xf((0, yy + 0.12, zc)), 0.2, seg=10)
    # ropes: down the shaft and slanting to the hoist house
    for yy in (-0.85, 0.85):
        ir.beam(xf((R, yy, zc)), xf((R, yy, 0.4)), 0.05, 0.05)
        ir.beam(xf((-0.2, yy, zc + R)), xf((-15.3, yy * 0.6, 3.0)), 0.05, 0.05)
    # stairs/ladder on the near face
    for i in range(12):
        z = 0.6 + i * 1.0
        t.beam(xf((-hx(z) + 0.7, -hy(z) - 0.05, z)), xf((-hx(z) + 1.5, -hy(z) - 0.05, z)), 0.08, 0.06, up=(0, 1, 0))
    # collar: the dark mouth of the shaft with a timber frame around it
    D = M('dark')
    D.quad(xf((-1.5, -1.0, 0.07)), xf((1.5, -1.0, 0.07)), xf((1.5, 1.0, 0.07)), xf((-1.5, 1.0, 0.07)))
    for sx in (-1, 1):
        t.beam(xf((sx * 1.7, -1.2, 0.15)), xf((sx * 1.7, 1.2, 0.15)), 0.3, 0.3)
    for sy in (-1, 1):
        t.beam(xf((-1.7, sy * 1.2, 0.15)), xf((1.7, sy * 1.2, 0.15)), 0.3, 0.3, up=(0, 0, 1))
    # lamp hanging on the frame
    lp = xf((hx(3.0) + 0.3, -hy(3.0) - 0.45, 3.0))
    ir.cyl(xf((hx(3.0), -hy(3.0), 3.1)), lp + Vector((0, 0, 0.0)), 0.03, seg=6) if False else None
    g = M('glow_hot')
    g.cyl(lp + Vector((0, 0, -0.12)), lp + Vector((0, 0, 0.12)), 0.1, seg=8)
    LIGHTS.append((tuple(lp + Vector((0, 0, 0))), 220, (1.0, 0.6, 0.28), 0.12))
    # a lamp on a bracket at the shaft mouth, where the rails end, and a hidden fill light by the wheels
    zl = 1.9
    leg = (hx(zl), -hy(zl), zl)
    bead = xf((leg[0] - 0.6, leg[1] - 0.15, zl))
    t.beam(xf(leg), bead, 0.07, 0.07)
    M('glow_hot').cyl(bead + Vector((0, 0, -0.1)), bead + Vector((0, 0, 0.1)), 0.07, seg=8)
    LIGHTS.append((tuple(bead + Vector((0, -0.1, 0.0))), 130, (1.0, 0.58, 0.25), 0.1))
    LIGHTS.append((tuple(xf((1.4, -2.0, Z + 0.6))), 90, (1.0, 0.58, 0.25), 0.1))
    return xf

# ---------------------------------------------------------------- hoist house with stack
def hoist_house(origin, rot):
    xf = mk_xf(origin, rot)
    br = M('brick'); t = M('timber')
    hx, hy, wall = 3.7, 2.6, 3.7
    frustum(br, xf, (hx, hy), (hx, hy), -0.3, wall)
    gable_roof(xf, hx, hy, wall - 0.1, wall + 1.5)
    # gable ends in brick: triangles
    for sx in (-1, 1):
        br.tri(xf((sx * hx, -hy, wall)), xf((sx * hx, hy, wall)), xf((sx * hx, 0, wall + 1.45))) if sx > 0 else br.tri(xf((sx * hx, hy, wall)), xf((sx * hx, -hy, wall)), xf((sx * hx, 0, wall + 1.45)))
    yf = -hy - 0.02
    # door, open and glowing
    lit_pane(xf, -0.2, 1.15, 1.3, 2.25, yf - 0.01, 'glow_hot')
    for sx in (-1, 1):
        t.beam(xf((-0.2 + sx * 0.75, yf - 0.06, -0.1)), xf((-0.2 + sx * 0.75, yf - 0.06, 2.45)), 0.18, 0.2)
    t.beam(xf((-1.05, yf - 0.06, 2.4)), xf((0.65, yf - 0.06, 2.4)), 1.8, 0.2, up=(0, 1, 0)) if False else None
    t.beam(xf((-1.1, yf - 0.06, 2.5)), xf((0.7, yf - 0.06, 2.5)), 0.2, 0.2)
    # planks and a cross-bar across the open doorway, so the glow reads as a door and not a lit square
    t.beam(xf((-0.2, yf - 0.07, 0.0)), xf((-0.2, yf - 0.07, 2.4)), 0.07, 0.07)
    t.beam(xf((-0.85, yf - 0.07, 1.15)), xf((0.45, yf - 0.07, 1.15)), 0.07, 0.07)
    # a door leaf, ajar, black against the glow
    M('dark').quad(xf((0.45, yf - 0.02, 0.0)), xf((0.45 + 0.35, yf - 0.55, 0.0)), xf((0.45 + 0.35, yf - 0.55, 2.3)), xf((0.45, yf - 0.02, 2.3)))
    for cx in (-2.5, 2.3):
        window_frame(xf, cx, 2.0, 0.85, 1.05, yf)
    # step and a plank walk
    t.beam(xf((-0.9, yf - 0.6, 0.05)), xf((0.5, yf - 0.6, 0.05)), 0.5, 0.18, up=(0, 0, 1))
    # chimney stack: tall, tapered, with a rim
    sxf = mk_xf(xf((hx - 0.9, hy - 0.9, 0)), rot)
    frustum(br, sxf, (0.9, 0.9), (0.55, 0.55), -0.3, 13.8)
    frustum(br, sxf, (0.72, 0.72), (0.72, 0.72), 13.7, 14.15)
    for z in (2.0, 7.0):
        frustum(br, sxf, (0.95 - 0.35 * z / 14, 0.95 - 0.35 * z / 14), (0.95 - 0.35 * z / 14, 0.95 - 0.35 * z / 14), z, z + 0.14)
    # leaning planks against the near end
    for i in range(9):
        xx = -hx - 0.3 - i * 0.28
        t.beam(xf((xx - 0.9, -hy - 1.6 + i * 0.1, 0.0)), xf((xx + 0.0, -hy - 0.15 + i * 0.07, 3.0 + 0.1 * (i % 3))), 0.22, 0.05, up=(0, 0, 1)) if False else \
            t.beam(xf((-hx - 1.9 - i * 0.12, -hy + 0.5 - i * 0.25, 0.0)), xf((-hx - 0.1, -hy + 0.6 - i * 0.25, 2.7 + 0.12 * (i % 3))), 0.22, 0.05)
    global STACK_TOP
    STACK_TOP = sxf((0, 0, 14.2))
    LIGHTS.append((tuple(xf((-0.2, yf - 1.0, 1.5))), 380, (1.0, 0.5, 0.2), 0.3))
    LIGHTS.append((tuple(xf((-2.5, yf - 0.8, 2.0))), 120, (1.0, 0.62, 0.3), 0.2))
    LIGHTS.append((tuple(xf((2.3, yf - 0.8, 2.0))), 120, (1.0, 0.62, 0.3), 0.2))
    return xf

# ---------------------------------------------------------------- bunkhouse
def bunkhouse(origin, rot):
    xf = mk_xf(origin, rot)
    t = M('timber'); br = M('brick')
    hx, hy, wall = 4.2, 2.2, 2.9
    # board-and-batten walls: timber
    frustum(t, xf, (hx, hy), (hx, hy), -0.3, wall)
    gable_roof(xf, hx, hy, wall - 0.05, wall + 0.9, over=0.5)
    for sx in (-1, 1):
        t.tri(xf((sx * hx, -hy, wall)), xf((sx * hx, hy, wall)), xf((sx * hx, 0, wall + 0.85))) if sx > 0 else t.tri(xf((sx * hx, hy, wall)), xf((sx * hx, -hy, wall)), xf((sx * hx, 0, wall + 0.85)))
    yf = -hy - 0.02
    for cx in (-2.9, -0.9, 2.6):
        window_frame(xf, cx, 1.6, 0.8, 0.95, yf)
    # door, dark
    M('dark').quad(xf((1.0, yf - 0.02, 0)), xf((1.9, yf - 0.02, 0)), xf((1.9, yf - 0.02, 2.0)), xf((1.0, yf - 0.02, 2.0)))
    for sx in (-1, 1):
        t.beam(xf((1.45 + sx * 0.55, yf - 0.05, -0.1)), xf((1.45 + sx * 0.55, yf - 0.05, 2.1)), 0.14, 0.14)
    # porch: deck and posts and a lean-to roof
    t.beam(xf((-hx, yf - 0.9, 0.12)), xf((hx, yf - 0.9, 0.12)), 0.12, 0.2) if False else None
    for sx in (-3.9, 0.0, 3.9):
        t.beam(xf((sx, yf - 1.5, -0.1)), xf((sx, yf - 1.5, 2.7)), 0.16, 0.16)
    ribbed_panel(M('tin'), xf((-hx - 0.2, yf - 1.7, 2.55)), xf((hx + 0.2, yf - 1.7, 2.55)), xf((-hx - 0.2, yf - 0.0, 3.0)), xf((hx + 0.2, yf - 0.0, 3.0)))
    # stove pipe
    M('iron').cyl(xf((-2.0, 0.6, wall + 0.2)), xf((-2.0, 0.6, wall + 2.5)), 0.12, seg=8)
    M('iron').cyl(xf((-2.0, 0.6, wall + 2.5)), xf((-2.0, 0.6, wall + 2.7)), 0.24, seg=8)
    for cx in (-2.9, -0.9, 2.6):
        LIGHTS.append((tuple(xf((cx, yf - 0.7, 1.6))), 70, (1.0, 0.62, 0.3), 0.15))
    LIGHTS.append((tuple(xf((0, yf - 1.2, 2.3))), 150, (1.0, 0.58, 0.26), 0.15))
    g = M('glow_hot')
    pt = xf((0.0, yf - 1.3, 2.35))
    g.cyl(pt + Vector((0, 0, -0.12)), pt + Vector((0, 0, 0.12)), 0.09, seg=8)
    return xf

# ---------------------------------------------------------------- water tank on a trestle
def water_tank(origin, rot):
    xf = mk_xf(origin, rot)
    t = M('timber'); ir = M('iron')
    P = 5.2
    for sx in (-1, 1):
        for sy in (-1, 1):
            t.beam(xf((sx * 1.7, sy * 1.7, -0.3)), xf((sx * 1.25, sy * 1.25, P)), 0.3, 0.3)
    for z0, z1 in ((0.4, 2.8), (2.8, P)):
        k0 = lerp(1.7, 1.25, z0 / P); k1 = lerp(1.7, 1.25, z1 / P)
        for (a, b) in (((-1, -1), (1, -1)), ((1, -1), (1, 1)), ((1, 1), (-1, 1)), ((-1, 1), (-1, -1))):
            t.beam(xf((a[0] * k0, a[1] * k0, z0)), xf((b[0] * k1, b[1] * k1, z1)), 0.14, 0.14)
            t.beam(xf((b[0] * k0, b[1] * k0, z0)), xf((a[0] * k1, a[1] * k1, z1)), 0.14, 0.14)
    for z in (0.4, 2.8, P):
        k = lerp(1.7, 1.25, z / P)
        for i in range(4):
            a = [(-1, -1), (1, -1), (1, 1), (-1, 1)]
            t.beam(xf((a[i][0] * k, a[i][1] * k, z)), xf((a[(i + 1) % 4][0] * k, a[(i + 1) % 4][1] * k, z)), 0.2, 0.2)
    # tank
    t.cyl(xf((0, 0, P + 0.1)), xf((0, 0, P + 2.7)), 1.55, seg=24)
    t.cyl(xf((0, 0, P + 2.7)), xf((0, 0, P + 3.9)), 1.7, 0.08, seg=24, caps=False)
    for z in (P + 0.35, P + 1.3, P + 2.25):
        ir.cyl(xf((0, 0, z)), xf((0, 0, z + 0.07)), 1.6, seg=24, caps=False)
    # spout pipe
    ir.beam(xf((1.0, 0.0, P + 0.2)), xf((1.0, 0.0, 0.2)), 0.13, 0.13)
    ir.beam(xf((1.0, 0.0, 0.3)), xf((1.7, 0.0, 0.2)), 0.13, 0.13)
    return xf

# ---------------------------------------------------------------- ore cars and rails
def track_z(y):
    return gh(float(track_x(y)), y)

def rails_and_ties(y0=CAMY + 1.5, y1=56.0):
    t = M('timber'); ir = M('iron')
    y = y0
    pts = []
    while y < y1:
        x = float(track_x(y)); z = track_z(y)
        dx = float(track_x(y + 0.05) - track_x(y - 0.05)) / 0.1
        rz = -math.atan(dx)
        if random.random() > 0.05:
            jit = random.uniform(-0.03, 0.03)
            t.box((x + random.uniform(-0.05, 0.05), y + jit, z + 0.03), (1.05, 0.14, 0.1), rz + random.uniform(-0.06, 0.06))
        pts.append((x, y, z, rz))
        y += 0.5 if y < CAMY + 18 else 0.8
    g = 0.30   # half the gauge
    for sgn in (-1, 1):
        prev = None
        y = y0
        while y < y1:
            x = float(track_x(y)); z = track_z(y)
            dx = float(track_x(y + 0.05) - track_x(y - 0.05)) / 0.1
            rz = -math.atan(dx)
            p = Vector((x + sgn * g * math.cos(rz), y + sgn * g * math.sin(rz), z + 0.14))
            if prev is not None:
                ir.beam(prev, p, 0.075, 0.1)
            prev = p
            y += 0.7
        # fishplate bolts: skip

def mine_car(y, loaded=True, yaw=0.0):
    xc = float(track_x(y)); z = track_z(y)
    dx = float(track_x(y + 0.05) - track_x(y - 0.05)) / 0.1
    rz = -math.atan(dx) + yaw
    xf = mk_xf((xc, y, z + 0.14), rz)
    ir = M('iron')
    # box: wider at the top, drawn as an open hopper
    bot = [(-0.42, -0.70, 0.30), (0.42, -0.70, 0.30), (0.42, 0.70, 0.30), (-0.42, 0.70, 0.30)]
    top = [(-0.62, -0.85, 1.02), (0.62, -0.85, 1.02), (0.62, 0.85, 1.02), (-0.62, 0.85, 1.02)]
    hexa(ir, [xf(p) for p in bot + top])
    # rim, bands, buffer beam, wheels
    for i in range(4):
        a = top[i]; b = top[(i + 1) % 4]
        ir.beam(xf((a[0], a[1], a[2] + 0.02)), xf((b[0], b[1], b[2] + 0.02)), 0.09, 0.09)
    for z0 in (0.55, 0.85):
        k = lerp(0.42, 0.62, (z0 - 0.3) / 0.72); kk = lerp(0.70, 0.85, (z0 - 0.3) / 0.72)
        c = [(-k, -kk), (k, -kk), (k, kk), (-k, kk)]
        for i in range(4):
            ir.beam(xf((c[i][0], c[i][1], z0)), xf((c[(i + 1) % 4][0], c[(i + 1) % 4][1], z0)), 0.07, 0.06)
    for sy in (-0.5, 0.5):
        ir.beam(xf((-0.45, sy, 0.22)), xf((0.45, sy, 0.22)), 0.1, 0.1)
        for sx in (-0.31, 0.31):
            ir.cyl(xf((sx - 0.03, sy, 0.0)), xf((sx + 0.03, sy, 0.0)), 0.17, seg=14)
    ir.beam(xf((0, -0.95, 0.25)), xf((0, -1.25, 0.25)), 0.07, 0.07)   # coupling bar
    ir.beam(xf((0, 0.95, 0.25)), xf((0, 1.25, 0.25)), 0.07, 0.07)
    if loaded:
        return [xf((random.uniform(-0.45, 0.45), random.uniform(-0.6, 0.6), 1.12)) for _ in range(9)]
    return []

def timber_stack(origin, rot, n=5, m=3):
    xf = mk_xf(origin, rot)
    t = M('timber')
    for k in range(m):
        for i in range(n):
            t.beam(xf((-1.1 + random.uniform(-0.1, 0.1), -0.4 + i * 0.22, 0.12 + k * 0.17)), xf((1.1 + random.uniform(-0.1, 0.1), -0.4 + i * 0.22, 0.12 + k * 0.17)), 0.2, 0.15) \
                if k % 2 == 0 else t.beam(xf((-0.4 + i * 0.22, -1.1, 0.12 + k * 0.17)), xf((-0.4 + i * 0.22, 1.1, 0.12 + k * 0.17)), 0.2, 0.15)

def barrel(origin, rz=0.0):
    ir = M('iron'); t = M('timber')
    x, y = origin
    z = gh(x, y)
    t.cyl((x, y, z - 0.02), (x, y, z + 0.9), 0.31, 0.28, seg=14)
    for zz in (0.12, 0.45, 0.8):
        ir.cyl((x, y, z + zz), (x, y, z + zz + 0.045), 0.325 - 0.04 * zz, seg=14, caps=False)

def crate(origin, rz=0.0, s=0.6):
    t = M('timber')
    x, y = origin
    z = gh(x, y)
    t.box((x, y, z + s / 2 - 0.03), (s, s * 1.2, s), rz)

# ----------------------------------------------------------------- rocks and tufts
ROCK_PROTOS = []
def make_rock_protos():
    for i in range(8):
        bm = bmesh.new()
        sub = 1 if i % 3 == 0 else 2
        bmesh.ops.create_icosphere(bm, subdivisions=sub, radius=1.0)
        sd = random.uniform(0, 100)
        sx, sy, sz = random.uniform(0.8, 1.2), random.uniform(0.8, 1.2), random.uniform(0.65, 1.0)
        for v in bm.verts:
            p = v.co
            n = mnoise.noise(p * 1.3 + Vector((sd, sd, sd)))
            n2 = mnoise.noise(p * 3.2 + Vector((sd + 5, sd, sd)))
            r = 1 + 0.28 * n + 0.12 * n2
            v.co = Vector((p.x * r * sx, p.y * r * sy, p.z * r * sz))
        me = bpy.data.meshes.new('rockproto%d' % i)
        bm.to_mesh(me)
        bm.free()
        ROCK_PROTOS.append(me)

def place_rocks(positions, sizes, mat='rock', zsink=0.25):
    for (x, y, zz), s in zip(positions, sizes):
        me = random.choice(ROCK_PROTOS)
        ob = bpy.data.objects.new('rock', me)
        scene.collection.objects.link(ob)
        ob.location = (x, y, zz - zsink * s)
        ob.rotation_euler = (random.uniform(-0.3, 0.3), random.uniform(-0.3, 0.3), random.uniform(0, 6.28))
        ob.scale = (s * random.uniform(0.8, 1.2), s * random.uniform(0.8, 1.2), s * random.uniform(0.7, 1.1))
        if mat != 'rock':
            ob.material_slots[0].link = 'OBJECT'
            ob.material_slots[0].material = MAT[mat]

def scatter_rocks():
    make_rock_protos()
    for me in ROCK_PROTOS:
        me.materials.append(MAT['rock'])
    # ballast along the track and the foreground wash
    n = 1000
    xs = []; ys = []; ss = []
    for i in range(n):
        y = CAMY + 1.8 + (random.random() ** 1.6) * 34
        side = random.choice([-1, 1])
        if random.random() < 0.55:
            x = float(track_x(y)) + side * random.uniform(0.38, 1.4)
            s = 0.045 * math.exp(random.gauss(0, 0.45))
        else:
            x = float(track_x(y)) + random.uniform(-7, 7) * (1 + y / 25)
            s = 0.13 * math.exp(random.gauss(0, 0.8))
        s *= (1 + (y - CAMY) / 30)
        xs.append(x); ys.append(y); ss.append(s)
    xs = np.array(xs); ys = np.array(ys)
    zs = ground_h(xs, ys)
    place_rocks(list(zip(xs, ys, zs)), ss)
    # a few big boulders to frame the bottom corners
    big = [(-2.3, CAMY + 4.6, 0.42), (2.0, CAMY + 4.0, 0.3), (-3.4, CAMY + 9.0, 0.5), (3.7, CAMY + 12.5, 0.55), (-4.8, CAMY + 16.0, 0.6), (5.4, CAMY + 22.0, 0.8)]
    place_rocks([(x, y, gh(x, y)) for x, y, s in big], [s for _, _, s in big])
    # rubble heap of the waste dump
    n = 260
    xs = np.random.uniform(7, 44, n); ys = np.random.uniform(66, 108, n)
    zs = ground_h(xs, ys)
    place_rocks(list(zip(xs, ys, zs)), list(0.5 * np.exp(np.random.normal(0, 0.5, n))), zsink=0.2)

def place_ore(points):
    pos = [(p.x, p.y, p.z) for p in points]
    place_rocks(pos, [random.uniform(0.11, 0.2) for _ in pos], mat='ore', zsink=0.0)

def grass_tufts():
    g = M('grass')
    spots = []
    for (cx, cy, ax, ay, dep), pk in zip(PUDDLES, range(len(PUDDLES))):
        for _ in range(3):
            th = random.uniform(0, 6.28)
            spots.append((cx + ax * 1.05 * math.cos(th), cy + ay * 1.05 * math.sin(th)))
    for _ in range(60):
        y = random.uniform(CAMY + 2, 48)
        spots.append((float(track_x(y)) + random.choice([-1, 1]) * random.uniform(0.6, 5), y))
    for (x, y) in spots:
        z = gh(x, y)
        nb = random.randint(10, 20)
        sc = 1.0 + 0.25 * y / 10
        for _ in range(nb):
            a = random.uniform(0, 6.28); r = random.uniform(0, 0.08)
            bx = x + r * math.cos(a); by = y + r * math.sin(a)
            L = random.uniform(0.28, 0.7) * min(sc, 2.2)
            lean = Vector((math.cos(a), math.sin(a), 0)) * L * random.uniform(0.25, 0.6)
            w = 0.022 * min(sc, 2.0)
            perp = Vector((-math.sin(a), math.cos(a), 0)) * w / 2
            b0 = Vector((bx, by, z)); m = b0 + Vector((0, 0, L * 0.55)) + lean * 0.35
            tp = b0 + Vector((0, 0, L * 0.9)) + lean
            g.quad(b0 - perp, b0 + perp, m + perp * 0.6, m - perp * 0.6)
            g.tri(m - perp * 0.6, m + perp * 0.6, tp)

def shrubs():
    # low desert scrub: dense sprays of thin dry stems, dusty sage in colour
    g = M('shrub')
    random.seed(11)
    spots = []
    for _ in range(46):
        y = CAMY + 7 + (random.random() ** 1.3) * 34
        x = float(track_x(y)) + random.choice([-1, 1]) * random.uniform(1.4, 4.0 + (y - CAMY) * 0.45)
        spots.append((x, y))
    for (x, y) in spots:
        z = gh(x, y)
        R = random.uniform(0.28, 0.5)
        nb = random.randint(34, 52)
        for _ in range(nb):
            a = random.uniform(0, 6.28)
            lean = Vector((math.cos(a), math.sin(a), 0)) * R * random.uniform(0.4, 1.0)
            L = random.uniform(0.45, 0.9)
            b0 = Vector((x + random.uniform(-0.04, 0.04), y + random.uniform(-0.04, 0.04), z - 0.03))
            m = b0 + Vector((0, 0, L * 0.6)) + lean * 0.4
            tp = b0 + Vector((0, 0, L * 0.95)) + lean
            perp = Vector((-math.sin(a), math.cos(a), 0)) * 0.012
            g.quad(b0 - perp, b0 + perp, m + perp * 0.7, m - perp * 0.7)
            g.tri(m - perp * 0.7, m + perp * 0.7, tp)
            # a few leaf tufts along the stem
            for tt in (0.55, 0.8):
                q = b0.lerp(tp, tt) + Vector((0, 0, 0.0))
                d = Vector((math.cos(a + 1.2), math.sin(a + 1.2), 0.3)).normalized() * 0.09
                pp = Vector((-d.y, d.x, 0)) * 0.3
                g.tri(q - pp * 0.2, q + pp * 0.2, q + d + Vector((0, 0, 0.04)))

def tube(mk, path, radii, seg=14, ribs=6, rib_amp=0.09):
    rings = []
    for i, p in enumerate(path):
        p = Vector(p)
        a = Vector(path[min(i + 1, len(path) - 1)]) - Vector(path[max(i - 1, 0)])
        a.normalize()
        v = Vector((0, 1, 0))
        u = a.cross(v).normalized()
        ring = []
        for k in range(seg):
            th = 2 * math.pi * k / seg
            rr = radii[i] * (1 + rib_amp * math.cos(ribs * th))
            ring.append(p + (u * math.cos(th) + v * math.sin(th)) * rr)
        rings.append(ring)
    for i in range(len(rings) - 1):
        for k in range(seg):
            k2 = (k + 1) % seg
            mk.quad(rings[i][k], rings[i][k2], rings[i + 1][k2], rings[i + 1][k])
    top = Vector(path[-1])
    for k in range(seg):
        mk.tri(rings[-1][k], rings[-1][(k + 1) % seg], top + (Vector(path[-1]) - Vector(path[-2])).normalized() * radii[-1] * 0.2)

def saguaro(origin, rot, H=4.6, arms=((1, 2.0, 0.95, 1.5), (-1, 2.9, 0.75, 1.0))):
    xf = mk_xf(origin, rot)
    mk = M('cactus')
    r0 = 0.23
    path = []; rad = []
    n = 14
    for i in range(n + 1):
        z = -0.2 + (H + 0.2) * i / n
        path.append(xf((0.03 * math.sin(i * 0.7), 0, z)))
        t = i / n
        rad.append(r0 * (1 - 0.12 * t) * (1.0 if t < 0.88 else math.sqrt(max(0.0, 1 - ((t - 0.88) / 0.12) ** 2)) * 0.98 + 0.02))
    tube(mk, path, rad)
    for side, z0, out, rise in arms:
        pa = []; ra = []
        for i in range(6):
            t = i / 5
            pa.append(xf((side * out * math.sin(t * math.pi / 2) * 1.0, 0, z0 + 0.25 * t)))
            ra.append(0.14)
        for i in range(1, 9):
            t = i / 8
            pa.append(xf((side * out, 0, z0 + 0.25 + rise * t)))
            ra.append(0.14 * (1.0 if t < 0.85 else math.sqrt(max(0.0, 1 - ((t - 0.85) / 0.15) ** 2)) * 0.98 + 0.02))
        tube(mk, pa, ra, seg=12)

STACK_TOP = Vector((0, 0, 0))

def smoke_plume(start, drift, rise, width0, width1, seed, alpha_gain=1.0):
    # a thin, streaky ribbon that always faces the camera; its edges and body are broken up by a stretched noise
    cam = Vector((-0.3, CAMY, 1.65))
    n = 60
    pts = []
    for i in range(n + 1):
        s_ = i / n
        p = Vector(start) + Vector((drift * s_ ** 1.35 + 0.9 * math.sin(s_ * 6.5 + seed) * s_, 2.5 * s_, rise * s_ ** 0.8))
        pts.append(p)
    verts = []; uvs = []; faces = []
    for i, p in enumerate(pts):
        s_ = i / n
        t = (pts[min(i + 1, n)] - pts[max(i - 1, 0)]).normalized()
        view = (p - cam).normalized()
        wv = t.cross(view).normalized()
        wd = lerp(width0, width1, s_ ** 0.9) * 0.5
        verts.append(p - wv * wd); verts.append(p + wv * wd)
        uvs.append((0.0, s_)); uvs.append((1.0, s_))
    for i in range(n):
        a = 2 * i
        faces.append((a, a + 1, a + 3, a + 2))
    me = bpy.data.meshes.new('smoke')
    me.from_pydata(verts, [], faces)
    me.update()
    uvl = me.uv_layers.new(name='UVMap')
    arr = []
    for f in me.polygons:
        for li in f.loop_indices:
            arr.append(uvs[me.loops[li].vertex_index])
    uvl.data.foreach_set('uv', np.array(arr, dtype=np.float32).ravel())
    ob = bpy.data.objects.new('smoke', me)
    scene.collection.objects.link(ob)
    mb = MB('smoke')
    uv = mb.node('ShaderNodeUVMap'); uv.uv_map = 'UVMap'
    ux, uy, uz = mb.sep(uv.outputs['UV'])
    vv = mb.node('ShaderNodeCombineXYZ')
    mb.put(vv.inputs['X'], mb.math('MULTIPLY', ux, 2.4)); mb.put(vv.inputs['Y'], mb.math('MULTIPLY', uy, 9.0)); vv.inputs['Z'].default_value = seed
    nz = mb.noise(1.0, 6, 0.62, vec=vv.outputs['Vector'], dist=0.7)
    across = mb.math('SUBTRACT', 1.0, mb.math('POWER', mb.math('ABSOLUTE', mb.math('SUBTRACT', mb.math('MULTIPLY', ux, 2.0), 1.0)), 2.2))
    along_in = mb.math('MINIMUM', mb.math('MULTIPLY', uy, 18.0), 1.0)
    along_out = mb.math('MINIMUM', mb.math('MAXIMUM', mb.math('MULTIPLY', mb.math('SUBTRACT', 1.0, uy), 1.9), 0.0), 1.0)
    shape = mb.math('MULTIPLY', mb.math('MULTIPLY', across, along_in), along_out)
    body = mb.ramp(nz, [(0.30, '#000000'), (0.62, '#ffffff')])
    bx, by, bz = mb.sep(body)
    alpha = mb.math('MULTIPLY', mb.math('MULTIPLY', bx, shape), 0.9 * alpha_gain, clamp=True)
    col = mb.mix(mb.ramp(nz, [(0.2, '#ffffff'), (0.8, '#000000')]), lin('#8c9aa0', 0.5), lin('#1a1d20', 1.0))
    sh = mb.principled(col, rough=1.0, spec=0.0)
    tr = mb.node('ShaderNodeBsdfTransparent')
    ms = mb.node('ShaderNodeMixShader')
    mb.put(ms.inputs['Fac'], alpha)
    mb.l.new(tr.outputs['BSDF'], ms.inputs[1]); mb.l.new(sh, ms.inputs[2])
    mb.finish(ms.outputs['Shader'], haze=False)
    ob.data.materials.append(mb.m)
    ob.visible_shadow = False

def lantern_post(x, y, h=1.25):
    z = gh(x, y)
    t = M('timber'); ir = M('iron'); g = M('glow_hot')
    t.beam((x, y, z - 0.1), (x, y, z + h), 0.12, 0.12)
    t.beam((x, y, z + h - 0.05), (x + 0.28, y, z + h - 0.05), 0.07, 0.07)
    lp = Vector((x + 0.28, y, z + h - 0.2))
    ir.cyl(lp + Vector((0, 0, -0.1)), lp + Vector((0, 0, -0.07)), 0.07, seg=8)
    ir.cyl(lp + Vector((0, 0, 0.09)), lp + Vector((0, 0, 0.13)), 0.08, 0.02, seg=8)
    M('glow').cyl(lp + Vector((0, 0, -0.07)), lp + Vector((0, 0, 0.09)), 0.052, seg=8)
    LIGHTS.append((tuple(lp), 45, (1.0, 0.55, 0.22), 0.06))

def build_structures():
    rails_and_ties()
    car1 = mine_car(CAMY + 17.0, True)
    car2 = mine_car(CAMY + 19.8, True, yaw=0.01)
    car3 = mine_car(41.0, False)
    scatter_rocks()
    place_ore(car1 + car2)
    grass_tufts()
    shrubs()
    gz = gh(3.6, 56.0)
    headframe((3.6, 56.0, gz), math.radians(25.6))
    hoist_house((-9.2, 49.0, gh(-9.2, 49.0)), math.radians(25.6))
    bunkhouse((12.5, 60.0, gh(12.5, 60.0)), math.radians(-10))
    water_tank((10.5, 47.0, gh(10.5, 47.0)), math.radians(15))
    timber_stack((-2.6, CAMY + 11.5, gh(-2.6, CAMY + 11.5)), math.radians(20))
    timber_stack((4.4, CAMY + 13.0, gh(4.4, CAMY + 13.0)), math.radians(-30), n=4, m=2)
    lantern_post(-1.25, CAMY + 5.4)
    saguaro((3.6, CAMY + 15.5, gh(3.6, CAMY + 15.5)), 0.4)
    smoke_plume(STACK_TOP + Vector((0, 0, 0.3)), 17.0, 9.0, 0.9, 4.6, 1.3)
    smoke_plume(STACK_TOP + Vector((0.2, -0.2, 0.2)), 14.0, 7.0, 0.6, 3.2, 7.1, 0.7)
    crate((-1.8, CAMY + 8.6), 0.4, 0.5)

def add_lights():
    for loc, power, col, rad in LIGHTS:
        add_point(loc, power, col, rad)

# ---------------------------------------------------------------- finishing (all in numpy, from the float picture)
def read_exr(path):
    img = bpy.data.images.load(path)
    w, h = img.size
    buf = np.empty(w * h * 4, dtype=np.float32)
    img.pixels.foreach_get(buf)
    bpy.data.images.remove(img)
    return buf.reshape(h, w, 4)[::-1, :, :3].copy()

def finish_image(src, dst, expo=None):
    from PIL import Image
    from scipy import ndimage
    lin_im = read_exr(src)
    h, w, _ = lin_im.shape
    s = h / 960.0
    E = float(os.environ.get('GRADE_EXPO', '1.0')) if expo is None else expo
    x = np.maximum(lin_im, 0) * E
    lum = lambda a: a[..., 0] * 0.2126 + a[..., 1] * 0.7152 + a[..., 2] * 0.0722
    # dusty air lit by the low sun: a warm veil that lies along the horizon, stronger toward the sun side
    yy0, xx0 = np.mgrid[0:h, 0:w]
    hor = 0.575 * h
    veil = np.exp(-((yy0 - hor) / (0.075 * h)) ** 2) * (1.0 - 0.55 * xx0 / w)
    x = x + (veil * float(os.environ.get('VEIL', '0.17')))[..., None] * np.array([0.34, 0.16, 0.05])
    # glow around the bright warm things (in linear light, so it behaves like light)
    L = lum(x)
    hi = np.clip(L - 0.9, 0, 8)[..., None] * x / np.maximum(L, 1e-4)[..., None]
    bl1 = np.stack([ndimage.gaussian_filter(hi[..., c], 7 * s) for c in range(3)], axis=-1)
    bl2 = np.stack([ndimage.gaussian_filter(hi[..., c], 26 * s) for c in range(3)], axis=-1)
    x = x + 0.35 * bl1 + 0.55 * bl2 * np.array([1.0, 0.72, 0.42])
    # filmic curve per channel (keeps the orange orange), then to screen
    a, b, c, d, e = 2.51, 0.03, 2.43, 0.59, 0.14
    y = np.clip((x * (a * x + b)) / (x * (c * x + d) + e), 0, 1)
    y = np.where(y <= 0.0031308, y * 12.92, 1.055 * np.power(np.maximum(y, 1e-6), 1 / 2.4) - 0.055)
    # grade: blue-black shadows, a little warmth in the lights
    L2 = lum(y)[..., None]
    sh = np.clip(1 - L2 * 2.6, 0, 1) ** 2
    teal = np.array([0.03, 0.09, 0.13])
    wt = ((1 - np.clip(L2 / 0.5, 0, 1)) ** 1.5) * 0.55
    y = y * (1 - wt) + (L2 * 0.9 + 0.02) * (teal / teal.mean() * 0.9) * wt + sh * np.array([-0.004, 0.012, 0.026])
    y = y * (1 + 0.06 * np.clip(L2 - 0.5, 0, 1) * np.array([1.0, 0.2, -0.6]))
    # blacks are never pure: a blue-black floor
    floor = np.array([0.012, 0.030, 0.044])
    y = floor + y * (1 - floor)
    # painterly: a gentle median blended back
    k = 3 if s < 1.5 else 5
    med = np.stack([ndimage.median_filter(y[..., ch], size=k) for ch in range(3)], axis=-1)
    y = y * 0.5 + med * 0.5
    # vignette
    yy, xx = np.mgrid[0:h, 0:w]
    r = np.sqrt(((xx - w / 2) / (w / 2)) ** 2 + ((yy - h * 0.5) / (h / 2)) ** 2)
    y = y * (1 - 0.32 * np.clip(r - 0.4, 0, 1.2) ** 1.5)[..., None]
    # fine grain
    rng = np.random.default_rng(3)
    g = ndimage.gaussian_filter(rng.normal(0, 1, (h, w)), 0.7 * s)
    y = y + (g * 0.011)[..., None]
    y = np.clip(y, 0, 1)
    Image.fromarray((y * 255 + 0.5).astype(np.uint8)).save(dst)

# ================================================================== main build
build_materials()
build_terrain()
add_puddle_water()
if 'build_structures' in globals():
    build_structures()
for key, mk in MESH.items():
    if mk.f:
        mk.build(key, MESH_MAT.get(key, key), smooth=key in SMOOTH_KEYS)
setup_camera()
setup_world()
add_sun()
if os.environ.get('DUSTON') == '1':
    add_dust()
if 'add_lights' in globals():
    add_lights()
print('built in', round(time.time() - T0, 1), 's')

OUT = os.path.abspath(OUT)
raw = os.path.splitext(OUT)[0] + '_raw.exr'
scene.render.image_settings.file_format = 'OPEN_EXR'
scene.render.image_settings.color_depth = '32'
scene.render.filepath = raw
t1 = time.time()
bpy.ops.render.render(write_still=True)
print('rendered in', round(time.time() - t1, 1), 's')
finish_image(raw, OUT)
if os.environ.get('KEEPRAW') != '1':
    try:
        os.remove(raw)
    except Exception:
        pass
print('done', OUT, 'total', round(time.time() - T0, 1), 's')
