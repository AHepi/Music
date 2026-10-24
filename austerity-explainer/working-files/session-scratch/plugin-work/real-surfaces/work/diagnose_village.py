# What this does: draws small EEVEE crops of the village run's finished scene (opened read-only, never saved) with one thing changed at a
# time, to find the causes of three faults the person saw: dark V-shaped specks on the grass and the road, white sparkles on the thatch
# roofs, and flat brown rectangles beside the road. Each crop is a JPG named by the region and the change.
# Run on a rented card: /workspace/blender/blender -b --disable-autoexec FINISHED.blend -P diagnose_village.py -- OUTPUT_FOLDER
import json
import os
import sys
import time

import bpy

output_folder = sys.argv[sys.argv.index('--') + 1]
os.makedirs(output_folder, exist_ok=True)
scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x, scene.render.resolution_y, scene.render.resolution_percentage = 1200, 800, 100
scene.render.image_settings.file_format = 'JPEG'
scene.render.image_settings.quality = 90
scene.render.use_border = True
scene.render.use_crop_to_border = True
log = {}


def draw(name, camera_name, left, top, right, bottom):
    scene.camera = bpy.data.objects[camera_name]
    scene.render.border_min_x, scene.render.border_max_x = left / 1200.0, right / 1200.0
    scene.render.border_min_y, scene.render.border_max_y = 1.0 - bottom / 800.0, 1.0 - top / 800.0
    scene.render.filepath = os.path.join(output_folder, name + '.jpg')
    started = time.time()
    bpy.ops.render.render(write_still=True)
    log[name] = round(time.time() - started, 1)
    print('DREW', name, log[name], 's', flush=True)


SPECKS = ('View road_eye', 380, 430, 820, 620)
THATCH = ('View wide', 80, 400, 420, 580)
BROWN = ('View road_eye', 0, 520, 320, 740)

scatter_objects = [o for o in bpy.data.objects if o.get('pk_scatter')]
scatter_material = bpy.data.materials.get('PK Scatter')
thatch_objects = [o for o in bpy.data.objects if (o.get('place_role') or '') == 'roof.thatch']
thatch_materials = {s.material for o in thatch_objects for s in o.material_slots if s.material}

# ---- 1. as it is
draw('specks_1_as_is', *SPECKS)
draw('thatch_1_as_is', *THATCH)
draw('brown_1_as_is', *BROWN)

# ---- 2. the specks: a fixed colour instead of the colour attribute
tree = scatter_material.node_tree
principled = next(n for n in tree.nodes if n.bl_idname == 'ShaderNodeBsdfPrincipled')
saved_links = [(l.from_socket, l.to_socket) for l in tree.links if l.to_socket == principled.inputs['Base Color']]
for link in [l for l in tree.links if l.to_socket == principled.inputs['Base Color']]:
    tree.links.remove(link)
principled.inputs['Base Color'].default_value = (0.12, 0.30, 0.06, 1.0)
draw('specks_2_fixed_colour', *SPECKS)
for a, b in saved_links:
    tree.links.new(a, b)

# ---- 3. the specks: the pieces cast no shadow
for obj in scatter_objects:
    obj.visible_shadow = False
draw('specks_3_no_shadow', *SPECKS)
for obj in scatter_objects:
    obj.visible_shadow = True

# ---- 4. the specks: every kind in its own flat key colour (emission), to say which kind the dark specks are
keys = {'tuft': (1, 1, 0), 'clover': (0, 1, 1), 'nettle': (1, 0, 1), 'fern': (1, 0, 0), 'bramble': (0, 0, 1), 'moss_cushion': (0, 1, 0),
        'leaf': (1, 0.5, 0), 'pine_needles': (0.5, 0, 1), 'stick': (1, 1, 1), 'straw': (0.5, 0.5, 0.5), 'clod': (0, 0.4, 0.2)}
key_materials = {}
saved_slots = {}
for obj in scatter_objects:
    kind = obj.get('pk_scatter_kind')
    material = key_materials.get(kind)
    if material is None:
        material = bpy.data.materials.new('key ' + str(kind))
        material.use_nodes = True
        nodes = material.node_tree.nodes
        nodes.clear()
        out = nodes.new('ShaderNodeOutputMaterial')
        emission = nodes.new('ShaderNodeEmission')
        emission.inputs['Color'].default_value = tuple(keys.get(kind, (0.3, 0.3, 0.3))) + (1.0,)
        emission.inputs['Strength'].default_value = 1.0
        material.node_tree.links.new(emission.outputs[0], out.inputs['Surface'])
        key_materials[kind] = material
    saved_slots[obj.name] = obj.data.materials[0]
    obj.data.materials[0] = material
draw('specks_4_kinds_keyed', *SPECKS)
for obj in scatter_objects:
    obj.data.materials[0] = saved_slots[obj.name]

# ---- 5. the specks: shading normals of the pieces pointed up (lit like the ground they stand on)
geometry = tree.nodes.new('ShaderNodeNewGeometry')
combine = tree.nodes.new('ShaderNodeCombineXYZ')
combine.inputs['Z'].default_value = 1.0
tree.links.new(combine.outputs[0], principled.inputs['Normal'])
draw('specks_5_normal_up', *SPECKS)
for link in [l for l in tree.links if l.to_socket == principled.inputs['Normal']]:
    tree.links.remove(link)

# ---- thatch: 2. no clear coat; 3. bump only (no displacement); 4. wetness amount 0
coat_saved = {}
for material in thatch_materials:
    p = next((n for n in material.node_tree.nodes if n.bl_idname == 'ShaderNodeBsdfPrincipled'), None)
    if p is None:
        continue
    coat_saved[material.name] = [(l.from_socket, l.to_socket) for l in material.node_tree.links if l.to_socket == p.inputs['Coat Weight']]
    for link in [l for l in material.node_tree.links if l.to_socket == p.inputs['Coat Weight']]:
        material.node_tree.links.remove(link)
    p.inputs['Coat Weight'].default_value = 0.0
draw('thatch_2_no_coat', *THATCH)
for material in thatch_materials:
    for a, b in coat_saved.get(material.name, []):
        material.node_tree.links.new(a, b)
methods = {m.name: m.displacement_method for m in thatch_materials}
for material in thatch_materials:
    material.displacement_method = 'BUMP'
draw('thatch_3_bump_only', *THATCH)
for material in thatch_materials:
    material.displacement_method = methods[material.name]
amounts = {o.name: o.get('pk_wetness_amount') for o in thatch_objects}
for obj in thatch_objects:
    obj['pk_wetness_amount'] = 0.0
    obj.update_tag()
draw('thatch_4_no_wetness', *THATCH)
for obj in thatch_objects:
    if amounts[obj.name] is not None:
        obj['pk_wetness_amount'] = amounts[obj.name]
rough_saved = {}
for material in thatch_materials:
    p = next((n for n in material.node_tree.nodes if n.bl_idname == 'ShaderNodeBsdfPrincipled'), None)
    rough_saved[material.name] = [(l.from_socket, l.to_socket) for l in material.node_tree.links if l.to_socket == p.inputs['Roughness']]
    for link in [l for l in material.node_tree.links if l.to_socket == p.inputs['Roughness']]:
        material.node_tree.links.remove(link)
    p.inputs['Roughness'].default_value = 0.9
draw('thatch_5_rough_0.9', *THATCH)

# ---- brown: 2. the forest floor hidden; 3. the forest floor with bump only
floor = [o for o in bpy.data.objects if (o.get('place_role') or '') == 'ground.forest_floor']
for obj in floor:
    obj.hide_render = True
draw('brown_2_forest_floor_hidden', *BROWN)
for obj in floor:
    obj.hide_render = False
floor_materials = {s.material for o in floor for s in o.material_slots if s.material}
for material in floor_materials:
    material.displacement_method = 'BUMP'
draw('brown_3_floor_bump_only', *BROWN)

with open(os.path.join(output_folder, 'times.json'), 'w') as handle:
    json.dump(log, handle, indent=1)
print('DONE', json.dumps(log))
