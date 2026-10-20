# What this does (plain words)
# ------------------------------------------------------------------------------------------------------------------------------------------------
# It turns the wet street (the street COPY with the WETNESS layer on) into flat pictures ("maps") that a .glb file can carry, then writes a wet .glb.
# "Photographing" = the trick the texture recipes' bake tool (lib/bake_harness.py) uses: a camera looks straight at a flat surface and draws one output of the layer as
# plain light, so every dot of the picture holds exactly one number.
#
# What gets photographed:
#   * THE GROUND ATLAS: road + gutter + kerb tops + both pavements seen from straight above as ONE picture of the whole street (x -4.4 to 4.4 m, y -12 to 72 m),
#     48 dots a metre (one dot = 2.1 cm), so the road is 4,032 dots long. The 3 ground materials share this one set of pictures, laid on a second set of texture
#     coordinates ("UV2": across and along the street, once, nothing repeats).
#   * THE FOUR WALL MESHES (stone and brick, two facade layouts each): the front of each shared cottage mesh photographed square-on, 200 dots a metre (0.5 cm),
#     laid on a UV2 of its own. One picture serves every cottage of that kind, because the layer measures walls in the cottage's own coordinates.
# Maps made for each (grey pictures unless said): wet colour (sRGB colour), roughness, clear coat strength, clear coat roughness, SPECULARITY (reflection strength as a
# share of its biggest value: 1 = the wet shine, 0.67 = a dry surface's normal shine), a wet-normal map (ground only; for checking, NOT used in the .glb, see the note) and the
# puddle mask and the wet mask (for checking).
# Then it builds, for the .glb, a plain material per photographed surface that wears only those pictures (plus the photo's own tiled normal map on the first
# coordinates, which keeps the setts' joints that 2 cm dots would wash out), gives every other changed material one flat "wet" set of numbers (colour x its measured
# wet ratio, roughness, coat, specular), writes the .glb and saves a .blend of that baked scene (so a later run can draw the baked street and compare it with the live one).
#
# Run: blender -b --disable-autoexec -t 2 set_copy/street.blend --python tools/06_bake_maps_and_export.py -- MAPS_FOLDER GLB_PATH BLEND_PATH [wetness puddles]
# Writes MAPS_FOLDER/*.png|jpg, MAPS_FOLDER/bake_report.json, the .glb and the .blend.
import json
import math
import os
import sys
import time

import bpy
import numpy as np
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.dont_write_bytecode = True
import apply_wetness_to_set as aw  # noqa: E402

args = sys.argv[sys.argv.index('--') + 1:]
REUSE = '--reuse' in args          # skip the photographing and use the picture files already in MAPS_FOLDER (to rebuild only the materials and the .glb)
args = [a for a in args if a != '--reuse']
maps_folder, glb_path, blend_path = args[0], args[1], args[2]
wetness = float(args[3]) if len(args) > 3 else 0.85
puddles = float(args[4]) if len(args) > 4 else 0.5
os.makedirs(maps_folder, exist_ok=True)
scene = bpy.context.scene
# the picture settings of the file as it is: the photographing changes them, and they are put back before the baked .blend is saved (a first run forgot, and the baked street was drawn with no sky light and no film look)
view = scene.view_settings
background_node = scene.world.node_tree.nodes['Background']
SAVED = dict(view=(view.view_transform, view.look, view.exposure, view.gamma), world=(tuple(background_node.inputs['Color'].default_value), background_node.inputs['Strength'].default_value),
             render=(scene.render.dither_intensity, scene.cycles.pixel_filter_type, scene.cycles.filter_width, scene.cycles.samples, scene.cycles.use_adaptive_sampling,
                     scene.cycles.use_denoising, scene.cycles.max_bounces, scene.render.engine))
report = {'wetness': wetness, 'puddles': puddles, 'seconds': {}, 'files': {}}
started_all = time.time()

# ------------------------------------------------------------------------------------------------------------------------------ settings
PPM_GROUND = 48                                   # dots per metre for the ground atlas
Y0, Y1 = -12.0, 72.0                              # the street from its start to where the setts stop
GROUND_WIDTH = round(8.8 * PPM_GROUND)            # 422 dots
GROUND_HEIGHT = round((Y1 - Y0) * PPM_GROUND)     # 4032 dots
X_HALF = GROUND_WIDTH / PPM_GROUND / 2
PPM_WALL = 200
WALL_HALF, WALL_Z0, WALL_Z1 = 2.25, -0.9, 6.0     # the cottage front in its own coordinates: y -2.25..2.25, z -0.9 (below the floor) .. 6.0 (the eaves)
WALL_WIDTH, WALL_HEIGHT = round(2 * WALL_HALF * PPM_WALL), round((WALL_Z1 - WALL_Z0) * PPM_WALL)
SPEC_MAX = 0.75                                   # the biggest Specular IOR Level the layer writes (0.5 + Specular Boost 0.25); the specularity map is level / SPEC_MAX
SLOPE = math.atan(aw.SLOPE)
GROUND_OBJECTS = ('street_setts', 'street_channels', 'street_kerbs', 'street_pavements')
GROUND_MATERIALS = ('street_setts', 'channel_stones', 'kerb_stone', 'pavement_flags')
WALL_SOURCES = {   # baked wall name: (object to photograph, its wall material variant)
    'wall_stone_door_left': ('right_row_a_cottage_01_walls', 'cottage_stone_door_left'),
    'wall_stone_door_right': ('right_row_a_cottage_02_walls', 'cottage_stone_door_right'),
    'wall_brick_door_left': ('left_row_a_cottage_01_walls', 'cottage_brick_door_left'),
    'wall_brick_door_right': ('left_row_a_cottage_02_walls', 'cottage_brick_door_right'),
}
# how much darker (as a share of dry) each material is when wet, measured by tools/04_colour_ratios.py (main camera, state wet 0.85 / puddles 0.5)
# round 2: measured again with the round 2 settings (tools/04b_colour_ratios.py on work/r30/colour, main camera); the walls' own numbers matter only for the chimneys, which wear the plain wall materials
# The first bake of round 2 used the measured colour ratios (colliery brick 0.86, dressed stone 0.88, dark dressed stone 0.82, slate 0.90) and the baked street then came out brighter than the live
# one for the flat stand-ins (colliery brick x1.24, dressed stone x1.21, slate x1.04; tools/31_compare_baked_live.py): a flat "wet all over" surface shines more than a surface that is wet in
# places. So these four were multiplied by live / baked from that comparison (0.69, 0.73, 0.68, 0.87): they are fitted to the main camera, not measured colour ratios.
COLOUR_RATIO = {'channel_stones': 0.69, 'kerb_stone': 0.76, 'colliery_brick': 0.69, 'cottage_brick': 0.70, 'cottage_stone': 0.72, 'dark_dressed_stone': 0.68,
                'dressed_stone': 0.73, 'roof_slate': 0.87, 'colliery_yard': 0.56}

# ------------------------------------------------------------------------------------------------------------------------------ before the layer goes on
for name in aw.MATERIALS:                         # keep a clean copy of every material that will be changed (the .glb materials are made from these)
    clean = bpy.data.materials[name].copy()
    clean.name = name + '__flat'
aw.apply(wetness=wetness, puddles=puddles)
groups = {name: pair[0] for name, pair in aw.APPLIED.items()}

# ------------------------------------------------------------------------------------------------------------------------------ the photographer
def emission_rig(material_names):
    rig = {}
    if REUSE:
        return rig
    for name in material_names:
        tree = bpy.data.materials[name].node_tree
        output = next(n for n in tree.nodes if n.type == 'OUTPUT_MATERIAL')
        emission = tree.nodes.new('ShaderNodeEmission')
        emission.inputs['Color'].default_value = (0, 0, 0, 1)
        tree.links.new(emission.outputs['Emission'], output.inputs['Surface'])
        rig[name] = (tree, emission)
    return rig


def grey_colour(tree, socket, scale=1.0):
    if scale != 1.0:
        maths = tree.nodes.new('ShaderNodeMath')
        maths.operation = 'MULTIPLY'
        maths.inputs[1].default_value = scale
        tree.links.new(socket, maths.inputs[0])
        socket = maths.outputs[0]
    combine = tree.nodes.new('ShaderNodeCombineColor')
    for channel in ('Red', 'Green', 'Blue'):
        tree.links.new(socket, combine.inputs[channel])
    return combine.outputs['Color']


def normal_colour(tree, socket):
    """The layer's world normal turned into the street's slope frame (x across, y along the slope, z out of the street), then 0..1: a normal map."""
    separate = tree.nodes.new('ShaderNodeSeparateXYZ')
    tree.links.new(socket, separate.inputs[0])

    def maths(operation, a, b, c=None):
        node = tree.nodes.new('ShaderNodeMath')
        node.operation = operation
        for index, value in enumerate((a, b, c)):
            if value is None:
                continue
            if isinstance(value, bpy.types.NodeSocket):
                tree.links.new(value, node.inputs[index])
            else:
                node.inputs[index].default_value = value
        return node.outputs[0]
    tx = separate.outputs['X']
    ty = maths('ADD', maths('MULTIPLY', separate.outputs['Y'], math.cos(SLOPE)), maths('MULTIPLY', separate.outputs['Z'], math.sin(SLOPE)))
    tz = maths('ADD', maths('MULTIPLY', separate.outputs['Y'], -math.sin(SLOPE)), maths('MULTIPLY', separate.outputs['Z'], math.cos(SLOPE)))
    combine = tree.nodes.new('ShaderNodeCombineColor')
    for channel, value in (('Red', tx), ('Green', ty), ('Blue', tz)):
        tree.links.new(maths('MULTIPLY_ADD', value, 0.5, 0.5), combine.inputs[channel])
    return combine.outputs['Color']


def show(rig, channel):
    """Wire one output of each material's layer into its emission (plain light)."""
    for name, (tree, emission) in rig.items():
        for link in list(emission.inputs['Color'].links):
            tree.links.remove(link)
        group = groups.get(name)
        if group is None:
            emission.inputs['Color'].default_value = (0, 0, 0, 1)
            continue
        if channel == 'colour':
            tree.links.new(group.outputs['Colour'], emission.inputs['Color'])
        elif channel == 'normal':
            tree.links.new(normal_colour(tree, group.outputs['Normal']), emission.inputs['Color'])
        else:
            source = {'roughness': ('Roughness', 1.0), 'coat': ('Coat Weight', 1.0), 'coat_roughness': ('Coat Roughness', 1.0), 'specularity': ('Specular IOR Level', 1.0 / SPEC_MAX),
                      'puddles': ('Puddle Mask', 1.0), 'wet': ('Wet Mask', 1.0)}[channel]
            tree.links.new(grey_colour(tree, group.outputs[source[0]], source[1]), emission.inputs['Color'])


def set_up_photography(width, height, samples=8):
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'
    scene.cycles.samples = samples
    scene.cycles.use_adaptive_sampling = False
    scene.cycles.use_denoising = False
    scene.cycles.max_bounces = 0
    scene.cycles.pixel_filter_type = 'BOX'
    scene.cycles.filter_width = 1.0
    scene.render.resolution_x, scene.render.resolution_y = width, height
    scene.render.resolution_percentage = 100
    scene.render.dither_intensity = 0.0
    scene.view_settings.look = 'None'
    scene.view_settings.exposure = 0.0
    scene.view_settings.gamma = 1.0
    background = scene.world.node_tree.nodes['Background']
    background.inputs['Color'].default_value = (0, 0, 0, 1)
    background.inputs['Strength'].default_value = 0.0


def shoot(path, channel):
    if REUSE:
        extension = 'jpg' if channel == 'colour' else 'png'
        return f'{path}.{extension}'
    scene.view_settings.view_transform = 'Standard' if channel == 'colour' else 'Raw'
    settings = scene.render.image_settings
    if channel == 'colour':
        settings.file_format, settings.color_mode, settings.quality = 'JPEG', 'RGB', 93
    elif channel == 'normal':
        settings.file_format, settings.color_mode, settings.color_depth = 'PNG', 'RGB', '8'
    else:
        settings.file_format, settings.color_mode, settings.color_depth = 'PNG', 'BW', '8'
    extension = 'jpg' if channel == 'colour' else 'png'
    scene.render.filepath = f'{path}.{extension}'
    started = time.time()
    bpy.ops.render.render(write_still=True)
    report['seconds'][os.path.basename(path)] = round(time.time() - started, 1)
    report['files'][os.path.basename(path)] = os.path.getsize(f'{path}.{extension}')
    return f'{path}.{extension}'


def only_visible(names):
    for obj in scene.objects:
        obj.hide_render = obj.name not in names


def new_ortho_camera(name, scale):
    data = bpy.data.cameras.new(name)
    data.type = 'ORTHO'
    data.ortho_scale = scale
    data.clip_start, data.clip_end = 0.1, 400.0
    camera = bpy.data.objects.new(name, data)
    scene.collection.objects.link(camera)
    return camera


# ------------------------------------------------------------------------------------------------------------------------------ 1. the ground atlas
ground_maps = {}
only_visible(GROUND_OBJECTS)
overhead = new_ortho_camera('overhead', Y1 - Y0)
overhead.location = (0.0, (Y0 + Y1) / 2, 120.0)
scene.camera = overhead
set_up_photography(GROUND_WIDTH, GROUND_HEIGHT)
rig = emission_rig(GROUND_MATERIALS)
for channel in ('colour', 'roughness', 'coat', 'coat_roughness', 'specularity', 'normal', 'puddles', 'wet'):
    show(rig, channel)
    ground_maps[channel] = shoot(os.path.join(maps_folder, f'ground_{channel}'), channel)
    print('PHOTOGRAPHED ground', channel)
# the second texture coordinates of the three ground meshes: one flat plan of the whole street
for object_name in ('street_setts', 'street_channels', 'street_pavements'):
    obj = bpy.data.objects[object_name]
    mesh = obj.data
    loops = np.empty(len(mesh.loops), dtype=np.int32)
    mesh.loops.foreach_get('vertex_index', loops)
    coords = np.empty(len(mesh.vertices) * 3, dtype=np.float32)
    mesh.vertices.foreach_get('co', coords)
    coords = coords.reshape(-1, 3)
    world = np.array(obj.matrix_world)
    coords = coords @ world[:3, :3].T + world[:3, 3]
    uv = np.stack([(coords[loops, 0] + X_HALF) / (2 * X_HALF), (coords[loops, 1] - Y0) / (Y1 - Y0)], axis=1).astype(np.float32)
    layer = mesh.uv_layers.get('UV2') or mesh.uv_layers.new(name='UV2')
    layer.data.foreach_set('uv', uv.ravel())

# ------------------------------------------------------------------------------------------------------------------------------ 2. the wall fronts
wall_maps = {}
wall_camera = new_ortho_camera('wall_camera', WALL_Z1 - WALL_Z0)
scene.camera = wall_camera
set_up_photography(WALL_WIDTH, WALL_HEIGHT)
for key, (object_name, variant) in WALL_SOURCES.items():
    obj = bpy.data.objects[object_name]
    only_visible((object_name,))
    # a camera in the cottage's own frame: 6 m in front of the wall (local -x), looking along local +x, up = local +z, right = local -y
    local = Matrix(((0, 0, -1, -6.0), (-1, 0, 0, 0.0), (0, 1, 0, (WALL_Z0 + WALL_Z1) / 2), (0, 0, 0, 1)))
    wall_camera.matrix_world = obj.matrix_world @ local
    rig = emission_rig([variant, 'interior_dark'])
    for channel in ('colour', 'roughness', 'coat', 'coat_roughness', 'specularity', 'wet'):
        show(rig, channel)
        wall_maps.setdefault(key, {})[channel] = shoot(os.path.join(maps_folder, f'{key}_{channel}'), channel)
    print('PHOTOGRAPHED', key)
    # the interior material was wired to a black emission for the photographs: put its own shader back (a mistake of the first run: it went into the .glb as an empty white metal)
    interior = bpy.data.materials['interior_dark'].node_tree
    interior.links.new(next(n for n in interior.nodes if n.type == 'BSDF_PRINCIPLED').outputs['BSDF'], next(n for n in interior.nodes if n.type == 'OUTPUT_MATERIAL').inputs['Surface'])
    mesh = obj.data
    loops = np.empty(len(mesh.loops), dtype=np.int32)
    mesh.loops.foreach_get('vertex_index', loops)
    coords = np.empty(len(mesh.vertices) * 3, dtype=np.float32)
    mesh.vertices.foreach_get('co', coords)
    coords = coords.reshape(-1, 3)
    uv = np.stack([(WALL_HALF - coords[loops, 1]) / (2 * WALL_HALF), (coords[loops, 2] - WALL_Z0) / (WALL_Z1 - WALL_Z0)], axis=1).astype(np.float32)
    layer = mesh.uv_layers.get('UV2') or mesh.uv_layers.new(name='UV2')
    layer.data.foreach_set('uv', uv.ravel())
report['seconds']['photographing_all'] = round(time.time() - started_all, 1)


# ------------------------------------------------------------------------------------------------------------------------------ 3. the materials for the .glb
def load_image(path, colour):
    image = bpy.data.images.load(path, check_existing=True)
    image.colorspace_settings.name = 'sRGB' if colour else 'Non-Color'
    return image


def clean_copy_normal(name):
    """(normal picture, strength) of the clean copy of a material."""
    tree = bpy.data.materials[name + '__flat'].node_tree
    normal_map = next(n for n in tree.nodes if n.type == 'NORMAL_MAP')
    picture = normal_map.inputs['Color'].links[0].from_node.image
    return picture, normal_map.inputs['Strength'].default_value


def baked_material(material_name, maps, normal_from, smooth_picture=None):
    """A material that wears only pictures: colour, roughness, coat, coat roughness, specularity on UV2; the photo's own normal map on the first coordinates."""
    material = bpy.data.materials.new(material_name)
    material.use_nodes = True
    tree = material.node_tree
    principled = next(n for n in tree.nodes if n.type == 'BSDF_PRINCIPLED')
    uv_node = tree.nodes.new('ShaderNodeUVMap')
    uv_node.uv_map = 'UV2'

    def picture(path, colour):
        node = tree.nodes.new('ShaderNodeTexImage')
        node.image = load_image(path, colour)
        node.extension = 'EXTEND'
        tree.links.new(uv_node.outputs['UV'], node.inputs['Vector'])
        return node
    tree.links.new(picture(maps['colour'], True).outputs['Color'], principled.inputs['Base Color'])
    tree.links.new(picture(maps['roughness'], False).outputs['Color'], principled.inputs['Roughness'])
    tree.links.new(picture(maps['coat'], False).outputs['Color'], principled.inputs['Coat Weight'])
    tree.links.new(picture(maps['coat_roughness'], False).outputs['Color'], principled.inputs['Coat Roughness'])
    # the specularity map: grey picture -> its red channel -> times the biggest level -> Specular IOR Level (the exporter writes the picture into the alpha channel
    # of KHR_materials_specular's picture and the 0.75 as a colour factor of 1.5)
    separate = tree.nodes.new('ShaderNodeSeparateColor')
    tree.links.new(picture(maps['specularity'], False).outputs['Color'], separate.inputs['Color'])
    times = tree.nodes.new('ShaderNodeMath')
    times.operation = 'MULTIPLY'
    times.inputs[1].default_value = SPEC_MAX
    tree.links.new(separate.outputs['Red'], times.inputs[0])
    tree.links.new(times.outputs[0], principled.inputs['Specular IOR Level'])
    principled.inputs['Coat IOR'].default_value = 1.33
    principled.inputs['Metallic'].default_value = 0.0
    normal_picture, strength = clean_copy_normal(normal_from)
    if smooth_picture is not None:
        normal_picture = smooth_picture       # round 2: a wet road wears the smoothed relief picture (water has filled the finest grain)
    normal_node = tree.nodes.new('ShaderNodeTexImage')
    normal_node.image = normal_picture
    normal_map = tree.nodes.new('ShaderNodeNormalMap')
    normal_map.inputs['Strength'].default_value = strength
    tree.links.new(normal_node.outputs['Color'], normal_map.inputs['Color'])
    tree.links.new(normal_map.outputs['Normal'], principled.inputs['Normal'])
    return material


def swap_material(old_name, new_material):
    for mesh in bpy.data.meshes:
        for index, slot_material in enumerate(mesh.materials):
            if slot_material is not None and slot_material.name == old_name:
                mesh.materials[index] = new_material


baked_names = {}
for old_name, normal_from in (('street_setts', 'street_setts'), ('channel_stones', 'channel_stones'), ('pavement_flags', 'pavement_flags')):
    smooth_name = aw.MATERIALS[old_name].get('smooth_normal')
    new = baked_material(old_name + '_wet', ground_maps, normal_from, smooth_picture=load_image(aw.TEX + smooth_name, False) if smooth_name else None)
    swap_material(old_name, new)
    baked_names[old_name] = new.name
for key, (object_name, variant) in WALL_SOURCES.items():
    wall_type = 'cottage_stone' if 'stone' in key else 'cottage_brick'
    new = baked_material(key + '_wet', wall_maps[key], wall_type)
    swap_material(variant, new)
    baked_names[variant] = new.name
# every other changed material: its clean copy with flat wet numbers
for name, spec in aw.MATERIALS.items():
    flat = bpy.data.materials[name + '__flat']
    if name in baked_names:
        continue
    tree = flat.node_tree
    principled = next(n for n in tree.nodes if n.type == 'BSDF_PRINCIPLED')
    effective = min(1.0, wetness * spec.get('wetness_scale', 1.0))
    principled.inputs['Roughness'].default_value = min(principled.inputs['Roughness'].default_value, spec['wet_roughness'])   # (wet roughness is the soaked value; the flat stand-in is soaked)
    # round 2: the flat numbers follow the material's own settings (the walls, roofs and stones got little coat and no extra shine), not round 1's fixed 0.3 and +0.25,
    # which made these stand-ins 1.2 to 1.7 times too bright against the live layer
    principled.inputs['Coat Weight'].default_value = spec.get('film_coat', 0.3) * effective
    principled.inputs['Coat Roughness'].default_value = 0.2
    principled.inputs['Coat IOR'].default_value = 1.33
    principled.inputs['Specular IOR Level'].default_value = 0.5 + spec.get('specular_boost', 0.25) * effective
    multiply = next((n for n in tree.nodes if n.type == 'MIX' and n.blend_type == 'MULTIPLY'), None)
    ratio = COLOUR_RATIO.get(name, 0.85)
    if multiply is not None:
        tint = multiply.inputs[7].default_value
        multiply.inputs[7].default_value = (tint[0] * ratio, tint[1] * ratio, tint[2] * ratio, 1.0)
    swap_material(name, flat)
    baked_names[name] = flat.name
# (the plain wall materials that the chimneys wear are in aw.MATERIALS too: they got the clean copy with flat numbers in the loop above)

# ------------------------------------------------------------------------------------------------------------------------------ 4. write the .glb and the baked .blend
for obj in scene.objects:
    obj.hide_render = False
for helper in (overhead, wall_camera):
    bpy.data.objects.remove(helper, do_unlink=True)
scene.camera = bpy.data.objects.get('main_camera')
started = time.time()
bpy.ops.export_scene.gltf(filepath=glb_path, export_format='GLB', export_yup=True, export_apply=True, export_cameras=True, export_lights=False, export_extras=True,
                          export_image_format='AUTO', export_materials='EXPORT')
report['seconds']['glb_export'] = round(time.time() - started, 1)
report['glb_bytes'] = os.path.getsize(glb_path)
view.view_transform, view.look, view.exposure, view.gamma = SAVED['view']
background_node.inputs['Color'].default_value, background_node.inputs['Strength'].default_value = SAVED['world']
(scene.render.dither_intensity, scene.cycles.pixel_filter_type, scene.cycles.filter_width, scene.cycles.samples, scene.cycles.use_adaptive_sampling, scene.cycles.use_denoising,
 scene.cycles.max_bounces, scene.render.engine) = SAVED['render']
bpy.ops.wm.save_as_mainfile(filepath=blend_path, copy=True)
report['seconds']['total'] = round(time.time() - started_all, 1)
report['ground_atlas'] = {'width': GROUND_WIDTH, 'height': GROUND_HEIGHT, 'dots_per_metre': PPM_GROUND, 'x_range': [-X_HALF, X_HALF], 'y_range': [Y0, Y1]}
report['wall_maps'] = {'width': WALL_WIDTH, 'height': WALL_HEIGHT, 'dots_per_metre': PPM_WALL}
report['materials_in_glb'] = baked_names
with open(os.path.join(maps_folder, 'bake_report_rebuild.json' if REUSE else 'bake_report.json'), 'w') as handle:
    json.dump(report, handle, indent=1)
print('REPORT', json.dumps(report['seconds']), report['glb_bytes'])
