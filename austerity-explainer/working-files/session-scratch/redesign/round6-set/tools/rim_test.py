"""What this does (scratch, round 6 set): run after assemble_works.py in the same Blender session. Draws film-size crops
of W1's composed frame (quiet state) with several rim-light arrangements for the waiting men, and of the gutter with a
few smoothings, so they can be compared side by side without rebuilding the Works each time.
Use: blender -b works-lane.blend --python assemble_works.py --python rim_test.py -- --view w1 --rim-out FOLDER"""
import os
import sys
import bpy
from mathutils import Vector

argv = sys.argv[sys.argv.index('--') + 1:]
out = argv[argv.index('--rim-out') + 1]
os.makedirs(out, exist_ok=True)
scene = bpy.context.scene
scene.render.resolution_x, scene.render.resolution_y = 1080, 1920
scene.render.resolution_percentage = 100
scene.eevee.taa_render_samples = 12
scene.render.use_border = True
scene.render.use_crop_to_border = True


def draw(name, box):
    x0, y0, x1, y1 = box          # fractions, y down
    scene.render.border_min_x, scene.render.border_max_x = x0, x1
    scene.render.border_min_y, scene.render.border_max_y = 1 - y1, 1 - y0
    scene.render.filepath = os.path.join(out, name + '.png')
    bpy.ops.render.render(write_still=True)
    print('rim_test: drew', name, flush=True)


rims = {key: bpy.data.objects[f'no-1-men-rim-{key}'] for key in ('yard', 'outer', 'lamp')}
MEN = (0.12, 0.46, 0.84, 0.72)
# arrangement: key -> (location, watts) ; keys not given are switched off
arrangements = {
    'r0-now': None,
    'r1-far-middle': {'yard': ((-3.9, 27.5, 2.1), 6000.0)},
    'r2-far-pair': {'yard': ((-5.0, 27.5, 2.1), 3500.0), 'lamp': ((-2.6, 27.5, 2.1), 3000.0)},
    'r3-far-pair-strong': {'yard': ((-5.0, 27.5, 2.1), 9000.0), 'lamp': ((-2.6, 27.5, 2.1), 8000.0)},
    'r4-mid-pair': {'yard': ((-4.9, 25.5, 2.0), 2500.0), 'lamp': ((-2.7, 25.5, 2.0), 2200.0)},
    'r5-now-quarter': 'quarter',
}
saved = {key: (light.location.copy(), light.data.energy) for key, light in rims.items()}
for name, setting in arrangements.items():
    for key, light in rims.items():
        if setting is None:
            light.location, light.data.energy = saved[key][0], saved[key][1]
        elif setting == 'quarter':
            light.location, light.data.energy = saved[key][0], saved[key][1] * 0.25
        elif key in setting:
            light.location, light.data.energy = Vector(setting[key][0]), setting[key][1]
        else:
            light.data.energy = 0.0
    draw(name, MEN)
for key, light in rims.items():
    light.location, light.data.energy = saved[key][0], saved[key][1]
# the gutter: as now, its colour flattened toward a plain stone, and with the kerb's stone instead
GUTTER = (0.55, 0.7, 1.0, 1.0)
draw('g0-now', GUTTER)
channel = bpy.data.objects['street_channels']
material = channel.data.materials[0]
nodes, links = material.node_tree.nodes, material.node_tree.links
shader = nodes['Principled BSDF']
source = shader.inputs['Base Color'].links[0].from_socket if shader.inputs['Base Color'].links else None
mix = nodes.new('ShaderNodeMix')
mix.data_type = 'RGBA'
mix.inputs[0].default_value = 0.75
mix.inputs[7].default_value = (0.2, 0.19, 0.18, 1.0)
if source is not None:
    links.new(source, mix.inputs[6])
links.new(mix.outputs[2], shader.inputs['Base Color'])
draw('g1-flat-75', GUTTER)
mix.inputs[0].default_value = 0.9
draw('g2-flat-90', GUTTER)
