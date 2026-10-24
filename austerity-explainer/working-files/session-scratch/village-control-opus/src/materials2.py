"""Pass 2 ground materials: damp rutted dirt with mud, grit and organic debris; murky puddle water; road stones.

Judges on pass 1: the road looked like "a too-smooth, too-clean sand plane", "plaster or beach sand", with
"polka-dot" pebbles, a "hard grey-green band" at the verge and puddles like "a flat over-saturated blue patch".
This shader answers that with:
- a darker damp-earth palette (dry crust only on high, dry stretches), wet mud in ruts, prints and low spots;
- clods and crumbs (relief and colour), compacted polished wheel tracks, squeezed-up mud lips, dry cracks;
- fine grit in clumps of varied colour instead of evenly sprinkled round dots;
- straw bits, leaf fragments, twigs and dung smears placed per cell with random angles, clumped;
- wet areas get a clear coat (sharp reflections over dark mud) instead of a blue sheen;
- a ragged verge of humus, moss and dead grass blades instead of one smooth olive band.
"""
import bpy
import math
import common as C
from common import NB, new_material
from materials import hexc, srgb


def cell_shapes(nb, vec, scale, length, width, ellipse=False, thresh=0.5, seed=0.0):
    """Randomly rotated small shapes (straws, leaves, twigs), one per Voronoi cell, some cells empty.
    vec: 3D vector socket (x, y used). length/width in metres. Returns (mask, cell colour)."""
    vor = nb.node('ShaderNodeTexVoronoi', voronoi_dimensions='2D', feature='F1')
    if seed:
        vec = nb.vmath('ADD', vec, (seed * 13.1, seed * 7.7, 0.0))
    nb.set(vor, 'Vector', vec)
    nb.set(vor, 'Scale', scale)
    nb.set(vor, 'Randomness', 1.0)
    pos = nb.out(vor, 'Position')
    colr = nb.out(vor, 'Color')
    cr, cg, cb = nb.sep(colr)
    px, py, _ = nb.sep(pos)
    vx, vy, _ = nb.sep(vec)
    dx = nb.math('SUBTRACT', vx, px)
    dy = nb.math('SUBTRACT', vy, py)
    ang = nb.math('MULTIPLY', cr, 6.2832)
    ca = nb.math('COSINE', ang)
    sa = nb.math('SINE', ang)
    lx = nb.math('ADD', nb.math('MULTIPLY', dx, ca), nb.math('MULTIPLY', dy, sa))
    ly = nb.math('SUBTRACT', nb.math('MULTIPLY', dy, ca), nb.math('MULTIPLY', dx, sa))
    lh = nb.math('MULTIPLY', nb.math('ADD', 0.45, cg), length * 0.5)
    wh = nb.math('MULTIPLY', nb.math('ADD', 0.6, nb.math('MULTIPLY', cb, 0.8)), width * 0.5)
    if ellipse:
        ex = nb.math('DIVIDE', lx, lh)
        ey = nb.math('DIVIDE', ly, wh)
        r = nb.math('SQRT', nb.math('ADD', nb.math('MULTIPLY', ex, ex), nb.math('MULTIPLY', ey, ey)))
        m = nb.maprange(r, 0.75, 1.0, 1.0, 0.0)
    else:
        ax = nb.math('ABSOLUTE', lx)
        ay = nb.math('ABSOLUTE', ly)
        mx = nb.maprange(nb.math('DIVIDE', ax, lh), 0.85, 1.0, 1.0, 0.0)
        my = nb.maprange(nb.math('DIVIDE', ay, wh), 0.55, 1.0, 1.0, 0.0)
        m = nb.math('MULTIPLY', mx, my)
    sel = nb.math('GREATER_THAN', nb.math('FRACT', nb.math('ADD', nb.math('MULTIPLY', cg, 17.31), nb.math('MULTIPLY', cb, 5.17))), thresh)
    return nb.math('MULTIPLY', m, sel), colr


def relief_field(nb, flat, hoof, ridge, prints, rut, Wf, band=None):
    """Mud relief on flat (x, y) coordinates, shared by the road shader (bump) and the geometry-nodes
    displacement of the close-view patches (roads2.disp_group), so colour and geometry line up.
    Broad lumps everywhere, chunky clods where hooves churn and mud is squeezed up, crumbs; wheel tracks are
    pressed smoother and wet mud flows flatter."""
    nz = nb.node('ShaderNodeTexNoise')
    nb.set(nz, 'Vector', flat)
    nb.set(nz, 'Scale', 9.0)
    nb.set(nz, 'Detail', 2.0)
    dvec = nb.out(nz, 'Color')
    dco = nb.vmath('ADD', flat, nb.vmath('MULTIPLY', nb.vmath('SUBTRACT', dvec, (0.5, 0.5, 0.5)), (0.035, 0.035, 0.0)))
    lumps = nb.noise(flat, scale=4.5, detail=5, rough=0.62)
    clod = nb.maprange(nb.voronoi(dco, scale=22.0, feature='SMOOTH_F1', which='Distance', smooth=0.12), 0.0, 0.55, 1.0, 0.0)
    clod2 = nb.maprange(nb.voronoi(dco, scale=58.0, feature='SMOOTH_F1', which='Distance', smooth=0.15), 0.0, 0.55, 1.0, 0.0)
    clods = nb.math('ADD', nb.math('MULTIPLY', clod, 0.55), nb.math('MULTIPLY', clod2, 0.45))
    crumb = nb.noise(flat, scale=150.0, detail=3, rough=0.65)
    rutf = nb.maprange(rut, 0.08, 0.7, 0.0, 1.0)
    churn = nb.math('MINIMUM', nb.math('ADD', nb.math('ADD', nb.math('MULTIPLY', hoof, 0.75), nb.math('MULTIPLY', ridge, 0.9)), nb.math('MULTIPLY', prints, 0.6)), 1.0)
    churn = nb.math('MAXIMUM', churn, 0.2)
    dry = nb.math('SUBTRACT', 1.0, Wf)
    clodamt = nb.math('MULTIPLY', nb.math('MULTIPLY', churn, nb.math('SUBTRACT', 1.0, nb.math('MULTIPLY', rutf, 0.8))), nb.math('ADD', 0.35, nb.math('MULTIPLY', dry, 0.65)))
    if band is not None:
        # pass 2b: the worn wheel bands are pressed flatter
        clodamt = nb.math('MULTIPLY', clodamt, nb.math('SUBTRACT', 1.0, nb.math('MULTIPLY', band, 0.55)))
    # pass 2b: broken clods - flat-topped lumps split by crisp cracks, each at its own height (churned mud drying
    # out), so the surface reads as crumbled earth and not as soft sand with round bumps
    brk = None
    for (bsc, bw, bseed) in ((30.0, 0.55, 0.0), (12.0, 0.45, 3.7)):
        bco = nb.vmath('ADD', dco, (bseed, bseed * 0.61, 0.0)) if bseed else dco
        ve = nb.node('ShaderNodeTexVoronoi', voronoi_dimensions='3D', feature='DISTANCE_TO_EDGE')
        nb.set(ve, 'Vector', bco)
        nb.set(ve, 'Scale', bsc)
        nb.set(ve, 'Randomness', 1.0)
        vc = nb.node('ShaderNodeTexVoronoi', voronoi_dimensions='3D', feature='F1')
        nb.set(vc, 'Vector', bco)
        nb.set(vc, 'Scale', bsc)
        nb.set(vc, 'Randomness', 1.0)
        plateau = nb.maprange(nb.out(ve, 'Distance'), 0.0, 0.1, 0.0, 1.0)
        cr = nb.sep(nb.out(vc, 'Color'))[0]
        one = nb.math('MULTIPLY', nb.math('MULTIPLY', plateau, nb.math('ADD', 0.3, nb.math('MULTIPLY', cr, 0.7))), bw)
        brk = one if brk is None else nb.math('ADD', brk, one)
    brkamt = nb.math('MULTIPLY', nb.math('MULTIPLY', churn, nb.math('SUBTRACT', 1.0, nb.math('MULTIPLY', rutf, 0.85))), nb.math('ADD', 0.25, nb.math('MULTIPLY', dry, 0.75)))
    if band is not None:
        brkamt = nb.math('MULTIPLY', brkamt, nb.math('SUBTRACT', 1.0, nb.math('MULTIPLY', band, 0.6)))
    # the mud squeezed up beside the ruts is crumbled too (pass 2a left those lips as smooth sausages), and the
    # plain strips get a weaker, patchy crumble so no stretch reads as smooth sand
    lipc = nb.math('MULTIPLY', ridge, nb.math('SUBTRACT', 1.0, nb.math('MULTIPLY', rutf, 0.9)))
    patchy = nb.maprange(nb.noise(flat, scale=1.3, detail=3, rough=0.6), 0.35, 0.65, 0.12, 0.45)
    brkamt = nb.math('MAXIMUM', brkamt, nb.math('MAXIMUM', nb.math('MULTIPLY', lipc, 0.85), patchy))
    h = nb.math('MULTIPLY', nb.math('SUBTRACT', lumps, 0.5), nb.math('MULTIPLY', nb.math('ADD', 0.85, nb.math('MULTIPLY', churn, 0.6)), nb.math('SUBTRACT', 1.0, nb.math('MULTIPLY', rutf, 0.5))))
    h = nb.math('ADD', h, nb.math('MULTIPLY', clods, nb.math('MULTIPLY', clodamt, 0.9)))
    h = nb.math('ADD', h, nb.math('MULTIPLY', crumb, 0.2))
    h = nb.math('ADD', h, nb.math('MULTIPLY', brk, nb.math('MULTIPLY', brkamt, 0.75)))
    h = nb.math('MULTIPLY', h, nb.math('SUBTRACT', 1.0, nb.math('MULTIPLY', Wf, 0.6)))
    return dict(h=h, dvec=dvec, dco=dco, clods=clods, crumb=crumb, rutf=rutf, churn=churn, clodamt=clodamt, lumps=lumps,
                brk=brk, brkamt=brkamt)


def wetness(nb, wet, shore, film, prints, wz):
    W = nb.math('MAXIMUM', nb.math('MAXIMUM', wet, shore), film)
    W = nb.math('MAXIMUM', W, nb.math('MULTIPLY', prints, nb.math('MULTIPLY', wz, 0.35)))
    return nb.maprange(W, 0.1, 0.85, 0.0, 1.0)


def ground_layers(nb, obj, uv, A, verge_only=False):
    """Shared dirt shading. A: dict of attribute sockets. Returns (colour, roughness, height, wetness)."""
    rut, edgef, wet, hoof, pathf, gm = A['rut'], A['edgef'], A['wet'], A['hoof'], A['pathf'], A['gmask']
    wz, ridge, shore, film, prints = A['wetzone'], A['ridge'], A['shore'], A['film'], A['prints']
    su, sv, _ = nb.sep(uv)
    # ---------------- palette
    dust = hexc('7e705f')
    dry = hexc('6b5b48')
    clay = hexc('6c5440')
    damp = hexc('543e2b')
    darkd = hexc('3a2b1e')
    mud = hexc('271e16')
    manure = hexc('3a3121')
    # ---------------- dampness field
    n_big = nb.noise(obj, scale=0.22, detail=3, rough=0.55)
    n_mid = nb.noise(obj, scale=1.4, detail=5, rough=0.6)
    n_tone = nb.noise(obj, scale=0.6, detail=3, rough=0.5)
    # pass 2b: damper overall (the road read as pale dry sand from above)
    dampf = nb.maprange(nb.math('ADD', n_big, nb.math('MULTIPLY', wz, 0.45)), 0.25, 0.85, 0.3, 0.95)
    dampf = nb.math('MAXIMUM', dampf, nb.math('MULTIPLY', nb.math('MINIMUM', nb.math('ADD', rut, nb.math('MULTIPLY', prints, 0.4)), 1.0), 0.85))
    dampf = nb.math('MAXIMUM', dampf, nb.math('MULTIPLY', edgef, 0.7))
    base_dry = nb.ramp(n_mid, [(0.25, dust), (0.5, dry), (0.8, clay)])
    base_damp = nb.ramp(n_mid, [(0.3, darkd), (0.6, damp), (0.85, hexc('5a422e'))])
    col = nb.mix(dampf, base_dry, base_damp)
    col = nb.hsv(col, h=nb.maprange(n_tone, 0.3, 0.7, 0.485, 0.515), s=nb.maprange(n_tone, 0.2, 0.8, 0.95, 1.3))
    # ---------------- wetness and relief (the relief is shared with roads2.disp_group)
    Wf = wetness(nb, wet, shore, film, prints, wz)
    oflat = nb.vmath('MULTIPLY', obj, (1.0, 1.0, 0.0))
    gnz = nb.sep(nb.geometry('Normal'))[2]
    steep = nb.maprange(gnz, 0.93, 0.72, 0.0, 1.0)
    band = A.get('band')
    R = relief_field(nb, oflat, hoof, ridge, prints, rut, Wf, band=band)
    dvec, dco, crumb = R['dvec'], R['dco'], R['crumb']
    rutf, churn, clodamt = R['rutf'], R['churn'], R['clodamt']
    grain_v = nb.node('ShaderNodeTexVoronoi', voronoi_dimensions='3D', feature='F1')
    nb.set(grain_v, 'Vector', oflat)
    nb.set(grain_v, 'Scale', 330.0)
    grain_d = nb.out(grain_v, 'Distance')
    grain_c = nb.out(grain_v, 'Color')
    grain_sel = nb.math('GREATER_THAN', nb.math('FRACT', nb.math('MULTIPLY', nb.sep(grain_c)[0], 11.3)), 0.62)
    grain = nb.math('MULTIPLY', nb.maprange(grain_d, 0.2, 0.42, 1.0, 0.0), grain_sel)
    # ---------------- cracks (dry crust only)
    cvec = nb.vmath('ADD', oflat, nb.vmath('MULTIPLY', nb.vmath('SUBTRACT', dvec, (0.5, 0.5, 0.5)), (0.12, 0.12, 0.0)))
    crk = nb.voronoi(cvec, scale=7.0, feature='DISTANCE_TO_EDGE', which='Distance')
    crk2 = nb.voronoi(cvec, scale=19.0, feature='DISTANCE_TO_EDGE', which='Distance')
    crackl = nb.math('MAXIMUM', nb.maprange(crk, 0.0, 0.016, 1.0, 0.0), nb.math('MULTIPLY', nb.maprange(crk2, 0.0, 0.02, 1.0, 0.0), 0.6))
    drym = nb.math('MULTIPLY', nb.maprange(dampf, 0.25, 0.45, 1.0, 0.0), nb.maprange(nb.noise(obj, scale=0.8, detail=2), 0.5, 0.6, 0.0, 1.0))
    crackm = nb.math('MULTIPLY', crackl, nb.math('MULTIPLY', drym, nb.math('SUBTRACT', 1.0, churn)))
    # ---------------- wheel track smear and polish
    streak = nb.noise(nb.comb(nb.math('MULTIPLY', su, 32.0), nb.math('MULTIPLY', sv, 1.4), 0.0), scale=1.0, detail=5, rough=0.6)
    # ---------------- colour from relief
    relief = R['clods']
    shade = nb.maprange(relief, 0.15, 0.85, 0.8, 1.12)
    shade = nb.math('ADD', 1.0, nb.math('MULTIPLY', nb.math('SUBTRACT', shade, 1.0), clodamt))
    shade = nb.math('MULTIPLY', shade, nb.maprange(R['lumps'], 0.3, 0.7, 0.92, 1.06))
    col = nb.hsv(col, v=shade)
    # dry dusty tops of clods
    dtop = nb.math('MULTIPLY', nb.maprange(relief, 0.6, 0.95, 0.0, 0.5), nb.math('MULTIPLY', nb.math('SUBTRACT', 1.0, dampf), clodamt))
    col = nb.mix(dtop, col, dust)
    # churned middle: darker, manure in it
    col = nb.mix(nb.math('MULTIPLY', hoof, nb.maprange(nb.noise(obj, scale=2.2, detail=3), 0.35, 0.7, 0.15, 0.55)), col, manure)
    # wheel tracks
    trackcol = nb.mix(nb.maprange(streak, 0.3, 0.7), darkd, hexc('4c3c2c'))
    # pass 2b: dry stretches of rut are pressed smooth and dusty, paler than the road - only wet stretches are dark,
    # so from above the ruts come and go instead of running as two dark lines like tram rails
    trackdry = nb.mix(nb.maprange(streak, 0.3, 0.7), hexc('5c4d3c'), hexc('786754'))
    trackcol = nb.mix(nb.maprange(Wf, 0.04, 0.35, 0.0, 1.0), trackdry, trackcol)
    col = nb.mix(nb.math('MULTIPLY', nb.math('MULTIPLY', rutf, 0.8), nb.math('SUBTRACT', 1.0, nb.math('MULTIPLY', steep, 0.8))), col, trackcol)
    # pass 2b: worn wheel bands - compacted, darker, smoother earth either side of each rut
    if band is not None:
        bandf = nb.math('MULTIPLY', band, nb.math('SUBTRACT', 1.0, nb.math('MULTIPLY', steep, 0.8)))
        bandn = nb.noise(obj, scale=3.5, detail=4, rough=0.6)
        compact = nb.mix(nb.maprange(nb.math('ADD', nb.math('MULTIPLY', streak, 0.6), nb.math('MULTIPLY', bandn, 0.4)), 0.3, 0.7), hexc('3b2e22'), hexc('5b4734'))
        col = nb.mix(nb.math('MULTIPLY', bandf, nb.maprange(bandn, 0.25, 0.75, 0.35, 0.7)), col, compact)
    # crumbled clods: the crack lines between them dark, their tops a shade lighter
    brkc = nb.math('MULTIPLY', R['brkamt'], nb.maprange(R['brk'], 0.0, 0.25, 1.0, 0.0))
    col = nb.mix(nb.math('MULTIPLY', brkc, 0.5), col, nb.hsv(col, v=0.55))
    # cracks
    col = nb.mix(nb.math('MULTIPLY', crackm, 0.7), col, hexc('2c231a'))
    # ---------------- grit: tiny stones in clumps, varied colours
    gclump = nb.maprange(nb.noise(obj, scale=1.7, detail=3, rough=0.6), 0.48, 0.66, 0.0, 1.0)
    gv = nb.node('ShaderNodeTexVoronoi', voronoi_dimensions='3D', feature='F1')
    nb.set(gv, 'Vector', dco)
    nb.set(gv, 'Scale', 58.0)
    gd = nb.out(gv, 'Distance')
    gcol = nb.out(gv, 'Color')
    gr, gg, gb = nb.sep(gcol)
    gsize = nb.math('ADD', 0.13, nb.math('MULTIPLY', nb.math('POWER', gg, 2.0), 0.3))
    gsel = nb.math('GREATER_THAN', nb.math('FRACT', nb.math('MULTIPLY', gr, 23.7)), nb.math('SUBTRACT', 0.9, nb.math('MULTIPLY', gclump, 0.6)))
    gsel = nb.math('MULTIPLY', gsel, nb.math('SUBTRACT', 1.0, nb.math('MULTIPLY', rutf, 0.85)))
    gdome = nb.math('MULTIPLY', nb.math('POWER', nb.math('MAXIMUM', nb.math('SUBTRACT', 1.0, nb.math('DIVIDE', gd, gsize)), 0.0), 0.5), gsel)
    grit = nb.math('MULTIPLY', nb.math('LESS_THAN', gd, gsize), gsel)
    gring = nb.math('MULTIPLY', nb.math('MULTIPLY', nb.math('LESS_THAN', gd, nb.math('MULTIPLY', gsize, 1.35)), nb.math('SUBTRACT', 1.0, grit)), gsel)
    col = nb.mix(nb.math('MULTIPLY', gring, 0.5), col, nb.hsv(col, v=0.55))
    stone_col = nb.ramp(gb, [(0.0, hexc('545049')), (0.2, hexc('675e51')), (0.38, hexc('776d5d')), (0.52, hexc('5f4d39')),
                             (0.66, hexc('7d776b')), (0.8, hexc('423e38')), (0.9, hexc('8a8478')), (1.0, hexc('6d5b46'))], interp='CONSTANT')
    col = nb.mix(nb.math('MULTIPLY', grit, 0.9), col, stone_col)
    # sand grains: single specks
    gcol2 = nb.ramp(nb.sep(grain_c)[1], [(0.3, hexc('2a2219')), (0.6, hexc('7d725f')), (0.85, hexc('5d5547'))], interp='CONSTANT')
    col = nb.mix(nb.math('MULTIPLY', grain, 0.45), col, gcol2)
    # mottling at hand-span scale: damp darker blotches, drier lighter crust, dark organic stains
    mot = nb.noise(oflat, scale=5.0, detail=4, rough=0.6)
    col = nb.hsv(col, v=nb.maprange(mot, 0.3, 0.7, 0.86, 1.1))
    stain = nb.math('MULTIPLY', nb.maprange(nb.noise(oflat, scale=2.6, detail=5, rough=0.6), 0.62, 0.72, 0.0, 1.0),
                    nb.maprange(nb.noise(oflat, scale=0.5, detail=2), 0.45, 0.6, 0.0, 1.0))
    col = nb.mix(nb.math('MULTIPLY', stain, 0.45), col, hexc('2a2118'))
    # ---------------- organic debris
    o2 = nb.vmath('MULTIPLY', obj, (1.0, 1.0, 0.0))
    dclump = nb.maprange(nb.noise(obj, scale=0.9, detail=3, rough=0.6), 0.42, 0.66, 0.0, 1.0)
    strawm, strawc = cell_shapes(nb, o2, 9.0, 0.07, 0.0035, thresh=0.45, seed=1.0)
    straw_amt = nb.math('MINIMUM', nb.math('ADD', nb.math('ADD', nb.math('MULTIPLY', hoof, 0.8), nb.math('MULTIPLY', edgef, 0.35)), nb.math('MULTIPLY', dclump, 0.6)), 1.0)
    strawm = nb.math('MULTIPLY', strawm, nb.math('GREATER_THAN', straw_amt, nb.math('FRACT', nb.math('MULTIPLY', nb.sep(strawc)[2], 7.13))))
    strawcol = nb.ramp(nb.sep(strawc)[0], [(0.0, hexc('a08a58')), (0.35, hexc('8a7a5a')), (0.6, hexc('6f6656')), (0.85, hexc('b49c63'))])
    strawcol = nb.mix(dampf, strawcol, nb.hsv(strawcol, v=0.6))
    col = nb.mix(nb.math('MULTIPLY', strawm, 0.95), col, strawcol)
    strawm2, strawc2 = cell_shapes(nb, o2, 16.0, 0.045, 0.0028, thresh=0.55, seed=2.0)
    strawm2 = nb.math('MULTIPLY', strawm2, straw_amt)
    col = nb.mix(nb.math('MULTIPLY', strawm2, 0.85), col, nb.hsv(strawcol, v=0.85))
    leafm, leafc = cell_shapes(nb, o2, 5.0, 0.065, 0.04, ellipse=True, thresh=0.62, seed=3.0)
    leaf_amt = nb.math('MINIMUM', nb.math('ADD', nb.math('MULTIPLY', edgef, 0.8), nb.math('MULTIPLY', dclump, 0.35)), 1.0)
    leafm = nb.math('MULTIPLY', leafm, nb.math('GREATER_THAN', leaf_amt, nb.math('FRACT', nb.math('MULTIPLY', nb.sep(leafc)[2], 5.91))))
    leafcol = nb.ramp(nb.sep(leafc)[0], [(0.0, hexc('5c3a1e')), (0.3, hexc('7a5226')), (0.55, hexc('8c6a2c')), (0.75, hexc('4a3a22')), (0.9, hexc('6b5a2a'))])
    leafcol = nb.mix(dampf, leafcol, nb.hsv(leafcol, v=0.55))
    col = nb.mix(nb.math('MULTIPLY', leafm, 0.92), col, leafcol)
    twigm, twigc = cell_shapes(nb, o2, 3.5, 0.13, 0.006, thresh=0.7, seed=4.0)
    twigm = nb.math('MULTIPLY', twigm, nb.math('ADD', 0.25, nb.math('MULTIPLY', edgef, 0.75)))
    col = nb.mix(nb.math('MULTIPLY', twigm, 0.9), col, hexc('2e261d'))
    # dung smears in the hoof band
    dn = nb.noise(obj, scale=3.0, detail=4, rough=0.6)
    dsel = nb.maprange(nb.noise(obj, scale=0.45, detail=2), 0.6, 0.7, 0.0, 1.0)
    dungm = nb.math('MULTIPLY', nb.math('MULTIPLY', nb.maprange(dn, 0.68, 0.72, 0.0, 1.0), dsel), hoof)
    dungcol = nb.mix(nb.maprange(nb.noise(obj, scale=40.0, detail=2), 0.4, 0.7), hexc('3d3620'), hexc('5a4f2c'))
    col = nb.mix(nb.math('MULTIPLY', dungm, 0.85), col, dungcol)
    # ---------------- verge: humus, moss, dead grass blades
    vn = nb.noise(obj, scale=3.0, detail=4, rough=0.6)
    verge = nb.math('POWER', nb.math('MINIMUM', nb.math('ADD', edgef, nb.math('MULTIPLY', gm, 0.5)), 1.0), 1.4)
    vragged = nb.maprange(nb.noise(obj, scale=2.4, detail=5, rough=0.65), 0.3, 0.7, -0.35, 0.35)
    verge = nb.math('MINIMUM', nb.math('MAXIMUM', nb.math('ADD', verge, vragged), 0.0), 1.0)
    humus = nb.ramp(vn, [(0.3, hexc('2f2a1d')), (0.55, hexc('3d3a24')), (0.75, hexc('4b4a2a'))])
    bladem, bladec = cell_shapes(nb, o2, 26.0, 0.06, 0.003, thresh=0.3, seed=5.0)
    humus = nb.mix(nb.math('MULTIPLY', bladem, 0.9), humus, nb.ramp(nb.sep(bladec)[0], [(0.2, hexc('8a8256')), (0.6, hexc('6a6a3a')), (0.9, hexc('a39668'))]))
    col = nb.mix(nb.math('MULTIPLY', verge, 0.9), col, humus)
    # pass 2b: where grass grows (the crown, the verge and its bites into the road) the ground between the tufts is a
    # mat of short grass and moss - green from the air, not bare earth with tufts stuck in it
    gm2 = nb.math('MULTIPLY', nb.maprange(gm, 0.1, 0.45, 0.0, 1.0), nb.maprange(nb.noise(obj, scale=1.8, detail=4, rough=0.6), 0.3, 0.6, 0.5, 1.0))
    # it stands for the grass blades' combined colour where they are too small to see one by one: fade it in with
    # distance from the camera (up close the real grass is there and a green wash under it would look painted)
    camd = nb.node('ShaderNodeCameraData')
    gm2 = nb.math('MULTIPLY', gm2, nb.maprange(nb.out(camd, 'View Distance'), 7.0, 28.0, 0.0, 1.0))
    gcol = nb.mix(nb.maprange(nb.noise(obj, scale=6.0, detail=3), 0.3, 0.7), hexc('34401d'), hexc('4f572b'))
    gcol = nb.mix(nb.maprange(nb.noise(obj, scale=2.5, detail=3), 0.45, 0.7, 0.0, 0.55), gcol, hexc('6a6338'))
    gcol = nb.mix(nb.math('MULTIPLY', bladem, 0.7), gcol, nb.ramp(nb.sep(bladec)[0], [(0.2, hexc('8a8256')), (0.6, hexc('6a6a3a')), (0.9, hexc('a39668'))]))
    # moss cushions and bare soil showing through, so up close it is not a flat green wash
    mossn = nb.noise(oflat, scale=38.0, detail=4, rough=0.65)
    gcol = nb.hsv(gcol, v=nb.maprange(mossn, 0.3, 0.7, 0.7, 1.15))
    soil = nb.maprange(nb.noise(oflat, scale=14.0, detail=3, rough=0.6), 0.56, 0.68, 0.0, 0.8)
    gcol = nb.mix(soil, gcol, nb.hsv(col, v=0.75))
    col = nb.mix(nb.math('MULTIPLY', gm2, 0.8), col, gcol)
    # footpaths: trodden, a little drier
    col = nb.mix(nb.math('MULTIPLY', pathf, 0.15), col, dry)
    # ---------------- wetness
    col = nb.mix(nb.math('MULTIPLY', Wf, 0.55), col, nb.hsv(col, s=1.12, v=0.5))
    col = nb.mix(nb.math('MULTIPLY', nb.maprange(shore, 0.3, 1.0, 0.0, 1.0), 0.6), col, mud)
    rough = nb.maprange(dampf, 0.1, 0.9, 0.93, 0.72)
    # pass 2b: water stands only in separate dips along a wet rut (glossy there); between them the mud is wet but
    # satin, so the ruts no longer read as one continuous mirror strip
    segn = nb.noise(nb.comb(nb.math('MULTIPLY', su, 2.2), nb.math('MULTIPLY', sv, 1.5), 0.0), scale=1.0, detail=3, rough=0.6)
    segf = nb.maprange(segn, 0.45, 0.6, 0.1, 1.0)
    wet_rough = nb.mix(segf, nb.maprange(nb.noise(obj, scale=9.0, detail=2), 0.3, 0.7, 0.5, 0.68),
                       nb.maprange(nb.noise(obj, scale=6.0, detail=2), 0.3, 0.7, 0.22, 0.42), dtype='FLOAT')
    rough = nb.mix(Wf, rough, wet_rough, dtype='FLOAT')
    rough = nb.math('SUBTRACT', rough, nb.math('MULTIPLY', grit, 0.25))
    # ---------------- height for bump (the patches also get R['h'] as real geometry)
    crust = nb.noise(oflat, scale=40.0, detail=6, rough=0.62)
    pits = nb.math('MULTIPLY', nb.maprange(nb.voronoi(oflat, scale=110.0, feature='F1', which='Distance'), 0.0, 0.18, 1.0, 0.0),
                   nb.maprange(nb.noise(oflat, scale=3.0, detail=2), 0.45, 0.6, 0.0, 1.0))
    e = nb.math('ADD', nb.math('MULTIPLY', gdome, 0.7), nb.math('MULTIPLY', grain, 0.08))
    e = nb.math('ADD', e, nb.math('MULTIPLY', crust, nb.math('MULTIPLY', nb.math('SUBTRACT', 1.0, churn), 0.35)))
    e = nb.math('SUBTRACT', e, nb.math('MULTIPLY', pits, 0.25))
    e = nb.math('ADD', e, nb.math('MULTIPLY', nb.math('MULTIPLY', streak, rutf), 0.25))
    # pass 2b: small lumps and slumps in the rut bottoms break up the reflections
    rutb = nb.noise(oflat, scale=16.0, detail=4, rough=0.6)
    e = nb.math('ADD', e, nb.math('MULTIPLY', nb.math('MULTIPLY', nb.math('SUBTRACT', rutb, 0.5), rutf), 0.7))
    e = nb.math('ADD', e, nb.math('MULTIPLY', nb.math('MAXIMUM', strawm, strawm2), 0.12))
    e = nb.math('ADD', e, nb.math('MULTIPLY', leafm, 0.06))
    e = nb.math('ADD', e, nb.math('MULTIPLY', nb.math('MULTIPLY', gm2, nb.math('SUBTRACT', mossn, 0.4)), 0.5))
    e = nb.math('ADD', e, nb.math('MULTIPLY', dungm, 0.35))
    e = nb.math('SUBTRACT', e, nb.math('MULTIPLY', crackm, 0.45))
    e = nb.math('MULTIPLY', e, nb.math('SUBTRACT', 1.0, nb.math('MULTIPLY', Wf, 0.4)))
    h = nb.math('ADD', R['h'], e)
    # rut walls and banks are steep: flat (x, y) mapping would stretch there, so use 3D crumbs instead
    crumb3 = nb.noise(obj, scale=90.0, detail=4, rough=0.65)
    h = nb.mix(steep, h, nb.math('ADD', nb.math('MULTIPLY', crumb3, 0.8), nb.math('MULTIPLY', nb.noise(obj, scale=22.0, detail=3), 0.5)), dtype='FLOAT')
    return col, rough, h, Wf, segf


def ground_attrs(nb):
    names = ['rut', 'edgef', 'wet', 'hoof', 'pathf', 'gmask', 'wetzone', 'ridge', 'shore', 'film', 'prints', 'band']
    return {n: nb.attr(n) for n in names}


def mat_road2(name="road_dirt", displace=False):
    m = new_material(name)
    nb = NB(m.node_tree)
    obj = nb.texcoord('Object')
    uv = nb.texcoord('UV')
    A = ground_attrs(nb)
    col, rough, h, Wf, segf = ground_layers(nb, obj, uv, A)
    bump = nb.bump(h, strength=0.6 if displace else 0.8, distance=0.01)
    bsdf = nb.principled(Base_Color=col, Roughness=rough, Normal=bump)
    nb.set(bsdf, 'Specular IOR Level', 0.45)
    # wet film: a clear coat gives sharp reflections over dark mud (not a blue sheen)
    # wet mud is glossy, not a mirror: only the wettest film (and the puddle water itself) reflects sharply
    filmf = nb.maprange(A['film'], 0.2, 0.8, 0.0, 1.0)
    # pass 2b: the shine along a wet rut is broken into separate wet dips with duller mud between them (pass 2a
    # gave long continuous mirror strips down the ruts), and its sharpness varies
    coatw = nb.math('ADD', nb.math('MULTIPLY', Wf, 0.3), nb.math('MULTIPLY', filmf, 0.25))
    nb.set(bsdf, 'Coat Weight', nb.math('MULTIPLY', coatw, segf))
    crough = nb.maprange(nb.noise(obj, scale=3.0, detail=3), 0.3, 0.7, 0.1, 0.32)
    crough = nb.math('ADD', crough, nb.maprange(nb.noise(obj, scale=28.0, detail=2), 0.35, 0.65, -0.04, 0.18))
    crough = nb.math('ADD', crough, nb.math('MULTIPLY', nb.math('SUBTRACT', 1.0, segf), 0.25))
    nb.set(bsdf, 'Coat Roughness', nb.math('MAXIMUM', nb.math('SUBTRACT', crough, nb.math('MULTIPLY', filmf, 0.08)), 0.03))
    nb.set(bsdf, 'Coat IOR', 1.33)
    # (displace=True: the patch material; the relief itself is real geometry made by roads2.disp_group)
    nb.output(bsdf)
    m.displacement_method = 'BUMP'
    return m


def mat_water2(name="puddle_water", shallow_hex='46372a', deep_hex='231b13', depth_full=0.035):
    """Murky puddle water: dark brown, a mud bottom near the shore, sky and surroundings in it, specks floating.
    (pass 2b: the stable yard's shallow puddles use a darker variant, 'puddle_water_yard', so they read as dark water
    holding reflections rather than as flat brown patches beside the sky-sheened wet mud)"""
    m = new_material(name)
    nb = NB(m.node_tree)
    obj = nb.texcoord('Object')
    dep = nb.attr('wdepth')
    t = nb.maprange(dep, 0.0, depth_full, 0.0, 1.0)
    shallow = hexc(shallow_hex)
    deep = hexc(deep_hex)
    col = nb.mix(t, shallow, deep)
    # floating dust film and specks
    film = nb.maprange(nb.noise(obj, scale=4.0, detail=4, rough=0.6), 0.5, 0.75, 0.0, 1.0)
    o2 = nb.vmath('MULTIPLY', obj, (1.0, 1.0, 0.0))
    speck, speckc = cell_shapes(nb, o2, 40.0, 0.012, 0.004, thresh=0.75, seed=9.0)
    col = nb.mix(nb.math('MULTIPLY', speck, 0.8), col, nb.ramp(nb.sep(speckc)[0], [(0.3, hexc('6b5a3a')), (0.7, hexc('8f7c52'))]))
    col = nb.mix(nb.math('MULTIPLY', film, 0.25), col, hexc('5a4c38'))
    rough = nb.math('ADD', 0.025, nb.math('MULTIPLY', film, 0.12))
    rough = nb.math('ADD', rough, nb.math('MULTIPLY', speck, 0.5))
    rip = nb.noise(obj, scale=9.0, detail=3, rough=0.5)
    bump = nb.bump(rip, strength=0.012, distance=0.02)
    bsdf = nb.principled(Base_Color=col, Roughness=rough, IOR=1.33, Normal=bump)
    nb.set(bsdf, 'Specular IOR Level', 0.5)
    nb.output(bsdf)
    m.displacement_method = 'BUMP'
    return m


def mat_road_stone():
    """Stones lying on the road: varied colours, muddy undersides, some wet."""
    m = new_material("road_stone")
    nb = NB(m.node_tree)
    obj = nb.texcoord('Object')
    gen = nb.texcoord('Generated')
    rnd = nb.objinfo('Random')
    base = nb.ramp(rnd, [(0.0, hexc('5c5953')), (0.15, hexc('6a5a47')), (0.3, hexc('77705f')), (0.42, hexc('46423d')),
                         (0.55, hexc('857e6e')), (0.68, hexc('5a4a38')), (0.8, hexc('4f5153')), (0.9, hexc('6f6553'))], interp='CONSTANT')
    n1 = nb.noise(obj, scale=30.0, detail=5, rough=0.6)
    speck = nb.maprange(nb.noise(obj, scale=140.0, detail=2), 0.55, 0.7, 0.0, 0.5)
    base = nb.mix(nb.maprange(n1, 0.3, 0.7, 0.0, 0.35), base, nb.hsv(base, v=0.7))
    base = nb.mix(speck, base, nb.hsv(base, v=1.35, s=0.8))
    gz = nb.sep(gen)[2]
    mudline = nb.maprange(nb.math('ADD', gz, nb.math('MULTIPLY', nb.math('SUBTRACT', n1, 0.5), 0.3)), 0.25, 0.55, 1.0, 0.0)
    mudamt = nb.math('MAXIMUM', mudline, nb.maprange(nb.noise(obj, scale=8.0, detail=2), 0.45, 0.7, 0.0, 0.75))
    base = nb.mix(mudamt, base, hexc('3d3024'))
    wet = nb.math('GREATER_THAN', nb.math('FRACT', nb.math('MULTIPLY', rnd, 7.7)), 0.75)
    rough = nb.mix(wet, nb.maprange(n1, 0.3, 0.7, 0.62, 0.85), 0.45, dtype='FLOAT')
    base = nb.mix(nb.math('MULTIPLY', wet, 0.4), base, nb.hsv(base, v=0.6))
    bsdf = nb.principled(Base_Color=base, Roughness=rough, Normal=nb.bump(n1, 0.35, 0.004))
    nb.output(bsdf)
    return m


def build():
    return dict(road=mat_road2(), road_patch=mat_road2("road_dirt_patch", displace=True), water=mat_water2(), stone=mat_road_stone())
