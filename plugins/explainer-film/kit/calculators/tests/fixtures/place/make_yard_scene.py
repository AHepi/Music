"""What this does: builds the second test scene the place kit's tests use, inside Blender: a YARD of plain-colour shapes, the way a model builds a place when it is only told what to
put in it: a big flat ground, two sheds (four wall boxes, a gable roof and a door each), a fence of posts and rails, a well, a barrel with two iron bands, an iron post and a stump, a
sun and a camera named "Camera A". Nothing has a normal map, wear or damage. It has everything the kit's roles and treatments need to be proved at a larger size than the one-hut
scene: wood, stone, iron, a tree, roofs, walls, a lot of ground for a road, ruts and plants, and a fence the plants must stay out from under.
Run: blender -b --python make_yard_scene.py -- OUT.blend [--no-light] [--no-camera]
The road the tests cut into the ground is written in the settings file the test makes (a polyline through y = 3 to 5); the scene itself has no road, only the ground.
"""
import math
import sys

import bpy
import bmesh
from mathutils import Vector

arguments = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
if not arguments or arguments[0].startswith('-'):
    print('usage: blender -b --python make_yard_scene.py -- OUT.blend [--no-light] [--no-camera]')
    sys.exit(2)
out_path = arguments[0]
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
materials = {}


def material(name, colour):
    if name not in materials:
        made = bpy.data.materials.new(name)
        made.use_nodes = True
        node = made.node_tree.nodes['Principled BSDF']
        node.inputs['Base Color'].default_value = colour
        node.inputs['Roughness'].default_value = 0.6
        materials[name] = made
    return materials[name]


def add(name, mesh, mat, location, rotation_z=0.0):
    mesh.materials.append(mat)
    obj = bpy.data.objects.new(name, mesh)
    scene.collection.objects.link(obj)
    obj.location = location
    obj.rotation_euler = (0.0, 0.0, rotation_z)
    return obj


def box(name, size, location, mat, rotation_z=0.0):
    mesh = bpy.data.meshes.new(name)
    builder = bmesh.new()
    bmesh.ops.create_cube(builder, size=1.0)
    for vertex in builder.verts:
        vertex.co.x *= size[0]
        vertex.co.y *= size[1]
        vertex.co.z *= size[2]
    builder.to_mesh(mesh)
    builder.free()
    return add(name, mesh, mat, location, rotation_z)


def cylinder(name, radius, height, location, mat, segments=16):
    mesh = bpy.data.meshes.new(name)
    builder = bmesh.new()
    bmesh.ops.create_cone(builder, cap_ends=True, cap_tris=False, segments=segments, radius1=radius, radius2=radius, depth=height)
    builder.to_mesh(mesh)
    builder.free()
    return add(name, mesh, mat, location)


# the ground: one big plane
ground_mesh = bpy.data.meshes.new('Ground')
ground_mesh.from_pydata([(-4, -10, 0), (36, -10, 0), (36, 16, 0), (-4, 16, 0)], [], [(0, 1, 2, 3)])
add('Ground', ground_mesh, material('ground_mat', (0.3, 0.25, 0.15, 1)), (0, 0, 0))


def shed(prefix, centre, turn=0.0):
    """Four wall boxes, a gable roof and a door around a point; turn rotates the whole shed about its centre (the parts are placed by hand, so only 0 and 90 degrees are supported)."""
    cx, cy = centre
    wall = material('wall_mat', (0.8, 0.75, 0.6, 1))
    along_x = turn == 0.0
    length, depth = (4.2, 3.4) if along_x else (3.4, 4.2)
    box(f'{prefix} wall north', (length, 0.3, 2.2) if along_x else (0.3, depth, 2.2), (cx, cy + depth / 2, 1.1) if along_x else (cx + length / 2, cy, 1.1), wall)
    box(f'{prefix} wall south', (length, 0.3, 2.2) if along_x else (0.3, depth, 2.2), (cx, cy - depth / 2, 1.1) if along_x else (cx - length / 2, cy, 1.1), wall)
    box(f'{prefix} wall east', (0.3, depth, 2.2) if along_x else (length, 0.3, 2.2), (cx + length / 2, cy, 1.1) if along_x else (cx, cy + depth / 2, 1.1), wall)
    box(f'{prefix} wall west', (0.3, depth, 2.2) if along_x else (length, 0.3, 2.2), (cx - length / 2, cy, 1.1) if along_x else (cx, cy - depth / 2, 1.1), wall)
    half_width, roof_length, rise = (depth / 2 + 0.3), length + 0.4, (depth / 2 + 0.3) * math.tan(math.radians(38))
    mesh = bpy.data.meshes.new(f'{prefix} roof')
    vertices = [(-roof_length / 2, -half_width, 0), (roof_length / 2, -half_width, 0), (roof_length / 2, half_width, 0), (-roof_length / 2, half_width, 0), (-roof_length / 2, 0, rise), (roof_length / 2, 0, rise)]
    mesh.from_pydata(vertices, [], [(0, 3, 2, 1), (0, 1, 5, 4), (2, 3, 4, 5), (0, 4, 3), (1, 2, 5)])
    mesh.update()
    add(f'{prefix} roof', mesh, material('roof_mat', (0.5, 0.35, 0.2, 1)), (cx, cy, 2.2), 0.0 if along_x else math.pi / 2)
    box(f'{prefix} door', (0.9, 0.06, 1.9), (cx, cy - depth / 2 - 0.1, 0.95) if along_x else (cx - length / 2 - 0.1, cy, 0.95), material('door_mat', (0.4, 0.25, 0.1, 1)), 0.0 if along_x else math.pi / 2)


shed('Shed A', (8.0, -3.0))
shed('Shed B', (22.0, 11.0))

wood = material('wood_mat', (0.45, 0.32, 0.2, 1))
for index in range(8):                                  # a fence along y = 8: posts every 2 m, two rails between them
    x = 2.0 + index * 2.0
    box(f'Fence post {index + 1}', (0.12, 0.12, 1.2), (x, 8.0, 0.6), wood)
    if index < 7:
        box(f'Fence rail {index + 1} low', (2.0, 0.05, 0.1), (x + 1.0, 8.0, 0.45), wood)
        box(f'Fence rail {index + 1} high', (2.0, 0.05, 0.1), (x + 1.0, 8.0, 0.9), wood)

cylinder('Prop well', 0.7, 0.9, (18.0, 6.8, 0.45), material('stone_mat', (0.5, 0.48, 0.45, 1)), 20)
cylinder('Prop barrel', 0.35, 0.9, (20.0, 0.5, 0.45), wood)
iron = material('iron_mat', (0.2, 0.2, 0.22, 1))
cylinder('Iron band 1', 0.37, 0.05, (20.0, 0.5, 0.25), iron)
cylinder('Iron band 2', 0.37, 0.05, (20.0, 0.5, 0.65), iron)
box('Iron post', (0.1, 0.1, 1.4), (27.0, 1.0, 0.7), iron)
cylinder('Tree stump', 0.4, 0.5, (12.0, 9.5, 0.25), material('bark_mat', (0.3, 0.22, 0.15, 1)))

if '--no-light' not in arguments:
    sun = bpy.data.lights.new('Sun', 'SUN')
    sun.energy = 3.0
    sun_object = bpy.data.objects.new('Sun', sun)
    scene.collection.objects.link(sun_object)
    sun_object.rotation_euler = (math.radians(55), 0, math.radians(35))
    scene.world = bpy.data.worlds.new('World')
    scene.world.use_nodes = True
    scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.7
if '--no-camera' not in arguments:
    data = bpy.data.cameras.new('Camera A')
    data.lens = 28
    camera = bpy.data.objects.new('Camera A', data)
    camera.location = (13.0, -11.0, 5.5)
    camera.rotation_euler = (Vector((13.0, 5.0, 0.8)) - Vector(camera.location)).to_track_quat('-Z', 'Y').to_euler()
    scene.collection.objects.link(camera)
    scene.camera = camera
bpy.ops.wm.save_as_mainfile(filepath=out_path)
print('saved', out_path)
