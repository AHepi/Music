"""Procedural materials for buildings and props."""
import bpy
import common as C
from common import NB, new_material
from materials import hexc, srgb


def _wood(name, light, dark, grain_scale=3.0, rough=0.78, moss=0.0, grey=0.0, bump=0.35, crack=True):
    m = new_material(name)
    nb = NB(m.node_tree)
    uv = nb.texcoord('UV')
    obj = nb.texcoord('Object')
    rnd = nb.attr('rnd')
    # per-part offset so neighbouring boards differ
    off = nb.comb(nb.math('MULTIPLY', rnd, 37.0), nb.math('MULTIPLY', rnd, 11.0), nb.math('MULTIPLY', rnd, 5.0))
    uvo = nb.vmath('ADD', uv, off)
    sx, sy, sz = nb.sep(uvo)
    # grain: stretched along U (the long axis)
    gvec = nb.comb(nb.math('MULTIPLY', sx, 0.35), nb.math('MULTIPLY', sy, 9.0), 0.0)
    grain = nb.noise(gvec, scale=grain_scale, detail=8, rough=0.62, distortion=0.5)
    fine = nb.noise(nb.comb(nb.math('MULTIPLY', sx, 1.5), nb.math('MULTIPLY', sy, 60.0), 0.0), scale=2.0, detail=3)
    col = nb.ramp(grain, [(0.3, dark), (0.7, light)])
    col = nb.mix(nb.maprange(fine, 0.4, 0.7, 0.0, 0.25), col, dark)
    # per-board tone
    col = nb.hsv(col, h=nb.math('ADD', 0.49, nb.math('MULTIPLY', rnd, 0.02)), s=nb.math('ADD', 0.8, nb.math('MULTIPLY', rnd, 0.35)), v=nb.math('ADD', 0.78, nb.math('MULTIPLY', rnd, 0.45)))
    h = nb.math('ADD', nb.math('MULTIPLY', grain, 0.6), nb.math('MULTIPLY', fine, 0.25))
    if crack:
        cr = nb.noise(nb.comb(nb.math('MULTIPLY', sx, 0.6), nb.math('MULTIPLY', sy, 22.0), 0.0), scale=1.5, detail=2)
        crm = nb.maprange(cr, 0.68, 0.72, 0.0, 1.0)
        col = nb.mix(nb.math('MULTIPLY', crm, 0.85), col, hexc('17120e'))
        h = nb.math('SUBTRACT', h, nb.math('MULTIPLY', crm, 0.8))
    if grey > 0:
        gw = nb.maprange(nb.noise(obj, scale=1.2, detail=3), 0.3, 0.7, grey * 0.5, grey)
        col = nb.mix(gw, col, hexc('7a7670'))
    if moss > 0:
        mz = nb.sep(nb.geometry('Normal'))[2]
        mm = nb.math('MULTIPLY', nb.maprange(mz, 0.2, 0.9, 0.0, 1.0), nb.maprange(nb.noise(obj, scale=2.5, detail=4), 0.5, 0.65, 0.0, moss))
        col = nb.mix(mm, col, hexc('4b5a24'))
    bmp = nb.bump(h, strength=bump, distance=0.004)
    bsdf = nb.principled(Base_Color=col, Roughness=rough, Normal=bmp)
    nb.set(bsdf, 'Specular IOR Level', 0.35)
    nb.output(bsdf)
    return m


def mat_daub():
    m = new_material("daub_limewash")
    nb = NB(m.node_tree)
    obj = nb.texcoord('Object')
    pos = nb.geometry('Position')
    n1 = nb.noise(obj, scale=1.5, detail=6, rough=0.6)
    n2 = nb.noise(obj, scale=12.0, detail=4, rough=0.6)
    n3 = nb.noise(obj, scale=40.0, detail=2)
    wash = nb.ramp(n1, [(0.3, hexc('cfc5ad')), (0.6, hexc('ddd5c2')), (0.8, hexc('c9bea4'))])
    # worn patches showing the ochre daub beneath
    worn = nb.maprange(nb.noise(obj, scale=2.2, detail=6, rough=0.65), 0.62, 0.68, 0.0, 1.0)
    daub = nb.mix(nb.maprange(n2, 0.3, 0.7), hexc('8c7454'), hexc('a38a63'))
    col = nb.mix(worn, wash, daub)
    # splash dirt near the ground and streaks under the eaves
    pz = nb.sep(pos)[2]
    gz = nb.sep(obj)[2]
    dirt = nb.maprange(gz, 1.3, 0.6, 0.0, 0.75)
    dirt = nb.math('MULTIPLY', dirt, nb.maprange(nb.noise(obj, scale=4.0, detail=5), 0.3, 0.7, 0.5, 1.0))
    col = nb.mix(dirt, col, hexc('6e6250'))
    streak = nb.noise(nb.mapping(obj, scale=(6.0, 6.0, 0.4)), scale=3.0, detail=3)
    col = nb.mix(nb.maprange(streak, 0.55, 0.75, 0.0, 0.35), col, hexc('968a72'))
    # grime collects in the corners against the timbers
    ao = nb.node('ShaderNodeAmbientOcclusion', samples=8)
    nb.set(ao, 'Distance', 0.12)
    aov = nb.out(ao, 'AO')
    col = nb.mix(nb.maprange(aov, 0.35, 0.95, 0.75, 0.0), col, hexc('7a6c56'))
    col = nb.hsv(col, v=0.92)
    h = nb.math('ADD', nb.math('MULTIPLY', n2, 0.5), nb.math('MULTIPLY', n3, 0.2))
    h = nb.math('SUBTRACT', h, nb.math('MULTIPLY', worn, 0.3))
    bmp = nb.bump(h, strength=0.35, distance=0.01)
    bsdf = nb.principled(Base_Color=col, Roughness=0.93, Normal=bmp)
    nb.set(bsdf, 'Specular IOR Level', 0.3)
    nb.output(bsdf)
    return m


def mat_stone():
    m = new_material("stone_field")
    nb = NB(m.node_tree)
    obj = nb.texcoord('Object')
    rnd = nb.attr('rnd')
    n1 = nb.noise(obj, scale=6.0, detail=6, rough=0.6)
    n2 = nb.noise(obj, scale=30.0, detail=3)
    tone = nb.ramp(rnd, [(0.0, hexc('6e6a62')), (0.15, hexc('8a8172')), (0.3, hexc('7d6a52')), (0.45, hexc('9a9282')), (0.6, hexc('5f6266')), (0.72, hexc('8f7a5c')), (0.86, hexc('a39b8a')), (1.0, hexc('6b5f50'))], interp='CONSTANT')
    col = nb.mix(nb.maprange(n1, 0.3, 0.7, 0.0, 0.5), tone, hexc('5a554d'))
    lich = nb.maprange(nb.noise(obj, scale=9.0, detail=3), 0.6, 0.66, 0.0, 0.8)
    col = nb.mix(lich, col, hexc('b5ad8a'))
    nz = nb.sep(nb.geometry('Normal'))[2]
    moss = nb.math('MULTIPLY', nb.maprange(nz, 0.3, 0.9, 0.0, 1.0), nb.maprange(nb.noise(obj, scale=3.0, detail=4), 0.5, 0.62, 0.0, 0.85))
    col = nb.mix(moss, col, hexc('4a5a22'))
    gz = nb.sep(obj)[2]
    col = nb.mix(nb.maprange(gz, 0.6, 0.0, 0.0, 0.5), col, hexc('4a4035'))
    h = nb.math('ADD', n1, nb.math('MULTIPLY', n2, 0.5))
    bmp = nb.bump(h, strength=0.5, distance=0.02)
    bsdf = nb.principled(Base_Color=col, Roughness=0.85, Normal=bmp)
    nb.output(bsdf)
    return m


def mat_mortar():
    m = new_material("mortar_lime")
    nb = NB(m.node_tree)
    obj = nb.texcoord('Object')
    n = nb.noise(obj, scale=20.0, detail=4)
    col = nb.mix(nb.maprange(n, 0.3, 0.7), hexc('6f685c'), hexc('857c6c'))
    gz = nb.sep(obj)[2]
    col = nb.mix(nb.maprange(gz, 0.8, 0.0, 0.0, 0.6), col, hexc('5a5045'))
    bmp = nb.bump(n, strength=0.6, distance=0.01)
    bsdf = nb.principled(Base_Color=col, Roughness=0.95, Normal=bmp)
    nb.output(bsdf)
    return m


def mat_thatch(name="thatch", fresh=0.0):
    """Aged thatch: straw strands along the slope (UV v), bundles, fixing courses, grey weathering and moss."""
    m = new_material(name)
    nb = NB(m.node_tree)
    uv = nb.texcoord('UV')
    obj = nb.texcoord('Object')
    eave = nb.attr('eave')
    sx, sy, sz = nb.sep(uv)
    # bundles: elongated cells along the slope
    bvec = nb.comb(nb.math('MULTIPLY', sx, 6.0), nb.math('MULTIPLY', sy, 1.1), 0.0)
    bund = nb.voronoi(bvec, scale=1.0, feature='F1', which='Color')
    bund_d = nb.voronoi(bvec, scale=1.0, feature='DISTANCE_TO_EDGE', which='Distance')
    brnd = nb.noise(bund, scale=3.0, detail=0)
    # strands at two scales, offset per bundle
    off = nb.vmath('MULTIPLY', bund, (3.0, 3.0, 3.0))
    svec = nb.vmath('ADD', nb.comb(nb.math('MULTIPLY', sx, 70.0), nb.math('MULTIPLY', sy, 2.0), 0.0), off)
    strands = nb.noise(svec, scale=1.0, detail=6, rough=0.65, distortion=0.3)
    svec2 = nb.comb(nb.math('MULTIPLY', sx, 190.0), nb.math('MULTIPLY', sy, 4.5), 0.0)
    strands2 = nb.noise(svec2, scale=1.0, detail=3, rough=0.5)
    # fixing courses (sways) across the slope every ~0.28 m
    course = nb.wave(nb.comb(sx, nb.math('ADD', sy, nb.math('MULTIPLY', brnd, 0.08)), 0.0), scale=3.6, distortion=0.0, detail=0, wtype='BANDS', direction='Y', profile='SAW')
    big = nb.noise(obj, scale=0.5, detail=4, rough=0.6)
    col = nb.ramp(strands, [(0.25, hexc('3d3428')), (0.45, hexc('6c5c42')), (0.62, hexc('8c7852')), (0.8, hexc('a68f60'))])
    col = nb.mix(nb.maprange(strands2, 0.55, 0.8, 0.0, 0.4), col, hexc('b09a68'))
    col = nb.hsv(col, v=nb.math('ADD', 0.8, nb.math('MULTIPLY', brnd, 0.4)))
    # soft darkening between bundles, irregular fixing courses
    gaps = nb.maprange(bund_d, 0.0, 0.05, 1.0, 0.0)
    col = nb.mix(nb.math('MULTIPLY', gaps, 0.18), col, hexc('2a241b'))
    cmask = nb.maprange(nb.noise(obj, scale=0.8, detail=2), 0.45, 0.6, 0.0, 1.0)
    col = nb.mix(nb.math('MULTIPLY', nb.maprange(course, 0.9, 1.0, 0.0, 0.2), cmask), col, hexc('3a3125'))
    # grey weathering
    col = nb.mix(nb.maprange(big, 0.35, 0.7, 0.0, 0.4 * (1 - fresh)), col, hexc('6a645a'))
    if fresh > 0:
        col = nb.mix(fresh, col, nb.ramp(strands, [(0.3, hexc('6e5a36')), (0.6, hexc('a08550')), (0.8, hexc('b89a5e'))]))
    # moss in clumps, mostly lower on the roof
    low = nb.maprange(sy, 0.2, 2.2, 1.0, 0.15)
    mclump = nb.maprange(nb.noise(obj, scale=1.4, detail=5, rough=0.6), 0.5, 0.64, 0.0, 1.0)
    moss = nb.math('MULTIPLY', nb.math('MULTIPLY', low, mclump), 0.7 * (1 - fresh))
    mosscol = nb.mix(nb.maprange(nb.noise(obj, scale=8.0, detail=3), 0.3, 0.7), hexc('3f4a1e'), hexc('5f6a2c'))
    col = nb.mix(moss, col, mosscol)
    col = nb.mix(nb.math('MULTIPLY', nb.maprange(sy, 0.0, 0.6, 1.0, 0.0), 0.3), col, hexc('2e2920'))
    # cut eave face: stippled straw ends
    ends = nb.voronoi(obj, scale=150.0, feature='F1', which='Distance')
    endsc = nb.voronoi(obj, scale=150.0, feature='F1', which='Color')
    endcol = nb.mix(nb.maprange(ends, 0.05, 0.45), hexc('1e1a14'), nb.mix(nb.noise(endsc, scale=4.0, detail=0), hexc('6c5c40'), hexc('8a7650')))
    col = nb.mix(eave, col, endcol)
    h = nb.math('ADD', nb.math('MULTIPLY', strands, 0.55), nb.math('MULTIPLY', strands2, 0.25))
    h = nb.math('ADD', h, nb.math('MULTIPLY', brnd, 0.3))
    h = nb.math('SUBTRACT', h, nb.math('MULTIPLY', nb.maprange(course, 0.9, 1.0, 0.0, 0.2), cmask))
    h = nb.math('ADD', h, nb.math('MULTIPLY', moss, 0.25))
    h = nb.mix(eave, h, nb.math('MULTIPLY', ends, 1.5), dtype='FLOAT')
    bmp = nb.bump(h, strength=1.0, distance=0.025)
    bsdf = nb.principled(Base_Color=col, Roughness=0.92, Normal=bmp)
    nb.set(bsdf, 'Specular IOR Level', 0.28)
    nb.set(bsdf, 'Sheen Weight', 0.3)
    nb.output(bsdf)
    return m


def mat_logs():
    m = new_material("firewood")
    nb = NB(m.node_tree)
    uv = nb.texcoord('UV')
    obj = nb.texcoord('Object')
    cap = nb.attr('cap')
    rnd = nb.attr('rnd')
    sx, sy, sz = nb.sep(uv)
    # bark on the sides
    bvec = nb.comb(nb.math('MULTIPLY', sx, 12.0), nb.math('MULTIPLY', sy, 2.0), 0.0)
    bark_n = nb.noise(bvec, scale=3.0, detail=6, rough=0.65)
    bark = nb.ramp(bark_n, [(0.3, hexc('2b231c')), (0.6, hexc('4d4033')), (0.8, hexc('6b5c4a'))])
    # split faces show pale wood (sides with small UV height are split faces -> use noise mask instead)
    split = nb.maprange(nb.noise(nb.comb(sx, nb.math('MULTIPLY', sy, 0.3), 0.0), scale=2.0, detail=2), 0.5, 0.52, 0.0, 1.0)
    pale = nb.ramp(nb.noise(nb.comb(nb.math('MULTIPLY', sx, 3.0), nb.math('MULTIPLY', sy, 30.0), 0), scale=2.0, detail=4), [(0.3, hexc('8a7254')), (0.7, hexc('a88d68'))])
    side = nb.mix(nb.math('MULTIPLY', split, 0.3), bark, pale)
    # end grain: rings from the cap UV radius
    rad = nb.vmath('LENGTH', nb.comb(sx, sy, 0.0))
    rings = nb.wave(nb.comb(sx, sy, 0.0), scale=1.0, wtype='RINGS', direction='SPHERICAL', distortion=1.5, detail=2, dscale=2.0)
    endc = nb.mix(nb.maprange(rings, 0.3, 0.9), hexc('9a7f5c'), hexc('c2a77f'))
    endc = nb.mix(nb.maprange(rad, 0.85, 1.0, 0.0, 1.0), endc, hexc('3a2e22'))
    endc = nb.mix(nb.maprange(nb.noise(obj, scale=30.0, detail=2), 0.6, 0.7, 0.0, 0.5), endc, hexc('5a4630'))
    col = nb.mix(cap, side, endc)
    col = nb.hsv(col, v=nb.math('ADD', 0.8, nb.math('MULTIPLY', rnd, 0.4)))
    h = nb.mix(cap, bark_n, nb.math('MULTIPLY', rings, 0.3), dtype='FLOAT')
    bsdf = nb.principled(Base_Color=col, Roughness=0.85, Normal=nb.bump(h, 0.5, 0.005))
    nb.output(bsdf)
    return m


def mat_withy():
    m = new_material("withy_hazel")
    nb = NB(m.node_tree)
    uv = nb.texcoord('UV')
    obj = nb.texcoord('Object')
    rnd = nb.attr('rnd')
    sx, sy, sz = nb.sep(uv)
    n = nb.noise(nb.comb(nb.math('MULTIPLY', sx, 20.0), nb.math('MULTIPLY', sy, 3.0), 0), scale=2.0, detail=5)
    col = nb.ramp(n, [(0.3, hexc('3b3128')), (0.6, hexc('5a4b3b')), (0.85, hexc('6e6253'))])
    col = nb.hsv(col, v=nb.math('ADD', 0.75, nb.math('MULTIPLY', rnd, 0.5)))
    lich = nb.maprange(nb.noise(obj, scale=6.0, detail=3), 0.6, 0.68, 0.0, 0.6)
    col = nb.mix(lich, col, hexc('8a8a6a'))
    bsdf = nb.principled(Base_Color=col, Roughness=0.7, Normal=nb.bump(n, 0.3, 0.003))
    nb.output(bsdf)
    return m


def mat_muck():
    m = new_material("muck_heap")
    nb = NB(m.node_tree)
    obj = nb.texcoord('Object')
    n1 = nb.noise(obj, scale=4.0, detail=6)
    n2 = nb.noise(nb.mapping(obj, scale=(1, 1, 1)), scale=30.0, detail=4, distortion=1.0)
    col = nb.ramp(n1, [(0.3, hexc('1e1610')), (0.6, hexc('3a2c1e')), (0.8, hexc('4f4026'))])
    straw = nb.maprange(n2, 0.6, 0.7, 0.0, 0.7)
    col = nb.mix(straw, col, hexc('8a7448'))
    bsdf = nb.principled(Base_Color=col, Roughness=nb.maprange(n1, 0.3, 0.7, 0.45, 0.85), Normal=nb.bump(nb.math('ADD', n1, n2), 0.6, 0.02))
    nb.output(bsdf)
    return m


def mat_soil():
    m = new_material("garden_soil")
    nb = NB(m.node_tree)
    obj = nb.texcoord('Object')
    n1 = nb.noise(obj, scale=3.0, detail=6)
    n2 = nb.noise(obj, scale=40.0, detail=3)
    col = nb.mix(nb.maprange(n1, 0.3, 0.7), hexc('2e2219'), hexc('45362a'))
    col = nb.mix(nb.maprange(n2, 0.6, 0.75, 0.0, 0.4), col, hexc('5a4a3a'))
    bsdf = nb.principled(Base_Color=col, Roughness=0.95, Normal=nb.bump(nb.math('ADD', n1, n2), 0.6, 0.02))
    nb.output(bsdf)
    return m


def mat_iron():
    m = new_material("iron_rusty")
    nb = NB(m.node_tree)
    obj = nb.texcoord('Object')
    n = nb.noise(obj, scale=25.0, detail=6)
    rust = nb.maprange(nb.noise(obj, scale=8.0, detail=5), 0.45, 0.65, 0.0, 1.0)
    col = nb.mix(rust, hexc('2a2826'), hexc('5c3a22'))
    bsdf = nb.principled(Base_Color=col, Roughness=nb.maprange(rust, 0.0, 1.0, 0.5, 0.9), Metallic=nb.maprange(rust, 0.0, 1.0, 0.7, 0.1), Normal=nb.bump(n, 0.3, 0.003))
    nb.output(bsdf)
    return m


def mat_straw():
    m = new_material("straw_hay")
    nb = NB(m.node_tree)
    obj = nb.texcoord('Object')
    n1 = nb.noise(nb.mapping(obj, scale=(1.0, 1.0, 1.0)), scale=40.0, detail=5, rough=0.6, distortion=1.2)
    n2 = nb.noise(obj, scale=3.0, detail=4)
    col = nb.ramp(n1, [(0.3, hexc('6e5a32')), (0.55, hexc('a88f55')), (0.75, hexc('c9b070'))])
    col = nb.mix(nb.maprange(n2, 0.3, 0.7, 0.0, 0.5), col, hexc('7d6a45'))
    bsdf = nb.principled(Base_Color=col, Roughness=0.8, Normal=nb.bump(n1, 0.6, 0.01))
    nb.set(bsdf, 'Sheen Weight', 0.3)
    nb.output(bsdf)
    return m


def mat_strands():
    """For hair-like straw strands (mesh strips with a 'col' attribute)."""
    m = new_material("straw_strands")
    nb = NB(m.node_tree)
    col = nb.attr('col', 'Color')
    rnd = nb.objinfo('Random')
    bsdf = nb.principled(Base_Color=nb.hsv(col, v=nb.math('ADD', 0.85, nb.math('MULTIPLY', rnd, 0.3))), Roughness=0.7)
    nb.set(bsdf, 'Specular IOR Level', 0.3)
    tr = nb.node('ShaderNodeBsdfTranslucent')
    nb.set(tr, 'Color', col)
    mix = nb.node('ShaderNodeMixShader')
    nb.set(mix, 'Fac', 0.2)
    nb.links.new(bsdf.outputs[0], mix.inputs[1])
    nb.links.new(tr.outputs[0], mix.inputs[2])
    nb.output(mix)
    return m


def mat_interior():
    m = new_material("interior_dark")
    nb = NB(m.node_tree)
    obj = nb.texcoord('Object')
    n = nb.noise(obj, scale=3.0, detail=4)
    col = nb.mix(n, hexc('2a2219'), hexc('3b3024'))
    bsdf = nb.principled(Base_Color=col, Roughness=0.9)
    nb.output(bsdf)
    return m


def mat_earth_floor():
    m = new_material("earth_floor")
    nb = NB(m.node_tree)
    obj = nb.texcoord('Object')
    n = nb.noise(obj, scale=4.0, detail=6)
    col = nb.mix(n, hexc('3d3126'), hexc('56463a'))
    bsdf = nb.principled(Base_Color=col, Roughness=0.95, Normal=nb.bump(nb.noise(obj, scale=30.0, detail=3), 0.3, 0.01))
    nb.output(bsdf)
    return m


def mat_rope():
    m = new_material("rope")
    nb = NB(m.node_tree)
    uv = nb.texcoord('UV')
    sx, sy, sz = nb.sep(uv)
    tw = nb.wave(nb.comb(nb.math('ADD', sx, nb.math('MULTIPLY', sy, 1.0)), sy, 0), scale=60.0, wtype='BANDS', direction='X')
    col = nb.mix(tw, hexc('6b5a3c'), hexc('9a8660'))
    bsdf = nb.principled(Base_Color=col, Roughness=0.85, Normal=nb.bump(tw, 0.5, 0.004))
    nb.output(bsdf)
    return m


def mat_burlap():
    m = new_material("burlap")
    nb = NB(m.node_tree)
    obj = nb.texcoord('Object')
    w1 = nb.wave(obj, scale=120.0, wtype='BANDS', direction='X')
    w2 = nb.wave(obj, scale=120.0, wtype='BANDS', direction='Z')
    weave = nb.math('MULTIPLY', w1, w2)
    n = nb.noise(obj, scale=5.0, detail=4)
    col = nb.mix(nb.maprange(n, 0.3, 0.7), hexc('8a7656'), hexc('a8946c'))
    col = nb.mix(nb.math('MULTIPLY', weave, 0.3), col, hexc('5e4f38'))
    gz = nb.sep(obj)[2]
    col = nb.mix(nb.maprange(gz, 0.15, 0.0, 0.0, 0.6), col, hexc('4a3f30'))
    bsdf = nb.principled(Base_Color=col, Roughness=0.95, Normal=nb.bump(weave, 0.4, 0.003))
    nb.set(bsdf, 'Sheen Weight', 0.4)
    nb.output(bsdf)
    return m


def mat_clay():
    m = new_material("clay_pot")
    nb = NB(m.node_tree)
    obj = nb.texcoord('Object')
    n = nb.noise(obj, scale=6.0, detail=5)
    col = nb.mix(nb.maprange(n, 0.3, 0.7), hexc('8a5a3a'), hexc('a46e48'))
    col = nb.mix(nb.maprange(nb.noise(obj, scale=2.0, detail=3), 0.55, 0.7, 0.0, 0.6), col, hexc('4a3a2a'))
    bsdf = nb.principled(Base_Color=col, Roughness=0.75, Normal=nb.bump(nb.noise(obj, scale=40.0), 0.2, 0.003))
    nb.output(bsdf)
    return m


def mat_water_still():
    m = new_material("water_still")
    nb = NB(m.node_tree)
    obj = nb.texcoord('Object')
    bsdf = nb.principled(Base_Color=hexc('15130f'), Roughness=0.02, IOR=1.33, Normal=nb.bump(nb.noise(obj, scale=8.0), 0.02, 0.01))
    nb.output(bsdf)
    return m


def mat_glow():
    m = new_material("hearth_glow")
    nb = NB(m.node_tree)
    em = nb.node('ShaderNodeEmission')
    nb.set(em, 'Color', srgb(1.0, 0.55, 0.22))
    nb.set(em, 'Strength', 6.0)
    nb.output(em)
    return m


def build_all():
    mats = {
        "timber": _wood("wood_timber", hexc('6d5f4e'), hexc('3a3128'), grain_scale=2.5, rough=0.82, grey=0.55, bump=0.45),
        "plank": _wood("wood_planks", hexc('7c6a54'), hexc('43372b'), grain_scale=3.0, rough=0.8, grey=0.45, bump=0.35),
        "plank_dark": _wood("wood_planks_dark", hexc('5a4a3a'), hexc('2c241c'), grain_scale=3.0, rough=0.75, grey=0.2, bump=0.3),
        "shingle": _wood("wood_shingles", hexc('7a7468'), hexc('3e3a33'), grain_scale=4.0, rough=0.85, moss=0.8, grey=0.75, bump=0.5),
        "fresh": _wood("wood_fresh", hexc('a88e68'), hexc('6a5338'), grain_scale=3.0, rough=0.7, grey=0.1, bump=0.3, crack=False),
        "daub": mat_daub(),
        "stone": mat_stone(),
        "mortar": mat_mortar(),
        "thatch": mat_thatch(),
        "thatch_ridge": mat_thatch("thatch_ridge", fresh=0.45),
        "iron": mat_iron(),
        "straw": mat_straw(),
        "strands": mat_strands(),
        "interior": mat_interior(),
        "floor": mat_earth_floor(),
        "rope": mat_rope(),
        "burlap": mat_burlap(),
        "clay": mat_clay(),
        "water": mat_water_still(),
        "glow": mat_glow(),
        "logs": mat_logs(),
        "withy": mat_withy(),
        "muck": mat_muck(),
        "soil": mat_soil(),
    }
    mats["hazel"] = mats["fresh"]
    return mats
