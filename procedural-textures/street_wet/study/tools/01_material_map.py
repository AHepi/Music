# What this does: draws a "false-colour" picture of a Blender scene from its camera: every material is painted one flat colour (no light, no
# texture), so that counting the coloured dots tells how much of the frame each material covers. It writes
#   OUT_FOLDER/<NAME>_ids.png     the picture (the red value is the material number)
#   OUT_FOLDER/<NAME>_numbers.json the number of each material (and how many objects wear it); 01b_count_materials.py then counts the dots
# It changes nothing in the file it opens and saves nothing back (run it on a copy or on a read-only original).
# Run:  blender -b --disable-autoexec -t 2 FILE.blend --python 01_material_map.py -- OUT_FOLDER NAME [WIDTH HEIGHT] [CAMERA_OBJECT_NAME]
import json
import os
import sys

import bpy

arguments = sys.argv[sys.argv.index('--') + 1:]
out_folder, name = arguments[0], arguments[1]
width = int(arguments[2]) if len(arguments) > 2 else 540
height = int(arguments[3]) if len(arguments) > 3 else 960
camera_name = arguments[4] if len(arguments) > 4 else None
os.makedirs(out_folder, exist_ok=True)

scene = bpy.context.scene
if camera_name:
    scene.camera = bpy.data.objects[camera_name]
print('camera', scene.camera.name, tuple(scene.camera.location), 'fov', scene.camera.data.angle_y)

# which materials are used by visible mesh objects, and by how many
used = {}
for obj in scene.objects:
    if obj.type != 'MESH' or obj.hide_render:
        continue
    for slot in obj.material_slots:
        if slot.material:
            used.setdefault(slot.material.name, 0)
            used[slot.material.name] += 1
names = sorted(used)
index_of = {material_name: i + 1 for i, material_name in enumerate(names)}   # 0 = nothing (black)
assert len(names) < 255

for material_name in names:
    material = bpy.data.materials[material_name]
    if material.node_tree is None:
        material.use_nodes = True
    tree = material.node_tree
    tree.nodes.clear()
    emission = tree.nodes.new('ShaderNodeEmission')
    value = index_of[material_name] / 255.0
    emission.inputs['Color'].default_value = (value, 0.0, 0.0, 1.0)
    emission.inputs['Strength'].default_value = 1.0
    output = tree.nodes.new('ShaderNodeOutputMaterial')
    tree.links.new(emission.outputs['Emission'], output.inputs['Surface'])

world = bpy.data.worlds.new('black')
world.use_nodes = True
world.node_tree.nodes['Background'].inputs['Color'].default_value = (0, 0, 0, 1)
scene.world = world
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.samples = 1
scene.cycles.use_adaptive_sampling = False
scene.cycles.use_denoising = False
scene.cycles.max_bounces = 0
scene.cycles.pixel_filter_type = 'BOX'
scene.cycles.filter_width = 1.0
scene.render.resolution_x, scene.render.resolution_y = width, height
scene.render.resolution_percentage = 100
scene.render.film_transparent = False
scene.view_settings.view_transform = 'Raw'
scene.view_settings.look = 'None'
scene.view_settings.exposure = 0.0   # the street file keeps an exposure of +0.6, which would scale every colour
scene.view_settings.gamma = 1.0
scene.render.dither_intensity = 0.0   # without this Blender adds a little noise to 8-bit pictures, which turns some dots into a neighbouring material number
scene.display_settings.display_device = 'sRGB'
scene.render.image_settings.file_format = 'PNG'
scene.render.image_settings.color_mode = 'RGB'
scene.render.image_settings.color_depth = '8'
path = os.path.join(out_folder, f'{name}_ids.png')
scene.render.filepath = path
bpy.ops.render.render(write_still=True)

# the counting is done outside Blender by 01b_count_materials.py (reading the picture back inside Blender mixed up the colour space)
with open(os.path.join(out_folder, f'{name}_numbers.json'), 'w') as handle:
    json.dump({'frame': [width, height], 'camera': scene.camera.name, 'numbers': index_of, 'objects_wearing_it': used}, handle, indent=1)
print('numbers written;', len(names), 'materials')
