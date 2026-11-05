"""
What this file does: the store's made materials, built in code (no photograph): old brass, old copper, glazed china,
weathered boards with peeling paint, wet bark, puddle water, a wet-ground film, rusty nail heads, a rust stain, rail steel,
smoke for a ribbon, six see-through stains (soot, damp, rust, mud, coal dust, ash) and four heavy ones for fronts seen
from 15 to 35 m (heavy soot, far soot, heavy damp with a salt line, leak), a slate roof, stove ash, trodden straw (the
litter tool's straw layer) and hedge leaves (the hedge tool). build_materials.py calls build_all().

Some of them read a number a tool writes on its meshes:
  - MADE • puddle water: 'shallow' on each point, 0 in the deep middle, 1 at the rim; where it is 1 the water is clear
    and the ground shows through. A mesh without it is deep water all over.
  - MADE • wet ground film: 'dry' on each point, 0 against the water, 1 at the film's outer edge; where it is 1 the film
    is gone. A mesh without it is wet all over.
  - MADE • rust stain and the ten MADE • stain ...: 'fade' on each point, 0 where the stain is strongest, 1 where it is
    gone (the walkway, stain, railing and downpipe tools write it). A mesh without it is stained all over.
  - MADE • straw: 'strand_random' and 'straw_shade' on the clump shapes, 'litter_tone', 'litter_mud' and 'wetness' on
    the points that lay them or on the draped straw itself (the litter tool writes them all). Without them every strand
    is a dark gold, dry and clean.
  - MADE • hedge leaves: 'leaf_random' on the spray shapes, 'hedge_tone', 'hedge_dry' and 'hedge_inner' on the points
    that place them (the hedge tool writes them all). Without them the leaves are near-black green.
"""

import bpy

from node_helpers import fresh_material, map_range, math, mix, noise, ramp, stretched

BRASS = {'polished': (0.78, 0.56, 0.24), 'tarnish': (0.11, 0.075, 0.035)}
COPPER = {'polished': (0.78, 0.40, 0.24), 'tarnish': (0.12, 0.05, 0.03), 'verdigris': (0.06, 0.19, 0.16)}
CHINA_GLAZES = [(0.0, (0.60, 0.56, 0.48)), (0.60, (0.46, 0.52, 0.56)), (0.82, (0.085, 0.040, 0.018))]


def _own_coordinates(nodes, links, spread=(17.0, 29.0, 11.0)):
    coordinates = nodes.new('ShaderNodeTexCoord')
    info = nodes.new('ShaderNodeObjectInfo')
    offset = nodes.new('ShaderNodeVectorMath')
    offset.operation = 'SCALE'
    offset.inputs[0].default_value = spread
    links.new(info.outputs['Random'], offset.inputs['Scale'])
    shifted = nodes.new('ShaderNodeVectorMath')
    shifted.operation = 'ADD'
    links.new(coordinates.outputs['Object'], shifted.inputs[0])
    links.new(offset.outputs['Vector'], shifted.inputs[1])
    return shifted.outputs['Vector'], info


def old_metal(name, copper=False):
    """Old brass or copper: polished where handled, tarnished in patches and in every hollow; copper turns blue-green."""
    material = fresh_material(name)
    nodes, links = material.node_tree.nodes, material.node_tree.links
    principled = nodes.get('Principled BSDF')
    colours = COPPER if copper else BRASS
    vector, _ = _own_coordinates(nodes, links)
    patches = noise(nodes, links, vector, 7.0, detail=5.0, roughness=0.62)
    patchy = map_range(nodes, links, patches, 0.50, 0.66, 0.0, 0.75)
    hollows = nodes.new('ShaderNodeAmbientOcclusion')
    hollows.samples = 8
    hollows.inputs['Distance'].default_value = 0.05
    hollow = map_range(nodes, links, hollows.outputs['AO'], 0.95, 0.55)
    tarnish = math(nodes, links, 'MAXIMUM', hollow, patchy)
    colour = mix(nodes, links, tarnish, colours['polished'], colours['tarnish'])
    metallic = math(nodes, links, 'MULTIPLY_ADD', tarnish, -0.5, 1.0)
    smudges = noise(nodes, links, vector, 23.0, detail=3.0)
    smooth = map_range(nodes, links, smudges, 0.3, 0.7, 0.20, 0.34)
    roughness = math(nodes, links, 'MAXIMUM', smooth, math(nodes, links, 'MULTIPLY', tarnish, 0.58))
    if copper:
        spots = noise(nodes, links, vector, 13.0, detail=4.0)
        spotty = map_range(nodes, links, spots, 0.52, 0.62)
        green = math(nodes, links, 'MULTIPLY', hollow, spotty)
        colour = mix(nodes, links, green, colour, colours['verdigris'])
        metallic = math(nodes, links, 'MULTIPLY_ADD', green, -1.0, metallic, clamp=True)
        roughness = math(nodes, links, 'MAXIMUM', roughness, math(nodes, links, 'MULTIPLY', green, 0.85))
    links.new(colour, principled.inputs['Base Color'])
    links.new(metallic, principled.inputs['Metallic'])
    links.new(roughness, principled.inputs['Roughness'])
    dents = noise(nodes, links, vector, 40.0, detail=2.0)
    bump = nodes.new('ShaderNodeBump')
    bump.inputs['Strength'].default_value = 0.06
    bump.inputs['Distance'].default_value = 0.002
    links.new(dents, bump.inputs['Height'])
    links.new(bump.outputs['Normal'], principled.inputs['Normal'])
    material.diffuse_color = (*colours['polished'], 1)
    return material


def glazed_china(name):
    """Glazed china: cream, pale blue-white or a teapot's dark brown, chosen per object; glossy under a clear coat."""
    material = fresh_material(name)
    nodes, links = material.node_tree.nodes, material.node_tree.links
    principled = nodes.get('Principled BSDF')
    vector, info = _own_coordinates(nodes, links)
    glaze = ramp(nodes, CHINA_GLAZES, 'CONSTANT')
    links.new(info.outputs['Random'], glaze.inputs[0])
    uneven = noise(nodes, links, vector, 35.0, detail=3.0)
    shade = map_range(nodes, links, uneven, 0.3, 0.7, 0.0, 0.14)
    colour = mix(nodes, links, shade, glaze.outputs['Color'], (0.20, 0.18, 0.15))
    links.new(colour, principled.inputs['Base Color'])
    principled.inputs['Roughness'].default_value = 0.16
    principled.inputs['Coat Weight'].default_value = 0.5
    principled.inputs['Coat Roughness'].default_value = 0.06
    material.diffuse_color = (0.6, 0.56, 0.48, 1)
    return material


def weathered_boards(name):
    """Weathered boards: grey wood with a shade per board (the mesh number 'board_tone', if present), rain streaks
    running down, and old paint left in peeling, cracked patches; one faded paint per building, by where it stands."""
    material = fresh_material(name)
    nodes, links = material.node_tree.nodes, material.node_tree.links
    principled = nodes.get('Principled BSDF')
    position = nodes.new('ShaderNodeNewGeometry').outputs['Position']
    tone = nodes.new('ShaderNodeAttribute')
    tone.attribute_type = 'GEOMETRY'
    tone.attribute_name = 'board_tone'
    info = nodes.new('ShaderNodeObjectInfo')
    fine = noise(nodes, links, position, 16.0, detail=6.0, roughness=0.55)
    mixed_tone = math(nodes, links, 'MULTIPLY_ADD', tone.outputs['Fac'], 0.65, math(nodes, links, 'MULTIPLY', fine, 0.45))
    bare = ramp(nodes, [(0.0, (0.045, 0.041, 0.036)), (0.45, (0.115, 0.105, 0.092)), (0.85, (0.215, 0.205, 0.185)), (1.0, (0.26, 0.25, 0.23))])
    links.new(mixed_tone, bare.inputs[0])
    paint = ramp(nodes, [(0.0, (0.36, 0.36, 0.33)), (0.2, (0.18, 0.25, 0.25)), (0.4, (0.11, 0.155, 0.23)),
                         (0.6, (0.12, 0.18, 0.12)), (0.8, (0.30, 0.27, 0.18)), (0.9, (0.07, 0.18, 0.18))], interpolation='CONSTANT')
    where = nodes.new('ShaderNodeTexNoise')
    where.inputs['Scale'].default_value = 0.045
    where.inputs['Detail'].default_value = 0.0
    links.new(info.outputs['Location'], where.inputs['Vector'])
    links.new(map_range(nodes, links, where.outputs['Fac'], 0.32, 0.68), paint.inputs[0])
    # paint flakes: smaller than a board's width and drawn out along the grain (weatherboards run level), so old paint
    # reads as flaking along the boards rather than as big blotches
    peel = noise(nodes, links, stretched(nodes, links, position, (1.0, 1.0, 2.6)), 5.2, detail=9.0, roughness=0.62, distortion=0.5)
    separate = nodes.new('ShaderNodeSeparateXYZ')
    links.new(position, separate.inputs['Vector'])
    low = map_range(nodes, links, separate.outputs['Z'], 0.0, 1.2, 0.10, 0.0)
    threshold = math(nodes, links, 'ADD', math(nodes, links, 'MULTIPLY_ADD', info.outputs['Random'], 0.16, 0.40), low)
    held = nodes.new('ShaderNodeMapRange')
    links.new(peel, held.inputs['Value'])
    links.new(math(nodes, links, 'SUBTRACT', threshold, 0.015), held.inputs['From Min'])
    links.new(math(nodes, links, 'ADD', threshold, 0.015), held.inputs['From Max'])
    voronoi = nodes.new('ShaderNodeTexVoronoi')
    voronoi.feature = 'DISTANCE_TO_EDGE'
    voronoi.inputs['Scale'].default_value = 34.0
    links.new(position, voronoi.inputs['Vector'])
    crack = map_range(nodes, links, voronoi.outputs['Distance'], 0.0, 0.05, 0.35, 1.0)
    cracked_paint = mix(nodes, links, 1.0, paint.outputs['Color'], crack, 'MULTIPLY')
    colour = mix(nodes, links, held.outputs['Result'], bare.outputs['Color'], cracked_paint)
    streak = noise(nodes, links, stretched(nodes, links, position, (1.7, 1.7, 0.085)), 1.0, detail=5.0, roughness=0.6)
    streak_ramp = ramp(nodes, [(0.32, (0.52, 0.52, 0.52)), (0.62, (1.0, 1.0, 1.0))])
    links.new(streak, streak_ramp.inputs[0])
    colour = mix(nodes, links, 1.0, colour, streak_ramp.outputs['Color'], 'MULTIPLY')
    links.new(colour, principled.inputs['Base Color'])
    links.new(map_range(nodes, links, fine, 0.0, 1.0, 0.48, 0.86), principled.inputs['Roughness'])
    bump = nodes.new('ShaderNodeBump')
    bump.inputs['Strength'].default_value = 0.22
    bump.inputs['Distance'].default_value = 0.002
    links.new(math(nodes, links, 'MULTIPLY_ADD', held.outputs['Result'], 0.6, math(nodes, links, 'MULTIPLY', fine, 0.4)), bump.inputs['Height'])
    links.new(bump.outputs['Normal'], principled.inputs['Normal'])
    material.diffuse_color = (0.13, 0.12, 0.11, 1)
    return material


def wet_bark(name):
    """Dark, wet, ringed bark: furrows running up the trunk and rings round it."""
    material = fresh_material(name)
    nodes, links = material.node_tree.nodes, material.node_tree.links
    principled = nodes.get('Principled BSDF')
    position = nodes.new('ShaderNodeNewGeometry').outputs['Position']
    furrow = noise(nodes, links, stretched(nodes, links, position, (7.0, 7.0, 0.7)), 1.0, detail=8.0, roughness=0.6)
    base = ramp(nodes, [(0.25, (0.028, 0.025, 0.021)), (0.7, (0.10, 0.088, 0.070)), (1.0, (0.15, 0.135, 0.11))])
    links.new(furrow, base.inputs[0])
    wave = nodes.new('ShaderNodeTexWave')
    wave.wave_type = 'BANDS'
    wave.bands_direction = 'Z'
    wave.inputs['Scale'].default_value = 3.6
    wave.inputs['Distortion'].default_value = 5.0
    wave.inputs['Detail'].default_value = 3.0
    links.new(position, wave.inputs['Vector'])
    rings = ramp(nodes, [(0.0, (0.5, 0.5, 0.5)), (0.25, (1.0, 1.0, 1.0))])
    links.new(wave.outputs['Fac'], rings.inputs[0])
    links.new(mix(nodes, links, 1.0, base.outputs['Color'], rings.outputs['Color'], 'MULTIPLY'), principled.inputs['Base Color'])
    principled.inputs['Roughness'].default_value = 0.62
    bump = nodes.new('ShaderNodeBump')
    bump.inputs['Strength'].default_value = 0.55
    bump.inputs['Distance'].default_value = 0.01
    links.new(math(nodes, links, 'ADD', furrow, math(nodes, links, 'MULTIPLY', wave.outputs['Fac'], 0.4)), bump.inputs['Height'])
    links.new(bump.outputs['Normal'], principled.inputs['Normal'])
    material.diffuse_color = (0.07, 0.06, 0.05, 1)
    return material


def puddle_water(name):
    """Puddle water: near-black, glossy, with a faint ripple that breaks the reflection; clear where it is shallow
    (the mesh number 'shallow', 1 at the rim), so the mud shows through at the edge instead of a hard cut. The dial node
    'Rain' (0 by default; 1 steady rain) adds rings spreading from raindrops."""
    material = fresh_material(name)
    nodes, links = material.node_tree.nodes, material.node_tree.links
    principled = nodes.get('Principled BSDF')
    position = nodes.new('ShaderNodeNewGeometry').outputs['Position']
    shallow = nodes.new('ShaderNodeAttribute')
    shallow.attribute_type = 'GEOMETRY'
    shallow.attribute_name = 'shallow'
    breakup = noise(nodes, links, position, 6.0, detail=4.0, roughness=0.6)
    edge = math(nodes, links, 'ADD', shallow.outputs['Fac'], math(nodes, links, 'MULTIPLY_ADD', breakup, 0.5, -0.25))
    alpha = map_range(nodes, links, edge, 0.55, 0.95, 1.0, 0.0)
    links.new(alpha, principled.inputs['Alpha'])
    colour = mix(nodes, links, map_range(nodes, links, edge, 0.3, 0.9), (0.006, 0.008, 0.010), (0.030, 0.026, 0.020))
    links.new(colour, principled.inputs['Base Color'])
    rough = map_range(nodes, links, noise(nodes, links, position, 3.0, detail=2.0), 0.3, 0.7, 0.02, 0.08)
    links.new(rough, principled.inputs['Roughness'])
    principled.inputs['IOR'].default_value = 1.333
    ripple = noise(nodes, links, stretched(nodes, links, position, (1.0, 1.0, 0.0)), 22.0, detail=3.0, roughness=0.5)
    swell = noise(nodes, links, stretched(nodes, links, position, (1.0, 1.0, 0.0)), 2.5, detail=1.0)
    height = math(nodes, links, 'MULTIPLY_ADD', swell, 2.0, ripple)
    # rain: rings spreading from drops on the water, each drop its own size; the dial 'Rain' (0 none, 1 steady rain)
    rain = nodes.new('ShaderNodeValue')
    rain.name = rain.label = 'Rain'
    rain.outputs[0].default_value = 0.0
    drops = nodes.new('ShaderNodeTexVoronoi')
    drops.inputs['Scale'].default_value = 6.0
    links.new(stretched(nodes, links, position, (1.0, 1.0, 0.0)), drops.inputs['Vector'])
    which = nodes.new('ShaderNodeSeparateColor')
    links.new(drops.outputs['Color'], which.inputs['Color'])
    reach = math(nodes, links, 'MULTIPLY_ADD', which.outputs['Red'], 0.35, 0.1)
    spread = drops.outputs['Distance']
    wave = math(nodes, links, 'SINE', math(nodes, links, 'MULTIPLY', spread, 2.0 * 3.14159 / 0.07))
    fading = math(nodes, links, 'SUBTRACT', 1.0, map_range(nodes, links, math(nodes, links, 'SUBTRACT', spread, reach), -0.15, 0.0))
    fading = math(nodes, links, 'MULTIPLY', fading, map_range(nodes, links, spread, 0.0, 0.02))
    fading = math(nodes, links, 'MULTIPLY', fading, math(nodes, links, 'GREATER_THAN', which.outputs['Green'], 0.35))
    rings = math(nodes, links, 'MULTIPLY', math(nodes, links, 'MULTIPLY', wave, fading), rain.outputs[0])
    height = math(nodes, links, 'MULTIPLY_ADD', rings, 1.5, height)
    bump = nodes.new('ShaderNodeBump')
    bump.inputs['Strength'].default_value = 0.1
    bump.inputs['Distance'].default_value = 0.004
    links.new(height, bump.inputs['Height'])
    links.new(bump.outputs['Normal'], principled.inputs['Normal'])
    material.surface_render_method = 'DITHERED'
    material.diffuse_color = (0.01, 0.012, 0.014, 1)
    return material


def wet_ground_film(name):
    """A wet film over ground: darker and glossy, thinning out in broken patches towards its outer edge (the mesh
    number 'dry', 1 at the outer edge). Lay it a few millimetres above the ground round a puddle or under a drip."""
    material = fresh_material(name)
    nodes, links = material.node_tree.nodes, material.node_tree.links
    principled = nodes.get('Principled BSDF')
    position = nodes.new('ShaderNodeNewGeometry').outputs['Position']
    dry = nodes.new('ShaderNodeAttribute')
    dry.attribute_type = 'GEOMETRY'
    dry.attribute_name = 'dry'
    patches = noise(nodes, links, position, 4.5, detail=5.0, roughness=0.65)
    wet = math(nodes, links, 'SUBTRACT', math(nodes, links, 'SUBTRACT', 1.0, dry.outputs['Fac']), math(nodes, links, 'MULTIPLY_ADD', patches, 0.6, -0.3))
    alpha = map_range(nodes, links, wet, 0.15, 0.55, 0.0, 0.78)
    links.new(alpha, principled.inputs['Alpha'])
    principled.inputs['Base Color'].default_value = (0.020, 0.018, 0.015, 1)
    # the sheen broken up: rougher grains in the film, and a fine relief so a lamp behind it glints instead of blooming
    grains = noise(nodes, links, position, 38.0, detail=4.0, roughness=0.6)
    rough = math(nodes, links, 'ADD', map_range(nodes, links, patches, 0.3, 0.7, 0.10, 0.28), map_range(nodes, links, grains, 0.45, 0.75, 0.0, 0.3))
    links.new(rough, principled.inputs['Roughness'])
    bump = nodes.new('ShaderNodeBump')
    bump.inputs['Strength'].default_value = 0.25
    bump.inputs['Distance'].default_value = 0.0025
    links.new(math(nodes, links, 'MULTIPLY_ADD', grains, 0.6, math(nodes, links, 'MULTIPLY', patches, 0.4)), bump.inputs['Height'])
    links.new(bump.outputs['Normal'], principled.inputs['Normal'])
    material.surface_render_method = 'DITHERED'
    material.diffuse_color = (0.02, 0.018, 0.015, 1)
    return material


def rusty_nail_heads(name):
    """Iron nail and bolt heads gone to rust: near-black iron with orange-brown rust in patches, rough."""
    material = fresh_material(name)
    nodes, links = material.node_tree.nodes, material.node_tree.links
    principled = nodes.get('Principled BSDF')
    vector, _ = _own_coordinates(nodes, links)
    patches = noise(nodes, links, vector, 140.0, detail=3.0, roughness=0.6)
    rusty = map_range(nodes, links, patches, 0.38, 0.62)
    links.new(mix(nodes, links, rusty, (0.028, 0.026, 0.024), (0.10, 0.042, 0.016)), principled.inputs['Base Color'])
    links.new(math(nodes, links, 'MULTIPLY_ADD', rusty, -0.35, 0.35), principled.inputs['Metallic'])
    links.new(map_range(nodes, links, rusty, 0.0, 1.0, 0.55, 0.92), principled.inputs['Roughness'])
    material.diffuse_color = (0.06, 0.032, 0.018, 1)
    return material


def rust_stain(name):
    """A rust stain run out from a nail, bolt or fitting: dark orange-brown, matte, soaked into the surface under it,
    fading out along its length (the mesh number 'fade': 0 at the start, 1 where it is gone) and at its edges."""
    material = fresh_material(name)
    nodes, links = material.node_tree.nodes, material.node_tree.links
    principled = nodes.get('Principled BSDF')
    position = nodes.new('ShaderNodeNewGeometry').outputs['Position']
    fade = nodes.new('ShaderNodeAttribute')
    fade.attribute_type = 'GEOMETRY'
    fade.attribute_name = 'fade'
    blotch = noise(nodes, links, position, 160.0, detail=4.0, roughness=0.65)
    strength = math(nodes, links, 'SUBTRACT', math(nodes, links, 'SUBTRACT', 1.0, fade.outputs['Fac']),
                    math(nodes, links, 'MULTIPLY_ADD', blotch, 0.7, -0.35))
    links.new(map_range(nodes, links, strength, 0.05, 0.75, 0.0, 0.85), principled.inputs['Alpha'])
    links.new(mix(nodes, links, map_range(nodes, links, blotch, 0.3, 0.7), (0.075, 0.028, 0.010), (0.040, 0.016, 0.007)),
              principled.inputs['Base Color'])
    principled.inputs['Roughness'].default_value = 0.9
    material.surface_render_method = 'DITHERED'
    material.diffuse_color = (0.06, 0.024, 0.01, 1)
    return material


def rail_steel(name):
    """Rail steel: the running top polished bright by wheels, the sides and foot rusted dark brown; chosen by which way
    each face points (up: polished), so it needs no numbers on the mesh. From the goods yard builder of log 51."""
    material = fresh_material(name)
    nodes, links = material.node_tree.nodes, material.node_tree.links
    principled = nodes.get('Principled BSDF')
    normal = nodes.new('ShaderNodeNewGeometry').outputs['Normal']
    separate = nodes.new('ShaderNodeSeparateXYZ')
    links.new(normal, separate.inputs[0])
    vector, _ = _own_coordinates(nodes, links)
    speckle = noise(nodes, links, vector, 5.0, detail=8.0)
    facing_up = math(nodes, links, 'ADD', separate.outputs['Z'], math(nodes, links, 'MULTIPLY', speckle, 0.35))
    # only the running top: faces that point up AND lie near the top of the rail (its own box, 0 at the foot, 1 at the
    # top), so the upper faces of the foot stay rusty
    height = nodes.new('ShaderNodeSeparateXYZ')
    links.new(nodes.new('ShaderNodeTexCoord').outputs['Generated'], height.inputs[0])
    facing_up = math(nodes, links, 'MULTIPLY', facing_up, map_range(nodes, links, height.outputs['Z'], 0.7, 0.88))
    links.new(map_range(nodes, links, facing_up, 0.55, 0.9), principled.inputs['Metallic'])
    colour = ramp(nodes, [(0.55, (0.09, 0.04, 0.025)), (0.9, (0.30, 0.27, 0.25))])
    links.new(facing_up, colour.inputs[0])
    links.new(colour.outputs['Color'], principled.inputs['Base Color'])
    links.new(map_range(nodes, links, facing_up, 0.3, 0.9, 0.7, 0.22), principled.inputs['Roughness'])
    material.diffuse_color = (0.12, 0.07, 0.05, 1)
    return material


def smoke_ribbon(name):
    """Smoke for a ribbon that faces the viewer (the smoke ribbon tool makes one): soft grey-blue, see-through, broken up,
    fading at its edges and out along its length, faintly warm low down where a fire lights it. It reads the ribbon's UV
    map: across 0 to 1, along 0 (the chimney) to 1 (where it has gone)."""
    material = fresh_material(name)
    nodes, links = material.node_tree.nodes, material.node_tree.links
    principled = nodes.get('Principled BSDF')
    uv = nodes.new('ShaderNodeTexCoord').outputs['UV']
    separate = nodes.new('ShaderNodeSeparateXYZ')
    links.new(uv, separate.inputs[0])
    billows = noise(nodes, links, stretched(nodes, links, uv, (1.0, 2.2, 1.0)), 3.5, detail=10.0, roughness=0.65)
    puffs = map_range(nodes, links, billows, 0.25, 0.75, 0.35, 1.0)
    edge = math(nodes, links, 'ABSOLUTE', math(nodes, links, 'MULTIPLY_ADD', separate.outputs['X'], 2.0, -1.0))
    across = math(nodes, links, 'SUBTRACT', 1.0, math(nodes, links, 'POWER', edge, 2.2))         # broad: solid most of the way across
    left = math(nodes, links, 'POWER', math(nodes, links, 'SUBTRACT', 1.0, separate.outputs['Y']), 0.7)
    starts = math(nodes, links, 'MINIMUM', math(nodes, links, 'MULTIPLY', separate.outputs['Y'], 40.0), 1.0)
    body = math(nodes, links, 'MULTIPLY', math(nodes, links, 'MULTIPLY', math(nodes, links, 'MULTIPLY', across, puffs), left), starts)
    links.new(map_range(nodes, links, body, 0.06, 0.45, 0.0, 0.75), principled.inputs['Alpha'])
    links.new(mix(nodes, links, map_range(nodes, links, billows, 0.3, 0.7), (0.045, 0.055, 0.08), (0.11, 0.12, 0.14)), principled.inputs['Base Color'])
    principled.inputs['Roughness'].default_value = 1.0
    principled.inputs['Emission Color'].default_value = (1.0, 0.5, 0.2, 1.0)
    links.new(math(nodes, links, 'MULTIPLY', math(nodes, links, 'POWER', left, 3.0), 0.08), principled.inputs['Emission Strength'])
    material.surface_render_method = 'DITHERED'
    material.diffuse_color = (0.08, 0.09, 0.11, 1)
    return material


STAINS = {
    # kind: colour (linear), roughness, streaked downwards, strongest alpha
    'soot': ((0.012, 0.012, 0.014), 0.9, True, 0.92),
    'damp': ((0.014, 0.020, 0.014), 0.42, True, 0.88),
    'rust': ((0.095, 0.036, 0.011), 0.85, True, 0.80),
    'mud': ((0.020, 0.014, 0.008), 0.35, False, 0.85),
    'coal dust': ((0.004, 0.004, 0.005), 0.32, False, 0.75),
    'ash': ((0.17, 0.165, 0.15), 0.9, False, 0.70),
}


def stain(name, kind):
    """A see-through stain to lay a few millimetres in front of a wall or on the ground (the stain tool makes the
    planes): one flat colour, its alpha the mesh number 'fade' (0 where the stain is strongest, 1 where it is gone)
    broken up by noise: soot, damp and rust are streaked downwards (the world's Z, so any wall's way), mud, coal dust
    and ash are blotched. From the chapel builders' `stain` and `smear` (log 51)."""
    colour, roughness, streaked, strongest = STAINS[kind]
    material = fresh_material(name)
    nodes, links = material.node_tree.nodes, material.node_tree.links
    principled = nodes.get('Principled BSDF')
    position = nodes.new('ShaderNodeNewGeometry').outputs['Position']
    fade = nodes.new('ShaderNodeAttribute')
    fade.attribute_type = 'GEOMETRY'
    fade.attribute_name = 'fade'
    if streaked:
        # drawn out downwards: fine across, long along Z; a broad noise makes some runs heavier than others
        runs = noise(nodes, links, stretched(nodes, links, position, (16.0, 16.0, 1.4)), 1.0, detail=6.0, roughness=0.55)
        breakup = map_range(nodes, links, runs, 0.3, 0.75, 0.1, 1.6)
        broad = map_range(nodes, links, noise(nodes, links, stretched(nodes, links, position, (3.0, 3.0, 0.5)), 1.0, detail=3.0), 0.35, 0.65, 0.45, 1.25)
    else:
        blotch = noise(nodes, links, position, 6.0, detail=8.0, roughness=0.6)
        breakup = map_range(nodes, links, blotch, 0.32, 0.66, 0.15, 1.6)
        broad = map_range(nodes, links, noise(nodes, links, position, 1.6, detail=3.0), 0.35, 0.65, 0.5, 1.2)
    left = math(nodes, links, 'POWER', math(nodes, links, 'SUBTRACT', 1.0, fade.outputs['Fac'], clamp=True), 0.7)   # holds on, then goes
    strength = math(nodes, links, 'MULTIPLY', left, math(nodes, links, 'MULTIPLY', breakup, broad))
    links.new(math(nodes, links, 'MULTIPLY', strength, strongest, clamp=True), principled.inputs['Alpha'])
    grain = noise(nodes, links, position, 40.0, detail=3.0)
    links.new(mix(nodes, links, map_range(nodes, links, grain, 0.3, 0.7, 0.0, 0.5), colour, tuple(c * 0.55 for c in colour)), principled.inputs['Base Color'])
    links.new(map_range(nodes, links, grain, 0.3, 0.7, roughness - 0.08, roughness + 0.08), principled.inputs['Roughness'])
    principled.inputs['Specular IOR Level'].default_value = 0.3 if roughness > 0.6 else 0.5
    material.surface_render_method = 'DITHERED'
    material.diffuse_color = (*colour, 1)
    return material


HEAVY_STAINS = {
    # kind: colour (linear), roughness, where the stain starts and where it is full (in 1 - fade, with the ragged edge
    # added), how ragged its edge is, the streaks' stretch (across, across, up), how much the streaks break it, strongest
    'heavy soot': ((0.010, 0.0085, 0.0075), 0.92, 0.02, 0.50, 0.30, (6.0, 6.0, 0.42), 0.62, 0.95),
    'far soot': ((0.009, 0.008, 0.007), 0.92, 0.00, 0.38, 0.30, (3.0, 3.0, 0.38), 0.50, 1.00),
    'heavy damp': ((0.016, 0.021, 0.013), 0.42, 0.22, 0.40, 0.42, (6.0, 6.0, 0.80), 0.35, 0.86),
    'leak': ((0.013, 0.019, 0.011), 0.38, 0.05, 0.55, 0.25, (6.0, 6.0, 0.40), 0.60, 0.90),
}
SALT = (0.20, 0.19, 0.165)


def heavy_stain(name, kind):
    """A see-through stain pushed hard enough to show on a front 15 to 35 m away: its alpha is the mesh number 'fade'
    (0 strongest, 1 gone) cut at a ragged edge, so the stain holds nearly full strength and then stops along a broken
    line instead of fading out, and broken by runs stretched up and down. 'far soot' has broader runs, for fronts 25 m
    and more away; 'heavy damp' carries a pale salt line along its edge (the tide line of rising damp); 'leak' is the
    green-black of water overflowing a gutter or a downpipe's socket. From `wear_mat` in the third street builder's
    script (log 55), on the world's coordinates so no two planes share one pattern."""
    colour, roughness, low, high, ragged, stretch, streak_amount, strongest = HEAVY_STAINS[kind]
    material = fresh_material(name)
    nodes, links = material.node_tree.nodes, material.node_tree.links
    principled = nodes.get('Principled BSDF')
    position = nodes.new('ShaderNodeNewGeometry').outputs['Position']
    fade = nodes.new('ShaderNodeAttribute')
    fade.attribute_type = 'GEOMETRY'
    fade.attribute_name = 'fade'
    held = math(nodes, links, 'SUBTRACT', 1.0, fade.outputs['Fac'])
    runs = map_range(nodes, links, noise(nodes, links, stretched(nodes, links, position, stretch), 1.0, detail=5.0, roughness=0.62), 0.34, 0.66)
    runs = math(nodes, links, 'MULTIPLY_ADD', runs, streak_amount, 1.0 - streak_amount)
    edge = noise(nodes, links, stretched(nodes, links, position, (3.2, 3.2, 2.2)), 1.0, detail=6.0, roughness=0.7)
    reach = math(nodes, links, 'ADD', held, math(nodes, links, 'MULTIPLY_ADD', edge, ragged, -0.5 * ragged))
    dark = math(nodes, links, 'MULTIPLY', map_range(nodes, links, reach, low, high, 0.0, strongest), runs, clamp=True)
    grain = noise(nodes, links, position, 40.0, detail=3.0)
    stained = mix(nodes, links, map_range(nodes, links, grain, 0.3, 0.7, 0.0, 0.5), colour, tuple(c * 0.6 for c in colour))
    if kind == 'heavy damp':
        # salt dried out along the tide line: a pale band just outside the dark, where the reach is a little short of it
        band = math(nodes, links, 'MULTIPLY', map_range(nodes, links, reach, low - 0.09, low - 0.035),
                    map_range(nodes, links, reach, low - 0.035, low + 0.02, 1.0, 0.0))
        salt = math(nodes, links, 'MULTIPLY', band, map_range(nodes, links, grain, 0.25, 0.65, 0.25, 0.55))
        alpha = math(nodes, links, 'ADD', dark, math(nodes, links, 'MULTIPLY', salt, math(nodes, links, 'SUBTRACT', 1.0, dark)), clamp=True)
        share = math(nodes, links, 'DIVIDE', dark, math(nodes, links, 'MAXIMUM', alpha, 0.0001), clamp=True)
        stained = mix(nodes, links, share, SALT, stained)
    else:
        alpha = dark
    links.new(alpha, principled.inputs['Alpha'])
    links.new(stained, principled.inputs['Base Color'])
    links.new(map_range(nodes, links, grain, 0.3, 0.7, roughness - 0.06, roughness + 0.06), principled.inputs['Roughness'])
    principled.inputs['Specular IOR Level'].default_value = 0.3 if roughness > 0.6 else 0.5
    material.surface_render_method = 'DITHERED'
    material.diffuse_color = (*colour, 1)
    return material


def _real_sized_coordinates(nodes, links):
    """The object's own coordinates with its unapplied scale undone: multiplied by the object number 'pp_scale'
    (store.prepare_for_render records it; where none was recorded the scale is taken as 1). The same logic as
    build_materials.py's box_coordinates_group, copied here so a made material carries it itself."""
    coordinates = nodes.new('ShaderNodeTexCoord')
    scale_attribute = nodes.new('ShaderNodeAttribute')
    scale_attribute.attribute_type = 'OBJECT'
    scale_attribute.attribute_name = 'pp_scale'

    def vmath(operation, a, b=None):
        node = nodes.new('ShaderNodeVectorMath')
        node.operation = operation
        for socket, value in zip(node.inputs, (a, b)):
            if value is None:
                continue
            if isinstance(value, bpy.types.NodeSocket):
                links.new(value, socket)
            else:
                socket.default_value = value
        return node.outputs[0]

    absolute = vmath('ABSOLUTE', scale_attribute.outputs['Vector'])
    missing = vmath('SUBTRACT', (1.0, 1.0, 1.0), vmath('SIGN', absolute))       # 1 where no scale was recorded
    real_scale = vmath('ADD', absolute, missing)
    return vmath('MULTIPLY', coordinates.outputs['Object'], real_scale)


def slate_roof(name):
    """A slate roof in courses: dark blue-grey slates, each a little different, the lap lines and the slates' lower
    edges in relief, a wet sheen. Laid in the object's own coordinates: slates sit side by side along X, courses climb
    along Y (a plane whose eave runs along X and that rises along its own Y, pitched by turning the object). Slates are
    0.28 m wide, courses 0.22 m. The object's unapplied scale is undone first (the object number 'pp_scale' that
    store.prepare_for_render records; absent means 1), the way the SURFACE materials' box coordinates do, so a plane
    scaled 4 x 2.5 still shows 0.28 m slates. From `slate_courses` in the chapel builder's script (log 51)."""
    material = fresh_material(name)
    nodes, links = material.node_tree.nodes, material.node_tree.links
    principled = nodes.get('Principled BSDF')
    own = _real_sized_coordinates(nodes, links)
    brick = nodes.new('ShaderNodeTexBrick')
    brick.offset = 0.5
    brick.inputs['Color1'].default_value = (0.030, 0.038, 0.050, 1)
    brick.inputs['Color2'].default_value = (0.070, 0.078, 0.092, 1)
    brick.inputs['Mortar'].default_value = (0.006, 0.008, 0.011, 1)
    brick.inputs['Scale'].default_value = 1.0
    brick.inputs['Mortar Size'].default_value = 0.006
    brick.inputs['Mortar Smooth'].default_value = 0.3
    brick.inputs['Bias'].default_value = 0.0
    brick.inputs['Brick Width'].default_value = 0.28
    brick.inputs['Row Height'].default_value = 0.22
    links.new(own, brick.inputs['Vector'])
    # each course laps the one below: a sawtooth up Y, the slate's lower edge standing proud
    separate = nodes.new('ShaderNodeSeparateXYZ')
    links.new(own, separate.inputs[0])
    course = math(nodes, links, 'FRACT', math(nodes, links, 'DIVIDE', separate.outputs['Y'], 0.22))
    lap = map_range(nodes, links, course, 0.0, 0.08, 0.0, 1.0)
    weathering = noise(nodes, links, own, 1.4, detail=8.0, roughness=0.6)
    tone = ramp(nodes, [(0.3, (0.55, 0.58, 0.62)), (0.7, (1.0, 1.0, 1.0))])
    links.new(weathering, tone.inputs[0])
    colour = mix(nodes, links, 0.9, brick.outputs['Color'], tone.outputs['Color'], 'MULTIPLY')
    wet = noise(nodes, links, stretched(nodes, links, own, (1.0, 3.0, 1.0)), 2.5, detail=3.0)
    colour = mix(nodes, links, map_range(nodes, links, wet, 0.35, 0.65, 0.0, 0.5), colour, (0.012, 0.016, 0.022))
    links.new(colour, principled.inputs['Base Color'])
    links.new(map_range(nodes, links, wet, 0.3, 0.7, 0.22, 0.42), principled.inputs['Roughness'])
    principled.inputs['Coat Weight'].default_value = 0.25
    principled.inputs['Coat Roughness'].default_value = 0.15
    grain = noise(nodes, links, own, 30.0, detail=4.0)
    height = math(nodes, links, 'ADD', math(nodes, links, 'MULTIPLY', lap, 0.6),
                  math(nodes, links, 'MULTIPLY_ADD', brick.outputs['Fac'], -0.5, math(nodes, links, 'MULTIPLY', grain, 0.15)))
    bump = nodes.new('ShaderNodeBump')
    bump.inputs['Strength'].default_value = 0.7
    bump.inputs['Distance'].default_value = 0.012
    links.new(height, bump.inputs['Height'])
    links.new(bump.outputs['Normal'], principled.inputs['Normal'])
    material.diffuse_color = (0.04, 0.05, 0.06, 1)
    return material


def ash(name):
    """Grey stove ash with clinker, matte, for heaps and spills: pale grey ash in lumps and fine dust, darker burnt
    clinker lumps through it. In the object's own coordinates. From `ash_mat` in the chapel dresser's script (log 51)."""
    material = fresh_material(name)
    nodes, links = material.node_tree.nodes, material.node_tree.links
    principled = nodes.get('Principled BSDF')
    own = nodes.new('ShaderNodeTexCoord').outputs['Object']
    lumps = noise(nodes, links, own, 45.0, detail=10.0, roughness=0.75)
    shade = ramp(nodes, [(0.38, (0.040, 0.040, 0.042)), (0.68, (0.30, 0.285, 0.26))])
    links.new(lumps, shade.inputs[0])
    clinker = nodes.new('ShaderNodeTexVoronoi')
    clinker.inputs['Scale'].default_value = 28.0
    clinker.inputs['Randomness'].default_value = 1.0
    warp = nodes.new('ShaderNodeTexNoise')                      # the cells warped, so no two clinker lumps are alike
    warp.inputs['Scale'].default_value = 9.0
    warp.inputs['Detail'].default_value = 2.0
    links.new(own, warp.inputs['Vector'])
    warped = nodes.new('ShaderNodeVectorMath')
    warped.operation = 'MULTIPLY_ADD'
    warped.inputs[1].default_value = (0.12, 0.12, 0.12)
    links.new(warp.outputs['Color'], warped.inputs[0])
    links.new(own, warped.inputs[2])
    links.new(warped.outputs['Vector'], clinker.inputs['Vector'])
    size = map_range(nodes, links, noise(nodes, links, own, 12.0, detail=2.0), 0.4, 0.62, 0.12, 0.34)
    burnt = nodes.new('ShaderNodeMapRange')
    burnt.clamp = True
    links.new(clinker.outputs['Distance'], burnt.inputs['Value'])
    links.new(math(nodes, links, 'SUBTRACT', size, 0.1), burnt.inputs['From Min'])
    links.new(size, burnt.inputs['From Max'])
    burnt.inputs['To Min'].default_value = 1.0
    burnt.inputs['To Max'].default_value = 0.0
    burnt = burnt.outputs['Result']
    colour = mix(nodes, links, burnt, shade.outputs['Color'], (0.020, 0.016, 0.014))
    links.new(colour, principled.inputs['Base Color'])
    links.new(map_range(nodes, links, burnt, 0.0, 1.0, 0.92, 0.7), principled.inputs['Roughness'])
    principled.inputs['Specular IOR Level'].default_value = 0.2
    bump = nodes.new('ShaderNodeBump')
    bump.inputs['Strength'].default_value = 1.0
    bump.inputs['Distance'].default_value = 0.01
    links.new(math(nodes, links, 'ADD', lumps, math(nodes, links, 'MULTIPLY', burnt, 0.6)), bump.inputs['Height'])
    links.new(bump.outputs['Normal'], principled.inputs['Normal'])
    material.diffuse_color = (0.18, 0.17, 0.16, 1)
    return material


def _attribute(nodes, name, kind='GEOMETRY'):
    node = nodes.new('ShaderNodeAttribute')
    node.attribute_type = kind
    node.attribute_name = name
    return node.outputs['Fac']


def straw(name):
    """Dropped and trodden straw for the litter tool's 'straw' layer: dull gold to grey-brown strands, kept in the look's
    range (pale straw in a dusk picture reads as stars); each strand its own shade ('strand_random' on the clump shape),
    the outer and lower strands of a clump darker ('straw_shade', 0 dark to 1 light, on the shape); trodden into the mud
    muddy and dark ('litter_mud' from the point that lays the clump), dark and a little glossy when wet ('wetness');
    each clump its own tone ('litter_tone'). From the barn builders' 'dropped straw' (log 54), toned down."""
    material = fresh_material(name)
    nodes, links = material.node_tree.nodes, material.node_tree.links
    principled = nodes.get('Principled BSDF')
    output = nodes.get('Material Output')
    strand = _attribute(nodes, 'strand_random')
    shade = _attribute(nodes, 'straw_shade')
    # the litter tool drapes the straw onto the ground (its copies made real), so the clump's numbers come on the
    # straw's own points; read from the point that places a copy as well, for straw laid as live copies
    tone = math(nodes, links, 'ADD', _attribute(nodes, 'litter_tone'), _attribute(nodes, 'litter_tone', 'INSTANCER'))
    mud = math(nodes, links, 'ADD', _attribute(nodes, 'litter_mud'), _attribute(nodes, 'litter_mud', 'INSTANCER'))
    wet = math(nodes, links, 'MAXIMUM', _attribute(nodes, 'wetness'), _attribute(nodes, 'wetness', 'INSTANCER'))
    golds = ramp(nodes, [(0.0, (0.085, 0.064, 0.03)), (0.45, (0.15, 0.113, 0.052)), (0.8, (0.2, 0.155, 0.072)),
                         (1.0, (0.23, 0.18, 0.088))])
    links.new(math(nodes, links, 'MULTIPLY_ADD', strand, 0.65, math(nodes, links, 'MULTIPLY', tone, 0.35)), golds.inputs[0])
    darker = map_range(nodes, links, shade, 0.0, 1.0, 0.35, 1.0)
    colour = mix(nodes, links, 1.0, golds.outputs['Color'], darker, 'MULTIPLY')
    muddy = math(nodes, links, 'MULTIPLY', mud, map_range(nodes, links, shade, 0.0, 1.0, 0.95, 0.55))
    colour = mix(nodes, links, muddy, colour, (0.032, 0.023, 0.014))
    colour = mix(nodes, links, 1.0, colour, math(nodes, links, 'MULTIPLY_ADD', wet, -0.3, 1.0), 'MULTIPLY')
    links.new(colour, principled.inputs['Base Color'])
    principled.inputs['Roughness'].default_value = 0.6
    principled.inputs['Specular IOR Level'].default_value = 0.25
    links.new(math(nodes, links, 'MULTIPLY', map_range(nodes, links, wet, 0.3, 0.8), 0.15), principled.inputs['Coat Weight'])
    principled.inputs['Coat Roughness'].default_value = 0.2
    through = nodes.new('ShaderNodeBsdfTranslucent')
    links.new(mix(nodes, links, 1.0, colour, (1.3, 1.3, 1.3), 'MULTIPLY'), through.inputs['Color'])
    both = nodes.new('ShaderNodeMixShader')
    both.inputs['Fac'].default_value = 0.15
    links.new(principled.outputs['BSDF'], both.inputs[1])
    links.new(through.outputs['BSDF'], both.inputs[2])
    links.new(both.outputs['Shader'], output.inputs['Surface'])
    material.diffuse_color = (0.14, 0.105, 0.05, 1.0)
    return material


def hedge_leaves(name):
    """Leaves for the hedge tool: hawthorn and hazel greens from near-black to olive, some turned russet brown; each
    leaf its own shade ('leaf_random' on the spray), each spray its own ('hedge_tone'), browner where the hedge tool says
    it is turning ('hedge_dry'), darker deep inside the hedge where little light gets in ('hedge_inner', 0 at its skin
    to 1 deep in); lit through a little from behind. The barn builder's hedge was one dark green."""
    material = fresh_material(name)
    nodes, links = material.node_tree.nodes, material.node_tree.links
    principled = nodes.get('Principled BSDF')
    output = nodes.get('Material Output')
    leaf = _attribute(nodes, 'leaf_random')
    tone = _attribute(nodes, 'hedge_tone', 'INSTANCER')
    dry = _attribute(nodes, 'hedge_dry', 'INSTANCER')
    inner = _attribute(nodes, 'hedge_inner', 'INSTANCER')
    greens = ramp(nodes, [(0.0, (0.011, 0.02, 0.008)), (0.4, (0.024, 0.038, 0.012)), (0.75, (0.042, 0.056, 0.017)),
                          (1.0, (0.058, 0.066, 0.021))])
    links.new(math(nodes, links, 'MULTIPLY_ADD', tone, 0.7, math(nodes, links, 'MULTIPLY', leaf, 0.3)), greens.inputs[0])
    browns = ramp(nodes, [(0.0, (0.045, 0.026, 0.011)), (0.6, (0.085, 0.052, 0.02)), (1.0, (0.115, 0.075, 0.028))])
    links.new(leaf, browns.inputs[0])
    turning = map_range(nodes, links, math(nodes, links, 'ADD', dry, math(nodes, links, 'MULTIPLY_ADD', leaf, 0.5, -0.25)), 0.45, 0.7)
    colour = mix(nodes, links, turning, greens.outputs['Color'], browns.outputs['Color'])
    colour = mix(nodes, links, 1.0, colour, math(nodes, links, 'MULTIPLY_ADD', inner, -0.65, 1.0), 'MULTIPLY')
    links.new(colour, principled.inputs['Base Color'])
    principled.inputs['Roughness'].default_value = 0.5
    principled.inputs['Specular IOR Level'].default_value = 0.4
    through = nodes.new('ShaderNodeBsdfTranslucent')
    links.new(mix(nodes, links, 1.0, colour, (1.5, 1.5, 1.5), 'MULTIPLY'), through.inputs['Color'])
    both = nodes.new('ShaderNodeMixShader')
    both.inputs['Fac'].default_value = 0.3
    links.new(principled.outputs['BSDF'], both.inputs[1])
    links.new(through.outputs['BSDF'], both.inputs[2])
    links.new(both.outputs['Shader'], output.inputs['Surface'])
    material.diffuse_color = (0.03, 0.045, 0.015, 1.0)
    return material


MADE = {
    'MADE • old brass': (lambda n: old_metal(n, copper=False), 'old brass: polished where handled, tarnished in patches and every hollow (urns, lamps, shell cases, fittings)'),
    'MADE • old copper': (lambda n: old_metal(n, copper=True), 'old copper: as brass, warmer, blue-green verdigris in the hollows (kettles, pipes, boilers)'),
    'MADE • glazed china': (glazed_china, 'glazed china: cream, pale blue-white or teapot brown, chosen per object (cups, pots, jugs)'),
    'MADE • weathered boards, peeling paint': (weathered_boards, 'grey weathered boards with old paint peeling in patches, rain streaks; one paint per building'),
    'MADE • wet bark': (wet_bark, 'dark wet ringed bark (tree trunks, poles left in the round)'),
    'MADE • puddle water': (puddle_water, "puddle water: near-black, glossy, a faint ripple, clear at the shallow rim (needs the mesh number 'shallow'; the puddle tool writes it)"),
    'MADE • wet ground film': (wet_ground_film, "a wet film to lay over ground: darker and glossy, breaking up towards its edge (mesh number 'dry'; the puddle tool writes it)"),
    'MADE • rusty nail heads': (rusty_nail_heads, 'rusty iron nail and bolt heads: near-black iron, rust in patches'),
    'MADE • rail steel': (rail_steel, 'rail steel: the running top polished by wheels, the sides and foot rusted dark (by which way each face points)'),
    'MADE • smoke ribbon': (smoke_ribbon, "smoke for a ribbon facing the viewer: soft, see-through, broken up, fading out (the smoke ribbon tool's UV map)"),
    'MADE • rust stain': (rust_stain, "a rust stain run out from a nail or bolt, fading along its length (mesh number 'fade': 0 at the start, 1 gone; the walkway tool writes it)"),
    'MADE • stain soot': (lambda n: stain(n, 'soot'), "a see-through soot stain, near-black, matte, streaked downwards (mesh number 'fade': 0 strongest, 1 gone; the stain tool writes it)"),
    'MADE • stain damp': (lambda n: stain(n, 'damp'), "a see-through damp stain, dark green-grey, a little glossy, streaked downwards (mesh number 'fade'; the stain tool writes it)"),
    'MADE • stain rust': (lambda n: stain(n, 'rust'), "a see-through rust run, orange-brown, matte, streaked downwards from a bracket or pipe joint (mesh number 'fade'; the stain and railing tools write it)"),
    'MADE • stain mud': (lambda n: stain(n, 'mud'), "a see-through smear of trodden mud, dark brown, a little glossy, blotched (mesh number 'fade'; the stain tool writes it)"),
    'MADE • stain coal dust': (lambda n: stain(n, 'coal dust'), "a see-through smear of coal dust, black, a little glossy, blotched (mesh number 'fade'; the stain tool writes it)"),
    'MADE • stain ash': (lambda n: stain(n, 'ash'), "a see-through smear of ash carried on boots, pale grey, matte, blotched (mesh number 'fade'; the stain tool writes it)"),
    'MADE • stain heavy soot': (lambda n: heavy_stain(n, 'heavy soot'), "a heavy soot stain that shows on a front 15 to 25 m away: near-black brown, held nearly full and stopped at a ragged edge, broken into runs (mesh number 'fade'; the stain tool writes it)"),
    'MADE • stain far soot': (lambda n: heavy_stain(n, 'far soot'), "the heavy soot with broader runs and darker, for fronts 25 to 35 m away (mesh number 'fade'; the stain tool writes it)"),
    'MADE • stain heavy damp': (lambda n: heavy_stain(n, 'heavy damp'), "heavy rising damp: green-black, a little glossy, a ragged tide line with a pale salt line along it (mesh number 'fade'; the stain tool writes it)"),
    'MADE • stain leak': (lambda n: heavy_stain(n, 'leak'), "a leak run: green-black water streaks down a wall from a gutter's joint or a downpipe's socket (mesh number 'fade'; the stain and downpipe tools write it)"),
    'MADE • slate roof': (slate_roof, "a slate roof in courses: dark blue-grey slates, lap lines in relief, wet sheen; in the object's own axes, slates along X, courses climbing Y"),
    'MADE • ash': (ash, 'grey stove ash with dark clinker lumps, matte, for heaps and spills'),
    'MADE • straw': (straw, "dropped and trodden straw for the litter tool's straw layer: dull gold to grey-brown strands, the outer ones "
                            "of a clump darker, muddy where trodden, dark and a little glossy when wet (reads the litter tool's numbers)"),
    'MADE • hedge leaves': (hedge_leaves, "hedge leaves for the hedge tool: near-black to olive greens, some russet brown, each spray and "
                                          "leaf its own shade, darker deep inside the hedge (reads the hedge tool's numbers)"),
}


def build_all():
    made = {}
    for name, (builder, what) in MADE.items():
        material = builder(name)
        material['store_what'] = what
        made[name] = material
    return made
