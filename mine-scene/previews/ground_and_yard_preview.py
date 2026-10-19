# What this does: takes quick preview photos of the ground and yard clutter on their own, under a dusk sky, so we can judge them
# without the other parts of the mine. It builds the part (modules/ground_and_yard.py), adds a plain dusk sky (orange glow low,
# teal above) and a low warm sun, then photographs it from a few places:
#   standard  = the finished-look camera (tall 9:16 frame, front-left three-quarter view)
#   detail    = a low close view of mud, ruts, puddles and coal lumps
#   back      = from the far back looking toward the camera side
#   side      = from the right side across the yard (fence, lamp post, sleepers)
#   rack      = the leaning timber stack at the far left, close
#   cart      = the handcart and the barrels, close
#   lamp      = the lamp post and fence
#   topdown   = straight down on the yard, to see the ruts and puddles laid out
# Use: blender -b --disable-autoexec -t 2 --python ground_and_yard_preview.py -- [views comma separated] [--width 506] [--samples 32] [--neutral] [--prefix NAME] [--nodisp] [--pixel-size N] [--report]
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, 'lib'))
sys.path.insert(0, os.path.join(ROOT, 'modules'))
import bpy
import mine_common as mc
import ground_and_yard

arguments = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
views_wanted = arguments[0].split(',') if arguments and not arguments[0].startswith('--') else ['standard', 'detail', 'back']


def option(name, default, cast=float):
    if name in arguments:
        return cast(arguments[arguments.index(name) + 1])
    return default


WIDTH = option('--width', 506, int)
SAMPLES = option('--samples', 32, int)
OUT_PREFIX = os.path.join(ROOT, 'out', 'ground_and_yard_')
if '--prefix' in arguments:
    OUT_PREFIX = os.path.join(ROOT, 'out', arguments[arguments.index('--prefix') + 1])

# name: (camera position, look-at point, lens, width/height shape)
VIEWS = {
    'standard': ((-9.5, -21.0, 1.7), (1.0, 2.0, 5.5), 28, 9 / 16),
    'detail': ((-7.5, -19.0, 0.9), (-5.5, -12.5, 0.0), 30, 1.0),
    'detail2': ((-2.0, -16.0, 0.8), (-6.5, -12.0, 0.0), 26, 1.0),
    'back': ((16.0, 38.0, 7.0), (-2.0, -12.0, 0.5), 28, 1.0),
    'side': ((26.0, -14.0, 2.4), (9.0, 0.0, 1.5), 26, 1.0),
    'rack': ((-13.0, -9.5, 1.8), (-7.8, -4.6, 1.4), 30, 1.0),
    'cart': ((-10.5, -12.0, 1.4), (-7.6, -9.0, 0.7), 30, 1.0),
    'lamp': ((13.5, -9.0, 2.0), (8.0, -0.5, 1.8), 30, 1.0),
    'fence': ((18.0, -9.0, 2.0), (16.0, 1.0, 0.8), 30, 1.0),
    'sleepers': ((2.2, -9.0, 1.5), (5.9, -3.6, 0.5), 32, 1.0),
    'barrels': ((-3.2, -7.0, 1.4), (-4.9, -2.1, 0.5), 32, 1.0),
    'pool': ((-5.8, -20.6, 0.7), (-8.7, -17.9, 0.0), 34, 1.0),
    'topdown': ((-2.0, -14.0, 42.0), (-2.0, -14.0, 0.0), 30, 1.0),
}


def dusk_sky():
    """A plain dusk: orange glow near the horizon, pale teal above, dark teal overhead."""
    scene = bpy.context.scene
    world = bpy.data.worlds.new('Dusk sky')
    scene.world = world
    world.use_nodes = True
    nodes, links = world.node_tree.nodes, world.node_tree.links
    nodes.clear()
    output = nodes.new('ShaderNodeOutputWorld')
    background = nodes.new('ShaderNodeBackground')
    background.inputs['Strength'].default_value = 1.0
    coords = nodes.new('ShaderNodeTexCoord')
    split = nodes.new('ShaderNodeSeparateXYZ')
    ramp = nodes.new('ShaderNodeValToRGB')
    links.new(coords.outputs['Generated'], split.inputs['Vector'])
    ramp.color_ramp.interpolation = 'EASE'
    stops = ramp.color_ramp.elements
    stops[0].position, stops[0].color = 0.0, (0.05, 0.05, 0.06, 1)
    stops[1].position, stops[1].color = 1.0, (0.10, 0.20, 0.26, 1)
    for position, colour in ((0.52, (0.55, 0.27, 0.10, 1)), (0.56, (1.4, 0.70, 0.30, 1)), (0.62, (0.62, 0.62, 0.55, 1)), (0.78, (0.20, 0.34, 0.38, 1))):
        element = stops.new(position)
        element.color = colour
    map_z = nodes.new('ShaderNodeMapRange')
    map_z.inputs['From Min'].default_value = -1.0
    map_z.inputs['From Max'].default_value = 1.0
    links.new(split.outputs['Z'], map_z.inputs['Value'])
    links.new(map_z.outputs['Result'], ramp.inputs['Fac'])
    links.new(ramp.outputs['Color'], background.inputs['Color'])
    links.new(background.outputs['Background'], output.inputs['Surface'])
    mc.set_sun(9, 212, strength=3.4, colour=(1.0, 0.66, 0.38), angle_degrees=2.5)


def photograph(name, size):
    position, target, lens, shape = VIEWS[name]
    width = size
    height = int(round(width / shape))
    if shape == 9 / 16:
        width, height = WIDTH, int(round(WIDTH * 16 / 9))
    for obj in list(bpy.data.objects):
        if obj.type == 'CAMERA':
            bpy.data.objects.remove(obj)
    started = time.time()
    path = OUT_PREFIX + name + '.png'
    scene = bpy.context.scene
    scene.cycles.dicing_rate = 1.0
    scene.cycles.offscreen_dicing_scale = 4.0
    mc.render_preview(path, position, target, lens=lens, size=(width, height), samples=SAMPLES)
    mc.say(f'photo {name}: {time.time() - started:.0f} s -> {path}')


mc.clear_scene()
build_started = time.time()
info = ground_and_yard.build('Mine ground and yard')
mc.say(f'built in {time.time() - build_started:.1f} s: {info["notes"]}')
if '--nodisp' in arguments:
    ground_and_yard.ground_mesh_object().modifiers.clear()
elif '--pixel-size' in arguments:
    ground_and_yard.ground_mesh_object().modifiers[0].adaptive_pixel_size = option('--pixel-size', 1.0)
if '--neutral' in arguments:
    # plain grey-blue daylight, to judge the true colours of the ground without the dusk colouring
    mc.set_flat_world((0.55, 0.62, 0.72), 0.9)
    mc.set_sun(32, 215, strength=3.2, colour=(1.0, 0.86, 0.68))
else:
    dusk_sky()
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.view_settings.view_transform = 'AgX'
for view in views_wanted:
    if view in VIEWS:
        photograph(view, WIDTH if view != 'topdown' else min(WIDTH * 2, 900))
print(json.dumps(ground_and_yard.LAST_BUILD_INFO, indent=1))
if '--report' in arguments:
    info_now = ground_and_yard.LAST_BUILD_INFO
    report = {
        'object_count': len(info_now['object_names']),
        'objects': info_now['object_names'],
        'triangle_count': sum(info_now['triangles'].values()),
        'triangles_by_object': info_now['triangles'],
        'uses_real_displacement': [ground_and_yard.GROUND_OBJECT_NAME + ' (mud, adaptive subdivision, %g px per facet)' % ground_and_yard.TERRAIN_DICING_PIXELS],
        'build_seconds': info_now['build_seconds'],
        'puddles': info_now['puddles'],
        'lamp_glass_position': ground_and_yard.lamp_light_position(),
        'known_flaws': ground_and_yard.KNOWN_FLAWS,
    }
    with open(os.path.join(ROOT, 'out', 'ground_and_yard_report.json'), 'w') as handle:
        json.dump(report, handle, indent=1)
    mc.say('wrote out/ground_and_yard_report.json')
