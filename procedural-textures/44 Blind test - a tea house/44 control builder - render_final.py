#!/usr/bin/env python3
"""A tea house, Britain 1915 -- one place for the narrated explainer film.

Run:  python3 render_final.py WIDTH HEIGHT SAMPLES OUT.png
Everything is made here by code (shapes, wood, brass, glass, haze, steam, light)
and then finished (paint-like softening, glow, colour grade, vignette, grain).
No picture files are read. Writes OUT.png (and nothing else except OUT.raw.png).
"""
import sys, os, math, random, time, warnings
warnings.simplefilter("ignore")
import bpy, bmesh
import numpy as np
from mathutils import Vector, Matrix, Euler

W = int(sys.argv[1]) if len(sys.argv) > 1 else 540
H = int(sys.argv[2]) if len(sys.argv) > 2 else 960
SAMPLES = int(sys.argv[3]) if len(sys.argv) > 3 else 64
OUT = sys.argv[4] if len(sys.argv) > 4 else "out.png"
FINISH_ONLY = os.environ.get("TEA_FINISH_ONLY", "")
CROP = os.environ.get("TEA_CROP", "")
raw_path = FINISH_ONLY or (os.path.splitext(OUT)[0] + ".raw.png")
FAST = os.environ.get("TEA_FAST", "") == "1"      # test builds only: skip the steam (slow to set up)
NOHAZE = os.environ.get("TEA_NOHAZE", "") == "1"
T0 = time.time()
random.seed(1915)

# ------------------------------------------------------------------ knobs
SUN_STRENGTH = 15.0
SUN_DIR = Vector((0.30, -1.0, -0.52))      # travels toward camera, a little right, down
FILL_STRENGTH = 260.0
HAZE_DENSITY = 0.015
PANE_BOTTOM = 3.3
PANE_TOP = 2.4
EXPOSURE = 0.0

# ------------------------------------------------------------------ colours
def s2l(v):
    return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4

def hx(h, a=1.0):
    h = h.lstrip('#')
    r, g, b = [int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4)]
    return (s2l(r), s2l(g), s2l(b), a)

# ------------------------------------------------------------------ scene reset
if not FINISH_ONLY:
    bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.engine = 'CYCLES'

if not FINISH_ONLY:
    # ------------------------------------------------------------------ node helpers
    def newmat(name):
        m = bpy.data.materials.new(name)
        m.use_nodes = True
        m.node_tree.nodes.clear()
        return m, m.node_tree

    def nd(nt, idname, p=None, i=None):
        n = nt.nodes.new(idname)
        for k, v in (p or {}).items():
            setattr(n, k, v)
        for k, v in (i or {}).items():
            n.inputs[k].default_value = v
        return n

    def setin(nt, sock, v):
        if v is None:
            return
        if isinstance(v, bpy.types.NodeSocket):
            nt.links.new(v, sock)
        else:
            sock.default_value = v

    def mixc(nt, fac, a, b, blend='MIX'):
        n = nt.nodes.new('ShaderNodeMix')
        n.data_type = 'RGBA'
        n.blend_type = blend
        setin(nt, n.inputs[0], fac)
        setin(nt, n.inputs[6], a)
        setin(nt, n.inputs[7], b)
        return n.outputs[2]

    def mixf(nt, fac, a, b):
        n = nt.nodes.new('ShaderNodeMix')
        n.data_type = 'FLOAT'
        setin(nt, n.inputs[0], fac)
        setin(nt, n.inputs[2], a)
        setin(nt, n.inputs[3], b)
        return n.outputs[0]

    def mth(nt, op, a, b=None, clamp=False):
        n = nt.nodes.new('ShaderNodeMath')
        n.operation = op
        n.use_clamp = clamp
        setin(nt, n.inputs[0], a)
        if b is not None:
            setin(nt, n.inputs[1], b)
        return n.outputs[0]

    def ramp(nt, fac, stops, dom=None):
        if dom is not None:
            lo, hi = dom
            mr = nt.nodes.new('ShaderNodeMapRange')
            mr.clamp = True
            mr.inputs['From Min'].default_value = lo
            mr.inputs['From Max'].default_value = hi
            mr.inputs['To Min'].default_value = 0.0
            mr.inputs['To Max'].default_value = 1.0
            setin(nt, mr.inputs['Value'], fac)
            fac = mr.outputs['Result']
            stops = [((p - lo) / (hi - lo), c) for p, c in stops]
        n = nt.nodes.new('ShaderNodeValToRGB')
        el = n.color_ramp.elements
        while len(el) > 2:
            el.remove(el[-1])
        el[0].position, el[0].color = stops[0][0], stops[0][1]
        el[1].position, el[1].color = stops[1][0], stops[1][1]
        for pos, col in stops[2:]:
            e = el.new(pos)
            e.color = col
        setin(nt, n.inputs[0], fac)
        return n.outputs[0]

    def fval(c):
        return (c, c, c, 1.0)

    def geo_pos(nt):
        return nt.nodes.new('ShaderNodeNewGeometry').outputs['Position']

    def mapping(nt, vec, scale=(1, 1, 1), loc=(0, 0, 0), rot=(0, 0, 0)):
        n = nt.nodes.new('ShaderNodeMapping')
        n.inputs['Scale'].default_value = scale
        n.inputs['Location'].default_value = loc
        n.inputs['Rotation'].default_value = rot
        setin(nt, n.inputs['Vector'], vec)
        return n.outputs['Vector']

    def noise(nt, vec, scale=5.0, detail=4.0, rough=0.55, distort=0.0):
        n = nt.nodes.new('ShaderNodeTexNoise')
        n.noise_dimensions = '3D'
        n.inputs['Scale'].default_value = scale
        n.inputs['Detail'].default_value = detail
        n.inputs['Roughness'].default_value = rough
        n.inputs['Distortion'].default_value = distort
        setin(nt, n.inputs['Vector'], vec)
        return n.outputs['Fac']

    def voro_edge(nt, vec, scale=5.0, rnd=1.0):
        n = nt.nodes.new('ShaderNodeTexVoronoi')
        n.voronoi_dimensions = '3D'
        n.feature = 'DISTANCE_TO_EDGE'
        n.inputs['Scale'].default_value = scale
        n.inputs['Randomness'].default_value = rnd
        setin(nt, n.inputs['Vector'], vec)
        return n.outputs['Distance']

    def voro_f1(nt, vec, scale=5.0, rnd=1.0):
        n = nt.nodes.new('ShaderNodeTexVoronoi')
        n.voronoi_dimensions = '3D'
        n.feature = 'F1'
        n.inputs['Scale'].default_value = scale
        n.inputs['Randomness'].default_value = rnd
        setin(nt, n.inputs['Vector'], vec)
        return n.outputs['Distance']

    def bump(nt, height, strength=0.2, dist=0.01, normal=None):
        n = nt.nodes.new('ShaderNodeBump')
        n.inputs['Strength'].default_value = strength
        n.inputs['Distance'].default_value = dist
        setin(nt, n.inputs['Height'], height)
        setin(nt, n.inputs['Normal'], normal)
        return n.outputs['Normal']

    def bevel(nt, radius=0.004):
        n = nt.nodes.new('ShaderNodeBevel')
        n.samples = 4
        n.inputs['Radius'].default_value = radius
        return n.outputs['Normal']

    def finish(nt, bsdf, vol=None, disp=None):
        out = nt.nodes.new('ShaderNodeOutputMaterial')
        nt.links.new(bsdf, out.inputs['Surface'])
        if vol is not None:
            nt.links.new(vol, out.inputs['Volume'])

    def principled(nt, base=None, metal=0.0, rough=0.5, normal=None, spec=0.5, coat=0.0,
                   coat_rough=0.1, emit=None, emit_strength=0.0, alpha=None, sheen=0.0):
        p = nt.nodes.new('ShaderNodeBsdfPrincipled')
        setin(nt, p.inputs['Base Color'], base)
        setin(nt, p.inputs['Metallic'], metal)
        setin(nt, p.inputs['Roughness'], rough)
        setin(nt, p.inputs['Specular IOR Level'], spec)
        setin(nt, p.inputs['Coat Weight'], coat)
        setin(nt, p.inputs['Coat Roughness'], coat_rough)
        setin(nt, p.inputs['Sheen Weight'], sheen)
        if normal is not None:
            nt.links.new(normal, p.inputs['Normal'])
        if emit is not None:
            setin(nt, p.inputs['Emission Color'], emit)
            setin(nt, p.inputs['Emission Strength'], emit_strength)
        if alpha is not None:
            setin(nt, p.inputs['Alpha'], alpha)
        return p.outputs['BSDF']

    # ------------------------------------------------------------------ materials
    def mat_wood(name, c1, c2, axis='Y', gscale=34.0, rough=0.5, bumpk=0.25, polish=0.0, lowfreq=1.2):
        m, nt = newmat(name)
        pos = geo_pos(nt)
        sx = {'X': (2.0, gscale, gscale), 'Y': (gscale, 2.0, gscale), 'Z': (gscale, gscale, 2.0)}[axis]
        mp = mapping(nt, pos, scale=sx)
        g = noise(nt, mp, scale=1.0, detail=5.0, rough=0.6, distort=0.25)
        low = noise(nt, pos, scale=lowfreq, detail=3.0, rough=0.5)
        col = ramp(nt, g, [(0.30, c1), (0.70, c2)])
        col = mixc(nt, 0.35, col, ramp(nt, low, [(0.2, hx('#0b0603')), (0.8, c2)]), 'MULTIPLY')
        nrm = bump(nt, g, strength=bumpk, dist=0.004, normal=bevel(nt, 0.004))
        r = mixf(nt, g, rough * 1.25, rough * 0.7)
        b = principled(nt, col, 0.0, r, nrm, 0.5, coat=polish, coat_rough=0.12)
        finish(nt, b)
        return m

    def mat_floor():
        m, nt = newmat("floor_boards")
        pos = geo_pos(nt)
        attr = nt.nodes.new('ShaderNodeAttribute')
        attr.attribute_name = 'rnd'
        attr.attribute_type = 'GEOMETRY'
        rnd = attr.outputs['Fac']
        mp = mapping(nt, pos, scale=(30.0, 2.0, 30.0))
        g = noise(nt, mp, scale=1.0, detail=5.0, rough=0.65, distort=0.3)
        base = ramp(nt, rnd, [(0.0, hx('#150b06')), (0.5, hx('#26150a')), (1.0, hx('#3c2410'))])
        col = mixc(nt, 0.45, base, ramp(nt, g, [(0.25, hx('#0d0704')), (0.75, hx('#5a3a1e'))]), 'MULTIPLY')
        # scuffed, pale wear down the middle of the room; dirt and wet near the walls
        sx = nt.nodes.new('ShaderNodeSeparateXYZ')
        nt.links.new(pos, sx.inputs[0])
        ax = mth(nt, 'ABSOLUTE', sx.outputs['X'])
        wearn = noise(nt, pos, scale=3.0, detail=6.0, rough=0.6)
        aisle = ramp(nt, ax, [(0.8, fval(1.0)), (1.9, fval(0.0))], dom=(0.8, 1.9))
        wearmask = mth(nt, 'MULTIPLY', aisle, ramp(nt, wearn, [(0.35, fval(0.0)), (0.7, fval(1.0))]), True)
        col = mixc(nt, mth(nt, 'MULTIPLY', wearmask, 0.35), col, hx('#6b4a2a'))
        scr_n = noise(nt, mapping(nt, pos, scale=(70.0, 1.2, 70.0)), scale=1.0, detail=2.0, rough=0.5)
        scr = ramp(nt, scr_n, [(0.60, fval(0.0)), (0.70, fval(1.0))])
        col = mixc(nt, mth(nt, 'MULTIPLY', scr, 0.40), col, hx('#8a6a44'))
        dirt = noise(nt, pos, scale=7.0, detail=7.0, rough=0.7)
        col = mixc(nt, ramp(nt, dirt, [(0.55, fval(0.0)), (0.85, fval(0.55))]), col, hx('#0a0705'), 'MIX')
        rough = mixf(nt, mth(nt, 'MULTIPLY', aisle, 0.8), 0.62, 0.38)
        # rain walked in: wet, mirror-like patches with ragged edges, thickest near the door
        wn = noise(nt, mapping(nt, pos, scale=(1.0, 0.8, 1.0)), scale=0.85, detail=6.0, rough=0.62, distort=0.5)
        ysep = sx.outputs['Y']
        door = ramp(nt, ysep, [(2.0, fval(0.0)), (4.2, fval(0.12)), (6.5, fval(0.0))], dom=(2.0, 6.5))
        wet = ramp(nt, mth(nt, 'ADD', wn, door), [(0.60, fval(0.0)), (0.635, fval(1.0))])
        wet = mth(nt, 'MULTIPLY', wet, ramp(nt, ysep, [(1.8, fval(0.0)), (2.8, fval(1.0))], dom=(1.8, 2.8)))
        col = mixc(nt, mth(nt, 'MULTIPLY', wet, 0.7), col, hx('#0a1218'))
        rough = mixf(nt, wet, rough, 0.045)
        nrm = bump(nt, mixf(nt, wet, g, mth(nt, 'MULTIPLY', g, 0.1)), strength=0.25, dist=0.004, normal=bevel(nt, 0.003))
        b = principled(nt, col, 0.0, rough, nrm, 0.6, coat=mixf(nt, aisle, 0.0, 0.2), coat_rough=0.12)
        finish(nt, b)
        return m

    def mat_plaster(name='plaster'):
        m, nt = newmat(name)
        pos = geo_pos(nt)
        sx = nt.nodes.new('ShaderNodeSeparateXYZ')
        nt.links.new(pos, sx.inputs[0])
        z = sx.outputs['Z']
        big = noise(nt, pos, scale=1.3, detail=6.0, rough=0.62, distort=0.5)
        mid = noise(nt, pos, scale=5.0, detail=7.0, rough=0.65)
        fine = noise(nt, pos, scale=40.0, detail=3.0, rough=0.5)
        peel = ramp(nt, big, [(0.57, fval(0.0)), (0.65, fval(1.0))])
        deep = ramp(nt, mid, [(0.61, fval(0.0)), (0.71, fval(1.0))])
        cracks = ramp(nt, voro_edge(nt, mapping(nt, pos, scale=(0.8, 0.8, 0.8)), 3.0), [(0.0, fval(1.0)), (0.05, fval(0.0))])
        paint = mixc(nt, mid, hx('#16272d'), hx('#223941'))
        under = mixc(nt, mid, hx('#4d463a'), hx('#62574a'))
        brick = mixc(nt, fine, hx('#36170e'), hx('#4f2415'))
        col = mixc(nt, peel, paint, under)
        col = mixc(nt, mth(nt, 'MULTIPLY', deep, peel, True), col, brick)
        col = mixc(nt, cracks, col, hx('#0c0b0a'))
        # soot toward the ceiling, mud toward the floor
        sootm = ramp(nt, z, [(2.4, fval(0.0)), (4.4, fval(0.75))], dom=(2.4, 4.4))
        mudm = ramp(nt, z, [(0.0, fval(0.6)), (1.0, fval(0.0))])
        col = mixc(nt, sootm, col, hx('#050607'))
        col = mixc(nt, mth(nt, 'MULTIPLY', mudm, ramp(nt, mid, [(0.3, fval(0.3)), (0.7, fval(1.0))])), col, hx('#0e0a07'))
        h = mixf(nt, peel, fine, mth(nt, 'MULTIPLY', fine, 0.4))
        nrm = bump(nt, mixf(nt, peel, mid, mth(nt, 'MULTIPLY', big, 0.5)), strength=0.5, dist=0.02)
        b = principled(nt, col, 0.0, 0.88, nrm, 0.25)
        finish(nt, b)
        return m

    def mat_iron(name='iron', paint_hex='#1d3b3b', zrust=True, chip=(0.50, 0.58)):
        m, nt = newmat(name)
        pos = geo_pos(nt)
        sx = nt.nodes.new('ShaderNodeSeparateXYZ')
        nt.links.new(pos, sx.inputs[0])
        z = sx.outputs['Z']
        big = noise(nt, pos, scale=2.2, detail=6.0, rough=0.62, distort=0.4)
        mid = noise(nt, pos, scale=9.0, detail=6.0, rough=0.6)
        fine = noise(nt, pos, scale=60.0, detail=2.0, rough=0.5)
        low = ramp(nt, z, [(0.0, fval(0.5)), (1.6, fval(0.0))], dom=(0.0, 1.6))
        chip = ramp(nt, mth(nt, 'ADD', big, mth(nt, 'MULTIPLY', low, 0.5)), [(chip[0], fval(0.0)), (chip[1], fval(1.0))])
        paint = mixc(nt, mid, hx(paint_hex), hx('#2b524c'))
        rust = mixc(nt, mid, hx('#4a1d0e'), hx('#7d3a18'))
        rust = mixc(nt, fine, rust, hx('#2a0f07'))
        col = mixc(nt, chip, paint, rust)
        rough = mixf(nt, chip, 0.55, 0.88)
        nrm = bump(nt, mth(nt, 'ADD', fine, mid), strength=0.3, dist=0.004, normal=bevel(nt, 0.006))
        b = principled(nt, col, mixf(nt, chip, 0.35, 0.05), rough, nrm, 0.5)
        finish(nt, b)
        return m

    def mat_brass(name='brass', tarnish=0.35, rough=0.28):
        m, nt = newmat(name)
        pos = geo_pos(nt)
        n1 = noise(nt, pos, scale=25.0, detail=6.0, rough=0.6)
        n2 = noise(nt, pos, scale=3.0, detail=4.0, rough=0.5)
        t = ramp(nt, mth(nt, 'ADD', n1, n2), [(0.8, fval(0.0)), (1.25, fval(min(1.0, tarnish * 1.6)))], dom=(0.6, 1.4))
        base = mixc(nt, t, hx('#c28a34'), hx('#3d2a12'))
        r = mixf(nt, t, rough, 0.55)
        nrm = bump(nt, n1, strength=0.06, dist=0.002, normal=bevel(nt, 0.003))
        b = principled(nt, base, 0.78, r, nrm, 0.5)
        finish(nt, b)
        return m

    def mat_marble():
        m, nt = newmat("marble")
        pos = geo_pos(nt)
        n = noise(nt, pos, scale=4.0, detail=5.0, rough=0.55, distort=1.5)
        vein = mth(nt, 'ABSOLUTE', mth(nt, 'SUBTRACT', n, 0.5))
        v = ramp(nt, vein, [(0.0, fval(1.0)), (0.035, fval(0.0))])
        stain = noise(nt, pos, scale=11.0, detail=6.0, rough=0.6)
        col = mixc(nt, ramp(nt, stain, [(0.4, fval(0.0)), (0.75, fval(1.0))]), hx('#6e7872'), hx('#3a3a33'))
        col = mixc(nt, v, col, hx('#1a2226'))
        b = principled(nt, col, 0.0, 0.16, bump(nt, stain, 0.04, 0.002), 0.6, coat=0.25, coat_rough=0.05)
        finish(nt, b)
        return m

    def mat_ceramic(name, hexc, rough=0.1):
        m, nt = newmat(name)
        pos = geo_pos(nt)
        n = noise(nt, pos, scale=30.0, detail=4.0)
        col = mixc(nt, ramp(nt, n, [(0.4, fval(0.0)), (0.7, fval(0.5))]), hx(hexc), hx('#2a2118'))
        b = principled(nt, col, 0.0, rough, None, 0.6, coat=0.4, coat_rough=0.03)
        finish(nt, b)
        return m

    def mat_emit(name, hexc, strength):
        m, nt = newmat(name)
        e = nd(nt, 'ShaderNodeEmission', i={'Color': hx(hexc), 'Strength': strength})
        finish(nt, e.outputs['Emission'])
        return m

    def mat_window_glass():
        """Steamed glass: the last amber of the sun low down, deep teal dusk above, panes clouded unevenly."""
        m, nt = newmat("steamed_glass")
        pos = geo_pos(nt)
        sx = nt.nodes.new('ShaderNodeSeparateXYZ')
        nt.links.new(pos, sx.inputs[0])
        z = sx.outputs['Z']
        gradc = ramp(nt, z, [(1.0, hx('#f4a64c')), (1.35, hx('#cf8a4c')), (1.8, hx('#5f8f98')), (2.6, hx('#2a6580')), (4.0, hx('#143a52'))], dom=(1.0, 4.0))
        gs = ramp(nt, z, [(1.0, fval(1.0)), (1.4, fval(0.40)), (2.0, fval(0.22)), (4.0, fval(0.12))], dom=(1.0, 4.0))
        # each pane gets its own cloudiness
        q = nt.nodes.new('ShaderNodeVectorMath')
        q.operation = 'MULTIPLY'
        q.inputs[1].default_value = (1.0 / 0.70, 1.0, 1.0 / 0.50)
        nt.links.new(pos, q.inputs[0])
        fl = nt.nodes.new('ShaderNodeVectorMath')
        fl.operation = 'FLOOR'
        nt.links.new(q.outputs[0], fl.inputs[0])
        wn = nt.nodes.new('ShaderNodeTexWhiteNoise')
        wn.noise_dimensions = '3D'
        nt.links.new(fl.outputs[0], wn.inputs['Vector'])
        pane = mixf(nt, wn.outputs['Value'], 0.3, 1.0)
        drip = noise(nt, mapping(nt, pos, scale=(22.0, 22.0, 2.2)), scale=1.0, detail=3.0, rough=0.6)
        fog = noise(nt, pos, scale=5.0, detail=4.0, rough=0.6)
        mod = mixf(nt, ramp(nt, drip, [(0.4, fval(0.0)), (0.7, fval(1.0))]), 0.72, 1.0)
        mod = mth(nt, 'MULTIPLY', mod, mixf(nt, fog, 0.7, 1.15))
        mod = mth(nt, 'MULTIPLY', mod, pane)
        s = mth(nt, 'MULTIPLY', mth(nt, 'MULTIPLY', mod, gs), PANE_BOTTOM)
        e = nd(nt, 'ShaderNodeEmission')
        nt.links.new(gradc, e.inputs['Color'])
        nt.links.new(s, e.inputs['Strength'])
        finish(nt, e.outputs['Emission'])
        return m

    def mat_skylight(strength=0.20):
        """Dirty roof glass glowing with the dusk sky: the cool light that fills the room."""
        m, nt = newmat("skylight")
        pos = geo_pos(nt)
        dirt = noise(nt, pos, scale=2.5, detail=6.0, rough=0.62, distort=0.4)
        fine = noise(nt, pos, scale=14.0, detail=4.0, rough=0.6)
        mod = mixf(nt, ramp(nt, dirt, [(0.35, fval(0.0)), (0.7, fval(1.0))]), 0.12, 1.0)
        mod = mth(nt, 'MULTIPLY', mod, mixf(nt, fine, 0.75, 1.1))
        col = mixc(nt, ramp(nt, dirt, [(0.3, fval(0.0)), (0.7, fval(1.0))]), hx('#244f63'), hx('#4f7480'))
        e = nd(nt, 'ShaderNodeEmission')
        nt.links.new(col, e.inputs['Color'])
        nt.links.new(mth(nt, 'MULTIPLY', mod, strength), e.inputs['Strength'])
        finish(nt, e.outputs['Emission'])
        return m

    def mat_puddle():
        m, nt = newmat("puddle")
        b = principled(nt, hx('#050a0d'), 0.0, 0.02, None, 0.7)
        finish(nt, b)
        return m

    def mat_haze():
        m, nt = newmat("haze")
        pos = geo_pos(nt)
        sx = nt.nodes.new('ShaderNodeSeparateXYZ')
        nt.links.new(pos, sx.inputs[0])
        low = ramp(nt, sx.outputs['Z'], [(0.0, fval(1.5)), (3.0, fval(0.8)), (4.4, fval(0.6))])
        sca = nd(nt, 'ShaderNodeVolumeScatter', i={'Color': (0.82, 0.88, 0.95, 1.0), 'Anisotropy': 0.45})
        sca.inputs['Density'].default_value = HAZE_DENSITY
        out = nd(nt, 'ShaderNodeOutputMaterial')
        nt.links.new(sca.outputs['Volume'], out.inputs['Volume'])
        m.cycles.volume_sampling = 'DISTANCE'
        return m

    def mat_steam(strength=6.0, half=0.95):
        m, nt = newmat("steam")
        pos = geo_pos(nt)
        # object-local coordinates: box centred at origin; column rises along local Z
        tc = nd(nt, 'ShaderNodeTexCoord').outputs['Object']
        sx = nt.nodes.new('ShaderNodeSeparateXYZ')
        nt.links.new(tc, sx.inputs[0])
        x, y, z = sx.outputs['X'], sx.outputs['Y'], sx.outputs['Z']
        # sway the column with height
        sway = mth(nt, 'MULTIPLY', mth(nt, 'SINE', mth(nt, 'MULTIPLY', z, 5.0)), 0.07)
        xs = mth(nt, 'ADD', x, sway)
        comb = nt.nodes.new('ShaderNodeCombineXYZ')
        nt.links.new(xs, comb.inputs['X'])
        nt.links.new(y, comb.inputs['Y'])
        nt.links.new(z, comb.inputs['Z'])
        wisp = noise(nt, mapping(nt, comb.outputs['Vector'], scale=(9.0, 9.0, 1.6)), scale=1.0, detail=5.0, rough=0.6, distort=0.6)
        r = mth(nt, 'POWER', mth(nt, 'ADD', mth(nt, 'MULTIPLY', xs, xs), mth(nt, 'MULTIPLY', y, y)), 0.5)
        radial = ramp(nt, r, [(0.0, fval(1.0)), (0.17, fval(0.0))])
        zf = ramp(nt, z, [(-half, fval(0.0)), (-half * 0.74, fval(1.0)), (half * 0.1, fval(0.8)), (half, fval(0.0))], dom=(-half, half))
        d = mth(nt, 'MULTIPLY', mth(nt, 'MULTIPLY', radial, zf), ramp(nt, wisp, [(0.35, fval(0.0)), (0.7, fval(1.0))]))
        sca = nd(nt, 'ShaderNodeVolumeScatter', i={'Color': (0.95, 0.93, 0.9, 1.0), 'Anisotropy': 0.55})
        nt.links.new(mth(nt, 'MULTIPLY', d, strength), sca.inputs['Density'])
        out = nd(nt, 'ShaderNodeOutputMaterial')
        nt.links.new(sca.outputs['Volume'], out.inputs['Volume'])
        m.cycles.volume_sampling = 'MULTIPLE_IMPORTANCE'
        return m

    # ------------------------------------------------------------------ geometry helpers
    def link(o):
        sc.collection.objects.link(o)
        return o

    def bm_to_obj(name, bm, mats=None, loc=(0, 0, 0), rot=(0, 0, 0), sharp_deg=None, smooth=False):
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
        if smooth:
            for f in bm.faces:
                f.smooth = True
            if sharp_deg is not None:
                for e in bm.edges:
                    if len(e.link_faces) == 2 and e.calc_face_angle(0.0) > math.radians(sharp_deg):
                        e.smooth = False
        me = bpy.data.meshes.new(name)
        bm.to_mesh(me)
        bm.free()
        for mt in (mats or []):
            me.materials.append(mt)
        o = bpy.data.objects.new(name, me)
        o.location = loc
        o.rotation_euler = rot
        return link(o)

    def add_box(bm, size, loc, rot=(0, 0, 0), mi=0):
        M = Matrix.Translation(loc) @ Euler(rot).to_matrix().to_4x4() @ Matrix.Diagonal((size[0], size[1], size[2], 1.0))
        r = bmesh.ops.create_cube(bm, size=1.0, matrix=M)
        return r

    def add_cyl(bm, r1, r2, h, loc, rot=(0, 0, 0), segs=16, cap=True):
        M = Matrix.Translation(loc) @ Euler(rot).to_matrix().to_4x4()
        bmesh.ops.create_cone(bm, cap_ends=cap, cap_tris=False, segments=segs, radius1=r1, radius2=r2, depth=h, matrix=M)

    def add_lathe(bm, prof, loc=(0, 0, 0), rot=(0, 0, 0), segs=28, mi=0, scale=1.0):
        M = Matrix.Translation(loc) @ Euler(rot).to_matrix().to_4x4()
        rings = []
        for (r, zz) in prof:
            r *= scale
            zz *= scale
            if r < 1e-7:
                rings.append([bm.verts.new(M @ Vector((0, 0, zz)))])
            else:
                rings.append([bm.verts.new(M @ Vector((r * math.cos(2 * math.pi * j / segs), r * math.sin(2 * math.pi * j / segs), zz))) for j in range(segs)])
        for a, b in zip(rings[:-1], rings[1:]):
            for j in range(segs):
                j2 = (j + 1) % segs
                q = [a[j % len(a)], a[j2 % len(a)], b[j2 % len(b)], b[j % len(b)]]
                u = []
                for v in q:
                    if v not in u:
                        u.append(v)
                if len(u) >= 3:
                    try:
                        f = bm.faces.new(u)
                        f.material_index = mi
                    except ValueError:
                        pass

    def tube(name, splines, radius, mat, loc=(0, 0, 0), rot=(0, 0, 0), res=2, scale=1.0, taper=None):
        cu = bpy.data.curves.new(name, 'CURVE')
        cu.dimensions = '3D'
        cu.bevel_depth = radius
        cu.bevel_resolution = res
        cu.use_fill_caps = True
        for pts, cyc in splines:
            sp = cu.splines.new('BEZIER')
            sp.bezier_points.add(len(pts) - 1)
            for bp, p in zip(sp.bezier_points, pts):
                bp.co = Vector(p) * scale
                bp.handle_left_type = 'AUTO'
                bp.handle_right_type = 'AUTO'
            sp.use_cyclic_u = cyc
            sp.resolution_u = 5
        cu.materials.append(mat)
        o = bpy.data.objects.new(name, cu)
        o.location = loc
        o.rotation_euler = rot
        return link(o)

    def instance(name, data, loc, rot=(0, 0, 0), scale=(1, 1, 1)):
        o = bpy.data.objects.new(name, data)
        o.location = loc
        o.rotation_euler = rot
        o.scale = scale
        return link(o)

    # ------------------------------------------------------------------ build materials
    M_WOOD = mat_wood('wood_dark', hx('#1c0f08'), hx('#3d2312'), 'Y', polish=0.0)
    M_WOOD_X = mat_wood('wood_dark_x', hx('#1c0f08'), hx('#3d2312'), 'X', polish=0.0)
    M_WOOD_Z = mat_wood('wood_dark_z', hx('#1c0f08'), hx('#3d2312'), 'Z', polish=0.0)
    M_COUNTER = mat_wood('counter', hx('#24130a'), hx('#4a2a15'), 'X', polish=0.5, rough=0.4)
    M_CHAIR = mat_wood('bentwood', hx('#2a1509'), hx('#55301a'), 'Z', gscale=60.0, polish=0.3, rough=0.4, bumpk=0.1)
    M_FLOOR = mat_floor()
    M_PLASTER = mat_plaster()
    M_IRON = mat_iron('iron_teal', '#1d3b3b', chip=(0.52, 0.60))
    M_IRON_PANE = mat_iron('iron_pane', '#1a3434', chip=(0.66, 0.74))
    M_IRON_BLACK = mat_iron('iron_black', '#0c1415')
    M_BRASS = mat_brass('brass')
    M_BRASS_OLD = mat_brass('brass_old', tarnish=0.7, rough=0.4)
    M_MARBLE = mat_marble()
    M_CUP = mat_ceramic('cup', '#bdb7a3')
    M_POT = mat_ceramic('brown_pot', '#4a2210')
    M_GLASS = mat_window_glass()
    M_LAMP = mat_emit('lamp_glow', '#ffb561', 22.0)
    M_PUDDLE = mat_puddle()
    M_SKY = mat_skylight()
    M_HAZE = mat_haze()
    M_STEAM = mat_steam()
    M_STEAM_S = mat_steam(5.0, 0.5)

    # ------------------------------------------------------------------ the room
    RX = 2.8        # half width
    RY0, RY1 = -1.5, 9.0
    RZ = 4.4
    WIN_X = 2.45
    WIN_Z0, WIN_Z1 = 1.0, 4.0

    # floor boards (real geometry, uneven, with dark gaps)
    bm = bmesh.new()
    rnd_layer = None
    boards = []
    x = -RX
    rows = []
    while x < RX - 0.05:
        w = random.uniform(0.13, 0.19)
        w = min(w, RX - x)
        rows.append((x, w))
        x += w + 0.004
    for (xx, w) in rows:
        y = RY0
        while y < RY1:
            L = random.uniform(0.9, 2.3)
            if y + L > RY1:
                L = RY1 - y
            if L < 0.05:
                break
            zoff = random.uniform(0.0, 0.006)
            tilt = random.uniform(-0.004, 0.004)
            add_box(bm, (w, L - 0.004, 0.05), (xx + w / 2, y + L / 2, -0.025 + zoff), (tilt, tilt * 0.5, 0))
            boards.append(random.random())
            y += L
    me_f = bpy.data.meshes.new("floor")
    bm.to_mesh(me_f)
    bm.free()
    lay = me_f.color_attributes.new(name='rnd', type='FLOAT_COLOR', domain='POINT')
    vals = []
    # 8 verts per box -> same value for every vertex of a board
    for v in boards:
        for k in range(8):
            vals.append((v, v, v, 1.0))
    lay.data.foreach_set('color', [c for t in vals for c in t])
    me_f.materials.append(M_FLOOR)
    o_floor = bpy.data.objects.new("floor", me_f)
    link(o_floor)
    # dark underlay so the gaps are black
    bm = bmesh.new()
    add_box(bm, (RX * 2 + 0.2, RY1 - RY0 + 0.2, 0.05), (0, (RY0 + RY1) / 2, -0.08))
    bm_to_obj("underfloor", bm, [M_IRON_BLACK])

    # walls (plaster) with wainscot, pilasters, ceiling, beams
    bm = bmesh.new()
    T = 0.3
    add_box(bm, (T, RY1 - RY0, RZ), (-RX - T / 2, (RY0 + RY1) / 2, RZ / 2))
    add_box(bm, (T, RY1 - RY0, RZ), (RX + T / 2, (RY0 + RY1) / 2, RZ / 2))
    add_box(bm, (2 * RX + 2 * T, T, RZ), (0, RY0 - T / 2, RZ / 2))            # wall behind the camera
    # window wall pieces: piers, sill, lintel
    add_box(bm, (RX - WIN_X, T, RZ), (-(RX + WIN_X) / 2, RY1 + T / 2, RZ / 2))
    add_box(bm, (RX - WIN_X, T, RZ), ((RX + WIN_X) / 2, RY1 + T / 2, RZ / 2))
    add_box(bm, (2 * WIN_X, T, WIN_Z0), (0, RY1 + T / 2, WIN_Z0 / 2))
    add_box(bm, (2 * WIN_X, T, RZ - WIN_Z1), (0, RY1 + T / 2, (RZ + WIN_Z1) / 2))
    bm_to_obj("walls", bm, [M_PLASTER])

    # ceiling boards
    bm = bmesh.new()
    add_box(bm, (2 * RX, RY1 - RY0, 0.12), (0, (RY0 + RY1) / 2, RZ + 0.06))
    bm_to_obj("ceiling", bm, [M_WOOD])

    # skylight: dirty roof glass between the beams, the room's cool light
    bm = bmesh.new()
    add_box(bm, (3.0, RY1 - 1.6, 0.02), (0, (RY1 + 1.6) / 2 - 0.1, RZ - 0.03))
    bm_to_obj("skylight", bm, [M_SKY])

    # beams across, purlins along, braces
    bm = bmesh.new()
    for by in (1.0, 2.6, 4.2, 5.8, 7.4, 8.9):
        add_box(bm, (2 * RX, 0.2, 0.34), (0, by, RZ - 0.17))
    for bx in (-1.7, 1.7):
        add_box(bm, (0.16, RY1 - RY0, 0.2), (bx, (RY0 + RY1) / 2, RZ - 0.34 - 0.1))
    for by in (2.6, 4.2, 5.8, 7.4):
        for sgn in (-1, 1):
            add_box(bm, (0.12, 0.14, 1.15), (sgn * (RX - 0.55), by, RZ - 0.62), (0, sgn * 0.78, 0))
    bm_to_obj("beams", bm, [M_WOOD_X])

    # iron pilasters (painted, chipped, rusting) on the side walls and at the window piers
    bm = bmesh.new()
    for py in (2.0, 4.1, 6.2, 8.3):
        for sgn in (-1, 1):
            add_box(bm, (0.34, 0.34, RZ), (sgn * (RX - 0.17), py, RZ / 2))
            add_box(bm, (0.44, 0.44, 0.16), (sgn * (RX - 0.22), py, 0.08))
            add_box(bm, (0.44, 0.44, 0.12), (sgn * (RX - 0.22), py, RZ - 0.06))
    bm_to_obj("pilasters", bm, [M_IRON])

    # dark wainscot (boards) along the side walls
    bm = bmesh.new()
    WH = 1.15
    for sgn in (-1, 1):
        add_box(bm, (0.08, RY1 - RY0, WH), (sgn * (RX - 0.04), (RY0 + RY1) / 2, WH / 2))
        add_box(bm, (0.14, RY1 - RY0, 0.06), (sgn * (RX - 0.07), (RY0 + RY1) / 2, WH + 0.03))
        add_box(bm, (0.1, RY1 - RY0, 0.14), (sgn * (RX - 0.05), (RY0 + RY1) / 2, 0.07))
        # raised panels
        py = 0.1
        while py < RY1 - 0.9:
            add_box(bm, (0.025, 1.0, 0.7), (sgn * (RX - 0.095), py + 0.5, 0.62))
            py += 1.15
    bm_to_obj("wainscot", bm, [M_WOOD])

    # window frames (iron) and the glowing pane behind them
    bm = bmesh.new()
    FY = RY1 - 0.02
    nvx, nvz = 7, 6
    for i in range(nvx + 1):
        xx = -WIN_X + i * (2 * WIN_X) / nvx
        add_box(bm, (0.06, 0.12, WIN_Z1 - WIN_Z0), (xx, FY, (WIN_Z0 + WIN_Z1) / 2))
    for j in range(nvz + 1):
        zz = WIN_Z0 + j * (WIN_Z1 - WIN_Z0) / nvz
        add_box(bm, (2 * WIN_X, 0.1, 0.05), (0, FY, zz))
    bm_to_obj("window_frames", bm, [M_IRON_BLACK])
    bm = bmesh.new()
    rb = random.Random(77)
    OPEN_PANES = {(1, 3), (1, 4), (2, 2), (2, 1), (3, 3), (3, 4), (3, 5), (4, 2), (4, 1), (5, 3), (5, 4), (6, 2), (0, 4), (4, 4), (6, 1)}
    cw = 2 * WIN_X / nvx
    chh = (WIN_Z1 - WIN_Z0) / nvz
    for i in range(nvx):
        for j in range(nvz):
            open_pane = (i, j) in OPEN_PANES   # only a few panes let the sun in -> distinct shafts
            if not open_pane:
                add_box(bm, (cw - 0.04, 0.05, chh - 0.04), (-WIN_X + (i + 0.5) * cw, RY1 - 0.07, WIN_Z0 + (j + 0.5) * chh))
    bm_to_obj("window_blockers", bm, [M_IRON_PANE])
    bm = bmesh.new()
    add_box(bm, (2 * WIN_X + 0.1, 0.02, WIN_Z1 - WIN_Z0 + 0.1), (0, RY1 + 0.12, (WIN_Z0 + WIN_Z1) / 2))
    o_pane = bm_to_obj("window_pane", bm, [M_GLASS])
    o_pane.visible_shadow = False

    # ------------------------------------------------------------------ furniture builders
    def make_table_mesh():
        bm = bmesh.new()
        prof = [(0.0, 0.0), (0.24, 0.0), (0.24, 0.02), (0.15, 0.045), (0.07, 0.11), (0.04, 0.22),
                (0.034, 0.34), (0.034, 0.60), (0.05, 0.66), (0.09, 0.70), (0.0, 0.70)]
        add_lathe(bm, prof, segs=20, mi=0)
        top = [(0.0, 0.70), (0.36, 0.70), (0.375, 0.715), (0.375, 0.735), (0.36, 0.745), (0.0, 0.745)]
        add_lathe(bm, top, segs=32, mi=1)
        me = bpy.data.meshes.new("table")
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
        for f in bm.faces:
            f.smooth = True
        for e in bm.edges:
            if len(e.link_faces) == 2 and e.calc_face_angle(0.0) > math.radians(40):
                e.smooth = False
        bm.to_mesh(me)
        bm.free()
        me.materials.append(M_IRON_BLACK)
        me.materials.append(M_MARBLE)
        return me

    def chair_curve():
        cu = bpy.data.curves.new("chair", 'CURVE')
        cu.dimensions = '3D'
        cu.bevel_depth = 0.0125
        cu.bevel_resolution = 2
        cu.use_fill_caps = True
        def spl(pts, cyc=False):
            sp = cu.splines.new('BEZIER')
            sp.bezier_points.add(len(pts) - 1)
            for bp, p in zip(sp.bezier_points, pts):
                bp.co = Vector(p)
                bp.handle_left_type = 'AUTO'
                bp.handle_right_type = 'AUTO'
            sp.use_cyclic_u = cyc
            sp.resolution_u = 5
        # chair faces +Y. rear legs run up into one bent back hoop
        back = [(-0.20, -0.21, 0.0), (-0.175, -0.19, 0.30), (-0.17, -0.20, 0.46), (-0.165, -0.235, 0.66),
                (-0.12, -0.27, 0.86), (-0.04, -0.285, 0.935), (0.04, -0.285, 0.935), (0.12, -0.27, 0.86),
                (0.165, -0.235, 0.66), (0.17, -0.20, 0.46), (0.175, -0.19, 0.30), (0.20, -0.21, 0.0)]
        spl(back)
        spl([(-0.21, 0.21, 0.0), (-0.18, 0.18, 0.46)])
        spl([(0.21, 0.21, 0.0), (0.18, 0.18, 0.46)])
        # under-seat ring and the little ring in the back
        ring = []
        for k in range(10):
            a = 2 * math.pi * k / 10
            ring.append((0.19 * math.cos(a), 0.02 + 0.19 * math.sin(a), 0.44))
        spl(ring, True)
        ring2 = []
        for k in range(10):
            a = 2 * math.pi * k / 10
            ring2.append((0.115 * math.cos(a), -0.262, 0.67 + 0.075 * math.sin(a)))
        spl(ring2, True)
        ring3 = []
        for k in range(10):
            a = 2 * math.pi * k / 10
            ring3.append((0.18 * math.cos(a), 0.015 + 0.18 * math.sin(a), 0.20))
        spl(ring3, True)
        cu.materials.append(M_CHAIR)
        return cu

    def chair_seat_mesh():
        bm = bmesh.new()
        prof = [(0.0, 0.445), (0.195, 0.445), (0.215, 0.452), (0.215, 0.470), (0.195, 0.478), (0.0, 0.478)]
        add_lathe(bm, prof, loc=(0, 0.01, 0), segs=24)
        me = bpy.data.meshes.new("seat")
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
        for f in bm.faces:
            f.smooth = True
        bm.to_mesh(me)
        bm.free()
        me.materials.append(M_CHAIR)
        return me

    def cup_mesh(scale=1.0):
        bm = bmesh.new()
        cup = [(0.0, 0.0), (0.025, 0.0), (0.03, 0.006), (0.042, 0.03), (0.046, 0.056), (0.0435, 0.058),
               (0.040, 0.054), (0.034, 0.03), (0.0, 0.012)]
        add_lathe(bm, cup, segs=24, scale=scale)
        sau = [(0.0, 0.0), (0.04, 0.0), (0.075, 0.012), (0.082, 0.017), (0.079, 0.018), (0.04, 0.007), (0.0, 0.007)]
        add_lathe(bm, sau, segs=28, scale=scale, loc=(0, 0, -0.0))
        me = bpy.data.meshes.new("cup")
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
        for f in bm.faces:
            f.smooth = True
        bm.to_mesh(me)
        bm.free()
        me.materials.append(M_CUP)
        return me

    def teapot_parts(loc, rot_z=0.0, mat_body=None, scale=1.0):
        bm = bmesh.new()
        body = [(0.0, 0.0), (0.05, 0.0), (0.075, 0.018), (0.092, 0.06), (0.087, 0.10), (0.062, 0.128), (0.045, 0.135),
                (0.047, 0.14), (0.04, 0.143), (0.038, 0.15), (0.02, 0.158), (0.02, 0.166), (0.012, 0.172), (0.0, 0.172)]
        add_lathe(bm, body, segs=24, scale=scale)
        o = bm_to_obj("teapot", bm, [mat_body or M_POT], loc=loc, rot=(0, 0, rot_z), smooth=True, sharp_deg=50)
        s = scale
        tube("spout", [([(0.07 * s, 0, 0.05 * s), (0.11 * s, 0, 0.08 * s), (0.15 * s, 0, 0.145 * s)], False)], 0.013 * s, mat_body or M_POT,
             loc=loc, rot=(0, 0, rot_z), res=2)
        tube("handle", [([(-0.075 * s, 0, 0.125 * s), (-0.135 * s, 0, 0.1 * s), (-0.13 * s, 0, 0.05 * s), (-0.08 * s, 0, 0.03 * s)], False)],
             0.009 * s, mat_body or M_POT, loc=loc, rot=(0, 0, rot_z), res=2)
        return o

    def place_cup(me, loc, rz=0.0):
        o = instance("cup", me, loc, (0, 0, rz))
        o.data.materials  # keep
        # handle
        tube("cup_handle", [([(0.04, 0, 0.05), (0.07, 0, 0.045), (0.07, 0, 0.025), (0.04, 0, 0.015)], False)], 0.0045, M_CUP,
             loc=(loc[0], loc[1], loc[2] + 0.017), rot=(0, 0, rz), res=1)
        return o

    TABLE_ME = make_table_mesh()
    CHAIR_CU = chair_curve()
    SEAT_ME = chair_seat_mesh()
    CUP_ME = cup_mesh()

    def add_table(x, y, rz=0.0):
        o = instance("table", TABLE_ME, (x, y, 0), (0, 0, rz))
        return o

    def add_chair(x, y, face_x, face_y, jitter=0.15, tipped=False):
        f = Vector((face_x - x, face_y - y))
        f.normalize()
        th = math.atan2(-f.x, f.y) + random.uniform(-jitter, jitter)
        instance("chair", CHAIR_CU, (x, y, 0), (0, 0, th))
        instance("seat", SEAT_ME, (x, y, 0), (0, 0, th))

    # table positions (x, y) -- an asymmetric room, tables hugging both walls
    tables = [(-1.22, 1.8), (1.18, 2.0), (-1.45, 3.9), (1.5, 4.2), (-1.5, 5.9), (1.45, 6.0)]
    for (tx, ty) in tables:
        add_table(tx, ty, random.uniform(0, 3))
        side = 1 if tx > 0 else -1
        # two or three chairs round each table
        for (dx, dy) in random.sample([(0.58 * side, 0.0), (-0.0, 0.55), (0.0, -0.55), (-0.58 * side, 0.1)], 3 if abs(ty) < 7 else 2):
            add_chair(tx + dx, ty + dy, tx, ty)

    # the foreground tea things (the near tables)
    TEAPOT_Z = 0.745
    teapot_parts((1.18, 2.0, TEAPOT_Z), rot_z=0.5, mat_body=M_POT)
    place_cup(CUP_ME, (1.0, 2.1, TEAPOT_Z), 0.3)
    place_cup(CUP_ME, (1.30, 1.83, TEAPOT_Z), 2.9)
    place_cup(CUP_ME, (-1.22 + 0.12, 1.8 + 0.1, TEAPOT_Z), 1.0)
    teapot_parts((-1.45, 3.9, TEAPOT_Z), rot_z=2.2, mat_body=M_CUP)
    place_cup(CUP_ME, (1.5 - 0.1, 4.25 + 0.1, TEAPOT_Z), 1.5)
    place_cup(CUP_ME, (-1.5 + 0.12, 5.9 - 0.08, TEAPOT_Z), 0.4)
    # a milk jug and a brass strainer bowl on the near right table
    bm = bmesh.new()
    jug = [(0.0, 0.0), (0.035, 0.0), (0.05, 0.03), (0.045, 0.07), (0.052, 0.085), (0.045, 0.09), (0.04, 0.07), (0.0, 0.05)]
    add_lathe(bm, jug, segs=20)
    bm_to_obj("jug", bm, [M_CUP], loc=(1.33, 2.12, TEAPOT_Z), smooth=True, sharp_deg=50)

    # tea trolley, parked in the aisle
    TR = (0.42, 2.75)
    bm = bmesh.new()
    add_box(bm, (0.95, 0.52, 0.035), (0, 0, 0.84))
    add_box(bm, (0.95, 0.52, 0.035), (0, 0, 0.30))
    add_box(bm, (0.95, 0.03, 0.05), (0, 0.255, 0.87))
    add_box(bm, (0.95, 0.03, 0.05), (0, -0.255, 0.87))
    add_box(bm, (0.03, 0.52, 0.05), (0.46, 0, 0.87))
    bm_to_obj("trolley_trays", bm, [M_WOOD_X], loc=(TR[0], TR[1], 0), rot=(0, 0, 0.35))
    bm = bmesh.new()
    for sx_ in (-0.44, 0.44):
        for sy_ in (-0.24, 0.24):
            add_cyl(bm, 0.017, 0.017, 0.86, (sx_, sy_, 0.43), segs=8)
            add_cyl(bm, 0.075, 0.075, 0.035, (sx_, sy_, 0.075), rot=(math.pi / 2, 0, 0), segs=18)
    bm_to_obj("trolley_legs", bm, [M_IRON_BLACK], loc=(TR[0], TR[1], 0), rot=(0, 0, 0.35), smooth=True)
    tube("trolley_handle", [([(-0.44, 0.24, 0.86), (-0.58, 0.24, 1.02), (-0.58, -0.24, 1.02), (-0.44, -0.24, 0.86)], False)], 0.014, M_BRASS_OLD,
         loc=(TR[0], TR[1], 0), rot=(0, 0, 0.35))
    _c, _s = math.cos(0.35), math.sin(0.35)
    def tr_pt(lx, ly, lz):
        return (TR[0] + lx * _c - ly * _s, TR[1] + lx * _s + ly * _c, lz)
    teapot_parts(tr_pt(0.12, 0.05, 0.8575), rot_z=0.35 + 0.8, mat_body=M_CUP, scale=1.1)
    place_cup(CUP_ME, tr_pt(-0.2, -0.08, 0.8575), 0.9)
    place_cup(CUP_ME, tr_pt(-0.28, 0.12, 0.8575), 2.2)
    place_cup(CUP_ME, tr_pt(0.3, -0.12, 0.8575), 4.0)
    place_cup(CUP_ME, tr_pt(0.0, 0.0, 0.3175), 0.2)
    place_cup(CUP_ME, tr_pt(0.22, -0.1, 0.3175), 1.7)

    # ------------------------------------------------------------------ the counter and the urn (hero)
    CY = 7.1
    bm = bmesh.new()
    add_box(bm, (3.0, 0.7, 1.0), (0, CY, 0.5))                # body
    add_box(bm, (3.1, 0.82, 0.05), (0, CY, 1.025))            # lip under the top
    add_box(bm, (2.9, 0.58, 0.012), (0, CY, 0.55), (0, 0, 0))
    for i in range(6):
        add_box(bm, (0.42, 0.03, 0.72), (-1.25 + i * 0.5, CY - 0.355, 0.5))   # panels on the front
    bm_to_obj("counter_body", bm, [M_COUNTER])
    bm = bmesh.new()
    add_box(bm, (3.14, 0.86, 0.045), (0, CY, 1.075))
    bm_to_obj("counter_top", bm, [M_MARBLE])
    # brass foot rail
    tube("footrail", [([(-1.4, CY - 0.47, 0.15), (1.4, CY - 0.47, 0.15)], False)], 0.022, M_BRASS_OLD)
    # the urn
    URN_Z = 1.098
    US = 1.2
    bm = bmesh.new()
    urn = [(0.0, 0.0), (0.20, 0.0), (0.205, 0.035), (0.15, 0.07), (0.15, 0.13), (0.17, 0.135), (0.235, 0.20), (0.262, 0.32),
           (0.265, 0.55), (0.25, 0.66), (0.215, 0.74), (0.21, 0.755), (0.225, 0.775), (0.215, 0.79), (0.18, 0.84),
           (0.12, 0.89), (0.05, 0.925), (0.032, 0.935), (0.032, 0.98), (0.05, 0.995), (0.052, 1.02), (0.03, 1.04), (0.0, 1.045)]
    add_lathe(bm, urn, segs=40, scale=US)
    bm_to_obj("urn", bm, [M_BRASS], loc=(0, CY, URN_Z), smooth=True, sharp_deg=48)
    UL = (0, CY, URN_Z)
    for sgn in (-1, 1):
        tube("urn_handle", [([(sgn * 0.262, 0, 0.62), (sgn * 0.36, 0, 0.64), (sgn * 0.40, 0, 0.52),
                              (sgn * 0.33, 0, 0.40), (sgn * 0.265, 0, 0.42)], False)], 0.016, M_BRASS, loc=UL, scale=US)
    tube("urn_tap", [([(0.0, -0.26, 0.30), (0.0, -0.36, 0.30), (0.0, -0.38, 0.24), (0.0, -0.38, 0.20)], False)],
         0.018, M_BRASS, loc=UL, scale=US)
    tube("urn_tap_lever", [([(0.0, -0.33, 0.32), (0.0, -0.30, 0.42)], False),
                           ([(-0.04, -0.30, 0.42), (0.04, -0.30, 0.42)], False)], 0.012, M_BRASS, loc=UL, scale=US)
    tube("gauge", [([(0.17, -0.19, 0.2), (0.17, -0.19, 0.55)], False)], 0.008, M_BRASS_OLD, loc=UL, scale=US)
    # tea canisters and cups along the counter
    bm = bmesh.new()
    for i, cx in enumerate((-1.35, -1.1, -0.85, 0.85, 1.1, 1.35)):
        h = 0.22 + 0.04 * (i % 3)
        add_cyl(bm, 0.07, 0.07, h, (cx, CY + 0.05, 1.098 + h / 2), segs=14)
    bm_to_obj("canisters", bm, [M_IRON_BLACK], smooth=True)
    bm = bmesh.new()
    for i, cx in enumerate((-1.35, -1.1, -0.85, 0.85, 1.1, 1.35)):
        h = 0.22 + 0.04 * (i % 3)
        add_cyl(bm, 0.062, 0.075, 0.03, (cx, CY + 0.05, 1.098 + h + 0.015), segs=14)
    bm_to_obj("canister_lids", bm, [M_BRASS], smooth=True)
    for cx in (-0.55, 0.55):
        instance("cup", CUP_ME, (cx, CY - 0.1, 1.098), (0, 0, 0.5))

    # ------------------------------------------------------------------ lamps (every lamp lights something)
    def lamp_globe(loc, r=0.1, mat=M_LAMP):
        bm = bmesh.new()
        prof = [(0.0, -r)]
        for k in range(1, 9):
            a = -math.pi / 2 + k * (math.pi * 0.85) / 8
            prof.append((r * math.cos(a), r * math.sin(a)))
        prof = [(0.0, -r)] + prof[1:]
        add_lathe(bm, prof, loc=loc, segs=18)
        bm_to_obj("globe", bm, [mat], smooth=True)

    def add_point(name, loc, power, color=(1.0, 0.56, 0.24), radius=0.05):
        l = bpy.data.lights.new(name, 'POINT')
        l.energy = power
        l.color = color
        l.shadow_soft_size = radius
        o = bpy.data.objects.new(name, l)
        o.location = loc
        link(o)
        return o

    def add_spot(name, loc, target, power, size_deg=30, blend=0.5, color=(1.0, 0.6, 0.28), radius=0.06):
        l = bpy.data.lights.new(name, 'SPOT')
        l.energy = power
        l.color = color
        l.shadow_soft_size = radius
        l.spot_size = math.radians(size_deg)
        l.spot_blend = blend
        o = bpy.data.objects.new(name, l)
        o.location = loc
        d = Vector(target) - Vector(loc)
        o.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
        link(o)
        return o

    def pendant(y, z, power, x=0.0):
        tube("chain", [([(x, y, RZ), (x, y, z + 0.28)], False)], 0.006, M_IRON_BLACK)
        bm = bmesh.new()
        cap = [(0.0, 0.0), (0.03, 0.0), (0.035, 0.05), (0.075, 0.115), (0.14, 0.15), (0.145, 0.16), (0.13, 0.17), (0.0, 0.17)]
        add_lathe(bm, cap, loc=(x, y, z + 0.1), segs=24)
        bm_to_obj("shade", bm, [M_BRASS_OLD], smooth=True, sharp_deg=50)
        lamp_globe((x, y, z + 0.12), 0.1)
        add_point("pendant_light", (x, y, z), power)

    pendant(3.3, 3.25, 120.0)
    pendant(5.4, 3.1, 100.0)
    pendant(6.55, 2.95, 120.0, x=-0.25)
    add_spot('urn_key', (-0.25, 6.55, 2.90), (0.0, CY - 0.1, URN_Z + 0.75), 420.0, size_deg=34, blend=0.6)

    def sconce(side, y, z=2.0, power=120.0):
        x = side * (RX - 0.05)
        tube("arm", [([(x, y, z - 0.12), (x - side * 0.10, y, z - 0.10), (x - side * 0.15, y, z)], False)], 0.012, M_BRASS_OLD)
        lamp_globe((x - side * 0.15, y, z + 0.02), 0.07)
        add_point("sconce_light", (x - side * 0.16, y, z + 0.03), power, radius=0.04)

    for yy in (3.1, 5.2, 7.3):
        sconce(-1, yy)
        sconce(1, yy + 0.4)

    # ------------------------------------------------------------------ the puddle (rain walked in)
    def puddle(cx, cy, rx, ry, seed, z=0.011):
        rnd = random.Random(seed)
        ph = [rnd.uniform(0, 6.28) for _ in range(4)]
        n = 48
        bm = bmesh.new()
        c = bm.verts.new((cx, cy, z))
        ring = []
        for k in range(n):
            a = 2 * math.pi * k / n
            f = 1 + 0.20 * math.sin(2 * a + ph[0]) + 0.15 * math.sin(3 * a + ph[1]) + 0.10 * math.sin(5 * a + ph[2]) + 0.06 * math.sin(8 * a + ph[3])
            ring.append(bm.verts.new((cx + rx * f * math.cos(a), cy + ry * f * math.sin(a), z)))
        for k in range(n):
            bm.faces.new((c, ring[k], ring[(k + 1) % n]))
        bm_to_obj("puddle", bm, [M_PUDDLE])


    # ------------------------------------------------------------------ air: haze + steam
    if not NOHAZE:
        bm = bmesh.new()
        add_box(bm, (2 * RX - 0.05, RY1 - RY0 - 0.05, RZ - 0.05), (0, (RY0 + RY1) / 2, RZ / 2))
        o_haze = bm_to_obj("haze", bm, [M_HAZE])
        o_haze.visible_shadow = False
    if not FAST:
        bm = bmesh.new()
        add_box(bm, (0.9, 0.9, 1.9), (0.0, 0.0, 0.0))
        o_st = bm_to_obj("steam_urn", bm, [M_STEAM], loc=(0.0, CY, URN_Z + 1.045 * US + 0.85))
        o_st.visible_shadow = False
        bm = bmesh.new()
        add_box(bm, (0.5, 0.5, 1.0), (0.0, 0.0, 0.0))
        o_st2 = bm_to_obj("steam_pot", bm, [M_STEAM_S], loc=(1.18 + 0.15, 2.0, TEAPOT_Z + 0.172 + 0.5))
        o_st2.visible_shadow = False

    # ------------------------------------------------------------------ light
    # the low sun behind the window wall: the dominant light
    sun = bpy.data.lights.new("sun", 'SUN')
    sun.energy = SUN_STRENGTH
    sun.color = (1.0, 0.76, 0.50)
    sun.angle = math.radians(1.2)
    o_sun = bpy.data.objects.new("sun", sun)
    o_sun.rotation_euler = SUN_DIR.to_track_quat('-Z', 'Y').to_euler()
    link(o_sun)
    # cool fill from the dusk sky, through the glass
    fill = bpy.data.lights.new("sky_fill", 'AREA')
    fill.shape = 'RECTANGLE'
    fill.size = 2 * WIN_X
    fill.size_y = WIN_Z1 - WIN_Z0
    fill.energy = FILL_STRENGTH
    fill.color = (0.45, 0.68, 0.9)
    fill.spread = math.radians(140)
    o_fill = bpy.data.objects.new("sky_fill", fill)
    o_fill.location = (0, RY1 + 0.16, (WIN_Z0 + WIN_Z1) / 2)
    o_fill.rotation_euler = (-math.pi / 2, 0, 0)       # faces -Y (toward the camera)
    link(o_fill)

    sky = bpy.data.lights.new("roof_light", 'AREA')
    sky.shape = 'RECTANGLE'
    sky.size = 3.0
    sky.size_y = RY1 - 2.2
    sky.energy = 200.0
    sky.color = (0.42, 0.66, 0.88)
    sky.spread = math.radians(160)
    o_sky = bpy.data.objects.new("roof_light", sky)
    o_sky.location = (0, (RY1 + 1.6) / 2 - 0.1, RZ - 0.08)
    o_sky.rotation_euler = (0, 0, 0)                  # faces down
    link(o_sky)

    # world: almost black
    w = bpy.data.worlds.new("world")
    w.use_nodes = True
    bgn = [n for n in w.node_tree.nodes if n.bl_idname == 'ShaderNodeBackground'][0]
    bgn.inputs['Color'].default_value = (0.004, 0.007, 0.011, 1.0)
    bgn.inputs['Strength'].default_value = 1.0
    sc.world = w

    # ------------------------------------------------------------------ camera
    cam = bpy.data.cameras.new("cam")
    cam.lens = 30.0
    cam.sensor_fit = 'HORIZONTAL'
    cam.sensor_width = 36.0
    cam.shift_y = -0.115
    cam.clip_start = 0.05
    cam.clip_end = 80.0
    o_cam = bpy.data.objects.new("cam", cam)
    o_cam.location = (0.05, 0.0, 1.58)
    o_cam.rotation_euler = (math.pi / 2, 0, 0)
    link(o_cam)
    sc.camera = o_cam

    # ------------------------------------------------------------------ render settings
    r = sc.render
    r.resolution_x, r.resolution_y, r.resolution_percentage = W, H, 100
    r.threads_mode = 'AUTO'
    r.film_transparent = False
    cy = sc.cycles
    cy.device = 'CPU'
    cy.samples = SAMPLES
    cy.use_adaptive_sampling = True
    cy.adaptive_threshold = 0.02
    cy.adaptive_min_samples = 16
    cy.use_denoising = True
    try:
        cy.denoiser = 'OPENIMAGEDENOISE'
        cy.denoising_input_passes = 'RGB_ALBEDO_NORMAL'
        cy.denoising_prefilter = 'ACCURATE'
    except Exception as e:
        print("denoise setup:", e)
    cy.max_bounces = 7
    cy.diffuse_bounces = 3
    cy.glossy_bounces = 4
    cy.transmission_bounces = 2
    cy.volume_bounces = 1
    cy.transparent_max_bounces = 8
    cy.caustics_reflective = False
    cy.caustics_refractive = False
    cy.sample_clamp_indirect = 4.0
    cy.sample_clamp_direct = 0.0
    cy.volume_step_rate = 1.0
    cy.volume_max_steps = 256
    cy.use_light_tree = True
    cy.filter_width = 1.4
    try:
        sc.view_settings.view_transform = 'AgX'
    except Exception as e:
        print("view transform:", e)
    try:
        sc.view_settings.look = 'AgX - High Contrast'
    except Exception:
        pass
    sc.view_settings.exposure = EXPOSURE
    sc.display_settings.display_device = 'sRGB'
    r.image_settings.file_format = 'PNG'
    r.image_settings.color_depth = '8'
    raw_path = os.path.splitext(OUT)[0] + ".raw.png"
    r.filepath = raw_path
    CROP = os.environ.get("TEA_CROP", "")
    if CROP:
        x0, y0, x1, y1 = [float(v) for v in CROP.split(",")]
        r.use_border = True
        r.use_crop_to_border = True
        r.border_min_x, r.border_max_x = x0, x1
        r.border_min_y, r.border_max_y = 1.0 - y1, 1.0 - y0
    print("scene built in %.1fs" % (time.time() - T0))
    t1 = time.time()
    bpy.ops.render.render(write_still=True)
    print("render took %.1fs" % (time.time() - t1))


# ------------------------------------------------------------------ finishing (paint-like softening, glow, grade, vignette, grain)
def load_png(path):
    img = bpy.data.images.load(path)
    img.colorspace_settings.name = 'Non-Color'
    w_, h_ = img.size
    px = np.empty(w_ * h_ * 4, dtype=np.float32)
    img.pixels.foreach_get(px)
    a = px.reshape(h_, w_, 4)[::-1, :, :3].copy()   # flip so row 0 is the top
    bpy.data.images.remove(img)
    return a

def save_png(a, path):
    h_, w_ = a.shape[:2]
    try:
        from PIL import Image
        Image.fromarray((np.clip(a, 0, 1) * 255 + 0.5).astype(np.uint8)).save(path)
        return
    except Exception:
        pass
    img = bpy.data.images.new("fin", w_, h_, alpha=False)
    img.colorspace_settings.name = 'Non-Color'
    buf = np.ones((h_, w_, 4), np.float32)
    buf[:, :, :3] = np.clip(a, 0, 1)[::-1]
    img.pixels.foreach_set(buf.ravel())
    img.filepath_raw = path
    img.file_format = 'PNG'
    img.save()

def box_blur(a, rad):
    rad = int(rad)
    if rad < 1:
        return a
    k = 2 * rad + 1
    ap = np.pad(a, ((rad, rad), (rad, rad), (0, 0)), mode='edge')
    c = np.cumsum(ap, axis=0, dtype=np.float64)
    c = np.concatenate([np.zeros((1,) + c.shape[1:]), c], axis=0)
    a1 = (c[k:] - c[:-k]) / k
    c = np.cumsum(a1, axis=1)
    c = np.concatenate([np.zeros((c.shape[0], 1, c.shape[2])), c], axis=1)
    return ((c[:, k:] - c[:, :-k]) / k).astype(np.float32)

def gauss(a, sigma):
    rad = max(1, int(round(sigma * 0.8)))
    for _ in range(3):
        a = box_blur(a, rad)
    return a

def kuwahara(img, m):
    if m < 1:
        return img
    p = np.pad(img, ((m, m), (m, m), (0, 0)), mode='edge')
    mean = box_blur(p, m)
    mean2 = box_blur(p * p, m)
    var = (mean2 - mean * mean).sum(axis=2)
    best = None
    out = None
    for sy in (-m, m):
        for sx in (-m, m):
            mv = np.roll(np.roll(mean, -sy, axis=0), -sx, axis=1)
            vv = np.roll(np.roll(var, -sy, axis=0), -sx, axis=1)
            if best is None:
                best, out = vv, mv
            else:
                msk = vv < best
                best = np.where(msk, vv, best)
                out = np.where(msk[:, :, None], mv, out)
    return out[m:-m, m:-m]

def luma(a):
    return 0.2126 * a[:, :, 0] + 0.7152 * a[:, :, 1] + 0.0722 * a[:, :, 2]

import json
G = dict(kuw=1.5, blend=0.72, glow1=0.30, glow2=0.22, lift=0.9, liftk=1.25, sat=1.16, gamma=1.10, vig=0.38, grain=0.012, mott=0.020)
G.update(json.loads(os.environ.get("TEA_GRADE", "{}")))

def finish_image(a):
    s = H / 960.0
    # 1. paint-like softening: flat brush patches, crisp edges kept
    k = kuwahara(a, max(1, int(round(G['kuw'] * s + 0.4))))
    # keep a little of the sharp original so built edges stay crisp
    a = G['blend'] * k + (1.0 - G['blend']) * a
    # 2. glow around the lamps and the window (light doing something to the air)
    L = luma(a)
    hot = np.clip((a - 0.62) / 0.38, 0, 1) * (L[:, :, None] > 0.55)
    g1 = gauss(hot, 6 * s)
    g2 = gauss(hot, 22 * s)
    a = 1.0 - (1.0 - a) * (1.0 - np.clip(G['glow1'] * g1 + G['glow2'] * g2, 0, 1))
    # 3. grade: blue-black shadows far from light, brown-black near it, amber highlights
    L = luma(a)
    warmth = gauss(np.clip((a[:, :, 0:1] - a[:, :, 2:3]) * 2.0, 0, 1) * (L[:, :, None] > 0.25), 38 * s)
    warmth = np.clip(warmth * 5.0, 0, 1)
    cool_black = np.array([0.026, 0.056, 0.078], np.float32)
    warm_black = np.array([0.062, 0.038, 0.020], np.float32)
    lift = (cool_black * (1 - warmth) + warm_black * warmth) * G['liftk']
    a = lift + a * (1.0 - G['lift'] * lift)
    L = luma(a)[:, :, None]
    sh = np.clip(1.0 - L / 0.35, 0, 1)
    hi = np.clip((L - 0.35) / 0.4, 0, 1)
    a = a * (1 + sh * np.array([-0.10, 0.0, 0.10], np.float32)) * (1 + hi * np.array([0.07, 0.0, -0.09], np.float32))
    # gentle saturation and contrast
    L = luma(a)[:, :, None]
    a = L + (a - L) * G['sat']
    a = np.clip(a, 0, 1)
    a = a ** G['gamma']
    # 4. vignette
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    rr = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 * 0.85 + ((yy - H * 0.47) / (H / 2)) ** 2 * 0.75)
    vig = 1.0 - G['vig'] * np.clip(rr - 0.35, 0, 1) ** 1.6
    a = a * vig[:, :, None]
    # 5. paper/canvas grain, soft brush-scale mottling
    rng = np.random.default_rng(15)
    n1 = rng.standard_normal((H, W, 1)).astype(np.float32)
    n2 = gauss(rng.standard_normal((H, W, 1)).astype(np.float32), 1.6 * s) * 3.0
    a = a * (1 + G['grain'] * n1 + G['mott'] * n2)
    return np.clip(a, 0, 1)

raw = load_png(raw_path)
if CROP:
    save_png(raw, OUT)
else:
    fin = finish_image(raw)
    save_png(fin, OUT)
print("finished %s (%dx%d) total %.1fs" % (OUT, W, H, time.time() - T0))
