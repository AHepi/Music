import bpy, math, random
import numpy as np
from mathutils import Vector, Euler, Matrix
from lib import *
import terrain

RAD = math.radians

# ---------------- materials ----------------
def m_weatherboard():
    m = new_mat('wall_weatherboard'); nb = NB(m)
    obj = nb.coord('Object')
    wv = nb.n('ShaderNodeTexWave'); wv.wave_type = 'BANDS'; wv.bands_direction = 'Z'; wv.wave_profile = 'SAW'
    wv.inputs['Scale'].default_value = 1 / 0.15; wv.inputs['Distortion'].default_value = 0.0
    nb.link(obj, wv.inputs['Vector'])
    groove = nb.ramp(wv.outputs['Fac'], [(0.0, (0.55, 0.55, 0.55)), (0.12, (1, 1, 1)), (1.0, (1, 1, 1))])
    n1 = nb.noise(nb.mapping(obj, (1.5, 1.5, 0.5)), 2.5, 5, 0.6)
    n2 = nb.noise(nb.mapping(obj, (6, 6, 0.4)), 3.0, 4, 0.6)
    grime = nb.ramp(n2.outputs['Fac'], [(0.35, (1, 1, 1)), (0.7, (0.62, 0.58, 0.5))])
    fade = nb.mix(n1.outputs['Fac'], (0.78, 0.74, 0.60, 1), (0.86, 0.84, 0.72, 1))
    base = nb.mix(0.7, fade, grime.outputs[0])
    # splash zone at the bottom: darker, greener
    z = nb.sep(obj)[2]
    low = nb.math('SUBTRACT', 1.0, nb.math('DIVIDE', nb.math('ADD', z, 1.25), 0.7, clamp=True))
    base = nb.mix(nb.math('MULTIPLY', low, 0.55), base, (0.28, 0.27, 0.2, 1))
    col = nb.mix(1.0, base, base)
    mul = nb.n('ShaderNodeMix'); mul.data_type = 'RGBA'; mul.blend_type = 'MULTIPLY'
    mul.inputs[0].default_value = 1.0
    nb.link(base, mul.inputs[6]); nb.link(groove.outputs[0], mul.inputs[7])
    bump = nb.bump(wv.outputs['Fac'], 0.5, 0.02)
    p = nb.principled(mul.outputs[2], 0.7, Normal=bump)
    nb.out(p.outputs[0]); return m

def m_paint(name, color, rough=0.35, wear=0.25):
    m = new_mat(name); nb = NB(m)
    obj = nb.coord('Object')
    n = nb.noise(nb.mapping(obj, (3, 3, 3)), 6, 5, 0.6)
    wornc = nb.ramp(n.outputs['Fac'], [(0.45, (*color, 1)), (0.72, (color[0] * 1.5 + 0.1, color[1] * 1.4 + 0.1, color[2] * 1.3 + 0.08, 1))])
    p = nb.principled(wornc.outputs[0], rough)
    nb.out(p.outputs[0]); return m

def m_roof():
    m = new_mat('roof_iron'); nb = NB(m)
    obj = nb.coord('Object')
    sx = nb.sep(obj)[0]
    sheet = nb.math('FLOOR', nb.math('DIVIDE', sx, 0.86))
    wn = nb.n('ShaderNodeTexWhiteNoise'); wn.noise_dimensions = '1D'
    nb.link(sheet, wn.inputs['W'])
    var = nb.math('ADD', nb.math('MULTIPLY', wn.outputs['Value'], 0.5), 0.75)
    n1 = nb.noise(nb.mapping(obj, (0.4, 0.4, 0.4)), 1.5, 5, 0.6)
    n2 = nb.noise(nb.mapping(obj, (4, 0.6, 4)), 4.0, 5, 0.65)
    paint = nb.ramp(n1.outputs['Fac'], [(0.3, (0.40, 0.045, 0.03)), (0.7, (0.55, 0.08, 0.045))])
    rust = nb.ramp(n2.outputs['Fac'], [(0.50, (0, 0, 0)), (0.68, (1, 1, 1))])
    c = nb.mix(rust.outputs[0], paint.outputs[0], (0.22, 0.08, 0.035, 1))
    mul = nb.n('ShaderNodeMix'); mul.data_type = 'RGBA'; mul.blend_type = 'MULTIPLY'; mul.inputs[0].default_value = 1.0
    nb.link(c, mul.inputs[6]); nb.link(nb.n('ShaderNodeCombineXYZ').outputs[0] if False else var, mul.inputs[7])
    p = nb.principled(mul.outputs[2], 0.42, Metallic=0.12)
    nb.out(p.outputs[0]); return m

def m_deck():
    m = new_mat('deck'); nb = NB(m)
    obj = nb.coord('Object')
    wv = nb.n('ShaderNodeTexWave'); wv.wave_type = 'BANDS'; wv.bands_direction = 'Y'; wv.wave_profile = 'SAW'
    wv.inputs['Scale'].default_value = 1 / 0.14
    nb.link(obj, wv.inputs['Vector'])
    gap = nb.ramp(wv.outputs['Fac'], [(0.0, (0.25, 0.25, 0.25)), (0.06, (1, 1, 1)), (1.0, (1, 1, 1))])
    n = nb.noise(nb.mapping(obj, (0.25, 8, 8)), 4, 5, 0.6)
    col = nb.ramp(n.outputs['Fac'], [(0.3, (0.17, 0.095, 0.05)), (0.7, (0.30, 0.19, 0.11))])
    mul = nb.n('ShaderNodeMix'); mul.data_type = 'RGBA'; mul.blend_type = 'MULTIPLY'; mul.inputs[0].default_value = 1.0
    nb.link(col.outputs[0], mul.inputs[6]); nb.link(gap.outputs[0], mul.inputs[7])
    bump = nb.bump(nb.math('ADD', wv.outputs['Fac'], n.outputs['Fac']), 0.4, 0.015)
    p = nb.principled(mul.outputs[2], 0.75, Normal=bump)
    nb.out(p.outputs[0]); return m

def m_concrete():
    m = new_mat('concrete'); nb = NB(m)
    obj = nb.coord('Object')
    n = nb.noise(nb.mapping(obj, (4, 4, 4)), 5, 6, 0.6)
    c = nb.ramp(n.outputs['Fac'], [(0.3, (0.30, 0.29, 0.26)), (0.7, (0.5, 0.48, 0.42))])
    n2 = nb.noise(obj, 60, 3, 0.7)
    p = nb.principled(c.outputs[0], 0.9, Normal=nb.bump(n2.outputs['Fac'], 0.4, 0.01))
    nb.out(p.outputs[0]); return m

def m_solar():
    m = new_mat('solar'); nb = NB(m)
    obj = nb.coord('Object')
    br = nb.n('ShaderNodeTexBrick')
    br.inputs['Scale'].default_value = 7
    br.inputs['Mortar Size'].default_value = 0.02; br.inputs['Bias'].default_value = 0
    br.inputs['Color1'].default_value = (0.012, 0.025, 0.08, 1); br.inputs['Color2'].default_value = (0.016, 0.03, 0.09, 1)
    br.inputs['Mortar'].default_value = (0.5, 0.5, 0.55, 1)
    br.offset = 0.0; br.squash = 1.0
    nb.link(nb.mapping(obj, (1, 0.8, 1), (0.5, 0.8, 0)), br.inputs['Vector'])
    p = nb.principled(br.outputs['Color'], 0.12, Metallic=0.4)
    p.inputs['Coat Weight'].default_value = 0.6
    nb.out(p.outputs[0]); return m

def build_bach(root_loc, rot_z_deg, coll=None):
    random.seed(11)
    root = bpy.data.objects.new('bach_root', None)
    bpy.context.scene.collection.objects.link(root)
    root.location = root_loc; root.rotation_euler = (0, 0, RAD(rot_z_deg))
    bpy.context.view_layer.update()
    MW = root.matrix_world
    def W(p): return MW @ Vector(p)
    M_wall = m_weatherboard(); M_trim = m_paint('trim_turq', (0.025, 0.30, 0.32), 0.3)
    M_white = m_paint('white_paint', (0.62, 0.60, 0.54), 0.4)
    M_roof = m_roof(); M_deck = m_deck(); M_conc = m_concrete(); M_solar = m_solar()
    M_glass = simple_mat('louvre_glass', (0.55, 0.7, 0.72, 1), 0.08, 0.0, Transmission_Weight=0.0)
    M_dark = new_mat('interior'); nb = NB(M_dark)
    e = nb.n('ShaderNodeEmission'); e.inputs['Color'].default_value = (1.0, 0.5, 0.18, 1); e.inputs['Strength'].default_value = 0.35
    nb.out(e.outputs[0])
    M_steel = simple_mat('steel', (0.45, 0.46, 0.48, 1), 0.35, 1.0)
    M_bulb = emission_mat('bulb', (1.0, 0.68, 0.32), 40)
    objs = []
    def B(name, size, loc, mat, rot=(0, 0, 0)):
        o = box(name, size, loc, mat, rot=rot, parent=root); objs.append(o); return o

    Z0 = 0.0   # deck surface
    # deck + frame
    B('deck', (6.5, 5.7, 0.12), (0, -0.85, -0.06), M_deck)
    for i, yy in enumerate((-3.2, -1.0, 0.9, 1.7)):
        B('bearer%d' % i, (6.6, 0.12, 0.22), (0, yy, -0.23), M_white)
    # piles down to the ground
    for ix in (-2.9, -1.0, 1.0, 2.9):
        for yy in (-3.3, -0.9, 1.7):
            gw = W((ix, yy, 0)); g = terrain.ground(gw.x, gw.y)
            top = -0.12; bottom = (g - root.location.z) - 0.35
            h = top - bottom
            B('pile', (0.24, 0.24, h), (ix, yy, bottom + h / 2), M_conc)
    # body
    body = B('body', (6.0, 3.6, 2.5), (0, 0, 1.25), M_wall)
    # gable ends (prism)
    zr = lambda y: 2.5 + math.tan(RAD(24)) * (2.9 - abs(y + 0.9))
    poly = [(-1.8, 2.5), (1.8, 2.5), (1.8, zr(1.8)), (-0.9, zr(-0.9)), (-1.8, zr(-1.8))]
    v = []; f = []
    for x in (-3.0, 3.0):
        for (y, z) in poly: v.append((x, y, z))
    n = len(poly)
    f.append(tuple(range(n))[::-1]); f.append(tuple(range(n, 2 * n)))
    for i in range(n):
        j = (i + 1) % n
        f.append((i, j, n + j, n + i))
    g = mesh_obj('gables', v, f, M_wall, smooth=False); g.parent = root; objs.append(g)
    # corner boards
    for sx in (-1, 1):
        for sy in (-1, 1):
            B('corner', (0.1, 0.1, 2.5), (sx * 3.02, sy * 1.82, 1.25), M_trim)
    # skirting / plinth
    B('plinth', (6.1, 3.7, 0.12), (0, 0, 0.06), M_trim)
    # ---- roof (corrugated)
    ang = RAD(24); L = 2.9 / math.cos(ang)
    nx = 7.0; per = 0.095
    nu = int(nx / per * 6); nv = 6
    def slope(name, y_eave, y_ridge, sign):
        # sign: -1 front slope, +1 back slope
        us = np.linspace(-3.5, 3.5, nu + 1)
        vs = np.linspace(0, L, nv + 1)
        vv = []; 
        for vsx in vs:
            for u in us:
                hx = vsx * math.cos(ang); hz = vsx * math.sin(ang)
                y = y_eave + (-sign) * -hx if False else (y_eave + hx * (1 if y_ridge > y_eave else -1))
                z = 2.5 + hz
                corr = 0.022 * math.sin(2 * math.pi * u / per)
                nrm_y = -math.sin(ang) * (1 if y_ridge > y_eave else -1) * -1
                # normal pointing up/outward of slope
                ny = -(1 if y_ridge > y_eave else -1) * math.sin(ang)
                nz = math.cos(ang)
                vv.append((u, y + ny * corr, z + nz * corr))
        ff = []
        for j in range(nv):
            for i in range(nu):
                a = j * (nu + 1) + i
                ff.append((a, a + 1, a + nu + 2, a + nu + 1) if y_ridge > y_eave else (a + 1, a, a + nu + 1, a + nu + 2))
        o = mesh_obj(name, vv, ff, M_roof, smooth=True); o.parent = root
        s = o.modifiers.new('sol', 'SOLIDIFY'); s.thickness = 0.008; s.offset = -1
        objs.append(o); return o
    slope('roof_front', -3.8, -0.9, -1)
    slope('roof_back', 2.0, -0.9, 1)
    # ridge cap
    for sgn in (-1, 1):
        B('ridge', (7.1, 0.28, 0.025), (0, -0.9 + sgn * 0.13, 3.79 + 0.035 - 0.0), M_roof, rot=(sgn * RAD(-24) * -1, 0, 0))
    # fascia and gutters
    B('fascia_f', (7.1, 0.03, 0.16), (0, -3.84, 2.42), M_white)
    B('fascia_b', (7.1, 0.03, 0.16), (0, 2.04, 2.42), M_white)
    B('gutter_f', (7.1, 0.1, 0.09), (0, -3.9, 2.34), M_steel)
    B('dp', (0.07, 0.07, 2.45), (3.35, -3.92, 1.1), M_steel)
    # barge boards along gable slopes
    for xx in (-3.55, 3.55):
        for sgn in (-1, 1):
            ycen = -0.9 + sgn * 1.45; zc = 2.5 + (3.79 - 2.5) / 2 + 0.03
            B('barge', (0.035, L + 0.05, 0.15), (xx, ycen, zc), M_white, rot=(-sgn * ang * -1 if False else sgn * -ang * -1 * -1, 0, 0))
    # ---- veranda posts and rails
    for px in (-3.0, -1.0, 1.0, 3.0):
        B('post', (0.13, 0.13, 2.5), (px, -3.55, 1.25), M_white)
        B('bracket', (0.1, 0.5, 0.1), (px, -3.3, 2.25), M_white, rot=(RAD(45), 0, 0))
    for zz, hh in ((0.95, 0.07), (0.5, 0.05)):
        B('rail_l', (2.55, 0.07, hh), (-1.82, -3.55, zz), M_white)
        B('rail_r', (2.55, 0.07, hh), (1.82, -3.55, zz), M_white)
        B('rail_side_l', (0.07, 1.75, hh), (-3.0, -2.65, zz), M_white)
        B('rail_side_r', (0.07, 1.75, hh), (3.0, -2.65, zz), M_white)
    for bx in np.linspace(-3.0, -0.6, 12):
        B('bal', (0.035, 0.035, 0.45), (bx, -3.55, 0.72), M_white)
    for bx in np.linspace(0.6, 3.0, 12):
        B('bal', (0.035, 0.035, 0.45), (bx, -3.55, 0.72), M_white)
    # steps
    for k in range(3):
        B('step', (1.3, 0.34, 0.06), (0, -3.72 - 0.3 * k - 0.02, -0.2 - 0.23 * k), M_deck)
        B('stepb', (1.3, 0.04, 0.2), (0, -3.58 - 0.3 * k, -0.30 - 0.23 * k), M_white)
    for sx_ in (-0.62, 0.62):
        B('stringer', (0.05, 1.1, 0.25), (sx_, -4.15, -0.5), M_white, rot=(RAD(34), 0, 0))
    # ---- windows (louvre) and door
    def louvre_window(name, face, loc, w, h):
        # face: 'front' (-y), 'left' (-x), 'back' (+y), 'right'(+x)
        e = bpy.data.objects.new(name, None); bpy.context.scene.collection.objects.link(e)
        e.parent = root; e.location = loc
        e.rotation_euler = (0, 0, {'front': 0, 'left': RAD(-90), 'back': RAD(180), 'right': RAD(90)}[face])
        def LB(nm, size, lc, mat, rot=(0, 0, 0)):
            o = box(nm, size, lc, mat, rot=rot, parent=e); objs.append(o); return o
        LB('recess', (w, 0.03, h), (0, 0.02, 0), M_dark)
        t = 0.07
        LB('f_top', (w + 2 * t, 0.1, t), (0, -0.04, h / 2 + t / 2), M_trim)
        LB('f_bot', (w + 2 * t + 0.1, 0.14, t), (0, -0.06, -h / 2 - t / 2), M_trim)
        LB('f_l', (t, 0.1, h), (-w / 2 - t / 2, -0.04, 0), M_trim)
        LB('f_r', (t, 0.1, h), (w / 2 + t / 2, -0.04, 0), M_trim)
        ns = int(h / 0.1)
        for i in range(ns):
            zz = -h / 2 + (i + 0.5) * h / ns
            LB('slat', (w - 0.02, 0.1, 0.012), (0, -0.03, zz), M_glass, rot=(RAD(-38), 0, 0))
        return e
    louvre_window('win_fl', 'front', (-2.05, -1.86, 1.15), 1.2, 1.0)
    louvre_window('win_fr', 'front', (2.05, -1.86, 1.15), 1.2, 1.0)
    louvre_window('win_l', 'left', (-3.06, -0.2, 1.15), 1.2, 1.0)
    louvre_window('win_b1', 'back', (-1.5, 1.86, 1.15), 1.0, 1.0)
    louvre_window('win_b2', 'back', (1.5, 1.86, 1.15), 1.0, 1.0)
    # door with louvres
    louvre_window('door_glass', 'front', (0, -1.86, 1.05), 0.8, 1.85)
    B('door_frame_top', (1.1, 0.1, 0.08), (0, -1.9, 2.04), M_trim)
    # roof solar panels on the front slope
    for k, ux in enumerate((-1.5, -0.4, 0.7)):
        o = bpy.data.objects.new('panel', None)
        pm = box('solar_panel', (1.0, 1.65, 0.04), (0, 0, 0), M_solar)
        pm.parent = root
        s = 1.65 / 2 + 0.55
        pm.location = (ux + 0.1 + (0.0), -3.8 + (s) * math.cos(ang) + math.sin(ang) * 0.1, 2.5 + s * math.sin(ang) + math.cos(ang) * 0.1)
        pm.rotation_euler = (ang, 0, 0)
        # frame rim
        objs.append(pm)
    # lights
    cat = []
    for span in range(3):
        x0 = -3.0 + span * 2.0; x1 = x0 + 2.0
        for i in range(1, 8):
            t = i / 8
            xx = x0 + (x1 - x0) * t
            zz = 2.36 - 0.17 * 4 * t * (1 - t)
            sph = sphere('bulb', 0.028, (xx, -3.78, zz), M_bulb, seg=8, ring=6); sph.parent = root
    # water tank at the back right
    tank = cyl('tank', 0.95, 2.1, (1.0, 4.8, 1.05 - 0.6 + (terrain.ground(*(W((1.0, 4.8, 0))[:2])) - root.location.z) * 0 + 0.0), simple_mat('tank', (0.02, 0.12, 0.05, 1), 0.3), seg=40)
    tank.parent = root
    gt = terrain.ground(*(W((1.0, 4.8, 0))[:2]))
    base_z = gt - root.location.z
    tank.location.z = base_z + 1.05
    # tank pad
    pad = cyl('pad', 1.2, 0.2, (1.0, 4.8, base_z + 0.0), M_conc, seg=32); pad.parent = root
    lid = cyl('lid', 0.5, 0.12, (1.0, 4.8, base_z + 2.12), simple_mat('lid', (0.01, 0.07, 0.03, 1), 0.4), seg=24, r2=0.4); lid.parent = root
    # pipe from the tank to the house
    # chairs and table
    def chair(x, y, rz):
        e = bpy.data.objects.new('chair', None); bpy.context.scene.collection.objects.link(e); e.parent = root
        e.location = (x, y, 0); e.rotation_euler = (0, 0, rz)
        Mp = simple_mat('plastic', (0.72, 0.72, 0.70, 1), 0.35)
        b1 = box('seat', (0.46, 0.44, 0.04), (0, 0, 0.44), Mp, parent=e, bevel=0.01)
        b2 = box('back', (0.44, 0.035, 0.45), (0, 0.23, 0.70), Mp, rot=(RAD(-12), 0, 0), parent=e, bevel=0.01)
        for lx in (-0.2, 0.2):
            for ly in (-0.19, 0.19):
                c = cyl('leg', 0.018, 0.44, (lx, ly, 0.22), Mp, seg=8, parent=e)
        for lx in (-0.2, 0.2):
            box('arm', (0.03, 0.4, 0.03), (lx, 0.02, 0.64), Mp, parent=e)
    chair(1.9, -2.7, RAD(25)); chair(2.65, -2.9, RAD(-15))
    tbl = cyl('table', 0.32, 0.03, (2.25, -3.2, 0.52), simple_mat('tbl', (0.62, 0.36, 0.16, 1), 0.5), seg=24); tbl.parent = root
    cyl('tl', 0.025, 0.5, (2.25, -3.2, 0.26), M_steel, seg=8, parent=root)
    import props
    for (nm, L, Wd, col, st, lx, ly, lean) in [('board1', 1.95, 0.27, (0.95, 0.75, 0.1), (0.05, 0.4, 0.45), -2.78, -3.2, 98), ('board2', 2.35, 0.3, (0.9, 0.9, 0.85), (0.75, 0.08, 0.06), -2.55, -3.0, 96)]:
        props.make_surfboard(nm, L, Wd, 0.035, col, st, parent=root, loc=(lx, ly, L / 2 * 0.99 + 0.04), rot=(RAD(4), -RAD(lean), 0))
    cb = box('cooler', (0.62, 0.38, 0.38), (-1.55, -3.0, 0.19), simple_mat('cooler', (0.85, 0.85, 0.82, 1), 0.4), parent=root, bevel=0.03)
    box('cooler_lid', (0.64, 0.4, 0.07), (-1.55, -3.0, 0.41), simple_mat('cooler_lid', (0.05, 0.25, 0.6, 1), 0.4), parent=root, bevel=0.02)
    cyl('bucket', 0.16, 0.3, (0.9, -3.0, 0.15), simple_mat('bucket', (0.8, 0.1, 0.05, 1), 0.4), seg=16, r2=0.2, parent=root)
    for k, (fx, fy, fz, fr) in enumerate([(-0.15, -4.05, -0.17, 0.4), (0.12, -3.95, -0.17, -0.3)]):
        box('thong', (0.1, 0.27, 0.025), (fx, fy, fz), simple_mat('thong', (0.9, 0.3, 0.5, 1), 0.5), rot=(0, 0, fr), parent=root, bevel=0.01)
    return root
