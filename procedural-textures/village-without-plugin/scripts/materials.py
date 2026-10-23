"""Procedural materials for the village (no image textures anywhere)."""
import bpy
from common import MatB

MATS = {}

def _reg(m):
    MATS[m.name] = m
    return m

# ---------------------------------------------------------------- ground
def ground():
    m = MatB('Ground')
    P = m.position()
    road = m.attr('road'); rut = m.attr('rut'); wet = m.attr('wet')
    cen = m.attr('center'); forest = m.attr('forest'); yard = m.attr('yard')
    n_big = m.noise(P, 0.22, 3, 0.55)
    n_mid = m.noise(P, 2.0, 4, 0.6)
    n_fine = m.noise(P, 13.0, 4, 0.6)
    n_micro = m.noise(P, 80.0, 2, 0.5)
    n_patch = m.noise(P, 0.9, 3, 0.5, w=3.0, dims='4D')

    # road / trampled coverage with a ragged edge
    rm = m.math('ADD', road, m.math('MULTIPLY', m.math('SUBTRACT', n_mid, 0.5), 0.5))
    road_m = m.maprange(rm, 0.36, 0.62, 0.0, 1.0, True, 'SMOOTHSTEP')

    # --- dirt
    dirt_a = (0.165, 0.112, 0.064)
    dirt_b = (0.072, 0.048, 0.029)
    dirt_c = (0.255, 0.195, 0.118)
    dcol = m.mixc(m.maprange(n_mid, 0.32, 0.68), dirt_b, dirt_a)
    dcol = m.mixc(m.maprange(n_big, 0.50, 0.66), dcol, dirt_c)
    dcol = m.mixc(m.maprange(n_fine, 0.35, 0.75, 0.0, 0.35), dcol, dirt_b)

    # gravel / pebbles pressed into the dirt
    vor = m.voronoi(P, 34.0, 'F1', 1.0, ret_node=True)
    vr, vg, vb = m.sepcol(vor.outputs['Color'])
    vd = vor.outputs['Distance']
    stone_pick = m.math('GREATER_THAN', vr, 0.80)
    stone_shape = m.maprange(vd, 0.55, 0.28, 0.0, 1.0, True, 'SMOOTHSTEP')
    stone_mask = m.math('MULTIPLY', m.math('MULTIPLY', stone_pick, stone_shape), m.maprange(road_m, 0.5, 0.9))
    stone_col = m.mixc(vg, (0.14, 0.13, 0.115), (0.27, 0.215, 0.145))
    dcol = m.mixc(stone_mask, dcol, stone_col)
    vor2 = m.voronoi(P, 11.0, 'F1', 1.0, ret_node=True)
    v2r, v2g, v2b = m.sepcol(vor2.outputs['Color'])
    stone2 = m.math('MULTIPLY', m.math('GREATER_THAN', v2r, 0.90), m.maprange(vor2.outputs['Distance'], 0.5, 0.25, 0.0, 1.0, True, 'SMOOTHSTEP'))
    stone2 = m.math('MULTIPLY', stone2, m.maprange(road_m, 0.6, 0.95))
    dcol = m.mixc(stone2, dcol, m.mixc(v2g, (0.16, 0.15, 0.135), (0.25, 0.20, 0.14)))

    # --- grass
    g_dark = (0.030, 0.062, 0.014)
    g_mid = (0.062, 0.110, 0.022)
    g_yel = (0.150, 0.165, 0.038)
    g_dry = (0.24, 0.19, 0.085)
    gcol = m.mixc(m.maprange(n_mid, 0.28, 0.72), g_dark, g_mid)
    gcol = m.mixc(m.maprange(n_big, 0.48, 0.72, 0.0, 0.85), gcol, g_yel)
    gcol = m.mixc(m.maprange(n_patch, 0.58, 0.72, 0.0, 0.9), gcol, g_dry)

    # --- forest floor: leaf litter, humus, moss
    vl = m.voronoi(P, 9.0, 'F1', 1.0, ret_node=True)
    lr, lg, lb = m.sepcol(vl.outputs['Color'])
    litter = m.ramp(lr, [(0.0, (0.024, 0.016, 0.010)), (0.30, (0.055, 0.032, 0.015)), (0.62, (0.115, 0.060, 0.020)), (0.85, (0.16, 0.10, 0.04)), (1.0, (0.085, 0.060, 0.030))])
    litter2 = m.ramp(m.noise(P, 40.0, 3, 0.6), [(0.0, (0.016, 0.012, 0.008)), (1.0, (0.09, 0.058, 0.028))])
    litter = m.mixc(m.maprange(vl.outputs['Distance'], 0.15, 0.55, 0.0, 0.55), litter, litter2)
    moss = m.mixc(m.maprange(n_mid, 0.35, 0.7), (0.020, 0.040, 0.010), (0.040, 0.075, 0.016))
    litter = m.mixc(m.maprange(n_patch, 0.54, 0.68, 0.0, 0.8), litter, moss)
    # needles: darker brown specks
    gfac = m.maprange(m.math('ADD', m.math('SUBTRACT', 1.0, forest), m.math('MULTIPLY', m.math('SUBTRACT', n_big, 0.5), 0.55)), 0.42, 0.62, 0.0, 1.0, True, 'SMOOTHSTEP')
    base = m.mixc(gfac, litter, gcol)

    # grass tufts growing in the centre strip of the lane and at the margins
    weed = m.math('MULTIPLY', m.maprange(cen, 0.15, 0.8), m.maprange(m.math('ADD', m.math('MULTIPLY', n_fine, 0.6), m.math('MULTIPLY', n_mid, 0.4)), 0.50, 0.60))
    dcol = m.mixc(m.math('MULTIPLY', weed, 0.75), dcol, gcol)

    # mud in wet ruts / puddle margins
    wetm = m.math('MULTIPLY', m.maprange(wet, 0.12, 0.7, 0.0, 1.0, True, 'SMOOTHSTEP'), 0.95)
    mud_col = m.mixc(m.maprange(n_mid, 0.3, 0.7), (0.030, 0.021, 0.014), (0.058, 0.041, 0.027))
    dcol = m.mixc(wetm, dcol, mud_col)

    # dried cracks in the drying rut margins
    crk = m.voronoi(P, 7.0, 'DISTANCE_TO_EDGE', 1.0)
    crack = m.math('MULTIPLY', m.maprange(crk, 0.05, 0.0, 0.0, 1.0), m.math('MULTIPLY', m.maprange(rut, 0.15, 0.6), m.math('SUBTRACT', 1.0, wetm)))
    dcol = m.mixc(m.math('MULTIPLY', crack, 0.8), dcol, (0.040, 0.027, 0.017))

    col = m.mixc(road_m, base, dcol)

    # roughness: wet mud glossy, rest matte
    rough_dirt = m.mixf(wetm, 0.92, 0.48)
    rough = m.mixf(road_m, 0.93, rough_dirt)

    # bump: layered noise, pebbles, litter lumps
    h_soil = m.math('ADD', m.math('MULTIPLY', n_mid, 0.5), m.math('MULTIPLY', n_fine, 0.35))
    h_soil = m.math('ADD', h_soil, m.math('MULTIPLY', n_micro, 0.15))
    h_soil = m.math('ADD', h_soil, m.math('MULTIPLY', m.math('ADD', stone_mask, stone2), 0.55))
    h_wild = m.math('ADD', m.math('MULTIPLY', n_fine, 0.5), m.math('MULTIPLY', vl.outputs['Distance'], 0.5))
    h_wild = m.math('ADD', h_wild, m.math('MULTIPLY', n_micro, 0.25))
    h = m.mixf(road_m, h_wild, h_soil)
    nrm = m.bump(h, 0.9, 0.07)
    bsdf = m.principled(col, rough, normal=nrm, spec=0.35, coat=m.math('MULTIPLY', wetm, 0.22), coat_rough=0.22)
    return _reg(m.finish(bsdf))

def water():
    m = MatB('PuddleWater')
    P = m.position()
    rip = m.noise(P, 45.0, 2, 0.5)
    nrm = m.bump(rip, 0.03, 0.01)
    col = m.mixc(m.maprange(m.noise(P, 5.0, 2), 0.3, 0.7), (0.020, 0.015, 0.010), (0.045, 0.034, 0.022))
    film = m.maprange(m.noise(P, 9.0, 4, 0.6), 0.52, 0.7)
    rough = m.mixf(film, 0.03, 0.35)
    bsdf = m.principled(col, rough, normal=nrm, spec=0.5, ior=1.33)
    return _reg(m.finish(bsdf))

# ---------------------------------------------------------------- buildings
def _uvec(m, sx=1.0, sy=1.0, off=0.0):
    u, v, _ = m.sepxyz(m.uv())
    return m.combxyz(m.math('MULTIPLY', u, sx), m.math('MULTIPLY', v, sy), off), u, v

def plaster():
    m = MatB('Plaster')
    rnd = m.obj_random()
    off = m.math('MULTIPLY', rnd, 40.0)
    vec, u, v = _uvec(m, 1.0, 1.0, off)
    base = m.ramp(rnd, [(0.0, (0.50, 0.47, 0.40)), (0.35, (0.52, 0.42, 0.28)), (0.7, (0.50, 0.38, 0.30)), (1.0, (0.45, 0.45, 0.39))])
    n1 = m.noise(vec, 0.8, 4, 0.5)
    col = m.mixc(m.maprange(n1, 0.3, 0.7, 0.0, 0.25), base, (0.30, 0.25, 0.18))
    n2 = m.noise(vec, 9.0, 3, 0.55)
    col = m.mixc(m.maprange(n2, 0.35, 0.7, 0.0, 0.10), col, (0.62, 0.58, 0.50))
    # rain streaks running down from the eaves / sills
    sv = m.combxyz(m.math('MULTIPLY', u, 5.0), m.math('MULTIPLY', v, 0.45), m.math('ADD', off, 3.0))
    streak = m.maprange(m.noise(sv, 1.0, 3, 0.6), 0.5, 0.75)
    top_w = m.maprange(v, 1.0, 2.7, 0.25, 1.0)
    col = m.mixc(m.math('MULTIPLY', m.math('MULTIPLY', streak, top_w), 0.45), col, (0.20, 0.17, 0.13))
    # damp and algae near the ground, splashed mud
    low = m.maprange(v, 1.1, 0.45, 0.0, 1.0, True, 'SMOOTHSTEP')
    low = m.math('MULTIPLY', low, m.maprange(m.noise(vec, 2.0, 3, 0.6), 0.25, 0.7, 0.4, 1.0))
    alg = m.mixc(m.maprange(m.noise(vec, 4.0, 3), 0.4, 0.7), (0.17, 0.16, 0.11), (0.14, 0.15, 0.08))
    col = m.mixc(m.math('MULTIPLY', low, 0.5), col, alg)
    splash = m.maprange(v, 0.6, 0.3, 0.0, 1.0, True, 'SMOOTHSTEP')
    splash = m.math('MULTIPLY', splash, m.maprange(m.noise(vec, 7.0, 4), 0.3, 0.65))
    col = m.mixc(m.math('MULTIPLY', splash, 0.75), col, (0.07, 0.05, 0.034))
    # a few chips showing the daub, hairline cracks
    chip = m.maprange(m.noise(vec, 2.5, 5, 0.6), 0.76, 0.80)
    chip = m.math('MULTIPLY', chip, m.maprange(v, 1.8, 0.4, 0.4, 1.0))
    col = m.mixc(chip, col, (0.12, 0.085, 0.055))
    crk = m.voronoi(vec, 1.6, 'DISTANCE_TO_EDGE', 1.0)
    crack = m.maprange(crk, 0.025, 0.003, 0.0, 1.0)
    crack = m.math('MULTIPLY', crack, m.maprange(m.noise(vec, 1.2, 2), 0.5, 0.7))
    col = m.mixc(m.math('MULTIPLY', crack, 0.6), col, (0.06, 0.05, 0.04))
    h = m.math('ADD', m.math('MULTIPLY', m.noise(vec, 22.0, 4, 0.6), 0.6), m.math('MULTIPLY', n2, 0.4))
    h = m.math('SUBTRACT', h, m.math('MULTIPLY', chip, 0.6))
    h = m.math('SUBTRACT', h, m.math('MULTIPLY', crack, 0.5))
    nrm = m.bump(h, 0.8, 0.006)
    return _reg(m.finish(m.principled(col, 0.93, normal=nrm, spec=0.2)))

def _wood(name, c_dark, c_mid, c_light, grain_scale=22.0, weather=0.5, tint_rnd=0.15):
    m = MatB(name)
    rnd = m.obj_random()
    off = m.math('MULTIPLY', rnd, 50.0)
    off2 = m.attr('rnd') if False else 0.0
    u, v, _ = m.sepxyz(m.uv())
    fib = m.combxyz(m.math('MULTIPLY', u, 0.7), m.math('MULTIPLY', v, grain_scale), off)
    broad = m.combxyz(m.math('MULTIPLY', u, 0.22), m.math('MULTIPLY', v, 3.0), m.math('ADD', off, 9.0))
    g1 = m.noise(fib, 1.0, 5, 0.62, 0.3)
    g2 = m.noise(broad, 1.0, 4, 0.55)
    mix = m.math('ADD', m.math('MULTIPLY', g1, 0.6), m.math('MULTIPLY', g2, 0.4))
    col = m.ramp(mix, [(0.0, c_dark), (0.5, c_mid), (1.0, c_light)])
    # silvered, weathered surface patches
    gray = m.maprange(m.noise(broad, 2.0, 3), 0.4, 0.7, 0.0, weather)
    col = m.mixc(gray, col, (0.20, 0.18, 0.15))
    # fine cracks (checks) along the grain
    ck = m.combxyz(m.math('MULTIPLY', u, 0.12), m.math('MULTIPLY', v, 45.0), m.math('ADD', off, 21.0))
    check = m.maprange(m.noise(ck, 1.0, 1, 0.5), 0.62, 0.68)
    col = m.mixc(m.math('MULTIPLY', check, 0.8), col, (0.012, 0.008, 0.005))
    # moss / grime near the bottom of the world (uses world z)
    P = m.position()
    px, py, pz = m.sepxyz(P)
    dirt = m.maprange(pz, 1.0, 0.1, 0.0, 0.5)
    col = m.mixc(m.math('MULTIPLY', dirt, m.maprange(m.noise(P, 4.0, 3), 0.3, 0.7)), col, (0.035, 0.03, 0.02))
    h = m.math('ADD', g1, m.math('MULTIPLY', check, -0.8))
    nrm = m.bump(h, 0.7, 0.006, normal=m.bevel(0.012, 4))
    return _reg(m.finish(m.principled(col, 0.85, normal=nrm, spec=0.3)))

def timber():
    return _wood('Timber', (0.012, 0.008, 0.005), (0.036, 0.025, 0.016), (0.100, 0.080, 0.060), 26.0, 0.30)

def planks():
    return _wood('Planks', (0.034, 0.023, 0.014), (0.100, 0.070, 0.045), (0.215, 0.170, 0.125), 20.0, 0.6)

def stone():
    m = MatB('Stone')
    rnd = m.attr('rnd')
    off = m.math('MULTIPLY', rnd, 60.0)
    u, v, _ = m.sepxyz(m.uv())
    vec = m.combxyz(u, v, off)
    base = m.ramp(rnd, [(0.0, (0.095, 0.092, 0.085)), (0.25, (0.150, 0.138, 0.115)), (0.5, (0.185, 0.160, 0.120)), (0.75, (0.120, 0.112, 0.105)), (1.0, (0.205, 0.175, 0.13))])
    n1 = m.noise(vec, 6.0, 5, 0.6)
    n2 = m.noise(vec, 28.0, 4, 0.6)
    col = m.mixc(m.maprange(n1, 0.3, 0.75, 0.0, 0.55), base, (0.045, 0.042, 0.038))
    col = m.mixc(m.maprange(n2, 0.4, 0.7, 0.0, 0.25), col, (0.30, 0.27, 0.22))
    P = m.position()
    px, py, pz = m.sepxyz(P)
    # lichen and moss
    lich = m.maprange(m.noise(P, 5.0, 4, 0.6), 0.55, 0.72)
    col = m.mixc(m.math('MULTIPLY', lich, 0.7), col, (0.16, 0.17, 0.07))
    moss = m.math('MULTIPLY', m.maprange(m.noise(P, 8.0, 4, 0.6), 0.52, 0.7), m.maprange(pz, 1.6, 0.05, 0.1, 1.0))
    col = m.mixc(m.math('MULTIPLY', moss, 0.75), col, (0.025, 0.055, 0.012))
    dirt = m.maprange(pz, 0.8, 0.0, 0.0, 0.6)
    col = m.mixc(dirt, col, (0.04, 0.03, 0.02))
    h = m.math('ADD', m.math('MULTIPLY', n1, 0.5), m.math('MULTIPLY', n2, 0.5))
    nrm = m.bump(h, 0.9, 0.02, normal=m.bevel(0.02, 4))
    return _reg(m.finish(m.principled(col, 0.9, normal=nrm, spec=0.3)))

def mortar():
    m = MatB('Mortar')
    P = m.position()
    col = m.mixc(m.maprange(m.noise(P, 30.0, 3), 0.3, 0.7), (0.07, 0.065, 0.055), (0.13, 0.12, 0.10))
    nrm = m.bump(m.noise(P, 60.0, 3), 0.6, 0.03)
    return _reg(m.finish(m.principled(col, 0.95, normal=nrm, spec=0.1)))

def thatch():
    m = MatB('Thatch')
    rnd = m.obj_random()
    off = m.math('MULTIPLY', rnd, 40.0)
    u, v, _ = m.sepxyz(m.uv())
    # straw strands run down the slope (v): high frequency across u, low along v
    sv = m.combxyz(m.math('MULTIPLY', u, 38.0), m.math('MULTIPLY', v, 2.5), off)
    s1 = m.noise(sv, 1.0, 4, 0.65)
    mid = m.combxyz(m.math('MULTIPLY', u, 9.0), m.math('MULTIPLY', v, 1.2), m.math('ADD', off, 7.0))
    s2 = m.noise(mid, 1.0, 3, 0.55)
    broad = m.combxyz(m.math('MULTIPLY', u, 0.5), m.math('MULTIPLY', v, 0.5), m.math('ADD', off, 3.0))
    big = m.noise(broad, 1.0, 4, 0.55)
    gold = m.ramp(m.math('ADD', m.math('MULTIPLY', s1, 0.55), m.math('MULTIPLY', s2, 0.45)),
                  [(0.0, (0.040, 0.028, 0.014)), (0.4, (0.12, 0.082, 0.036)), (0.7, (0.21, 0.150, 0.066)), (1.0, (0.32, 0.24, 0.10))])
    aged = m.ramp(m.math('ADD', m.math('MULTIPLY', s1, 0.5), m.math('MULTIPLY', s2, 0.5)),
                  [(0.0, (0.028, 0.022, 0.016)), (0.5, (0.075, 0.058, 0.040)), (1.0, (0.15, 0.12, 0.085))])
    col = m.mixc(m.maprange(big, 0.30, 0.55), gold, aged)
    # fine layering of the laid straw (small, irregular steps rather than wide bands)
    lay = m.noise(m.combxyz(m.math('MULTIPLY', u, 2.0), m.math('MULTIPLY', v, 9.0), m.math('ADD', off, 11.0)), 1.0, 3, 0.6)
    course = m.math('SUBTRACT', lay, 0.5)
    col = m.mixc(m.maprange(lay, 0.55, 0.75, 0.0, 0.25), col, (0.03, 0.024, 0.016))
    # moss near the eaves and in the damp patches
    P = m.position()
    moss = m.maprange(m.noise(P, 1.3, 4, 0.6), 0.55, 0.72)
    moss = m.math('MULTIPLY', moss, m.maprange(v, 1.6, 0.0, 0.25, 1.0))
    col = m.mixc(m.math('MULTIPLY', moss, 0.85), col, (0.030, 0.052, 0.012))
    h = m.math('ADD', m.math('MULTIPLY', s1, 0.5), m.math('MULTIPLY', s2, 0.7))
    h = m.math('ADD', h, m.math('MULTIPLY', course, 0.6))
    nrm = m.bump(h, 1.5, 0.035)
    return _reg(m.finish(m.principled(col, 0.97, normal=nrm, spec=0.12, sheen=0.3, sheen_rough=0.5)))

def thatch_dark():
    m = MatB('ThatchDark')
    P = m.position()
    col = m.mixc(m.maprange(m.noise(P, 12.0, 4), 0.3, 0.7), (0.022, 0.016, 0.010), (0.075, 0.055, 0.035))
    nrm = m.bump(m.noise(P, 60.0, 3), 0.8, 0.03)
    return _reg(m.finish(m.principled(col, 0.97, normal=nrm, spec=0.05)))

def shingle():
    m = MatB('Shingle')
    rnd = m.attr('rnd')
    off = m.math('MULTIPLY', rnd, 90.0)
    u, v, _ = m.sepxyz(m.uv())
    gv = m.combxyz(m.math('MULTIPLY', u, 45.0), m.math('MULTIPLY', v, 3.0), off)
    gr = m.noise(gv, 1.0, 5, 0.6)
    base = m.ramp(rnd, [(0.0, (0.060, 0.045, 0.034)), (0.3, (0.105, 0.080, 0.058)), (0.6, (0.150, 0.125, 0.098)), (0.85, (0.205, 0.185, 0.155)), (1.0, (0.075, 0.062, 0.050))])
    col = m.mixc(m.maprange(gr, 0.3, 0.75, 0.0, 0.5), base, (0.03, 0.022, 0.016))
    P = m.position()
    moss = m.math('MULTIPLY', m.maprange(m.noise(P, 0.9, 4, 0.6), 0.52, 0.7), m.maprange(v, 0.34, 0.0, 0.2, 1.0))
    col = m.mixc(m.math('MULTIPLY', moss, 0.8), col, (0.028, 0.05, 0.012))
    nrm = m.bump(m.math('ADD', gr, m.math('MULTIPLY', m.noise(P, 120.0, 2), 0.3)), 0.7, 0.01, normal=m.bevel(0.008, 3))
    return _reg(m.finish(m.principled(col, 0.9, normal=nrm, spec=0.25)))

def iron():
    m = MatB('Iron')
    P = m.position()
    rust = m.maprange(m.noise(P, 22.0, 5, 0.6), 0.5, 0.65)
    col = m.mixc(rust, (0.025, 0.025, 0.028), (0.20, 0.075, 0.025))
    rough = m.mixf(rust, 0.45, 0.9)
    metal = m.mixf(rust, 0.85, 0.1)
    nrm = m.bump(m.noise(P, 90.0, 3), 0.5, 0.01)
    return _reg(m.finish(m.principled(col, rough, metal=metal, normal=nrm, spec=0.5)))

def glass():
    m = MatB('WindowGlass')
    P = m.position()
    col = m.mixc(m.maprange(m.noise(P, 3.0, 2), 0.3, 0.7), (0.008, 0.011, 0.014), (0.02, 0.026, 0.03))
    nrm = m.bump(m.noise(P, 25.0, 2), 0.1, 0.01)
    return _reg(m.finish(m.principled(col, 0.06, normal=nrm, spec=0.8)))

def straw():
    m = MatB('Straw')
    P = m.position()
    rnd = m.obj_random()
    u, v, _ = m.sepxyz(m.uv())
    vec = m.combxyz(m.math('MULTIPLY', u, 30.0), m.math('MULTIPLY', v, 3.0), m.math('MULTIPLY', rnd, 30.0))
    s1 = m.noise(vec, 1.0, 4, 0.65)
    col = m.ramp(s1, [(0.0, (0.07, 0.048, 0.022)), (0.5, (0.20, 0.14, 0.055)), (1.0, (0.36, 0.27, 0.11))])
    col = m.mixc(m.maprange(m.noise(P, 1.5, 3), 0.4, 0.7, 0.0, 0.5), col, (0.12, 0.10, 0.06))
    nrm = m.bump(s1, 1.2, 0.04)
    return _reg(m.finish(m.principled(col, 0.95, normal=nrm, spec=0.1)))



def bark(name='Bark', dark=(0.010, 0.007, 0.005), mid=(0.040, 0.030, 0.022), light=(0.120, 0.100, 0.080), scale_u=7.0, moss=0.8):
    m = MatB(name)
    rnd = m.obj_random()
    off = m.math('MULTIPLY', rnd, 40.0)
    u, v, _ = m.sepxyz(m.uv())
    f1 = m.combxyz(m.math('MULTIPLY', u, scale_u), m.math('MULTIPLY', v, 0.9), off)
    n_f = m.noise(f1, 1.0, 6, 0.62, 0.15)
    ridge = m.math('ABSOLUTE', m.math('SUBTRACT', n_f, 0.5))
    plate = m.maprange(ridge, 0.0, 0.16, 0.0, 1.0, True, 'SMOOTHSTEP')
    col = m.ramp(plate, [(0.0, dark), (0.35, mid), (1.0, light)])
    big = m.noise(m.combxyz(m.math('MULTIPLY', u, 1.2), m.math('MULTIPLY', v, 0.3), m.math('ADD', off, 5.0)), 1.0, 3, 0.5)
    col = m.mixc(m.maprange(big, 0.4, 0.7, 0.0, 0.5), col, (0.16, 0.15, 0.12))
    P = m.position()
    px, py, pz = m.sepxyz(P)
    mo = m.math('MULTIPLY', m.maprange(m.noise(P, 2.5, 4, 0.6), 0.5, 0.68), m.maprange(pz, 1.8, 0.0, 0.1, 1.0))
    col = m.mixc(m.math('MULTIPLY', mo, moss), col, (0.020, 0.045, 0.010))
    h = m.math('ADD', plate, m.math('MULTIPLY', n_f, 0.3))
    nrm = m.bump(h, 1.4, 0.035)
    return _reg(m.finish(m.principled(col, 0.95, normal=nrm, spec=0.15)))

def birch_bark():
    m = MatB('BarkBirch')
    rnd = m.obj_random()
    off = m.math('MULTIPLY', rnd, 40.0)
    u, v, _ = m.sepxyz(m.uv())
    mk = m.combxyz(m.math('MULTIPLY', u, 1.1), m.math('MULTIPLY', v, 11.0), off)
    n_m = m.noise(mk, 1.0, 4, 0.6)
    marks = m.maprange(n_m, 0.58, 0.68)
    fine = m.noise(m.combxyz(m.math('MULTIPLY', u, 9.0), m.math('MULTIPLY', v, 2.0), m.math('ADD', off, 3.0)), 1.0, 5, 0.6)
    base = m.mixc(m.maprange(fine, 0.35, 0.7, 0.0, 0.55), (0.62, 0.60, 0.55), (0.30, 0.28, 0.24))
    col = m.mixc(marks, base, (0.025, 0.022, 0.02))
    P = m.position()
    px, py, pz = m.sepxyz(P)
    dark_base = m.maprange(pz, 1.3, 0.25, 0.0, 1.0, True, 'SMOOTHSTEP')
    dark_base = m.math('MULTIPLY', dark_base, m.maprange(fine, 0.2, 0.6, 0.6, 1.0))
    col = m.mixc(dark_base, col, (0.035, 0.03, 0.026))
    mo = m.math('MULTIPLY', m.maprange(m.noise(P, 3.0, 4, 0.6), 0.5, 0.7), m.maprange(pz, 1.2, 0.0, 0.0, 1.0))
    col = m.mixc(m.math('MULTIPLY', mo, 0.8), col, (0.03, 0.05, 0.015))
    nrm = m.bump(m.math('ADD', fine, marks), 0.8, 0.012)
    return _reg(m.finish(m.principled(col, 0.8, normal=nrm, spec=0.3)))

def rope():
    m = MatB('Rope')
    u, v, _ = m.sepxyz(m.uv())
    tw = m.math('SINE', m.math('ADD', m.math('MULTIPLY', v, 90.0), m.math('MULTIPLY', u, 40.0)))
    col = m.mixc(m.maprange(tw, -1, 1), (0.09, 0.065, 0.035), (0.30, 0.22, 0.12))
    nrm = m.bump(tw, 1.0, 0.004)
    return _reg(m.finish(m.principled(col, 0.95, normal=nrm, spec=0.1)))

def sack():
    m = MatB('Sack')
    P = m.position()
    rnd = m.obj_random()
    u, v, _ = m.sepxyz(m.uv())
    weave = m.math('MULTIPLY', m.math('SINE', m.math('MULTIPLY', u, 150.0)), m.math('SINE', m.math('MULTIPLY', v, 150.0)))
    n1 = m.noise(P, 4.0, 4, 0.6)
    col = m.mixc(m.maprange(n1, 0.3, 0.7), (0.20, 0.15, 0.085), (0.34, 0.27, 0.16))
    col = m.mixc(m.maprange(weave, -1, 1, 0.0, 0.25), col, (0.12, 0.09, 0.05))
    dirt = m.maprange(m.noise(P, 9.0, 4), 0.55, 0.7, 0.0, 0.5)
    col = m.mixc(dirt, col, (0.06, 0.045, 0.03))
    nrm = m.bump(m.math('ADD', weave, m.noise(P, 18.0, 3)), 0.5, 0.004)
    return _reg(m.finish(m.principled(col, 0.97, normal=nrm, spec=0.05, sheen=0.4, sheen_rough=0.5)))

def clay():
    m = MatB('Clay')
    P = m.position()
    n1 = m.noise(P, 6.0, 4, 0.6)
    col = m.mixc(m.maprange(n1, 0.3, 0.7), (0.17, 0.075, 0.035), (0.26, 0.12, 0.055))
    gl = m.maprange(m.noise(P, 3.0, 3), 0.45, 0.6)
    col = m.mixc(m.math('MULTIPLY', gl, 0.7), col, (0.035, 0.022, 0.012))
    rough = m.mixf(gl, 0.55, 0.25)
    nrm = m.bump(m.noise(P, 40.0, 3), 0.4, 0.002)
    return _reg(m.finish(m.principled(col, rough, normal=nrm, spec=0.4)))

def muck():
    m = MatB('Muck')
    P = m.position()
    n1 = m.noise(P, 8.0, 5, 0.6)
    col = m.mixc(m.maprange(n1, 0.3, 0.7), (0.020, 0.014, 0.008), (0.060, 0.042, 0.024))
    sp = m.maprange(m.noise(P, 40.0, 2), 0.62, 0.72)
    col = m.mixc(sp, col, (0.28, 0.20, 0.08))
    nrm = m.bump(m.math('ADD', n1, m.noise(P, 50.0, 3)), 1.0, 0.03)
    return _reg(m.finish(m.principled(col, 0.8, normal=nrm, spec=0.3)))

def rock():
    m = MatB('Rock')
    P = m.position()
    rnd = m.obj_random()
    off = m.math('MULTIPLY', rnd, 30.0)
    Pv = m.vmath('ADD', P, m.combxyz(off, off, off))
    n1 = m.noise(Pv, 1.8, 5, 0.6)
    n2 = m.noise(Pv, 12.0, 5, 0.6)
    col = m.mixc(m.maprange(n1, 0.3, 0.7), (0.07, 0.068, 0.062), (0.17, 0.155, 0.13))
    col = m.mixc(m.maprange(n2, 0.4, 0.7, 0.0, 0.3), col, (0.03, 0.03, 0.028))
    px, py, pz = m.sepxyz(P)
    lich = m.maprange(m.noise(Pv, 4.0, 4, 0.6), 0.55, 0.72)
    col = m.mixc(m.math('MULTIPLY', lich, 0.6), col, (0.18, 0.19, 0.08))
    nz = m.geometry('Normal')
    nx_, ny_, nz_ = m.sepxyz(nz)
    top = m.maprange(nz_, 0.3, 0.9)
    mos = m.math('MULTIPLY', m.maprange(m.noise(Pv, 3.0, 4, 0.6), 0.42, 0.62), m.math('ADD', 0.35, m.math('MULTIPLY', top, 0.65)))
    col = m.mixc(m.math('MULTIPLY', mos, 0.85), col, (0.022, 0.05, 0.011))
    nrm = m.bump(m.math('ADD', m.math('MULTIPLY', n2, 0.6), m.math('MULTIPLY', n1, 0.5)), 1.1, 0.05)
    return _reg(m.finish(m.principled(col, 0.92, normal=nrm, spec=0.25)))

def leather():
    m = MatB('Leather')
    P = m.position()
    n1 = m.noise(P, 14.0, 4, 0.6)
    col = m.mixc(m.maprange(n1, 0.3, 0.7), (0.030, 0.018, 0.010), (0.085, 0.050, 0.028))
    nrm = m.bump(m.math('ADD', n1, m.noise(P, 60.0, 3)), 0.6, 0.004)
    return _reg(m.finish(m.principled(col, 0.55, normal=nrm, spec=0.4)))

def make_building_mats():
    return [plaster(), timber(), stone(), thatch(), thatch_dark(), glass(), iron(), planks(), mortar(), shingle(), straw(),
            bark(), rope(), sack(), clay(), muck(), rock(), leather()]


# ---------------------------------------------------------------- vegetation
def leaf(name='Leaf', birch=False):
    m = MatB(name)
    rnd = m.attr('rnd'); hgt = m.attr('hgt'); orand = m.obj_random()
    u, v, _ = m.sepxyz(m.uv())
    if not birch:
        greens = m.ramp(rnd, [(0.0, (0.016, 0.046, 0.008)), (0.5, (0.034, 0.082, 0.012)), (1.0, (0.062, 0.120, 0.017))])
    else:
        greens = m.ramp(rnd, [(0.0, (0.04, 0.09, 0.012)), (0.5, (0.07, 0.13, 0.02)), (1.0, (0.11, 0.17, 0.03))])
    col = m.mixc(m.maprange(hgt, 0.3, 1.2, 0.0, 0.6), greens, (0.10, 0.13, 0.028))
    aut = m.maprange(orand, 0.93, 0.95, 0.0, 1.0)
    autcol = m.ramp(rnd, [(0.0, (0.14, 0.065, 0.008)), (0.5, (0.20, 0.13, 0.014)), (1.0, (0.22, 0.19, 0.03))])
    col = m.mixc(m.math('MULTIPLY', aut, m.maprange(rnd, 0.1, 0.45)), col, autcol)
    mid = m.maprange(m.math('ABSOLUTE', m.math('SUBTRACT', u, 0.5)), 0.06, 0.0, 0.0, 1.0)
    col = m.mixc(m.math('MULTIPLY', mid, 0.35), col, (0.12, 0.16, 0.04))
    edge = m.maprange(m.math('ABSOLUTE', m.math('SUBTRACT', u, 0.5)), 0.3, 0.5, 0.0, 0.5)
    col = m.mixc(edge, col, (0.02, 0.04, 0.008))
    d = m.principled(col, 0.55, spec=0.25)
    t = m.translucent(m.hsv(col, 0.5, 1.0, 1.6))
    return _reg(m.finish(m.mixsh(0.42, d.outputs[0], t)))

def needles():
    m = MatB('Needles')
    orand = m.obj_random()
    u, v, _ = m.sepxyz(m.uv())
    c = m.math('MULTIPLY', m.math('ABSOLUTE', m.math('SUBTRACT', v, 0.5)), 2.0)
    wid = m.math('ADD', m.math('MULTIPLY', m.math('SINE', m.math('MULTIPLY', m.math('POWER', m.maprange(u, 0.0, 1.0, 0.02, 0.98), 0.7), 3.14159)), 0.95), 0.05)
    outline = m.maprange(m.math('SUBTRACT', wid, c), 0.0, 0.12)
    q = m.math('ADD', m.math('MULTIPLY', u, 26.0), m.math('MULTIPLY', c, 8.0))
    nz = m.noise(m.combxyz(m.math('MULTIPLY', u, 14.0), m.math('MULTIPLY', c, 6.0), m.math('MULTIPLY', orand, 20.0)), 1.0, 3, 0.6)
    line = m.maprange(m.math('ADD', m.math('SINE', m.math('MULTIPLY', q, 6.28318)), m.math('MULTIPLY', m.math('SUBTRACT', nz, 0.5), 1.1)), 0.15, 0.55)
    spine = m.maprange(c, 0.09, 0.03)
    alpha_ = m.math('MULTIPLY', outline, m.math('MAXIMUM', line, spine))
    alpha_ = m.maprange(alpha_, 0.45, 0.55)
    col = m.mixc(m.maprange(c, 0.1, 0.9), (0.012, 0.034, 0.016), (0.05, 0.095, 0.035))
    col = m.mixc(m.maprange(nz, 0.3, 0.8, 0.0, 0.5), col, (0.07, 0.11, 0.035))
    d = m.principled(col, 0.6, spec=0.2)
    t = m.translucent(col)
    surf = m.mixsh(0.3, d.outputs[0], t)
    return _reg(m.finish(m.mixsh(alpha_, m.transparent(), surf)))

def grass_mat():
    m = MatB('Grass')
    rnd = m.attr('rnd'); tip = m.attr('tip')
    green_b = m.mixc(m.maprange(rnd, 0.0, 0.7), (0.012, 0.035, 0.006), (0.030, 0.062, 0.010))
    green_t = m.mixc(m.maprange(rnd, 0.0, 0.7), (0.07, 0.12, 0.02), (0.16, 0.20, 0.035))
    dry_b = (0.085, 0.065, 0.025)
    dry_t = (0.32, 0.25, 0.09)
    dry = m.maprange(rnd, 0.78, 0.9)
    base = m.mixc(dry, green_b, dry_b)
    topc = m.mixc(dry, green_t, dry_t)
    col = m.mixc(m.maprange(tip, 0.0, 0.9, 0.0, 1.0, True, 'SMOOTHSTEP'), base, topc)
    d = m.principled(col, 0.6, spec=0.2)
    t = m.translucent(m.hsv(col, 0.5, 1.0, 1.5))
    return _reg(m.finish(m.mixsh(0.35, d.outputs[0], t)))

def fern_mat():
    m = MatB('Fern')
    rnd = m.attr('rnd'); orand = m.obj_random()
    col = m.mixc(m.maprange(rnd, 0.0, 1.0), (0.020, 0.062, 0.010), (0.055, 0.125, 0.018))
    col = m.mixc(m.maprange(orand, 0.8, 1.0, 0.0, 0.5), col, (0.13, 0.12, 0.025))
    d = m.principled(col, 0.55, spec=0.2)
    t = m.translucent(m.hsv(col, 0.5, 1.0, 1.5))
    return _reg(m.finish(m.mixsh(0.4, d.outputs[0], t)))

def leaf_dry():
    m = MatB('LeafDry')
    rnd = m.attr('rnd')
    col = m.ramp(rnd, [(0.0, (0.060, 0.030, 0.008)), (0.4, (0.13, 0.065, 0.014)), (0.75, (0.20, 0.12, 0.03)), (1.0, (0.09, 0.07, 0.03))])
    return _reg(m.finish(m.principled(col, 0.8, spec=0.2)))

def flower_mat():
    m = MatB('Flower')
    rnd = m.attr('rnd')
    col = m.ramp(rnd, [(0.0, (0.80, 0.78, 0.70)), (0.25, (0.78, 0.60, 0.04)), (0.5, (0.30, 0.16, 0.45)), (0.75, (0.62, 0.20, 0.26)), (0.97, (0.8, 0.7, 0.05)), (1.0, (0.9, 0.5, 0.02))], 'CONSTANT')
    d = m.principled(col, 0.6, spec=0.2)
    t = m.translucent(col)
    return _reg(m.finish(m.mixsh(0.3, d.outputs[0], t)))

def make_plant_mats():
    b = MATS.get('Bark') or bark()
    return [b, leaf('Leaf'), needles(), birch_bark(), grass_mat(), fern_mat(), leaf('LeafBirch', True), leaf_dry(), flower_mat()]
