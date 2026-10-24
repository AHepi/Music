"""Procedural materials for buildings and props."""
import bpy
import common as C
from common import NB, new_material
from materials import hexc, srgb


def _wood(name, light, dark, grain_scale=3.0, rough=0.78, moss=0.0, grey=0.0, bump=0.35, crack=True, weather=1.0, lichen=0.0, tb=0.78, tv=0.45):
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
    col = nb.hsv(col, h=nb.math('ADD', 0.49, nb.math('MULTIPLY', rnd, 0.02)), s=nb.math('ADD', 0.8, nb.math('MULTIPLY', rnd, 0.35)), v=nb.math('ADD', tb, nb.math('MULTIPLY', rnd, tv)))
    h = nb.math('ADD', nb.math('MULTIPLY', grain, 0.6), nb.math('MULTIPLY', fine, 0.25))
    if crack:
        cr = nb.noise(nb.comb(nb.math('MULTIPLY', sx, 0.6), nb.math('MULTIPLY', sy, 22.0), 0.0), scale=1.5, detail=2)
        crm = nb.maprange(cr, 0.68, 0.72, 0.0, 1.0)
        col = nb.mix(nb.math('MULTIPLY', crm, 0.85), col, hexc('17120e'))
        h = nb.math('SUBTRACT', h, nb.math('MULTIPLY', crm, 0.8))
    if grey > 0:
        gw = nb.maprange(nb.noise(obj, scale=1.2, detail=3), 0.3, 0.7, grey * 0.5, grey)
        col = nb.mix(gw, col, hexc('7a7670'))
        # each board / shingle weathers on its own: keep a per-piece tone after the greying
        col = nb.hsv(col, v=nb.math('ADD', 0.85 + (tb - 0.78), nb.math('MULTIPLY', nb.math('FRACT', nb.math('MULTIPLY', rnd, 7.31)), tv * 0.7)))
    if moss > 0:
        # moss only in sheltered damp spots: lower edges and joints (AO), a little on upward faces
        mz = nb.sep(nb.geometry('Normal'))[2]
        aoN = nb.node('ShaderNodeAmbientOcclusion', samples=6)
        nb.set(aoN, 'Distance', 0.05)
        joint = nb.maprange(nb.out(aoN, 'AO'), 0.55, 0.95, 1.0, 0.0)
        clump = nb.maprange(nb.noise(obj, scale=1.6, detail=5, rough=0.65), 0.52, 0.66, 0.0, 1.0)
        mm = nb.math('MULTIPLY', nb.math('MAXIMUM', joint, nb.maprange(mz, 0.5, 0.95, 0.0, 0.5)), nb.math('MULTIPLY', clump, moss))
        mcol = nb.mix(nb.maprange(nb.noise(obj, scale=30.0, detail=3), 0.3, 0.7), hexc('3c4a1c'), hexc('6a7230'))
        col = nb.mix(mm, col, mcol)
    if lichen > 0:
        # crusty pale lichen rosettes, a few centimetres across
        lv = nb.voronoi(obj, scale=14.0, feature='F1', which='Distance')
        lc = nb.voronoi(obj, scale=14.0, feature='F1', which='Color')
        lsel = nb.math('GREATER_THAN', nb.math('FRACT', nb.math('MULTIPLY', nb.sep(lc)[0], 9.3)), 0.72)
        lm = nb.math('MULTIPLY', nb.maprange(lv, 0.12, 0.3, 1.0, 0.0), lsel)
        lm = nb.math('MULTIPLY', lm, nb.maprange(nb.noise(obj, scale=40.0, detail=3), 0.3, 0.6, 0.3, 1.0))
        col = nb.mix(nb.math('MULTIPLY', lm, lichen), col, nb.mix(nb.sep(lc)[1], hexc('9a9a80'), hexc('8a8f5e')))
    if weather > 0:
        # foot of posts and boards: damp, darker, greenish, splashed with mud; stains run down from above
        gz = nb.sep(obj)[2]
        foot = nb.math('MULTIPLY', nb.maprange(gz, 0.65, 0.05, 0.0, 1.0), nb.maprange(nb.noise(obj, scale=3.0, detail=4), 0.3, 0.7, 0.55, 1.0))
        col = nb.mix(nb.math('MULTIPLY', foot, 0.7 * weather), col, nb.mix(nb.maprange(nb.noise(obj, scale=9.0), 0.3, 0.7), hexc('2f2b20'), hexc('47472c')))
        drip = nb.noise(nb.mapping(obj, scale=(9.0, 9.0, 0.6)), scale=2.0, detail=4)
        col = nb.mix(nb.math('MULTIPLY', nb.maprange(drip, 0.55, 0.75, 0.0, 0.35), weather), col, hexc('2c261f'))
        splash = nb.math('MULTIPLY', nb.maprange(gz, 0.35, 0.0, 0.0, 1.0), nb.maprange(nb.noise(obj, scale=60.0, detail=2), 0.55, 0.65, 0.0, 1.0))
        col = nb.mix(nb.math('MULTIPLY', splash, 0.8 * weather), col, hexc('4a3d2e'))
        rough = nb.math('ADD', rough, 0.0)
    bmp = nb.bump(h, strength=bump, distance=0.004)
    bsdf = nb.principled(Base_Color=col, Roughness=rough, Normal=bmp)
    nb.set(bsdf, 'Specular IOR Level', 0.35)
    nb.output(bsdf)
    return m


def mat_daub():
    """Old limewash over daub: patchy off-white, rising damp and a tide line at the foot, green algae in damp
    corners and under the eaves, rain streaks from timbers and sills, hairline cracks, worn patches showing daub."""
    m = new_material("daub_limewash")
    nb = NB(m.node_tree)
    obj = nb.texcoord('Object')
    n1 = nb.noise(obj, scale=1.5, detail=6, rough=0.6)
    n2 = nb.noise(obj, scale=12.0, detail=4, rough=0.6)
    n3 = nb.noise(obj, scale=40.0, detail=2)
    wash = nb.ramp(n1, [(0.25, hexc('b3a98f')), (0.5, hexc('c6bca4')), (0.75, hexc('b9ad92')), (0.9, hexc('cdc4ae'))])
    # older coats: yellowed and greyed patches, soot-grey towards the top
    patches = nb.maprange(nb.noise(obj, scale=0.8, detail=4, rough=0.6), 0.42, 0.68, 0.0, 0.75)
    wash = nb.mix(patches, wash, hexc('a39a80'))
    grey = nb.maprange(nb.noise(obj, scale=2.0, detail=5, rough=0.6), 0.45, 0.7, 0.0, 0.5)
    wash = nb.mix(grey, wash, hexc('979386'))
    worn = nb.maprange(nb.noise(obj, scale=2.2, detail=6, rough=0.65), 0.6, 0.66, 0.0, 1.0)
    daub = nb.mix(nb.maprange(n2, 0.3, 0.7), hexc('7d6648'), hexc('9a805a'))
    col = nb.mix(worn, wash, daub)
    gz = nb.sep(obj)[2]
    # rising damp with an irregular tide line
    edge = nb.math('ADD', 1.05, nb.math('MULTIPLY', nb.math('SUBTRACT', nb.noise(obj, scale=2.5, detail=5), 0.5), 0.8))
    damp = nb.math('SUBTRACT', 1.0, nb.math('GREATER_THAN', gz, edge))
    dampsoft = nb.maprange(nb.math('SUBTRACT', edge, gz), -0.04, 0.25, 0.0, 1.0)
    col = nb.mix(nb.math('MULTIPLY', dampsoft, 0.75), col, nb.mix(nb.maprange(n2, 0.3, 0.7), hexc('7a7462'), hexc('8f8770')))
    tide = nb.math('MULTIPLY', nb.maprange(nb.math('ABSOLUTE', nb.math('SUBTRACT', gz, edge)), 0.0, 0.035, 1.0, 0.0), 0.5)
    col = nb.mix(tide, col, hexc('6a6252'))
    # mud splashed up from the ground
    splash = nb.math('MULTIPLY', nb.maprange(gz, 1.0, 0.5, 0.0, 1.0), nb.maprange(nb.noise(obj, scale=45.0, detail=3), 0.5, 0.62, 0.0, 1.0))
    col = nb.mix(nb.math('MULTIPLY', splash, 0.8), col, hexc('5a4a38'))
    # green algae in damp places and under the eaves
    alg = nb.maprange(nb.noise(obj, scale=3.0, detail=5, rough=0.6), 0.5, 0.68, 0.0, 1.0)
    algz = nb.math('MAXIMUM', dampsoft, nb.maprange(gz, 2.0, 2.8, 0.0, 0.8))
    col = nb.mix(nb.math('MULTIPLY', nb.math('MULTIPLY', alg, algz), 0.55), col, hexc('6f7552'))
    # rain streaks running down
    streak = nb.noise(nb.mapping(obj, scale=(7.0, 7.0, 0.35)), scale=3.0, detail=4)
    col = nb.mix(nb.maprange(streak, 0.5, 0.72, 0.0, 0.6), col, hexc('7a705c'))
    streak2 = nb.noise(nb.mapping(obj, scale=(22.0, 22.0, 0.5)), scale=2.0, detail=3)
    col = nb.mix(nb.maprange(streak2, 0.6, 0.78, 0.0, 0.5), col, hexc('6e6553'))
    # grime in the corners against the timbers
    ao = nb.node('ShaderNodeAmbientOcclusion', samples=8)
    nb.set(ao, 'Distance', 0.15)
    aov = nb.out(ao, 'AO')
    col = nb.mix(nb.maprange(aov, 0.35, 0.95, 0.85, 0.0), col, hexc('6a5c48'))
    # hairline cracks
    cvec = nb.vmath('ADD', obj, nb.vmath('MULTIPLY', nb.out(nb.node('ShaderNodeTexNoise', inputs={'Vector': obj, 'Scale': 4.0}), 'Color'), (0.15, 0.15, 0.15)))
    crk = nb.voronoi(cvec, scale=5.0, feature='DISTANCE_TO_EDGE', which='Distance')
    crm = nb.math('MULTIPLY', nb.maprange(crk, 0.0, 0.01, 1.0, 0.0), nb.maprange(nb.noise(obj, scale=1.3, detail=2), 0.55, 0.65, 0.0, 1.0))
    col = nb.mix(nb.math('MULTIPLY', crm, 0.6), col, hexc('5e5446'))
    h = nb.math('ADD', nb.math('MULTIPLY', n2, 0.5), nb.math('MULTIPLY', n3, 0.25))
    h = nb.math('SUBTRACT', h, nb.math('MULTIPLY', worn, 0.35))
    h = nb.math('SUBTRACT', h, nb.math('MULTIPLY', crm, 0.4))
    bmp = nb.bump(h, strength=0.45, distance=0.01)
    bsdf = nb.principled(Base_Color=col, Roughness=0.93, Normal=bmp)
    nb.set(bsdf, 'Specular IOR Level', 0.3)
    nb.output(bsdf)
    return m


def mat_limewash_wood():
    """Pass 2b: limewashed boards inside the stable (stables were limewashed for cleanliness): an off-white wash with
    the grain and board edges showing through, rubbed grey where horses leaned, splashed and stained at the foot."""
    m = new_material("wood_limewashed")
    nb = NB(m.node_tree)
    obj = nb.texcoord('Object')
    n1 = nb.noise(obj, scale=1.6, detail=5, rough=0.6)
    grain = nb.noise(nb.mapping(obj, scale=(18.0, 18.0, 0.8)), scale=4.0, detail=4)
    wash = nb.ramp(n1, [(0.25, hexc('aaa391')), (0.5, hexc('bdb6a3')), (0.75, hexc('b2aa96')), (0.9, hexc('c4bda9'))])
    wood = nb.mix(nb.maprange(grain, 0.3, 0.7), hexc('6a5a47'), hexc('8c7a62'))
    thin = nb.maprange(nb.math('ADD', nb.math('MULTIPLY', grain, 0.6), nb.math('MULTIPLY', nb.noise(obj, scale=3.0, detail=4), 0.4)), 0.5, 0.7, 0.0, 0.7)
    col = nb.mix(thin, wash, wood)
    gz = nb.sep(obj)[2]
    # rubbed and soiled where horses stood and leaned, dung-splashed at the foot
    rub = nb.math('MULTIPLY', nb.maprange(gz, 0.5, 0.9, 0.0, 1.0), nb.maprange(gz, 1.6, 1.2, 0.0, 1.0))
    rub = nb.math('MULTIPLY', rub, nb.maprange(nb.noise(obj, scale=2.0, detail=4), 0.4, 0.65, 0.0, 0.6))
    col = nb.mix(rub, col, hexc('7d7466'))
    foot = nb.maprange(nb.math('ADD', gz, nb.math('MULTIPLY', nb.math('SUBTRACT', nb.noise(obj, scale=6.0, detail=4), 0.5), 0.3)), 0.55, 0.15, 0.0, 0.85)
    col = nb.mix(foot, col, hexc('4f4433'))
    ao = nb.node('ShaderNodeAmbientOcclusion', samples=8)
    nb.set(ao, 'Distance', 0.12)
    col = nb.mix(nb.maprange(nb.out(ao, 'AO'), 0.35, 0.95, 0.7, 0.0), col, hexc('5a5040'))
    bsdf = nb.principled(Base_Color=col, Roughness=0.9, Normal=nb.bump(grain, strength=0.3, distance=0.01))
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
    """Aged thatch read as bundles of straw, not brushed fur: per-bundle tone and height, short butt-end streaks,
    dark gaps, weathering to grey-brown, run-off streaks, moss in clumps on the lower slope; the eave face shows
    the cut straw ends. UV: u along the eave, v up the slope (metres)."""
    m = new_material(name)
    nb = NB(m.node_tree)
    uv = nb.texcoord('UV')
    obj = nb.texcoord('Object')
    eave = nb.attr('eave')
    sx, sy, sz = nb.sep(uv)
    # bundles about 12 cm wide and 40 cm long, overlapping down the slope
    bvec = nb.comb(nb.math('MULTIPLY', sx, 8.0), nb.math('MULTIPLY', sy, 2.4), 0.0)
    bvor = nb.node('ShaderNodeTexVoronoi', voronoi_dimensions='2D', feature='F1')
    nb.set(bvor, 'Vector', bvec)
    nb.set(bvor, 'Scale', 1.0)
    bund = nb.out(bvor, 'Color')
    bpos = nb.out(bvor, 'Position')
    bund_d = nb.voronoi(bvec, scale=1.0, feature='DISTANCE_TO_EDGE', which='Distance', dims='2D')
    brnd = nb.noise(bund, scale=3.0, detail=0)
    # height within a bundle: rises from its upper end to its lower (butt) end
    by = nb.math('SUBTRACT', nb.sep(bvec)[1], nb.sep(bpos)[1])
    bh = nb.maprange(by, 0.45, -0.45, 0.0, 1.0)
    # short butt-end streaks along the slope, offset per bundle
    off = nb.vmath('MULTIPLY', bund, (5.0, 5.0, 5.0))
    svec = nb.vmath('ADD', nb.comb(nb.math('MULTIPLY', sx, 110.0), nb.math('MULTIPLY', sy, 11.0), 0.0), off)
    strands = nb.noise(svec, scale=1.0, detail=5, rough=0.6, distortion=0.4)
    tips = nb.voronoi(nb.comb(nb.math('MULTIPLY', sx, 1.0), nb.math('MULTIPLY', sy, 0.45), 0.0), scale=95.0, feature='F1', which='Distance', dims='2D')
    tipm = nb.maprange(tips, 0.05, 0.3, 1.0, 0.0)
    big = nb.noise(obj, scale=0.45, detail=4, rough=0.6)
    col = nb.ramp(strands, [(0.2, hexc('2f281e')), (0.42, hexc('54473a')), (0.6, hexc('6e5d45')), (0.8, hexc('8a7656'))])
    col = nb.hsv(col, v=nb.math('ADD', 0.72, nb.math('MULTIPLY', brnd, 0.5)))
    col = nb.mix(nb.math('MULTIPLY', tipm, 0.35), col, hexc('2a241c'))
    gaps = nb.maprange(bund_d, 0.0, 0.07, 1.0, 0.0)
    col = nb.mix(nb.math('MULTIPLY', gaps, 0.55), col, hexc('241e17'))
    # weathering: grey on exposed patches, dark run-off streaks down the slope
    col = nb.mix(nb.maprange(big, 0.35, 0.7, 0.0, 0.5 * (1 - fresh)), col, hexc('6a6458'))
    run = nb.noise(nb.comb(nb.math('MULTIPLY', sx, 3.5), nb.math('MULTIPLY', sy, 0.35), 0.0), scale=1.0, detail=4)
    col = nb.mix(nb.maprange(run, 0.55, 0.75, 0.0, 0.45 * (1 - fresh)), col, hexc('2e2a22'))
    if fresh > 0:
        col = nb.mix(fresh, col, nb.ramp(strands, [(0.3, hexc('6e5a36')), (0.6, hexc('9a8050')), (0.8, hexc('b0955c'))]))
    # moss: clumps, mostly on the lower slope
    low = nb.maprange(sy, 0.3, 2.6, 1.0, 0.2)
    mclump = nb.maprange(nb.noise(obj, scale=1.2, detail=6, rough=0.65), 0.52, 0.66, 0.0, 1.0)
    moss = nb.math('MULTIPLY', nb.math('MULTIPLY', low, mclump), 0.8 * (1 - fresh))
    mosscol = nb.mix(nb.maprange(nb.noise(obj, scale=25.0, detail=3), 0.3, 0.7), hexc('34401a'), hexc('5d6a28'))
    col = nb.mix(moss, col, mosscol)
    col = nb.mix(nb.math('MULTIPLY', nb.maprange(sy, 0.0, 0.5, 1.0, 0.0), 0.35), col, hexc('2b261d'))
    # cut eave face: the ends of the straws
    ends = nb.voronoi(obj, scale=180.0, feature='F1', which='Distance')
    endsc = nb.voronoi(obj, scale=180.0, feature='F1', which='Color')
    # pass 2b: the cut butt ends read lighter and straw-coloured (pass 2a's eave was a uniform dark band)
    endcol = nb.mix(nb.maprange(ends, 0.02, 0.22), hexc('1e1912'), nb.mix(nb.noise(endsc, scale=4.0, detail=0), hexc('5e4f37'), hexc('8a7552')))
    endcol = nb.mix(nb.maprange(big, 0.35, 0.7, 0.0, 0.5), endcol, hexc('3e3930'))
    estri = nb.noise(nb.mapping(obj, scale=(30.0, 30.0, 3.0)), scale=4.0, detail=4)
    endcol = nb.hsv(endcol, v=nb.maprange(estri, 0.3, 0.7, 0.55, 1.15))
    col = nb.mix(eave, col, endcol)
    h = nb.math('ADD', nb.math('MULTIPLY', bh, 0.8), nb.math('MULTIPLY', strands, 0.45))
    h = nb.math('SUBTRACT', h, nb.math('MULTIPLY', gaps, 0.6))
    h = nb.math('SUBTRACT', h, nb.math('MULTIPLY', tipm, 0.25))
    h = nb.math('ADD', h, nb.math('MULTIPLY', moss, 0.3))
    h = nb.mix(eave, h, nb.math('MULTIPLY', nb.maprange(ends, 0.0, 0.4, 0.0, 1.0), 1.4), dtype='FLOAT')
    bmp = nb.bump(h, strength=0.9, distance=0.02)
    bsdf = nb.principled(Base_Color=col, Roughness=0.9, Normal=bmp)
    nb.set(bsdf, 'Specular IOR Level', 0.25)
    nb.set(bsdf, 'Sheen Weight', 0.2)
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
        "timber": _wood("wood_timber", hexc('675a4a'), hexc('342c24'), grain_scale=2.5, rough=0.84, grey=0.6, bump=0.55, moss=0.35, lichen=0.5),
        "plank": _wood("wood_planks", hexc('74634f'), hexc('3d3228'), grain_scale=3.0, rough=0.82, grey=0.5, bump=0.45, moss=0.25, lichen=0.35),
        "plank_dark": _wood("wood_planks_dark", hexc('5e4f3e'), hexc('2a231b'), grain_scale=3.0, rough=0.8, grey=0.35, bump=0.45, lichen=0.25),
        "shingle": _wood("wood_shingles", hexc('5f584d'), hexc('2e2a25'), grain_scale=4.0, rough=0.86, moss=0.75, grey=0.55, bump=0.6, lichen=0.8, tb=0.55, tv=0.8),
        "fresh": _wood("wood_fresh", hexc('a88e68'), hexc('6a5338'), grain_scale=3.0, rough=0.7, grey=0.1, bump=0.3, crack=False),
        "daub": mat_daub(),
        "lime": mat_limewash_wood(),
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
