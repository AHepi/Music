# What this does (plain words)
# ------------------------------------------------------------------------------------------------------------------------------------------------
# Round 2, run 1. The checker found that in EEVEE (the fast renderer the film's plates are drawn with) the wet road is covered in white speckle ("grit"), which the
# slower Cycles pictures hide. This run finds out WHICH picture of the road material makes the speckle, by drawing the same lower-left part of the main camera view
# (a "border" render: only that part is drawn, which is quick) several times with ONE thing changed each time:
#   dry          the layer switched off (the reference: how grainy a dry road is)
#   wet_first    round 1's wet road, unchanged
#   flatten      Relief Flatten 1.0 (the checker's cure: water flattens the road's relief completely)
#   smooth2      the relief picture replaced by a copy blurred 2 dots wide (4 mm): grain gone, joints kept
#   smooth4      same, 4 dots wide (8 mm)
#   no_height    the relief HEIGHT picture (which decides where stone tops stay dry) replaced by a flat grey
#   rough_half   Wet Roughness 0.5 instead of 0.3
#   no_normal    the road's relief picture removed altogether (flat road) to see what is left
# It prints the machine's texture settings too (mipmaps: smaller copies of a picture that a graphics card uses for far-away dots).
# Writes OUT_FOLDER/<variant>.png and OUT_FOLDER/seconds.txt; tools/21b_grain_numbers.py measures them afterwards.
# Run: xvfb-run -a blender -b --disable-autoexec -t 2 set_copy/street.blend --python tools/21_eevee_grit_diagnosis.py -- OUT_FOLDER
import os
import sys
import time

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.dont_write_bytecode = True
import apply_wetness_to_set as aw  # noqa: E402

out_folder = sys.argv[sys.argv.index('--') + 1]
os.makedirs(out_folder, exist_ok=True)
scene = bpy.context.scene
prefs = bpy.context.preferences.system
print('PREFS', {k: getattr(prefs, k) for k in dir(prefs) if ('mip' in k or 'aniso' in k or 'filter' in k) and not k.startswith('_')})
aw.cameras()
aw.apply(wetness=0.85, puddles=0.5)
node, spec = aw.APPLIED['street_setts']
tree = bpy.data.materials['street_setts'].node_tree
normal_map = next(n for n in tree.nodes if n.type == 'NORMAL_MAP')
normal_image_node = normal_map.inputs['Color'].links[0].from_node
sharp_image = normal_image_node.image
print('NORMAL IMAGE', sharp_image.name, sharp_image.size[:], 'strength', normal_map.inputs['Strength'].default_value, 'interp', normal_image_node.interpolation)

scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x, scene.render.resolution_y = 540, 960
scene.render.image_settings.file_format = 'PNG'
scene.render.image_settings.color_mode = 'RGB'
scene.eevee.taa_render_samples = 16
scene.eevee.use_raytracing = True
scene.render.use_border = True
scene.render.use_crop_to_border = False
scene.render.border_min_x, scene.render.border_max_x = 0.0, 0.5
scene.render.border_min_y, scene.render.border_max_y = 0.0, 0.42


def smooth_image(name):
    return bpy.data.images.load(f'{aw.TEX}{name}', check_existing=True)


height_source = node.inputs['Height'].links[0].from_socket


def reset():
    """Put the road material back to round 1's state before each variant."""
    node.inputs['Relief Flatten'].default_value = spec.get('relief_flatten', 0.35)
    node.inputs['Wet Roughness'].default_value = spec['wet_roughness']
    normal_image_node.image = sharp_image
    normal_map.inputs['Strength'].default_value = 1.4
    if not node.inputs['Height'].is_linked:
        tree.links.new(height_source, node.inputs['Height'])
    if not node.inputs['Normal'].is_linked:
        tree.links.new(normal_map.outputs['Normal'], node.inputs['Normal'])
VARIANTS = ['dry', 'wet_first', 'flatten', 'smooth2', 'smooth4', 'no_height', 'rough_half', 'no_normal']
seconds = {}
for variant in VARIANTS:
    reset()
    aw.set_state(0.0, 0.0) if variant == 'dry' else aw.set_state(0.85, 0.5)
    if variant == 'flatten':
        node.inputs['Relief Flatten'].default_value = 1.0
    elif variant == 'smooth2':
        normal_image_node.image = smooth_image('square_cobblestone_normal_smooth_2.png')
        normal_image_node.image.colorspace_settings.name = 'Non-Color'
    elif variant == 'smooth4':
        normal_image_node.image = smooth_image('square_cobblestone_normal_smooth_4.png')
        normal_image_node.image.colorspace_settings.name = 'Non-Color'
    elif variant == 'no_height':
        for link in list(node.inputs['Height'].links):
            tree.links.remove(link)
        node.inputs['Height'].default_value = 0.5
    elif variant == 'rough_half':
        node.inputs['Wet Roughness'].default_value = 0.5
    elif variant == 'no_normal':
        for link in list(node.inputs['Normal'].links):
            tree.links.remove(link)
        node.inputs['Normal'].default_value = (0.0, 0.0, 1.0)
    scene.render.filepath = os.path.join(out_folder, f'{variant}.png')
    started = time.time()
    bpy.ops.render.render(write_still=True)
    seconds[variant] = round(time.time() - started, 1)
    print('DRAWN', variant, seconds[variant], 's', flush=True)
open(os.path.join(out_folder, 'seconds.txt'), 'w').write(str(seconds) + '\n')
