# What this does: builds the small proof scene for the plugin 1.5.0 surfaces and weeds, inside Blender, the way a model builds a place when told only what to put in it:
# plain-colour shapes. A dirt road with a grass strip between its ruts crosses two grass grounds; a low stone wall stands on the north grass, a small plastered hut with a
# thatched roof beside it, a fence of posts and rails on the south grass; a sun, a sky and one low camera looking along the road. Every object carries its role.
# Run: blender -b --factory-startup --python make_proof_scene.py -- OUT.blend
import math
import sys

import bmesh
import bpy
from mathutils import Vector

out_path = sys.argv[sys.argv.index('--') + 1]
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
cache = {}


def material(name, colour):
    if name not in cache:
        made = bpy.data.materials.new(name)
        made.use_nodes = True
        made.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = colour
        cache[name] = made
    return cache[name]


def add(name, mesh, mat, role, location=(0, 0, 0), rotation_z=0.0):
    mesh.materials.append(mat)
    obj = bpy.data.objects.new(name, mesh)
    scene.collection.objects.link(obj)
    obj.location = location
    obj.rotation_euler = (0, 0, rotation_z)
    obj['place_role'] = role
    return obj


def plane(name, x0, x1, y0, y1, mat, role):
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata([(x0, y0, 0), (x1, y0, 0), (x1, y1, 0), (x0, y1, 0)], [], [(0, 1, 2, 3)])
    return add(name, mesh, mat, role)


def box(name, size, location, mat, role, rotation_z=0.0):
    mesh = bpy.data.meshes.new(name)
    builder = bmesh.new()
    bmesh.ops.create_cube(builder, size=1.0)
    for vertex in builder.verts:
        vertex.co.x *= size[0]
        vertex.co.y *= size[1]
        vertex.co.z *= size[2]
    builder.to_mesh(mesh)
    builder.free()
    return add(name, mesh, mat, role, location, rotation_z)


grass = material('grass_mat', (0.25, 0.35, 0.15, 1))
plane('Ground grass north', -60, 60, 1.6, 60, grass, 'ground.grass')
plane('Ground grass south', -60, 60, -60, -1.6, grass, 'ground.grass')
plane('Ground road', -60, 60, -1.6, 1.6, material('road_mat', (0.4, 0.3, 0.2, 1)), 'ground.dirt_road')
stone = material('stone_mat', (0.5, 0.48, 0.45, 1))
box('Wall stone', (7.0, 0.5, 1.0), (-1.0, 5.0, 0.5), stone, 'wall.stone')
plaster = material('plaster_mat', (0.8, 0.76, 0.66, 1))
box('Hut wall north', (3.6, 0.25, 2.2), (7.0, 8.0, 1.1), plaster, 'wall.plaster')
box('Hut wall south', (3.6, 0.25, 2.2), (7.0, 4.8, 1.1), plaster, 'wall.plaster')
box('Hut wall east', (0.25, 3.0, 2.2), (8.7, 6.4, 1.1), plaster, 'wall.plaster')
box('Hut wall west', (0.25, 3.0, 2.2), (5.3, 6.4, 1.1), plaster, 'wall.plaster')
half, length, rise = 2.0, 4.2, 2.0 * math.tan(math.radians(45))
roof = bpy.data.meshes.new('Hut roof')
roof.from_pydata([(-length / 2, -half, 0), (length / 2, -half, 0), (length / 2, half, 0), (-length / 2, half, 0), (-length / 2, 0, rise), (length / 2, 0, rise)], [],
                 [(0, 3, 2, 1), (0, 1, 5, 4), (2, 3, 4, 5), (0, 4, 3), (1, 2, 5)])
roof.update()
add('Hut roof thatch', roof, material('thatch_mat', (0.6, 0.5, 0.3, 1)), 'roof.thatch', (7.0, 6.4, 2.2))
box('Hut door', (0.9, 0.06, 1.9), (7.0, 4.62, 0.95), material('door_mat', (0.4, 0.25, 0.1, 1)), 'timber.door')
wood = material('wood_mat', (0.45, 0.32, 0.2, 1))
for index in range(6):
    x = -7.0 + index * 2.0
    box(f'Fence post {index + 1}', (0.12, 0.12, 1.2), (x, -4.0, 0.6), wood, 'timber.fence')
    if index < 5:
        box(f'Fence rail {index + 1} low', (2.0, 0.05, 0.1), (x + 1.0, -4.0, 0.45), wood, 'timber.fence')
        box(f'Fence rail {index + 1} high', (2.0, 0.05, 0.1), (x + 1.0, -4.0, 0.9), wood, 'timber.fence')
sun = bpy.data.lights.new('Sun', 'SUN')
sun.energy = 4.0
sun_object = bpy.data.objects.new('Sun', sun)
scene.collection.objects.link(sun_object)
sun_object.rotation_euler = (math.radians(50), 0, math.radians(-35))
scene.world = bpy.data.worlds.new('World')
scene.world.use_nodes = True
background = scene.world.node_tree.nodes['Background']
background.inputs['Color'].default_value = (0.45, 0.6, 0.85, 1)
background.inputs['Strength'].default_value = 0.8
data = bpy.data.cameras.new('View road')
data.lens = 30
data.clip_end = 1000.0
camera = bpy.data.objects.new('View road', data)
camera.location = (-10.5, -2.6, 1.55)
camera.rotation_euler = (Vector((4.0, 2.2, 0.2)) - Vector(camera.location)).to_track_quat('-Z', 'Y').to_euler()
scene.collection.objects.link(camera)
scene.camera = camera
centre, radius, segments = (1.0, 1.0), 90.0, 96                       # far hills all round (the role backdrop), as the audit's world check asks
vertices, faces = [], []
for index in range(segments):
    angle = 2 * math.pi * index / segments
    x, y = centre[0] + radius * math.cos(angle), centre[1] + radius * math.sin(angle)
    vertices += [(x, y, -40.0), (x, y, 8.0 + 2.5 * math.sin(3 * angle) + 1.5 * math.sin(7 * angle))]
for index in range(segments):
    a, b = 2 * index, 2 * ((index + 1) % segments)
    faces.append((a, b, b + 1, a + 1))
hills = bpy.data.meshes.new('Far hills backdrop')
hills.from_pydata(vertices, [], faces)
hills.update()
add('Far hills backdrop', hills, material('far_hills_mat', (0.42, 0.5, 0.45, 1)), 'backdrop')
floor = bpy.data.meshes.new('Ground far')                              # the plain ground out to the hills, under the place
floor.from_pydata([(-95, -95, -0.5), (95, -95, -0.5), (95, 95, -0.5), (-95, 95, -0.5)], [], [(0, 1, 2, 3)])
add('Ground far backdrop', floor, material('far_ground_mat', (0.2, 0.26, 0.12, 1)), 'backdrop')
scene.render.resolution_x, scene.render.resolution_y = 1200, 800
bpy.ops.wm.save_as_mainfile(filepath=out_path)
print('saved', out_path)
