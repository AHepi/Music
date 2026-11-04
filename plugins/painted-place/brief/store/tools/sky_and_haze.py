"""
What this file does: a dusk sky and a box of thin hazy air, the two things both builders of log 51 spent their first
quarter of an hour on (a black sky; a haze that swallowed the sky; a hard step where the haze ended). It decides nothing
about where things go: the sky is the whole world's background, and the haze fills the box you give it.

From your own script:

    import sys; sys.path.insert(0, FOLDER + '/store/tools')
    import sky_and_haze
    sky_and_haze.sky(bpy.context.scene)                                   # the dusk sky as the world's background
    sky_and_haze.haze(low=(-60, -5, 0), high=(60, 220, 30))               # thin air over the place, gone by the box's top
    sky_and_haze.photo_sky(bpy.context.scene, 'mud_road_puresky')        # or a photographed sky from the store's skies

The sky is coloured by how high you look: an amber band on the horizon, a dull warm band just above it, teal-blue
higher up and deep blue overhead, with streaky clouds drawn darker and bluer across it. It lights the scene a little
(strength 1.1); bring your own low sun and a cool fill light. The haze is a box of thin scattering air whose density
fades towards its top, so the sky above it stays clear and there is no step where it ends; keep the box over the place
and up to about twice the height of your tallest thing.

From the command line:

    python3 sky_and_haze.py --help
    python3 sky_and_haze.py --blend IN.blend --out OUT.blend --low -60 -5 0 --high 60 220 30 [--density 0.0016]

Options of sky(): horizon, low_band, high_band, top (the four colours, linear RGB), clouds (0 none to 1 heavy; default
0.8), strength (default 1.1), seed (moves the clouds; default 0).
Options of haze(): low, high (the box's corners, metres; required), density (default 0.0016; 0.004 is a misty evening),
colour (default a cool grey-blue), anisotropy (how much the haze glows towards a light behind it; default 0.35),
collection (default a new collection 'haze').
photo_sky(scene, name, strength, turn): a sky photographed all round (Poly Haven, CC0; the store's skies folder lists
them in skies/manifest.json: 'mud_road_puresky', a flat grey overcast day; 'overcast_soil_puresky', rain clouds;
'kloofendal_48d_partly_cloudy_puresky', a sunny day with its sun in it) as the world's background and light;
strength (default 1.0), turn (degrees the sky is turned about the vertical; default 0).
"""

import argparse
import os
import sys

import bpy
from mathutils import Vector

TOOLS = os.path.dirname(os.path.abspath(__file__))
if TOOLS not in sys.path:
    sys.path.insert(0, TOOLS)

TOOL = {
    'name': 'sky_and_haze',
    'what': 'a dusk sky for the world (amber horizon, teal-blue above, streaky cloud low down) and a box of thin haze that fades smoothly to nothing at its top',
    'call': 'sky_and_haze.sky(scene); sky_and_haze.haze(low=(-60, -5, 0), high=(60, 220, 30), density=0.0016)',
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
    },
    'materials': [],
    'source': 'the goods yard and military base builders of log 51 (their skies and haze boxes), made into a tool',
    'trap': 'a haze filling the whole world (a world volume) swallows the sky; keep the haze in a box over the place',
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


def main():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
    parser = argparse.ArgumentParser(description='A dusk sky and a box of thin haze (see the note at the top of sky_and_haze.py).')
    parser.add_argument('--blend', help='open this .blend file first (otherwise a new empty one)')
    parser.add_argument('--out', help='save the result here')
    parser.add_argument('--low', type=float, nargs=3, help='the haze box\'s low corner x y z (leave out for no haze)')
    parser.add_argument('--high', type=float, nargs=3, help='the haze box\'s high corner x y z')
    parser.add_argument('--density', type=float, default=0.0016, help='how thick the air is; default 0.0016')
    parser.add_argument('--clouds', type=float, default=0.8, help='streaky cloud, 0 none to 1 heavy; default 0.8')
    parser.add_argument('--seed', type=int, default=0, help='moves the clouds; default 0')
    args = parser.parse_args(argv)
    if args.blend:
        bpy.ops.wm.open_mainfile(filepath=args.blend)
    else:
        bpy.ops.wm.read_factory_settings(use_empty=True)
    sky(bpy.context.scene, clouds=args.clouds, seed=args.seed)
    if bool(args.low) != bool(args.high):
        parser.error('give both --low and --high for the haze box (or neither, for no haze)')
    if args.low and args.high:
        haze(args.low, args.high, density=args.density)
    if args.out:
        bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(args.out))
        print('saved', args.out)
    else:
        print('note: nothing was saved; give --out FILE.blend')


if __name__ == '__main__':
    main()
