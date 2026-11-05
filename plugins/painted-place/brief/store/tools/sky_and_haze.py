"""
What this file does: a dusk sky and a box of thin hazy air, the two things both builders of log 51 spent their first
quarter of an hour on (a black sky; a haze that swallowed the sky; a hard step where the haze ended); a low sun with a
deck of cloud lit by it (the garden builders of log 58: a golden glow round a sun just behind the far ridge, the cloud
undersides gold near it and pale grey away from it, which wet ground mirrors); and a light of the mist's own, so that a
sun or a fill light shining into the mist does not veil the far hills pale. It decides nothing about where things go:
the sky is the whole world's background, the haze fills the box you give it, and the mist's light lights that box.

From your own script:

    import sys; sys.path.insert(0, FOLDER + '/store/tools')
    import sky_and_haze
    sky_and_haze.sky(bpy.context.scene)                                   # the dusk sky as the world's background
    box = sky_and_haze.haze(low=(-60, -5, 0), high=(60, 220, 30))         # thin air over the place, gone by the box's top
    sky_and_haze.photo_sky(bpy.context.scene, 'mud_road_puresky')        # or a photographed sky from the store's skies
    made = sky_and_haze.low_sun(bpy.context.scene, bearing=0, height=12)  # or a low sun with its cloud deck, and its light
    sky_and_haze.mist_light(box, keep_out=[made['sun'], my_fill])        # the mist lit by its own weak light only

The dusk sky is coloured by how high you look: an amber band on the horizon, a dull warm band just above it, teal-blue
higher up and deep blue overhead, with streaky clouds drawn darker and bluer across it. It lights the scene a little
(strength 1.1); bring your own low sun and a cool fill light. The haze is a box of thin scattering air whose density
fades towards its top, so the sky above it stays clear and there is no step where it ends; keep the box over the place
and up to about twice the height of your tallest thing.

The low sun (LOW_SUN): a sun at the bearing and height you give, and a sun light shining from it, its colour taken from
the length of air its light comes through (golden at 15 degrees, orange at 8, red at 3; or give `colour`). Round it the
sky glows: a tight bright core (hidden when the sun stands behind a ridge), a soft aureole falling off with the angle
from the sun, and a warm band along the horizon either side of it, much wider sideways than upwards. Overhead a deck
of broken cloud `deck_height` up: the clouds shrink towards the horizon as a real layer does and sink into the
horizon's air with distance; their undersides are pale grey where only the sky lights them and darker where the cloud
is thick, and near the sun its light lights them gold, most of all at their thin edges, the thick cores staying dark
against the glow. The deck is drawn in the sky itself (where the way you look meets a layer at that height), so no
camera far limit cuts it off and wet ground mirrors it: `made['far_limit']` is 0, the far limit the sky needs. Hills
standing taller than the deck still stand in front of it. A sun just behind a ridge stands about 1 to 2 degrees under
the ridge's top at its bearing: far_hills.ridge_height() tells you that height from your eye before anything is drawn.

The mist's light (MIST_LIGHT): a sun or a fill light shining into a haze box between the eye and the far hills lights
the mist, and the mist veils the hills pale from end to end (the third garden builder's find). mist_light() keeps the
lights you name out of the mist (Blender's visible_volume_scatter switched off on each: they still light everything
else) and gives the mist a weak sky-blue light of its own from above, the size of the box, that nothing but the mist
sees; `share` leaves each named light a weak copy that only the mist sees, for a faint glow towards the sun.

From the command line:

    python3 sky_and_haze.py --help
    python3 sky_and_haze.py --blend IN.blend --out OUT.blend --low -60 -5 0 --high 60 220 30 [--density 0.0016]
    python3 sky_and_haze.py --low-sun --bearing 0 --height 12 --out OUT.blend

Options of sky(): horizon, low_band, high_band, top (the four colours, linear RGB), clouds (0 none to 1 heavy; default
0.8), strength (default 1.1), seed (moves the clouds; default 0).
Options of haze(): low, high (the box's corners, metres; required), density (default 0.0016; 0.004 is a misty evening),
colour (default a cool grey-blue), anisotropy (how much the haze glows towards a light behind it; default 0.35),
collection (default a new collection 'haze').
photo_sky(scene, name, strength, turn): a sky photographed all round (Poly Haven, CC0; the store's skies folder lists
them in skies/manifest.json: 'mud_road_puresky', a flat grey overcast day; 'overcast_soil_puresky', rain clouds;
'kloofendal_48d_partly_cloudy_puresky', a sunny day with its sun in it) as the world's background and light;
strength (default 1.0), turn (degrees the sky is turned about the vertical; default 0).
Options of low_sun(): bearing (the way to the sun, degrees counter-clockwise from +Y as far_hills' facing; default 0),
height (degrees above the horizon; default 12), strength (the sun light's strength; default 2.4), deck_height (metres
up to the cloud deck; default 420), clouds (the share of the sky the deck covers, 0 to 1; default 0.55), cloud_size
(metres across a cloud; default 150), wind (the way the clouds are drawn out, degrees as bearing; default 30), colour
(the sun's colour; default from its height), sky_strength (how much the sky lights the scene; default 1.4), glow (how
bright the glow round the sun; default 1.0), seed (moves the clouds; default 0), collection (where the sun light goes;
default the scene's own). Returns {'world', 'sun', 'direction', 'colour', 'deck_height', 'far_limit'}.
Options of mist_light(): box (the haze box; required), keep_out (the lights to keep out of the mist; default none),
strength (the mist light's watts on each square metre of the box's ground; default 1.0), colour (default the sky's
blue (0.33, 0.52, 1.0)), share (each kept-out light's weak copy for the mist, 0 none to 1; default 0), collection
(default the box's). Returns {'light', 'kept_out', 'twins'}.
"""

import argparse
import math
import os
import sys

import bpy
from mathutils import Vector

TOOLS = os.path.dirname(os.path.abspath(__file__))
if TOOLS not in sys.path:
    sys.path.insert(0, TOOLS)

TOOL = {
    'name': 'sky_and_haze',
    'what': 'a dusk sky for the world (amber horizon, teal-blue above, streaky cloud low down) and a box of thin haze that fades smoothly to nothing at its top; '
            'or a low sun with its sun light, a golden glow round it and a deck of broken cloud overhead, lit gold near the sun and pale grey away from it, '
            'that wet ground mirrors; and a light of the mist\'s own, so a sun or fill light in the mist does not veil the far hills pale',
    'call': "sky_and_haze.sky(scene); box = sky_and_haze.haze(low=(-60, -5, 0), high=(60, 220, 30), density=0.0016);  "
            "made = sky_and_haze.low_sun(scene, bearing=0, height=12, strength=2.4, deck_height=420);  sky_and_haze.mist_light(box, keep_out=[made['sun'], my_fill])",
    'options': {
        'sky: horizon, low_band, high_band, top': 'the sky\'s four colours from the horizon up (linear RGB)',
        'sky: clouds': 'streaky cloud, 0 none to 1 heavy (0.8)',
        'sky: strength': 'how much the sky lights the scene (1.1)',
        'haze: low, high': 'the haze box\'s two corners, metres (required)',
        'haze: density': 'how thick the air is (0.0016; 0.004 a misty evening)',
        'haze: anisotropy': 'how much the haze glows towards a light behind it (0.35)',
        'sky: seed': 'moves the clouds (0)', 'haze: colour, collection': 'the air\'s colour (a cool grey-blue); where the box goes (a new collection)',
        'photo_sky: name, strength, turn': "a photographed sky from the store's skies ('mud_road_puresky', a grey overcast day; 'overcast_soil_puresky', rain clouds; "
                                           "'kloofendal_48d_partly_cloudy_puresky', a sunny day whose sun casts the shadows); its light (1.0); "
                                           "degrees turned (0; the sunny sky's sun stands at bearing -34 - turn, see skies/README.md)",
        'low_sun: bearing, height': "the way to the sun, degrees counter-clockwise from +Y, counted as far_hills' facing (0); its height above the horizon, "
                                    'degrees (12; behind a ridge: 1 to 2 under far_hills.ridge_height at that bearing)',
        'low_sun: strength, colour': "the sun light's strength (2.4); its colour (none: from the air its light comes through, golden at 15 degrees, orange at 8, red at 3)",
        'low_sun: deck_height, clouds, cloud_size, wind': 'metres up to the cloud deck (420); the share of the sky it covers, 0 to 1 (0.55); '
                                                          'metres across a cloud (150); the way the clouds are drawn out, degrees as bearing (30)',
        'low_sun: sky_strength, glow, seed, collection': "how much the sky lights the scene (1.4); how bright the glow round the sun (1.0); moves the clouds (0); "
                                                          "where the sun light goes (the scene's own)",
        'mist_light: box, keep_out': 'the haze box to light (required); the lights to keep out of the mist, your sun and fill (none)',
        'mist_light: strength, colour, share': "watts on each square metre of the box's ground (1.0); the light's colour (the sky's blue (0.33, 0.52, 1.0)); "
                                               "a weak copy of each kept-out light that only the mist sees, as a share of its strength (0; 0.1 a faint glow towards the sun)",
    },
    'materials': [],
    'source': "the goods yard and military base builders of log 51 (their skies and haze boxes), made into a tool; the low sun from the third garden "
              "builder's golden_sky() and its cloud deck ('/home/claude/build-57-garden/closer/render_final.py', lines 1920-2016), and the mist's light from "
              "its lines 2018-2027, made into calls: the deck moved into the sky itself (no camera far limit cuts it off), the glow given its real shape "
              "(a band along the horizon either side of the sun, an aureole falling off with the angle), silver-lined clouds whose thin edges glow and "
              "thick cores stay dark, far clouds sunk into the horizon's air, and the sun's colour from the air its light comes through",
    'trap': 'a haze filling the whole world (a world volume) swallows the sky; keep the haze in a box over the place. A sun or fill light shining into '
            'a haze box between the eye and far hills veils them pale: use mist_light. A sun just behind a ridge still lights the whole place, '
            'because the far hills cast no shadow: over wet ground before the eye it draws a blinding path of light; give the hills their shadow '
            '(obj.visible_shadow = True) or turn the sun down. Clouds lit gold over a wide part of the sky turn a whole wet path warm, '
            'because it mirrors them: keep glow at 1 or under. Hills taller than deck_height stand in front of the deck',
}
SKIES = os.path.join(os.path.dirname(TOOLS), 'skies')

HORIZON = (0.85, 0.36, 0.12)
LOW_BAND = (0.30, 0.15, 0.10)
HIGH_BAND = (0.028, 0.085, 0.15)
TOP = (0.003, 0.025, 0.06)


def photo_sky(scene, name='mud_road_puresky', strength=1.0, turn=0.0):
    """A photographed sky from the store's skies folder as the world's background and light (see the note at the top)."""
    import json
    import math
    manifest = json.load(open(os.path.join(SKIES, 'manifest.json')))
    if name not in manifest:
        raise ValueError('no sky %r; the store has %s' % (name, ', '.join(sorted(manifest))))
    world = scene.world or bpy.data.worlds.new('photographed sky')
    scene.world = world
    world.use_nodes = True
    nodes, links = world.node_tree.nodes, world.node_tree.links
    for node in list(nodes):
        nodes.remove(node)
    output = nodes.new('ShaderNodeOutputWorld')
    background = nodes.new('ShaderNodeBackground')
    background.inputs['Strength'].default_value = float(strength)
    picture = nodes.new('ShaderNodeTexEnvironment')
    picture.image = bpy.data.images.load(os.path.join(SKIES, manifest[name]['file']), check_existing=True)
    coordinates = nodes.new('ShaderNodeTexCoord')
    mapping = nodes.new('ShaderNodeMapping')
    mapping.inputs['Rotation'].default_value = (0.0, 0.0, math.radians(turn))
    links.new(coordinates.outputs['Generated'], mapping.inputs['Vector'])
    links.new(mapping.outputs['Vector'], picture.inputs['Vector'])
    links.new(picture.outputs['Color'], background.inputs['Color'])
    links.new(background.outputs['Background'], output.inputs['Surface'])
    return world


def _link(links, a, b):
    links.new(a, b)


def sky(scene, horizon=HORIZON, low_band=LOW_BAND, high_band=HIGH_BAND, top=TOP, clouds=0.8, strength=1.1, seed=0):
    """Make the dusk sky the scene's world. Returns the world."""
    world = bpy.data.worlds.new('dusk sky')
    world.use_nodes = True
    nodes, links = world.node_tree.nodes, world.node_tree.links
    nodes.clear()
    output = nodes.new('ShaderNodeOutputWorld')
    background = nodes.new('ShaderNodeBackground')
    background.inputs['Strength'].default_value = strength
    direction = nodes.new('ShaderNodeTexCoord').outputs['Object']        # for a world: the direction you look in
    separate = nodes.new('ShaderNodeSeparateXYZ')
    _link(links, direction, separate.inputs[0])
    height = nodes.new('ShaderNodeMapRange')
    height.clamp = True
    height.inputs['From Min'].default_value = 0.0
    height.inputs['From Max'].default_value = 0.9
    _link(links, separate.outputs['Z'], height.inputs['Value'])
    ramp = nodes.new('ShaderNodeValToRGB')
    elements = ramp.color_ramp.elements
    elements[0].position, elements[0].color = 0.0, (*horizon, 1.0)
    elements.new(0.10).color = (*low_band, 1.0)
    elements.new(0.26).color = (*high_band, 1.0)
    elements[-1].position, elements[-1].color = 1.0, (*top, 1.0)
    _link(links, height.outputs['Result'], ramp.inputs['Fac'])
    colour = ramp.outputs['Color']
    if clouds > 0:
        stretch = nodes.new('ShaderNodeMapping')
        stretch.inputs['Scale'].default_value = (1.0, 1.0, 5.0)              # drawn out sideways: streaks, not blobs
        stretch.inputs['Location'].default_value = (seed * 1.37, seed * 0.71, 0.0)
        _link(links, direction, stretch.inputs['Vector'])
        cloud = nodes.new('ShaderNodeTexNoise')
        cloud.inputs['Scale'].default_value = 2.2
        cloud.inputs['Detail'].default_value = 9.0
        cloud.inputs['Roughness'].default_value = 0.6
        _link(links, stretch.outputs['Vector'], cloud.inputs['Vector'])
        amount = nodes.new('ShaderNodeMapRange')
        amount.inputs['From Min'].default_value = 0.42
        amount.inputs['From Max'].default_value = 0.68
        amount.inputs['To Max'].default_value = clouds
        _link(links, cloud.outputs['Fac'], amount.inputs['Value'])
        thin_high = nodes.new('ShaderNodeMapRange')                          # clouds thin out high up, where the streaks
        thin_high.inputs['From Min'].default_value = 0.35                    # would close into rings round the top
        thin_high.inputs['From Max'].default_value = 0.8
        thin_high.inputs['To Min'].default_value = 1.0
        thin_high.inputs['To Max'].default_value = 0.0
        _link(links, separate.outputs['Z'], thin_high.inputs['Value'])
        thinned = nodes.new('ShaderNodeMath')
        thinned.operation = 'MULTIPLY'
        _link(links, amount.outputs['Result'], thinned.inputs[0])
        _link(links, thin_high.outputs['Result'], thinned.inputs[1])
        darker = nodes.new('ShaderNodeVectorMath')
        darker.operation = 'MULTIPLY'
        darker.inputs[1].default_value = (0.35, 0.40, 0.62)                 # cloud undersides: darker and bluer
        _link(links, colour, darker.inputs[0])
        mix = nodes.new('ShaderNodeMix')
        mix.data_type = 'RGBA'
        _link(links, thinned.outputs['Value'], mix.inputs[0])
        _link(links, colour, mix.inputs[6])
        _link(links, darker.outputs[0], mix.inputs[7])
        colour = mix.outputs[2]
    _link(links, colour, background.inputs['Color'])
    _link(links, background.outputs['Background'], output.inputs['Surface'])
    scene.world = world
    return world


def haze(low, high, density=0.0016, colour=(0.55, 0.68, 0.8), anisotropy=0.35, collection=None):
    """A box of thin scattering air from corner `low` to corner `high`, its density fading to nothing at its top.
    Returns the box object ('haze box')."""
    low, high = Vector(low), Vector(high)
    size = high - low
    if min(size) <= 0:
        raise ValueError('haze needs low below and behind high on every axis (got %s and %s)' % (tuple(low), tuple(high)))
    material = bpy.data.materials.new('haze')
    material.use_nodes = True
    nodes, links = material.node_tree.nodes, material.node_tree.links
    nodes.clear()
    output = nodes.new('ShaderNodeOutputMaterial')
    scatter = nodes.new('ShaderNodeVolumeScatter')
    scatter.inputs['Color'].default_value = (*colour, 1.0)
    scatter.inputs['Anisotropy'].default_value = anisotropy
    # density from the box's own coordinates (0 at its floor, 1 at its top), so the box may stand anywhere
    generated = nodes.new('ShaderNodeTexCoord').outputs['Generated']
    separate = nodes.new('ShaderNodeSeparateXYZ')
    _link(links, generated, separate.inputs[0])
    fade = nodes.new('ShaderNodeMapRange')
    fade.interpolation_type = 'SMOOTHSTEP'
    fade.inputs['From Min'].default_value = 0.15
    fade.inputs['From Max'].default_value = 1.0
    fade.inputs['To Min'].default_value = density
    fade.inputs['To Max'].default_value = 0.0
    _link(links, separate.outputs['Z'], fade.inputs['Value'])
    _link(links, fade.outputs['Result'], scatter.inputs['Density'])
    _link(links, scatter.outputs['Volume'], output.inputs['Volume'])
    mesh = bpy.data.meshes.new('haze box')
    half = size / 2
    corners = [(x, y, z) for z in (-half.z, half.z) for y in (-half.y, half.y) for x in (-half.x, half.x)]
    faces = [(0, 2, 3, 1), (4, 5, 7, 6), (0, 1, 5, 4), (2, 6, 7, 3), (0, 4, 6, 2), (1, 3, 7, 5)]
    mesh.from_pydata(corners, [], faces)
    mesh.materials.append(material)
    obj = bpy.data.objects.new('haze box', mesh)
    obj.location = (low + high) / 2
    obj.visible_shadow = False
    if collection is None:
        collection = bpy.data.collections.new('haze')
        bpy.context.scene.collection.children.link(collection)
    collection.objects.link(obj)
    return obj


# ------------------------------------------------------------------------------------------- a low sun and its cloud deck

def _math(nodes, links, operation, a, b=None, clamp=False):
    """A math node on a socket or a number (and a second one); returns its output."""
    node = nodes.new('ShaderNodeMath')
    node.operation = operation
    node.use_clamp = clamp
    for index, value in enumerate((a, b)):
        if value is None:
            continue
        if isinstance(value, (int, float)):
            node.inputs[index].default_value = float(value)
        else:
            links.new(value, node.inputs[index])
    return node.outputs[0]


def _add_colour(nodes, links, amount, base, colour):
    """base + amount * colour (amount a socket, colour a fixed RGB)."""
    add = nodes.new('ShaderNodeMix')
    add.data_type = 'RGBA'
    add.blend_type = 'ADD'
    links.new(amount, add.inputs[0])
    links.new(base, add.inputs[6])
    add.inputs[7].default_value = (*colour, 1.0)
    return add.outputs[2]


def _mix(nodes, links, factor, a, b):
    """a where factor is 0, b where it is 1 (each a socket or a fixed RGB)."""
    mix = nodes.new('ShaderNodeMix')
    mix.data_type = 'RGBA'
    links.new(factor, mix.inputs[0])
    for index, value in ((6, a), (7, b)):
        if isinstance(value, tuple):
            mix.inputs[index].default_value = (*value, 1.0)
        else:
            links.new(value, mix.inputs[index])
    return mix.outputs[2]


def _smooth(nodes, links, value, low, high):
    """0 below `low`, 1 above `high`, a smooth step between."""
    step = nodes.new('ShaderNodeMapRange')
    step.interpolation_type = 'SMOOTHSTEP'
    step.inputs['From Min'].default_value = low
    step.inputs['From Max'].default_value = high
    links.new(value, step.inputs['Value'])
    return step.outputs['Result']


def sun_direction(bearing, height):
    """The way to the sun as a unit vector: `bearing` in degrees counted as far_hills' facing (counter-clockwise from
    +Y; 0 straight behind a place whose front faces -Y), `height` in degrees above the horizon."""
    b, h = math.radians(bearing), math.radians(height)
    return Vector((-math.sin(b) * math.cos(h), math.cos(b) * math.cos(h), math.sin(h)))


def sun_colour(height, air=1.0):
    """The colour of sunlight at `height` degrees above the horizon, brightest channel 1: the lower the sun, the longer
    its way through the air and the more of its blue and green the air takes out (Kasten and Young's air mass through a
    hazy evening air; `air` above 1 for thicker air). About (1, 0.74, 0.46) at 23 degrees, orange at 8, red at 3."""
    h = max(float(height), -0.5)
    mass = 1.0 / (math.sin(math.radians(h)) + 0.50572 * (h + 6.07995) ** -1.6364)
    through = [math.exp(-depth * air * mass) for depth in (0.09, 0.21, 0.40)]
    top = max(through)
    return tuple(round(value / top, 4) for value in through)


def low_sun(scene, bearing=0.0, height=12.0, strength=2.4, deck_height=420.0, clouds=0.55, cloud_size=150.0, wind=30.0,
            colour=None, sky_strength=1.4, glow=1.0, seed=0, collection=None):
    """A low sun in the sky and a light shining from it, and a deck of broken cloud overhead lit by it.
    Makes the world (the scene's new background) and a sun light; returns {'world', 'sun', 'direction', 'colour',
    'deck_height', 'far_limit'} (far_limit 0: the deck is drawn in the sky itself; see the note at the top)."""
    if not -5.0 <= height <= 60.0:
        raise ValueError('height is the sun\'s height above the horizon, -5 to 60 degrees, not %r' % (height,))
    if deck_height <= 0 or cloud_size <= 0:
        raise ValueError('deck_height and cloud_size are metres above 0, not %r and %r' % (deck_height, cloud_size))
    if not 0.0 <= clouds <= 1.0:
        raise ValueError('clouds is the share of the sky the deck covers, 0 to 1, not %r' % (clouds,))
    sun_way = sun_direction(bearing, height)
    gold = tuple(colour) if colour is not None else sun_colour(height)
    paler = tuple(0.5 * c + 0.5 for c in gold)                     # the sky right round the sun is paler than the sun's light
    world = bpy.data.worlds.new('low sun sky')
    world.use_nodes = True
    nodes, links = world.node_tree.nodes, world.node_tree.links
    nodes.clear()
    output = nodes.new('ShaderNodeOutputWorld')
    background = nodes.new('ShaderNodeBackground')
    background.inputs['Strength'].default_value = float(sky_strength)
    look = nodes.new('ShaderNodeTexCoord').outputs['Object']       # for a world: the way you look
    xyz = nodes.new('ShaderNodeSeparateXYZ')
    links.new(look, xyz.inputs[0])
    up = xyz.outputs['Z']
    # the dome, by how high you look: pale grey at the horizon, deep blue overhead (the builder's colours)
    height_share = nodes.new('ShaderNodeMapRange')
    height_share.clamp = True
    height_share.inputs['From Max'].default_value = 0.9
    links.new(up, height_share.inputs['Value'])
    dome = nodes.new('ShaderNodeValToRGB')
    stops = dome.color_ramp.elements
    stops[0].position, stops[0].color = 0.0, (0.42, 0.40, 0.40, 1.0)
    stops.new(0.07).color = (0.26, 0.27, 0.29, 1.0)
    stops.new(0.2).color = (0.11, 0.155, 0.225, 1.0)
    stops.new(0.45).color = (0.04, 0.09, 0.18, 1.0)
    stops[-1].position, stops[-1].color = 1.0, (0.015, 0.04, 0.10, 1.0)
    links.new(height_share.outputs['Result'], dome.inputs['Fac'])
    sky_colour = dome.outputs['Color']
    # the angle between where you look and the sun (radians)
    toward = nodes.new('ShaderNodeVectorMath')
    toward.operation = 'DOT_PRODUCT'
    toward.inputs[1].default_value = sun_way
    links.new(look, toward.inputs[0])
    angle = _math(nodes, links, 'ARCCOSINE', _math(nodes, links, 'MINIMUM', _math(nodes, links, 'MAXIMUM', toward.outputs['Value'], -1.0), 1.0))
    # a warm band hugging the horizon either side of the sun, much wider sideways than upwards (a sunset's glow lies
    # along the horizon; it is not a round blob)
    flat_way = Vector((sun_way.x, sun_way.y, 0.0)).normalized() if Vector((sun_way.x, sun_way.y)).length > 1e-6 else Vector((0.0, 1.0, 0.0))
    level = nodes.new('ShaderNodeVectorMath')
    level.operation = 'MULTIPLY'
    level.inputs[1].default_value = (1.0, 1.0, 0.0)
    links.new(look, level.inputs[0])
    level_way = nodes.new('ShaderNodeVectorMath')
    level_way.operation = 'NORMALIZE'
    links.new(level.outputs['Vector'], level_way.inputs[0])
    sideways = nodes.new('ShaderNodeVectorMath')
    sideways.operation = 'DOT_PRODUCT'
    sideways.inputs[1].default_value = flat_way
    links.new(level_way.outputs['Vector'], sideways.inputs[0])
    beside = _math(nodes, links, 'POWER', _math(nodes, links, 'MULTIPLY', _math(nodes, links, 'ADD', sideways.outputs['Value'], 1.0), 0.5), 4.0)
    low_down = _math(nodes, links, 'EXPONENT', _math(nodes, links, 'MULTIPLY', _math(nodes, links, 'MAXIMUM', up, 0.0), -1.0 / math.sin(math.radians(7.0))))
    band = _math(nodes, links, 'MULTIPLY', _math(nodes, links, 'MULTIPLY', beside, low_down), 0.28 * glow)
    sky_colour = _add_colour(nodes, links, band, sky_colour, (gold[0], gold[1] * 0.9, gold[2] * 0.85))
    # the glow round the sun: a soft aureole falling off with the angle, and a tight bright core (the sun itself, hidden
    # when it stands behind a ridge)
    aureole = _math(nodes, links, 'DIVIDE', 1.0, _math(nodes, links, 'ADD', 1.0, _math(nodes, links, 'POWER', _math(nodes, links, 'DIVIDE', angle, math.radians(8.0)), 2.0)))
    sky_colour = _add_colour(nodes, links, _math(nodes, links, 'MULTIPLY', aureole, 0.5 * glow), sky_colour, gold)
    core = _math(nodes, links, 'EXPONENT', _math(nodes, links, 'MULTIPLY', _math(nodes, links, 'POWER', _math(nodes, links, 'DIVIDE', angle, math.radians(2.5)), 2.0), -1.0))
    sky_colour = _add_colour(nodes, links, _math(nodes, links, 'MULTIPLY', core, 1.6 * glow), sky_colour, paler)
    sky_colour.node.name = 'Sun glow'
    if clouds > 0:
        # the deck: where the way you look meets a flat layer `deck_height` up (the eye near the ground), so the clouds
        # shrink towards the horizon as a real layer does; drawn in the sky itself, so no camera far limit cuts it off
        reach = _math(nodes, links, 'DIVIDE', float(deck_height), _math(nodes, links, 'MAXIMUM', up, 0.002))
        meet = nodes.new('ShaderNodeVectorMath')
        meet.operation = 'SCALE'
        links.new(level.outputs['Vector'], meet.inputs[0])
        links.new(reach, meet.inputs['Scale'])
        wind_turn = nodes.new('ShaderNodeMapping')                 # first turn the deck so the wind's way is +Y ...
        wind_turn.inputs['Rotation'].default_value = (0.0, 0.0, -math.radians(wind))
        links.new(meet.outputs['Vector'], wind_turn.inputs['Vector'])
        drawn_out = nodes.new('ShaderNodeMapping')                 # ... then draw the clouds out along it
        drawn_out.inputs['Location'].default_value = (seed * 1731.0, seed * -977.0, seed * 3.7)
        drawn_out.inputs['Scale'].default_value = (1.0 / cloud_size, 1.0 / (cloud_size * 2.2), 1.0)
        links.new(wind_turn.outputs['Vector'], drawn_out.inputs['Vector'])
        wind_turn = drawn_out
        texture = nodes.new('ShaderNodeTexNoise')
        texture.inputs['Scale'].default_value = 1.0
        texture.inputs['Detail'].default_value = 6.0
        texture.inputs['Roughness'].default_value = 0.6
        texture.inputs['Distortion'].default_value = 0.25
        links.new(wind_turn.outputs['Vector'], texture.inputs['Vector'])
        texture.name = 'Clouds'
        edge = 0.5 + (0.5 - clouds) * 0.32                         # where cloud begins in the noise, from how much is covered
        body = _smooth(nodes, links, texture.outputs['Fac'], edge, edge + 0.10)          # 0 clear sky, 1 cloud
        thick = _smooth(nodes, links, texture.outputs['Fac'], edge + 0.04, edge + 0.26)  # how deep inside a cloud
        thin = _math(nodes, links, 'SUBTRACT', 1.0, thick)
        # the undersides away from the sun: lit only by the sky, pale grey at their thin edges, darker where thick
        underside = _mix(nodes, links, thick, (0.13, 0.14, 0.165), (0.065, 0.07, 0.085))
        # near the sun: its light coming through the cloud and under the deck lights the undersides gold, most of all
        # at the thin edges (a silver lining); thick cores stay dark against the glow behind them
        near = _math(nodes, links, 'DIVIDE', 1.0, _math(nodes, links, 'ADD', 1.0, _math(nodes, links, 'POWER', _math(nodes, links, 'DIVIDE', angle, math.radians(15.0)), 2.0)))
        lining = _math(nodes, links, 'MULTIPLY', near, _math(nodes, links, 'ADD', 0.3, _math(nodes, links, 'MULTIPLY', thin, 0.7)))
        lit = _add_colour(nodes, links, _math(nodes, links, 'MULTIPLY', lining, 1.1 * glow), underside, (gold[0] * 1.05, gold[1] * 0.95, gold[2] * 0.85))
        # far clouds sink into the horizon's air: the farther the deck from the eye, the less of it shows
        clear_air = _math(nodes, links, 'EXPONENT', _math(nodes, links, 'DIVIDE', reach, -5000.0))
        showing = _math(nodes, links, 'MULTIPLY', body, clear_air)
        above = _smooth(nodes, links, up, 0.0, 0.01)
        sky_colour = _mix(nodes, links, _math(nodes, links, 'MULTIPLY', showing, above), sky_colour, lit)
    links.new(sky_colour, background.inputs['Color'])
    links.new(background.outputs['Background'], output.inputs['Surface'])
    scene.world = world
    sun = bpy.data.objects.new('low sun', bpy.data.lights.new('low sun', 'SUN'))
    sun.data.energy = float(strength)
    sun.data.color = gold
    sun.data.angle = math.radians(1.5)
    sun.rotation_euler = (-sun_way).to_track_quat('-Z', 'Y').to_euler()
    (collection or scene.collection).objects.link(sun)
    return {'world': world, 'sun': sun, 'direction': sun_way, 'colour': gold, 'deck_height': float(deck_height), 'far_limit': 0.0}


def mist_light(box, keep_out=(), strength=1.0, colour=(0.33, 0.52, 1.0), share=0.0, collection=None):
    """Light the mist in `box` (a haze box, as haze() makes) with its own weak sky-blue light from above, which nothing
    else sees, and keep the lights in `keep_out` (your sun, your fill) out of the mist (see the note at the top). Returns
    {'light': the mist's light, 'kept_out': the lights kept out, 'twins': the weak copies made when share > 0}."""
    if box is None or getattr(box, 'type', None) != 'MESH':
        raise ValueError('mist_light needs the haze box (the object haze() returns), not %r' % (box,))
    if strength < 0 or not 0.0 <= share <= 1.0:
        raise ValueError('strength is 0 or more and share 0 to 1, not %r and %r' % (strength, share))
    for light in keep_out:
        if getattr(light, 'type', None) != 'LIGHT':
            raise ValueError('keep_out takes light objects, not %r' % (light,))
    bpy.context.view_layer.update()                       # a new box's place is in its matrix only after an update
    corners = [box.matrix_world @ Vector(corner) for corner in box.bound_box]
    low = Vector([min(c[i] for c in corners) for i in range(3)])
    high = Vector([max(c[i] for c in corners) for i in range(3)])
    size_x, size_y = high.x - low.x, high.y - low.y
    data = bpy.data.lights.new('mist light', 'AREA')
    data.shape = 'RECTANGLE'
    data.size, data.size_y = size_x, size_y
    data.energy = float(strength) * size_x * size_y       # the same light on every square metre, whatever the box's size
    data.color = tuple(colour)
    light = bpy.data.objects.new('mist light', data)
    light.location = ((low.x + high.x) / 2, (low.y + high.y) / 2, high.z)   # at the box's top, shining down
    for flag in ('visible_camera', 'visible_diffuse', 'visible_glossy', 'visible_transmission'):
        setattr(light, flag, False)
    light.visible_volume_scatter = True
    target = collection or (box.users_collection[0] if box.users_collection else bpy.context.scene.collection)
    target.objects.link(light)
    twins = []
    for kept in keep_out:
        kept.visible_volume_scatter = False
        if share > 0:
            twin = kept.copy()
            twin.data = kept.data.copy()
            twin.data.energy = kept.data.energy * share
            twin.name = kept.name + ' (in the mist)'
            for flag in ('visible_camera', 'visible_diffuse', 'visible_glossy', 'visible_transmission'):
                setattr(twin, flag, False)
            twin.visible_volume_scatter = True
            (kept.users_collection[0] if kept.users_collection else target).objects.link(twin)
            twins.append(twin)
    return {'light': light, 'kept_out': list(keep_out), 'twins': twins}


def main():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
    parser = argparse.ArgumentParser(description='A dusk sky and a box of thin haze, or a low sun with its cloud deck (see the note at the top of sky_and_haze.py).')
    parser.add_argument('--blend', help='open this .blend file first (otherwise a new empty one)')
    parser.add_argument('--out', help='save the result here')
    parser.add_argument('--low', type=float, nargs=3, help='the haze box\'s low corner x y z (leave out for no haze)')
    parser.add_argument('--high', type=float, nargs=3, help='the haze box\'s high corner x y z')
    parser.add_argument('--density', type=float, default=0.0016, help='how thick the air is; default 0.0016')
    parser.add_argument('--clouds', type=float, default=None, help='the dusk sky: streaky cloud, 0 none to 1 heavy (default 0.8); the low sun: the share of the sky its deck covers (default 0.55)')
    parser.add_argument('--seed', type=int, default=0, help='moves the clouds; default 0')
    parser.add_argument('--low-sun', action='store_true', help='a low sun with its cloud deck instead of the dusk sky')
    parser.add_argument('--bearing', type=float, default=0.0, help="the low sun's bearing, degrees counter-clockwise from +Y (as far_hills' facing); default 0")
    parser.add_argument('--height', type=float, default=12.0, help="the low sun's height above the horizon, degrees; default 12")
    parser.add_argument('--strength', type=float, default=2.4, help="the low sun light's strength; default 2.4")
    parser.add_argument('--deck-height', type=float, default=420.0, help='metres up to the cloud deck; default 420')
    parser.add_argument('--mist-light', action='store_true', help='with a haze box and the low sun: keep the sun out of the mist and give the mist its own light')
    args = parser.parse_args(argv)
    if args.blend:
        bpy.ops.wm.open_mainfile(filepath=args.blend)
    else:
        bpy.ops.wm.read_factory_settings(use_empty=True)
    made = None
    if args.low_sun:
        made = low_sun(bpy.context.scene, bearing=args.bearing, height=args.height, strength=args.strength, deck_height=args.deck_height,
                       clouds=0.55 if args.clouds is None else args.clouds, seed=args.seed)
        print('a low sun at bearing %.0f, %.1f degrees up, colour %s; the deck %.0f m up, drawn in the sky (no far limit needed)'
              % (args.bearing, args.height, made['colour'], args.deck_height))
    else:
        sky(bpy.context.scene, clouds=0.8 if args.clouds is None else args.clouds, seed=args.seed)
    if bool(args.low) != bool(args.high):
        parser.error('give both --low and --high for the haze box (or neither, for no haze)')
    if args.low and args.high:
        box = haze(args.low, args.high, density=args.density)
        if args.mist_light:
            mist_light(box, keep_out=[made['sun']] if made else [])
    if args.out:
        bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(args.out))
        print('saved', args.out)
    else:
        print('note: nothing was saved; give --out FILE.blend')


if __name__ == '__main__':
    main()
