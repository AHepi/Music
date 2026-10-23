"""What this does: builds the small test scene the place kit's tests use, inside Blender: a flat HUT of plain-colour boxes (nothing but boxes and one gable
prism: a ground plane, four walls, a roof, a door and a few floor planks, each with a plain Principled material and no normal map, no wear, no bevel). It is the
shape of thing a model builds when it is only told "make a hut": it passes the older model lint and must FAIL the place audit. One floor plank can float
6 cm above the ground on purpose (the negative proof that the construction check can fail); --no-floating leaves it out.
Run: blender -b --python make_hut_scene.py -- OUT.blend [--no-floating] [--no-light] [--roles-by-property] [--cameras]
--cameras adds two cameras, "Camera A" (a wide view) and "Camera B" (a view of the door), for the variations tests.
--roles-by-property also tags place_role on every object (the way a part builder would). The scene is a few boxes: it saves in about a second.
"""
import math
import sys

import bpy
import bmesh

arguments = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
if not arguments or arguments[0].startswith('-'):
    print('usage: blender -b --python make_hut_scene.py -- OUT.blend [--no-floating] [--no-light] [--roles-by-property] [--cameras]')
    sys.exit(2)
out_path = arguments[0]
floating = '--no-floating' not in arguments
with_light = '--no-light' not in arguments
tag_roles = '--roles-by-property' in arguments

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene


def plain_material(name, colour):
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    node = material.node_tree.nodes['Principled BSDF']
    node.inputs['Base Color'].default_value = colour
    node.inputs['Roughness'].default_value = 0.5
    return material


def box(name, size, location, material, role=None):
    mesh = bpy.data.meshes.new(name)
    builder = bmesh.new()
    bmesh.ops.create_cube(builder, size=1.0)
    for vertex in builder.verts:
        vertex.co.x *= size[0]
        vertex.co.y *= size[1]
        vertex.co.z *= size[2]
    builder.to_mesh(mesh)
    builder.free()
    mesh.materials.append(material)
    obj = bpy.data.objects.new(name, mesh)
    scene.collection.objects.link(obj)
    obj.location = location
    if tag_roles and role:
        obj['place_role'] = role
    return obj


# the ground: one plane
ground_mesh = bpy.data.meshes.new('ground')
ground_mesh.from_pydata([(-7, -7, 0), (7, -7, 0), (7, 7, 0), (-7, 7, 0)], [], [(0, 1, 2, 3)])
ground_mesh.materials.append(plain_material('ground_mat', (0.3, 0.25, 0.15, 1)))
ground = bpy.data.objects.new('ground', ground_mesh)
scene.collection.objects.link(ground)
if tag_roles:
    ground['place_role'] = 'ground.earth'

wall_material = plain_material('wall_mat', (0.8, 0.75, 0.6, 1))
box('wall_north', (4.3, 0.3, 2.4), (0, 2.0, 1.2), wall_material, 'wall.plaster')
box('wall_south', (4.3, 0.3, 2.4), (0, -2.0, 1.2), wall_material, 'wall.plaster')
box('wall_east', (0.3, 3.7, 2.4), (2.0, 0, 1.2), wall_material, 'wall.plaster')
box('wall_west', (0.3, 3.7, 2.4), (-2.0, 0, 1.2), wall_material, 'wall.plaster')

# a gable roof: a closed prism with a 40 degree pitch resting on the wall tops
half_width, length, rise = 2.5, 4.6, 2.5 * math.tan(math.radians(40))
roof_mesh = bpy.data.meshes.new('roof')
vertices = [(-length / 2, -half_width, 0), (length / 2, -half_width, 0), (length / 2, half_width, 0), (-length / 2, half_width, 0), (-length / 2, 0, rise), (length / 2, 0, rise)]
faces = [(0, 3, 2, 1), (0, 1, 5, 4), (2, 3, 4, 5), (0, 4, 3), (1, 2, 5)]
roof_mesh.from_pydata(vertices, [], faces)
roof_mesh.update()
roof_mesh.materials.append(plain_material('roof_mat', (0.5, 0.3, 0.2, 1)))
roof = bpy.data.objects.new('roof', roof_mesh)
scene.collection.objects.link(roof)
roof.location = (0, 0, 2.4)
if tag_roles:
    roof['place_role'] = 'roof.shingle'

box('door', (0.9, 0.05, 1.9), (0, -2.2, 0.95), plain_material('door_mat', (0.4, 0.25, 0.1, 1)), 'timber.door')
floor_material = plain_material('floor_mat', (0.55, 0.4, 0.25, 1))
for index in range(4):
    box(f'floor_plank_{index + 1}', (0.2, 3.0, 0.04), (-0.6 + index * 0.4, 0, 0.02), floor_material, 'timber.floor')
if floating:
    box('floor_plank_float', (0.2, 3.0, 0.04), (1.1, 0, 0.08), floor_material, 'timber.floor')      # 6 cm above the ground: it floats

if with_light:
    sun = bpy.data.lights.new('sun', 'SUN')
    sun.energy = 3.0
    sun_object = bpy.data.objects.new('sun', sun)
    scene.collection.objects.link(sun_object)
    sun_object.rotation_euler = (math.radians(50), 0, math.radians(35))
    scene.world = bpy.data.worlds.new('world')
    scene.world.use_nodes = True
    scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.6
if '--cameras' in arguments:
    from mathutils import Vector
    for camera_name, location, target in (('Camera A', (6.0, -6.5, 3.2), (0, 0, 1.2)), ('Camera B', (1.2, -5.0, 1.4), (0, -2.2, 1.0))):
        camera_data = bpy.data.cameras.new(camera_name)
        camera_object = bpy.data.objects.new(camera_name, camera_data)
        camera_object.location = location
        camera_object.rotation_euler = (Vector(target) - Vector(location)).to_track_quat('-Z', 'Y').to_euler()
        scene.collection.objects.link(camera_object)
        if scene.camera is None:
            scene.camera = camera_object
bpy.ops.wm.save_as_mainfile(filepath=out_path)
print('saved', out_path)
