# What this does: a test of the WETNESS draft (wetness_group.py) on the real pit village street: opens street.blend (read only, never saved),
# draws the main camera view DRY (as the street is today), then puts the WETNESS group on the road, pavement, kerbs, channel, walls, dressed stone and
# roofs and draws it WET, then draws the masks (wet, puddle, streak) as plain light and measures how much of the road they cover.
# Run: blender -b --disable-autoexec -t 2 street.blend --python 03_wet_street_test.py -- OUT_FOLDER [--engine CYCLES|EEVEE] [--samples N] [--size W H]
#        [--wetness 0.85] [--puddles 0.55] [--only wet|dry|masks] [--camera main|close_left|close_road] [--raytracing]
# --only ablation draws five pictures: dry today, then the wet look built up one part at a time (colour, + gloss, + reflection film, + puddles and flat relief).
# Writes OUT_FOLDER/<camera>_<state>.png and OUT_FOLDER/<camera>_report.json (times, coverage).
import json
import math
import os
import sys
import time

import bpy
from mathutils import Vector

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wetness_group as wg  # noqa: E402

args = sys.argv[sys.argv.index('--') + 1:]
out_folder = args[0]
def opt(name, default=None, count=1):
    if name not in args:
        return default
    i = args.index(name)
    return args[i + 1] if count == 1 else [a for a in args[i + 1:i + 1 + count]]
engine = opt('--engine', 'CYCLES')
samples = int(opt('--samples', '48'))
size = [int(v) for v in opt('--size', ['540', '960'], 2)]
wetness = float(opt('--wetness', '0.85'))
puddles = float(opt('--puddles', '0.55'))
only = opt('--only', 'all')
camera_choice = opt('--camera', 'main')
raytracing = '--raytracing' in args
os.makedirs(out_folder, exist_ok=True)
TEX = 'proc-work/street_wet/study/work/polyhaven_maps/'

scene = bpy.context.scene
report = {'engine': engine, 'samples': samples, 'size': size, 'wetness': wetness, 'puddles': puddles, 'camera': camera_choice, 'times_seconds': {}}

# ---- cameras: the main camera as it is, or a close one beside the gutter
if camera_choice != 'main':
    data = bpy.data.cameras.new('close')
    cam = bpy.data.objects.new('close', data)
    scene.collection.objects.link(cam)
    data.sensor_fit = 'VERTICAL'
    data.angle_y = math.radians(38)
    if camera_choice == 'close_left':      # standing in the road looking up the left gutter: kerb, pavement, wall foot
        cam.location = Vector((-1.2, 5.0, 1.35)); target = Vector((-3.0, 11.0, 0.55))
    else:                                  # 'close_road': a low look at the setts
        cam.location = Vector((0.5, 6.0, 1.0)); target = Vector((0.0, 11.0, 0.45))
    cam.rotation_euler = (target - cam.location).to_track_quat('-Z', 'Y').to_euler()
    scene.camera = cam

# ---- render settings
scene.render.resolution_x, scene.render.resolution_y = size
scene.render.resolution_percentage = 100
if engine == 'CYCLES':
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'
    scene.cycles.samples = samples
    scene.cycles.use_adaptive_sampling = True
    scene.cycles.adaptive_threshold = 0.03
    scene.cycles.use_denoising = True
    scene.cycles.denoiser = 'OPENIMAGEDENOISE'
    scene.cycles.max_bounces = 6
    scene.cycles.glossy_bounces = 4
    scene.cycles.sample_clamp_indirect = 8.0
else:
    scene.render.engine = 'BLENDER_EEVEE'
    scene.eevee.taa_render_samples = samples
    scene.eevee.use_raytracing = raytracing
    if raytracing:
        try:
            scene.eevee.ray_tracing_method = 'SCREEN'
        except Exception as error:
            print('ray_tracing_method not set:', error)
scene.render.image_settings.file_format = 'PNG'
scene.render.image_settings.color_mode = 'RGB'

def draw(name):
    started = time.time()
    scene.render.filepath = os.path.join(out_folder, f'{camera_choice}_{name}.png')
    bpy.ops.render.render(write_still=True)
    report['times_seconds'][name] = round(time.time() - started, 1)
    print('DRAWN', name, report['times_seconds'][name], 's')

# ---- 1. dry, as the street is today
if only in ('all', 'dry', 'ablation', 'dry_wet'):
    draw('dry_today')

# ---- 2. put the wetness layer on
def load(name):
    image = bpy.data.images.load(TEX + name, check_existing=True)
    return image

MATERIALS = {   # name: (rough picture, height picture, porosity, ground offset)
    'street_setts': ('square_cobblestone_rough.jpg', 'square_cobblestone_displacement.jpg', 0.6, 0.0),
    'pavement_flags': ('large_grey_tiles_rough.jpg', 'large_grey_tiles_displacement.jpg', 0.55, 0.13),
    'cottage_brick': ('red_brick_rough.jpg', 'red_brick_displacement.jpg', 0.7, 0.13),
    'cottage_stone': ('stone_brick_wall_001_rough.jpg', 'stone_brick_wall_001_displacement.jpg', 0.6, 0.13),
    'kerb_stone': (None, None, 0.5, 0.0), 'channel_stones': (None, None, 0.5, 0.0), 'dressed_stone': (None, None, 0.5, 0.13),
    'dark_dressed_stone': (None, None, 0.5, 0.13), 'roof_slate': (None, None, 0.3, 0.0), 'colliery_brick': (None, None, 0.7, 0.0),
    'colliery_yard': (None, None, 0.7, 0.0),
}
state = {'wetness': wetness, 'puddles': puddles}
groups = {}
for name, (rough, height, porosity, offset) in MATERIALS.items():
    material = bpy.data.materials[name]
    lowness = None
    if name == 'street_setts':     # the road falls to the gutters: low beside the kerb, high on the crown
        tree = material.node_tree
        geometry = tree.nodes.new('ShaderNodeNewGeometry')
        split = tree.nodes.new('ShaderNodeSeparateXYZ')
        tree.links.new(geometry.outputs['Position'], split.inputs[0])
        absolute = tree.nodes.new('ShaderNodeMath'); absolute.operation = 'ABSOLUTE'
        tree.links.new(split.outputs['X'], absolute.inputs[0])
        ramp = tree.nodes.new('ShaderNodeMapRange'); ramp.interpolation_type = 'SMOOTHSTEP'
        ramp.inputs['From Min'].default_value = 0.6; ramp.inputs['From Max'].default_value = 2.1
        tree.links.new(absolute.outputs[0], ramp.inputs['Value'])
        lowness = ramp.outputs['Result']
    groups[name] = wg.add_wetness_to_material(material, state, rough_image=load(rough) if rough else None, height_image=load(height) if height else None,
                                              lowness=lowness, ground_offset=offset, porosity=porosity, seed=3.0)
if only in ('all', 'wet', 'dry_wet'):
    if engine == 'EEVEE' and '--raytracing_wet' in args:
        scene.eevee.use_raytracing = True
        try:
            scene.eevee.ray_tracing_method = 'SCREEN'
        except Exception as error:
            print('ray_tracing_method not set:', error)
    draw('wet')

if only == 'ablation':
    steps = [('a1_colour_only', dict(puddles=0.0, rough=0.0, spec=0.0, coat=0.0, normal=0.0)),
             ('a2_plus_gloss', dict(puddles=0.0, rough=1.0, spec=0.0, coat=0.0, normal=0.0)),
             ('a3_plus_film', dict(puddles=0.0, rough=1.0, spec=1.0, coat=1.0, normal=1.0)),
             ('a4_plus_puddles', dict(puddles=puddles, rough=1.0, spec=1.0, coat=1.0, normal=1.0))]
    for label, setting in steps:
        for group in groups.values():
            group.inputs['Puddles'].default_value = setting['puddles']
            group.inputs['Roughness Effect'].default_value = setting['rough']
            group.inputs['Specular Effect'].default_value = setting['spec']
            group.inputs['Coat Effect'].default_value = setting['coat']
            group.inputs['Normal Effect'].default_value = setting['normal']
        draw(label)

# ---- 3. the masks as plain light, and how much of the road they cover
if only in ('all', 'masks'):
    for material in bpy.data.materials:
        if not material.node_tree:
            continue
        tree = material.node_tree
        output = next((n for n in tree.nodes if n.type == 'OUTPUT_MATERIAL'), None)
        if output is None:
            continue
        group = groups.get(material.name)
        emission = tree.nodes.new('ShaderNodeEmission')
        if group is not None:
            combine = tree.nodes.new('ShaderNodeCombineColor')
            tree.links.new(group.outputs['Wet Mask'], combine.inputs['Red'])
            tree.links.new(group.outputs['Puddle Mask'], combine.inputs['Green'])
            tree.links.new(group.outputs['Streak Mask'], combine.inputs['Blue'])
            tree.links.new(combine.outputs['Color'], emission.inputs['Color'])
        else:
            emission.inputs['Color'].default_value = (0, 0, 0, 1)
        tree.links.new(emission.outputs['Emission'], output.inputs['Surface'])
    scene.view_settings.view_transform = 'Raw'
    scene.view_settings.look = 'None'
    scene.view_settings.exposure = 0.0
    scene.view_settings.gamma = 1.0
    scene.render.dither_intensity = 0.0
    if engine == 'CYCLES':
        scene.cycles.samples = 1
        scene.cycles.use_adaptive_sampling = False
        scene.cycles.use_denoising = False
        scene.cycles.pixel_filter_type = 'BOX'
        scene.cycles.filter_width = 1.0
        scene.world.node_tree.nodes['Background'].inputs['Color'].default_value = (0, 0, 0, 1)
        scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.0
    for value in [float(v) for v in opt('--puddle_list', str(puddles)).split(',')]:
        for group in groups.values():
            group.inputs['Puddles'].default_value = value
        draw(f'masks_p{value}')
with open(os.path.join(out_folder, f'{camera_choice}_{only}_report.json'), 'w') as handle:
    json.dump(report, handle, indent=1)
print('REPORT', report)
