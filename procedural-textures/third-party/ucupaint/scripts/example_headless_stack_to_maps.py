# What this does (plain words): a worked example. It starts Blender with no screen, switches on the Ucupaint add-on, builds a small
# stack of layers on a flat square (a base colour, a brick pattern, and a layer of sooty patches that only shows where a noise mask allows),
# asks Ucupaint to bake the finished surface into flat pictures, and saves them with the same names our own bake harness uses:
# colour.png, roughness.png, normal.png, height.png (16-bit, from Ucupaint's float displacement picture).
# It is our own code (not part of Ucupaint) and it contains two workarounds, each marked WORKAROUND, that were needed to run Ucupaint
# without a screen (see "03 Research - Ucupaint.md").
# Run:  BLENDER_USER_RESOURCES=<folder where the extension was installed> blender -b --factory-startup -t 2 --python THIS_FILE -- OUTPUT_FOLDER 1254
import sys, os, time, importlib
import bpy, addon_utils, numpy as np

OUTPUT_FOLDER = sys.argv[sys.argv.index('--') + 1]
SIZE = int(sys.argv[sys.argv.index('--') + 2])
MODULE = 'bl_ext.user_default.ucupaint'       # where "blender --command extension install-file -r user_default" puts it
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

addon_utils.enable(MODULE, default_set=True, persistent=False)   # default_set=True is needed: Ucupaint looks itself up in the preferences
ucupaint_bake = importlib.import_module(MODULE + '.Bake')
ucupaint_bake.YBakeChannels.no_layer_using = False   # WORKAROUND 1: the pop-up code that normally sets this does not run without a window

bpy.ops.mesh.primitive_plane_add(size=1.0)           # a 1 x 1 square whose UV goes 0..1, like our bake harness uses
square = bpy.context.active_object
material = bpy.data.materials.new('Material'); material.use_nodes = True; square.data.materials.append(material)
bpy.context.scene.render.engine = 'CYCLES'; bpy.context.scene.cycles.device = 'CPU'

bpy.ops.wm.y_quick_ypaint_node_setup(type='BSDF_PRINCIPLED')   # makes the Ucupaint group with channels Color, Metallic, Roughness, Normal
bpy.ops.wm.y_new_layer(name='Base', type='COLOR', solid_color=(0.55, 0.25, 0.12), uv_map='UVMap')
bpy.ops.wm.y_new_layer(name='Bricks', type='BRICK', uv_map='UVMap', blend_type='MULTIPLY')
bpy.ops.wm.y_new_layer(name='Soot', type='COLOR', solid_color=(0.04, 0.03, 0.025), uv_map='UVMap')
bpy.ops.wm.y_new_layer_mask(name='SootMask', type='NOISE', texcoord_type='UV', uv_name='UVMap', blend_type='MULTIPLY')

ucupaint_group = [n for n in material.node_tree.nodes if n.type == 'GROUP' and n.node_tree.yp.is_ypaint_node][0]
stack = ucupaint_group.node_tree.yp
for layer in stack.layers:                           # channel 0 Colour, 2 Roughness, 3 Normal; every layer takes part in each
    for channel_number in (0, 2, 3):
        layer.channels[channel_number].enable = True
    layer.channels[2].socket_input_name = 'Factor' if layer.type in ('NOISE', 'BRICK') else 'Color'   # a single-number channel wants a grey input
    layer.channels[3].normal_map_type = 'BUMP_MAP'
stack.layers['Soot'].channels[0].intensity_value = 0.85
stack.layers['Soot'].masks[0].scale = (3, 3, 3)

# WORKAROUND 2: Ucupaint's bake code asks Blender for the 3D view, the window and the screen. Background Blender has the objects but no
# "current" one; the factory file still contains a window with a 3D view area, so we lend it to the bake call.
window = bpy.context.window_manager.windows[0]
area = [a for a in window.screen.areas if a.type == 'VIEW_3D'][0]
override = dict(window=window, screen=window.screen, area=area, region=[r for r in area.regions if r.type == 'WINDOW'][0])
started = time.time()
with bpy.context.temp_override(**override):
    bpy.ops.wm.y_bake_channels(width=SIZE, height=SIZE, samples=1, margin=0, fxaa=False, uv_map='UVMap',
                               bake_device='CPU', use_float_for_displacement=True)
print('Ucupaint bake took %.1f s' % (time.time() - started))

suffix_to_file_name = {' Color': 'colour', ' Roughness': 'roughness', ' Normal': 'normal', ' Displacement': 'height'}   # picture names look like 'Ucupaint Material.001 Color'
names = {}
for image in bpy.data.images:
    for suffix, file_name in suffix_to_file_name.items():
        if image.name.startswith('Ucupaint') and image.name.endswith(suffix):
            names[image.name] = file_name
settings = bpy.context.scene.render.image_settings
for image in bpy.data.images:
    if image.name in names:
        settings.file_format = 'PNG'; settings.color_mode = 'RGB'
        settings.color_depth = '16' if names[image.name] == 'height' else '8'
        image.save_render(os.path.join(OUTPUT_FOLDER, names[image.name] + '.png'), scene=bpy.context.scene)
        print('saved', names[image.name], tuple(image.size), 'float' if image.is_float else '8-bit')
