# What this file does (plain words)
# ------------------------------------------------------------------------------------------------------------------------------------------------
# Draws, for the lockout plate camera at 1536 x 2730, a flat-colour picture of WHAT THE GROUND IS (road = red, gutter channel = green, kerb = blue, pavement = yellow, anything else = black)
# WITH THE FILM'S NEAR PROPS HIDDEN (the same props, picked the same way, as in the props-free plate). The front step's surface masks have the near props standing in them, so they cannot say
# whether the spot where a prop stood is road or pavement; this picture can. It opens the film's lockout shot file READ-ONLY (never saved), changes nothing in it, and writes only the picture.
# Run (on the rented machine): /workspace/blender/blender -b --disable-autoexec LOCKOUT.blend --python make_ground_labels_no_props.py -- OUT.png
import sys
import bpy
from mathutils import Vector

out_path = sys.argv[sys.argv.index('--') + 1]
scene = bpy.context.scene
W, H = 1536, 2730
FILM_NEAR_PROPS = ['handcart', 'coal-sacks', 'coal-pile', 'wooden-pail', 'hurricane-lantern', 'spade', 'brazier', 'dustbins', 'notice-on-board', 'Cube']
FILM_NEAR_METRES = 16.0
PLATE_CAMERA_AT = (-1.0, 1.2, 1.69709)


def top(obj):
    while obj.parent is not None:
        obj = obj.parent
    return obj


roots = {}
for obj in scene.objects:
    if obj.type in ('LIGHT', 'CAMERA'):
        continue
    r = top(obj)
    if r.type in ('LIGHT', 'CAMERA'):
        continue
    roots.setdefault(r.name, [r, []])[1].append(obj)
hidden = 0
for name, (root, members) in sorted(roots.items()):
    if not any(name.startswith(p) for p in FILM_NEAR_PROPS):
        continue
    pts = []
    for m in members:
        if m.type == 'MESH':
            pts += [m.matrix_world @ Vector(c) for c in m.bound_box]
    centre = sum(pts, Vector()) / len(pts) if pts else root.matrix_world.translation
    if (centre - Vector(PLATE_CAMERA_AT)).length < FILM_NEAR_METRES:
        for m in members:
            m.hide_render = True
            hidden += 1
print('hidden objects', hidden, flush=True)

cam = scene.camera
print('camera', cam.name if cam else None, tuple(round(v, 4) for v in cam.matrix_world.translation) if cam else None, 'lens fov', cam.data.angle if cam else None, flush=True)

names = {'street_setts': 1, 'street_channels': 2, 'street_kerbs': 3, 'street_pavements': 4}
for n, i in names.items():
    bpy.data.objects[n].pass_index = i
for obj in scene.objects:
    if obj.name not in names:
        obj.pass_index = 0

mat = bpy.data.materials.new('ground_labels')
mat.use_nodes = True
tree = mat.node_tree
tree.nodes.clear()
info = tree.nodes.new('ShaderNodeObjectInfo')


def is_index(k):
    c = tree.nodes.new('ShaderNodeMath')
    c.operation = 'COMPARE'
    c.inputs[1].default_value, c.inputs[2].default_value = float(k), 0.1
    tree.links.new(info.outputs['Object Index'], c.inputs[0])
    return c


def add(a, b):
    n = tree.nodes.new('ShaderNodeMath')
    n.operation = 'ADD'
    tree.links.new(a.outputs[0], n.inputs[0])
    tree.links.new(b.outputs[0], n.inputs[1])
    return n


i1, i2, i3, i4 = (is_index(k) for k in (1, 2, 3, 4))
red, green, blue = add(i1, i4), add(i2, i4), i3
combine = tree.nodes.new('ShaderNodeCombineColor')
tree.links.new(red.outputs[0], combine.inputs['Red'])
tree.links.new(green.outputs[0], combine.inputs['Green'])
tree.links.new(blue.outputs[0], combine.inputs['Blue'])
emission = tree.nodes.new('ShaderNodeEmission')
tree.links.new(combine.outputs['Color'], emission.inputs['Color'])
output = tree.nodes.new('ShaderNodeOutputMaterial')
tree.links.new(emission.outputs['Emission'], output.inputs['Surface'])

scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x, scene.render.resolution_y, scene.render.resolution_percentage = W, H, 100
scene.render.image_settings.file_format = 'PNG'
scene.render.image_settings.color_mode = 'RGB'
scene.render.image_settings.color_depth = '8'
scene.eevee.taa_render_samples = 1
scene.eevee.use_raytracing = False
scene.render.filter_size = 0.0
scene.view_settings.view_transform, scene.view_settings.look, scene.view_settings.exposure, scene.view_settings.gamma = 'Raw', 'None', 0.0, 1.0
scene.render.dither_intensity = 0.0
bg = scene.world.node_tree.nodes['Background']
bg.inputs['Color'].default_value, bg.inputs['Strength'].default_value = (0, 0, 0, 1), 0.0
bpy.context.view_layer.material_override = mat
scene.render.filepath = out_path
bpy.ops.render.render(write_still=True)
print('WROTE', out_path, flush=True)
