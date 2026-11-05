"""
jar: a large glazed porcelain storage jar, blue-and-white: a thrown body with a small foot ring, swelling to a high
shoulder, a short neck and rolled lip, painted in cobalt under a clear glaze: double lines at the foot, a band of lotus
panels round the lower body, flowers on scrolling stems round the belly, a scalloped cloud collar on the shoulder, a
blue band on the neck; the cobalt heavier in some strokes than others, as a brush leaves it. The glaze glossy, finely
crazed; rain streaks of grime running down from the shoulder, dirt splashed up round the unglazed foot. An optional
domed lid with a knob, painted to match.

Options:
    lid    (default True) the domed lid with its knob on the neck; False: the mouth open, dark inside
    seed   the hand-thrown wobble of the body, where the flowers and scrolls fall, the streaks

Where it came from: the builders' blue-and-white jar in '/home/claude/build-57-garden/first pass/render_final.py'
(mat_jar(), line 397: white glaze with cobalt blots and bands, crazing, wet) and its rain streaks in
'/home/claude/build-57-garden/second pass/render_final.py' (mat_jar(), lines 409-446). Rebuilt here with a turned body
with a foot ring and lip, painting laid out in bands as such jars are painted (lotus panels, flower scrolls, a cloud
collar) and painted round the jar rather than projected through it, a lid, and grime at the foot.
"""

import math
import os
import sys

import bpy
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import _shapes_chapel as shapes  # noqa: E402
import _shapes_garden as garden  # noqa: E402

PART = 'jar'
HEIGHT = 0.61          # foot to lip

CARD = {
    'name': PART,
    'what': 'a large blue-and-white glazed porcelain jar: cobalt lotus panels, flower scrolls and a cloud collar under a glossy '
            'crazed glaze, a domed lid with a knob; rain streaks from the shoulder, dirt at its unglazed foot',
    'size_m': (0.48, 0.48, 0.71),
    'options': {
        'lid': 'True (default): the domed lid with its knob on the neck; False: the mouth open, dark inside',
        'seed': 'the body\'s wobble, where the flowers and scrolls fall, the streaks (default 0)',
    },
    'materials': ['PART • jar: blue-and-white glaze'],
    'source': "the jar in '/home/claude/build-57-garden/first pass/render_final.py' (mat_jar(), line 397) and its rain streaks in "
              "'/home/claude/build-57-garden/second pass/render_final.py' (mat_jar(), lines 409-446)",
    'views': 'reads from every side; the painting goes all round',
    'trap': 'white glaze is the brightest thing near the eye at dusk: it mirrors lamps as hard white spots; keep it out of a lamp\'s '
            'full glare or turn it so the glare falls on the neck',
}


def glaze():
    """Blue-and-white: painted round the jar in bands (the angle round it and the height, so nothing is stretched),
    flowers placed from the object's own number 'jar_seed'; glossy and crazed; grime streaks and a dirty foot."""
    def maker(m, nodes, links, p):
        coords = shapes.own_coordinates(nodes)
        sep = nodes.new('ShaderNodeSeparateXYZ')
        links.new(coords, sep.inputs[0])
        x, y, z = sep.outputs['X'], sep.outputs['Y'], sep.outputs['Z']
        seed = nodes.new('ShaderNodeAttribute')
        seed.attribute_type = 'OBJECT'
        seed.attribute_name = 'jar_seed'
        angle = shapes.math_node(nodes, links, 'ARCTAN2', y, x)                   # -pi..pi round the jar
        around = shapes.math_node(nodes, links, 'MULTIPLY', angle, 0.232)        # metres round the belly's radius
        flat = nodes.new('ShaderNodeCombineXYZ')
        links.new(around, flat.inputs['X'])
        links.new(z, flat.inputs['Y'])
        links.new(seed.outputs['Fac'], flat.inputs['Z'])
        uv = flat.outputs[0]

        def band(z0, z1, soft=0.002):
            a = shapes.map_range(nodes, links, z, z0 - soft, z0 + soft)
            b = shapes.map_range(nodes, links, z, z1 + soft, z1 - soft)
            return shapes.math_node(nodes, links, 'MULTIPLY', a, b)

        def add(a, b):
            return shapes.math_node(nodes, links, 'MAXIMUM', a, b)

        def mul(a, b):
            return shapes.math_node(nodes, links, 'MULTIPLY', a, b)

        # lines: foot, under the lotus, over the belly, the collar's foot, the neck
        lines = band(0.045, 0.052)
        for z0, z1 in ((0.06, 0.064), (0.158, 0.164), (0.4, 0.406), (0.414, 0.418), (0.522, 0.528), (0.578, 0.584)):
            lines = add(lines, band(z0, z1))
        neck = band(0.536, 0.572)
        # lotus panels round the lower body: twelve petal outlines with a pale wash inside
        k12 = shapes.math_node(nodes, links, 'MULTIPLY', angle, 12 / (2 * math.pi))
        px = shapes.math_node(nodes, links, 'ABSOLUTE', shapes.math_node(nodes, links, 'SUBTRACT', shapes.math_node(nodes, links, 'FRACT', k12), 0.5))
        pz = shapes.map_range(nodes, links, z, 0.068, 0.152)
        reach = shapes.math_node(nodes, links, 'MULTIPLY', shapes.math_node(nodes, links, 'POWER', shapes.math_node(nodes, links, 'SUBTRACT', 1.0, pz), 0.6), 0.44)
        edge = shapes.math_node(nodes, links, 'SUBTRACT', px, reach)
        petal_fill = shapes.map_range(nodes, links, edge, 0.0, -0.01)
        petal_line = mul(shapes.map_range(nodes, links, edge, -0.045, -0.03), shapes.map_range(nodes, links, edge, 0.0, -0.012))
        lotus_zone = band(0.068, 0.152)
        petal_line = mul(add(mul(petal_line, 1.0), shapes.map_range(nodes, links, edge, -0.012, 0.0)), mul(lotus_zone, petal_fill))
        petal_wash = mul(mul(petal_fill, lotus_zone), 0.45)
        # flowers on the belly: one in each cell of a loose grid, five-petalled, with a dark heart
        shifted = nodes.new('ShaderNodeCombineXYZ')                              # round the jar and up it, moved by the seed
        links.new(shapes.math_node(nodes, links, 'ADD', around, seed.outputs['Fac']), shifted.inputs['X'])
        links.new(z, shifted.inputs['Y'])
        vor = nodes.new('ShaderNodeTexVoronoi')
        vor.voronoi_dimensions = '2D'
        vor.inputs['Scale'].default_value = 7.0
        vor.inputs['Randomness'].default_value = 0.75
        links.new(shifted.outputs[0], vor.inputs['Vector'])
        rel = nodes.new('ShaderNodeVectorMath')                                  # from the flower's middle (Position is in metres)
        rel.operation = 'SUBTRACT'
        links.new(shifted.outputs[0], rel.inputs[0])
        links.new(vor.outputs['Position'], rel.inputs[1])
        rsep = nodes.new('ShaderNodeSeparateXYZ')
        links.new(rel.outputs[0], rsep.inputs[0])
        theta = shapes.math_node(nodes, links, 'ARCTAN2', rsep.outputs['Y'], rsep.outputs['X'])
        span = nodes.new('ShaderNodeVectorMath')
        span.operation = 'LENGTH'
        links.new(rel.outputs[0], span.inputs[0])
        dist = span.outputs['Value']
        lobes = shapes.math_node(nodes, links, 'ABSOLUTE', shapes.math_node(nodes, links, 'COSINE', shapes.math_node(nodes, links, 'MULTIPLY', theta, 2.5)))
        radius = shapes.math_node(nodes, links, 'ADD', 0.016, shapes.math_node(nodes, links, 'MULTIPLY', shapes.math_node(nodes, links, 'POWER', lobes, 0.6), 0.03))
        petal_edge = shapes.math_node(nodes, links, 'SUBTRACT', dist, radius)
        flower = shapes.map_range(nodes, links, petal_edge, 0.002, -0.002)
        flower_line = mul(shapes.map_range(nodes, links, petal_edge, -0.006, -0.003), shapes.map_range(nodes, links, petal_edge, 0.003, 0.0))
        heart = shapes.map_range(nodes, links, dist, 0.014, 0.011)
        veins = add(mul(shapes.map_range(nodes, links, lobes, 0.985, 0.998), shapes.map_range(nodes, links, dist, 0.04, 0.014)),
                    mul(shapes.map_range(nodes, links, dist, 0.019, 0.021), shapes.map_range(nodes, links, dist, 0.025, 0.023)))
        # scrolling stems and leaves between the flowers: wandering lines where a noise crosses its middle
        stem_noise = shapes.noise_fac(nodes, links, uv, 10.0, detail=0.5, roughness=0.3)
        stem = shapes.map_range(nodes, links, shapes.math_node(nodes, links, 'ABSOLUTE', shapes.math_node(nodes, links, 'SUBTRACT', stem_noise, 0.5)), 0.022, 0.012)
        leaf_noise = shapes.noise_fac(nodes, links, uv, 22.0, detail=0.5)
        leaves = mul(shapes.map_range(nodes, links, leaf_noise, 0.6, 0.63), shapes.map_range(nodes, links, shapes.math_node(nodes, links, 'ABSOLUTE', shapes.math_node(nodes, links, 'SUBTRACT', stem_noise, 0.5)), 0.05, 0.02))
        belly = band(0.172, 0.392)
        outside_flower = shapes.math_node(nodes, links, 'SUBTRACT', 1.0, flower)
        belly_ink = add(add(mul(flower_line, 1.0), add(heart, veins)), mul(add(stem, leaves), outside_flower))
        belly_ink = mul(belly_ink, belly)
        belly_wash = mul(mul(flower, belly), 0.8)
        # the cloud collar on the shoulder: eight scalloped lobes hanging from the neck, outlined, washed pale
        k8 = shapes.math_node(nodes, links, 'MULTIPLY', angle, 8 / (2 * math.pi))
        qx = shapes.math_node(nodes, links, 'SUBTRACT', shapes.math_node(nodes, links, 'FRACT', k8), 0.5)
        hang = shapes.math_node(nodes, links, 'ADD', 0.455, shapes.math_node(nodes, links, 'MULTIPLY', shapes.math_node(nodes, links, 'COSINE',
                                shapes.math_node(nodes, links, 'MULTIPLY', qx, 2 * math.pi)), -0.03))
        below = shapes.math_node(nodes, links, 'SUBTRACT', z, hang)
        collar_fill = mul(shapes.map_range(nodes, links, below, -0.002, 0.002), band(0.42, 0.52))
        collar_line = mul(shapes.map_range(nodes, links, below, -0.006, -0.002), shapes.map_range(nodes, links, below, 0.004, 0.0))
        collar_line = mul(collar_line, band(0.42, 0.52))
        # the lid: rings of blue round its top and a blue knob
        radial = nodes.new('ShaderNodeVectorMath')
        radial.operation = 'LENGTH'
        xy = nodes.new('ShaderNodeCombineXYZ')
        links.new(x, xy.inputs['X'])
        links.new(y, xy.inputs['Y'])
        links.new(xy.outputs[0], radial.inputs[0])
        r = radial.outputs['Value']
        lid_zone = shapes.map_range(nodes, links, z, 0.603, 0.607)
        lid_ink = add(mul(shapes.map_range(nodes, links, r, 0.104, 0.1), shapes.map_range(nodes, links, r, 0.088, 0.092)),
                      add(mul(shapes.map_range(nodes, links, r, 0.072, 0.068), shapes.map_range(nodes, links, r, 0.06, 0.064)),
                          shapes.map_range(nodes, links, r, 0.03, 0.026)))
        lid_ink = mul(lid_ink, lid_zone)
        ink = add(add(add(lines, neck), add(petal_line, belly_ink)), add(collar_line, lid_ink))
        wash = add(add(petal_wash, belly_wash), mul(collar_fill, 0.7))
        # the cobalt heaped in some strokes, thin in others
        heap = shapes.noise_fac(nodes, links, uv, 40.0, detail=3.0)
        dark_blue = shapes.mix_colour(nodes, links, shapes.map_range(nodes, links, heap, 0.35, 0.7), (0.035, 0.06, 0.2), (0.006, 0.014, 0.085))
        white = shapes.mix_colour(nodes, links, shapes.noise_fac(nodes, links, coords, 6.0), (0.4, 0.43, 0.44), (0.47, 0.49, 0.49))
        colour = shapes.mix_colour(nodes, links, wash, white, (0.07, 0.12, 0.3))
        colour = shapes.mix_colour(nodes, links, ink, colour, dark_blue)
        # rain streaks of grime from the shoulder down, and dirt splashed up the foot (the foot ring itself unglazed)
        stretch = nodes.new('ShaderNodeMapping')
        stretch.inputs['Scale'].default_value = (1.0, 1.0, 0.08)
        links.new(uv, stretch.inputs['Vector'])
        streaks = shapes.noise_fac(nodes, links, stretch.outputs['Vector'], 22.0, detail=4.0)
        streak = mul(shapes.map_range(nodes, links, streaks, 0.55, 0.72, 0.0, 0.55), shapes.map_range(nodes, links, z, 0.5, 0.25))
        colour = shapes.mix_colour(nodes, links, streak, colour, (0.09, 0.085, 0.07))
        splash = shapes.noise_fac(nodes, links, coords, 30.0, detail=4.0)
        foot = shapes.map_range(nodes, links, shapes.math_node(nodes, links, 'ADD', z, shapes.math_node(nodes, links, 'MULTIPLY', splash, 0.04)), 0.07, 0.03)
        colour = shapes.mix_colour(nodes, links, foot, colour, (0.06, 0.05, 0.035))
        biscuit = shapes.map_range(nodes, links, z, 0.022, 0.016)
        colour = shapes.mix_colour(nodes, links, biscuit, colour, (0.13, 0.11, 0.08))
        links.new(colour, p.inputs['Base Color'])
        dull = add(add(foot, biscuit), mul(streak, 0.6))
        links.new(shapes.map_range(nodes, links, dull, 0.0, 1.0, 0.07, 0.75), p.inputs['Roughness'])
        p.inputs['Coat Weight'].default_value = 0.5
        p.inputs['Coat Roughness'].default_value = 0.04
        craze = nodes.new('ShaderNodeTexVoronoi')
        craze.feature = 'DISTANCE_TO_EDGE'
        craze.inputs['Scale'].default_value = 55.0
        links.new(coords, craze.inputs['Vector'])
        ripple = shapes.noise_fac(nodes, links, coords, 9.0, detail=2.0)
        height = shapes.math_node(nodes, links, 'ADD', shapes.map_range(nodes, links, craze.outputs['Distance'], 0.0, 0.04, 0.0, 1.0), mul(ripple, 0.5))
        links.new(shapes.bump(nodes, links, height, 0.04, 0.001), p.inputs['Normal'])
        m.diffuse_color = (0.42, 0.44, 0.47, 1.0)
    return shapes.part_material(PART, 'blue-and-white glaze', maker)


def build(collection, seed=0, lid=True):
    rng = shapes.rng_for(PART, seed)
    body = garden.Shape()
    profile = [(0.0, 0.004), (0.118, 0.004), (0.122, 0.0), (0.132, 0.0), (0.136, 0.016), (0.128, 0.022), (0.15, 0.05), (0.19, 0.12),
               (0.222, 0.21), (0.236, 0.3), (0.236, 0.36), (0.226, 0.41), (0.2, 0.46), (0.16, 0.505), (0.118, 0.535), (0.102, 0.548),
               (0.099, 0.58), (0.104, 0.598), (0.108, 0.603), (0.106, HEIGHT), (0.097, HEIGHT), (0.09, 0.6), (0.088, 0.56),
               (0.1, 0.53), (0.0, 0.52)]
    body.lathe(profile, segments=64)
    wob = [rng.uniform(0, 2 * math.pi) for _ in range(2)]
    for v in body.bm.verts:
        a = math.atan2(v.co.y, v.co.x)
        f = 1.0 + 0.008 * math.sin(2 * a + wob[0]) * math.sin(math.pi * min(1.0, v.co.z / HEIGHT)) + 0.004 * math.sin(3 * a + wob[1])
        v.co.x *= f
        v.co.y *= f
    material = glaze()
    jar = body.finish('%s body' % PART, collection, material, smooth=True, sharp=70.0)
    jar['jar_seed'] = rng.uniform(0, 30)
    made = [jar]
    if lid:
        top = garden.Shape()
        top.lathe([(0.0, 0.596), (0.088, 0.596), (0.088, 0.604), (0.114, 0.606), (0.116, 0.616), (0.108, 0.632), (0.09, 0.654), (0.06, 0.67),
                   (0.032, 0.676), (0.026, 0.684), (0.03, 0.696), (0.026, 0.706), (0.012, 0.71), (0.0, 0.711)], segments=48)
        cover = top.finish('%s lid' % PART, collection, material, smooth=True, sharp=70.0)
        cover['jar_seed'] = jar['jar_seed']
        made.append(cover)
    return made
