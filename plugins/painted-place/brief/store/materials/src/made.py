"""
What this file does: the store's made materials, built in code (no photograph): old brass, old copper, glazed china,
weathered boards with peeling paint, wet bark, puddle water, a wet-ground film, rusty nail heads, a rust stain, rail steel and
smoke for a ribbon.
build_materials.py calls build_all().

Two of them read a number the puddle tool writes on its meshes:
  - MADE • puddle water: 'shallow' on each point, 0 in the deep middle, 1 at the rim; where it is 1 the water is clear
    and the ground shows through. A mesh without it is deep water all over.
  - MADE • wet ground film: 'dry' on each point, 0 against the water, 1 at the film's outer edge; where it is 1 the film
    is gone. A mesh without it is wet all over.
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
    (the mesh number 'shallow', 1 at the rim), so the mud shows through at the edge instead of a hard cut."""
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
    across = math(nodes, links, 'SUBTRACT', 1.0, math(nodes, links, 'ABSOLUTE', math(nodes, links, 'MULTIPLY_ADD', separate.outputs['X'], 2.0, -1.0)))
    left = math(nodes, links, 'SUBTRACT', 1.0, separate.outputs['Y'])
    starts = math(nodes, links, 'MINIMUM', math(nodes, links, 'MULTIPLY', separate.outputs['Y'], 14.0), 1.0)
    body = math(nodes, links, 'MULTIPLY', math(nodes, links, 'MULTIPLY', math(nodes, links, 'MULTIPLY', across, billows), left), starts)
    links.new(map_range(nodes, links, body, 0.10, 0.42, 0.0, 0.7), principled.inputs['Alpha'])
    links.new(mix(nodes, links, map_range(nodes, links, billows, 0.3, 0.7), (0.045, 0.055, 0.08), (0.11, 0.12, 0.14)), principled.inputs['Base Color'])
    principled.inputs['Roughness'].default_value = 1.0
    principled.inputs['Emission Color'].default_value = (1.0, 0.5, 0.2, 1.0)
    links.new(math(nodes, links, 'MULTIPLY', math(nodes, links, 'POWER', left, 3.0), 0.08), principled.inputs['Emission Strength'])
    material.surface_render_method = 'DITHERED'
    material.diffuse_color = (0.08, 0.09, 0.11, 1)
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
}


def build_all():
    made = {}
    for name, (builder, what) in MADE.items():
        material = builder(name)
        material['store_what'] = what
        made[name] = material
    return made
