"""Procedural materials for the forest village (no image files)."""
import bpy
import common as C
from common import NB, new_material


def srgb(r, g=None, b=None):
    if g is None:
        g = b = r
    def f(c):
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    return (f(r), f(g), f(b), 1.0)


def hexc(h):
    h = h.lstrip('#')
    return srgb(int(h[0:2], 16) / 255, int(h[2:4], 16) / 255, int(h[4:6], 16) / 255)


# ----------------------------------------------------------------------------
# Ground: road / yard / path dirt
# ----------------------------------------------------------------------------
def mat_road(displace=False):
    m = new_material("road_dirt_disp" if displace else "road_dirt")
    nb = NB(m.node_tree)
    obj = nb.texcoord('Object')
    uv = nb.texcoord('UV')
    rut = nb.attr('rut')
    edgef = nb.attr('edgef')
    wet = nb.attr('wet')
    hoof = nb.attr('hoof')
    pathf = nb.attr('pathf')
    gm = nb.attr('gmask')
    sx, sy, sz = nb.sep(uv)
    # palette
    dust = hexc('7c6a54')
    soil = hexc('574533')
    dark = hexc('3a2c20')
    mud = hexc('251c14')
    # large/medium tone variation
    n_big = nb.noise(obj, scale=0.3, detail=3, rough=0.55)
    n_mid = nb.noise(obj, scale=1.8, detail=6, rough=0.62)
    n_fine = nb.noise(obj, scale=30.0, detail=4, rough=0.7)
    base = nb.ramp(n_big, [(0.32, soil), (0.6, dust)])
    base = nb.mix(nb.maprange(n_mid, 0.38, 0.72, 0.0, 0.6), base, dark)
    # loose clods everywhere, more in the hoof-churned middle
    clods = nb.voronoi(obj, scale=26.0, feature='SMOOTH_F1', which='Distance', smooth=0.4)
    clodh = nb.maprange(clods, 0.0, 0.45, 1.0, 0.0)
    base = nb.mix(nb.math('MULTIPLY', nb.math('ADD', 0.25, hoof), nb.maprange(clodh, 0.3, 0.8, 0.1, 0.4)), base, hexc('2e241a'))
    # dried mud cracks in the drier, compacted parts
    crk = nb.voronoi(nb.mapping(obj, scale=(1.0, 1.0, 1.0)), scale=13.0, feature='DISTANCE_TO_EDGE', which='Distance')
    crk2 = nb.noise(obj, scale=0.9, detail=2)
    crackm = nb.math('MULTIPLY', nb.maprange(crk, 0.0, 0.012, 1.0, 0.0), nb.maprange(crk2, 0.6, 0.68, 0.0, 1.0))
    crackm = nb.math('MULTIPLY', crackm, nb.math('SUBTRACT', 1.0, nb.math('MINIMUM', nb.math('ADD', wet, hoof), 1.0)))
    base = nb.mix(nb.math('MULTIPLY', crackm, 0.45), base, hexc('3a2d21'))
    # ruts: compacted, darker, smeared along the road
    streak_vec = nb.comb(nb.math('MULTIPLY', sx, 26.0), nb.math('MULTIPLY', sy, 1.6), 0.0)
    streak = nb.noise(streak_vec, scale=1.0, detail=5, rough=0.6)
    rutcol = nb.mix(nb.maprange(streak, 0.3, 0.7), dark, hexc('4a3c2e'))
    rutf = nb.maprange(rut, 0.08, 0.7, 0.0, 1.0)
    base = nb.mix(rutf, base, rutcol)
    # pebbles: two sizes, muted stone colours
    def pebbles(scale, thresh, r0, r1):
        vor = nb.node('ShaderNodeTexVoronoi', voronoi_dimensions='3D', feature='F1')
        nb.set(vor, 'Vector', obj)
        nb.set(vor, 'Scale', scale)
        nb.set(vor, 'Randomness', 1.0)
        pdist = nb.out(vor, 'Distance')
        pcol = nb.out(vor, 'Color')
        sel = nb.math('GREATER_THAN', nb.noise(pcol, scale=3.0, detail=0), thresh)
        shape = nb.maprange(pdist, r0, r1, 1.0, 0.0, interp='SMOOTHSTEP')
        return nb.math('MULTIPLY', shape, sel), pcol
    peb1, pc1 = pebbles(16.0, 0.63, 0.18, 0.36)
    peb2, pc2 = pebbles(45.0, 0.56, 0.16, 0.34)
    notrut = nb.math('SUBTRACT', 1.0, nb.math('MULTIPLY', rutf, 0.75))
    peb1 = nb.math('MULTIPLY', peb1, notrut)
    peb2 = nb.math('MULTIPLY', peb2, notrut)
    stone_col = nb.ramp(nb.noise(pc1, scale=7.0, detail=0), [(0.25, hexc('5a554d')), (0.5, hexc('716a5c')), (0.75, hexc('655646')), (0.9, hexc('837b6a'))])
    stone_col2 = nb.ramp(nb.noise(pc2, scale=7.0, detail=0), [(0.3, hexc('4a453e')), (0.6, hexc('665e50')), (0.9, hexc('7b715f'))])
    base = nb.mix(nb.math('MULTIPLY', peb1, 0.85), base, stone_col)
    base = nb.mix(nb.math('MULTIPLY', peb2, 0.7), base, stone_col2)
    # organic debris: dark specks, straw bits, a few fallen leaves
    spk = nb.voronoi(obj, scale=70.0, feature='F1', which='Distance')
    spkc = nb.voronoi(obj, scale=70.0, feature='F1', which='Color')
    spsel = nb.math('GREATER_THAN', nb.noise(spkc, scale=5.0, detail=0), 0.66)
    specks = nb.math('MULTIPLY', nb.maprange(spk, 0.15, 0.3, 1.0, 0.0), spsel)
    base = nb.mix(nb.math('MULTIPLY', specks, 0.8), base, hexc('1c1712'))
    straw_vec = nb.mapping(obj, rot=(0, 0, 0.6), scale=(1.0, 14.0, 1.0))
    straw = nb.noise(straw_vec, scale=9.0, detail=2, rough=0.5)
    strawm = nb.math('MULTIPLY', nb.maprange(straw, 0.7, 0.76, 0.0, 1.0), nb.maprange(nb.noise(obj, scale=1.3, detail=2), 0.55, 0.7, 0.0, 1.0))
    base = nb.mix(nb.math('MULTIPLY', strawm, 0.8), base, hexc('a08a55'))
    lv = nb.voronoi(obj, scale=9.0, feature='F1', which='Distance')
    lvc = nb.voronoi(obj, scale=9.0, feature='F1', which='Color')
    lsel = nb.math('GREATER_THAN', nb.noise(lvc, scale=4.0, detail=0), 0.7)
    leafm = nb.math('MULTIPLY', nb.maprange(lv, 0.12, 0.2, 1.0, 0.0), lsel)
    leafm = nb.math('MULTIPLY', leafm, nb.math('ADD', 0.25, nb.math('MULTIPLY', edgef, 0.75)))
    leafcol = nb.ramp(nb.noise(lvc, scale=9.0, detail=0), [(0.3, hexc('6b4422')), (0.6, hexc('8a6a2a')), (0.85, hexc('4a3a20'))])
    base = nb.mix(leafm, base, leafcol)
    # grit speckle
    base = nb.mix(nb.maprange(n_fine, 0.6, 0.8, 0.0, 0.22), base, hexc('86765f'))
    # grassy, mossy soil where tufts grow and at the verges
    greens = nb.mix(nb.maprange(n_mid, 0.4, 0.6), hexc('3e3c22'), hexc('34381b'))
    base = nb.mix(nb.math('MINIMUM', nb.math('ADD', nb.math('POWER', edgef, 1.5), nb.math('MULTIPLY', gm, 0.7)), 1.0), base, greens)
    # footpaths: trodden, a little lighter and drier
    base = nb.mix(nb.math('MULTIPLY', pathf, 0.3), base, hexc('6c5c4a'))
    # wetness darkens and adds gloss
    wetf = nb.maprange(wet, 0.15, 0.85, 0.0, 1.0)
    base = nb.mix(nb.math('MULTIPLY', wetf, 0.75), base, mud)
    rough = nb.maprange(wetf, 0.0, 1.0, 0.94, 0.3)
    rough = nb.math('SUBTRACT', rough, nb.math('MULTIPLY', peb1, 0.2))
    # bump: grit + pebbles + clods + streaks
    h = nb.math('ADD', nb.math('MULTIPLY', peb1, 0.9), nb.math('MULTIPLY', peb2, 0.45))
    h = nb.math('ADD', h, nb.math('MULTIPLY', n_fine, 0.25))
    h = nb.math('ADD', h, nb.math('MULTIPLY', nb.math('MULTIPLY', streak, rutf), 0.35))
    h = nb.math('ADD', h, nb.math('MULTIPLY', clodh, nb.math('ADD', 0.3, nb.math('MULTIPLY', hoof, 0.4))))
    h = nb.math('ADD', h, nb.math('MULTIPLY', leafm, 0.1))
    h = nb.math('SUBTRACT', h, nb.math('MULTIPLY', crackm, 0.3))
    if displace:
        # true micro-displacement (used with adaptive subdivision for the close view)
        bump = nb.bump(h, strength=0.25, distance=0.006)
        disp = nb.node('ShaderNodeDisplacement', space='OBJECT')
        nb.set(disp, 'Height', h)
        nb.set(disp, 'Midlevel', 0.35)
        nb.set(disp, 'Scale', 0.011)
        bsdf = nb.principled(Base_Color=base, Roughness=rough, Normal=bump)
        nb.set(bsdf, 'Specular IOR Level', 0.45)
        nb.output(bsdf, displacement=nb.out(disp))
        m.displacement_method = 'BOTH'
        return m
    bump = nb.bump(h, strength=0.65, distance=0.012)
    bsdf = nb.principled(Base_Color=base, Roughness=rough, Normal=bump)
    nb.set(bsdf, 'Specular IOR Level', 0.45)
    nb.output(bsdf)
    return m


def mat_water():
    m = new_material("puddle_water")
    nb = NB(m.node_tree)
    obj = nb.texcoord('Object')
    rip = nb.noise(obj, scale=7.0, detail=3, rough=0.5)
    bump = nb.bump(rip, strength=0.03, distance=0.02)
    # murky, slightly transparent water: you see the mud bottom near the shore and the sky in it
    bsdf = nb.principled(Base_Color=hexc('8a7458'), Roughness=0.03, IOR=1.33, Normal=bump)
    nb.set(bsdf, 'Transmission Weight', 1.0)
    nb.set(bsdf, 'Specular IOR Level', 0.5)
    nb.output(bsdf)
    return m


# ----------------------------------------------------------------------------
# Terrain (meadow soil / forest floor)
# ----------------------------------------------------------------------------
def mat_terrain():
    m = new_material("terrain_ground")
    nb = NB(m.node_tree)
    obj = nb.texcoord('Object')
    forest = nb.attr('forest')
    roadedge = nb.attr('roadedge')
    mvar = nb.attr('mvar')
    n1 = nb.noise(obj, scale=0.12, detail=4, rough=0.6)
    n2 = nb.noise(obj, scale=1.3, detail=5, rough=0.6)
    n3 = nb.noise(obj, scale=9.0, detail=3, rough=0.6)
    # meadow floor: mossy soil with dead grass
    meadow = nb.ramp(n2, [(0.3, hexc('2f3518')), (0.5, hexc('4a4a22')), (0.7, hexc('5d5232'))])
    meadow = nb.mix(nb.maprange(mvar, 0.2, 0.8, 0.0, 0.5), meadow, hexc('3e4a1c'))
    # forest floor: leaf litter
    leaf = nb.voronoi(obj, scale=22.0, feature='F1', which='Color')
    leafc = nb.ramp(nb.noise(leaf, scale=2.0, detail=0), [(0.25, hexc('4a2e17')), (0.45, hexc('6e4a26')), (0.62, hexc('8a5c2a')), (0.8, hexc('3a2a1a'))])
    litter = nb.mix(nb.maprange(n3, 0.3, 0.7, 0.0, 0.6), leafc, hexc('2c2216'))
    moss = nb.maprange(n1, 0.55, 0.7, 0.0, 0.7)
    litter = nb.mix(moss, litter, hexc('3d4a1a'))
    base = nb.mix(nb.maprange(forest, 0.15, 0.85), meadow, litter)
    # bare trodden soil near roads and yards
    soil = nb.mix(nb.maprange(n2, 0.4, 0.65), hexc('4d3d2b'), hexc('63513a'))
    base = nb.mix(nb.math('MULTIPLY', nb.math('POWER', roadedge, 1.4), 0.85), base, soil)
    h = nb.math('ADD', nb.math('MULTIPLY', n3, 0.5), nb.math('MULTIPLY', nb.voronoi(obj, scale=22.0, feature='DISTANCE_TO_EDGE'), 0.6))
    bump = nb.bump(h, strength=0.35, distance=0.02)
    bsdf = nb.principled(Base_Color=base, Roughness=0.9, Normal=bump)
    nb.set(bsdf, 'Specular IOR Level', 0.35)
    nb.output(bsdf)
    return m


def build_ground_materials():
    return dict(road=mat_road(), water=mat_water(), terrain=mat_terrain())
