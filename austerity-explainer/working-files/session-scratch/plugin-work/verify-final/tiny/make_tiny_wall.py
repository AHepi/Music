"""What this does: builds a tiny test place inside Blender for trying the place kit's `variations` tool as a newcomer would:
a 6 x 6 m gravel ground, a brick garden wall (3 m long, 0.3 m thick, 1.6 m high) standing on it, a timber gate post beside the wall,
a timber gate leaf hanging on that post, a sun, and two cameras ("Camera A" wide, "Camera B" close on the wall foot).
Every object gets its role as it is made (the object property `place_role`), as the skill says.
Run: blender -b --disable-autoexec --python make_tiny_wall.py -- OUT.blend
"""
import math
import sys

import bmesh
import bpy
from mathutils import Vector

arguments = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
if not arguments:
    print('usage: blender -b --python make_tiny_wall.py -- OUT.blend')
    sys.exit(2)
out_path = arguments[0]

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene


def plain_material(name, colour):
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    principled = material.node_tree.nodes['Principled BSDF']
    principled.inputs['Base Color'].default_value = colour
    principled.inputs['Roughness'].default_value = 0.6
    return material


def box(name, size, centre, material, role):
    mesh = bpy.data.meshes.new(name)
    builder = bmesh.new()
    bmesh.ops.create_cube(builder, size=1.0)
    for vertex in builder.verts:
        vertex.co = Vector((vertex.co.x * size[0], vertex.co.y * size[1], vertex.co.z * size[2]))
    builder.to_mesh(mesh)
    builder.free()
    mesh.materials.append(material)
    thing = bpy.data.objects.new(name, mesh)
    thing.location = centre
    thing['place_role'] = role
    scene.collection.objects.link(thing)
    return thing


gravel = plain_material('Gravel', (0.42, 0.40, 0.36, 1))
brick = plain_material('Brick', (0.45, 0.16, 0.10, 1))
timber = plain_material('Timber', (0.30, 0.21, 0.13, 1))

box('Gravel ground', (6.0, 6.0, 0.1), (0, 0, -0.05), gravel, 'ground.gravel')
box('Brick wall', (3.0, 0.3, 1.6), (0, 0, 0.8), brick, 'wall.brick')
box('Gate post', (0.15, 0.15, 1.4), (1.62, 0, 0.7), timber, 'timber.post')
box('Gate leaf', (0.9, 0.05, 1.1), (2.145, 0, 0.6), timber, 'timber.door')   # touches the post (post face at x = 1.695)

sun_data = bpy.data.lights.new('Sun', 'SUN')
sun_data.energy = 3.0
sun = bpy.data.objects.new('Sun', sun_data)
sun.rotation_euler = (math.radians(50), 0, math.radians(30))
scene.collection.objects.link(sun)

for camera_name, location, target in (('Camera A', (4.5, -5.5, 2.4), (0.3, 0, 0.8)), ('Camera B', (0.8, -2.4, 0.9), (0.2, 0, 0.4))):
    camera_data = bpy.data.cameras.new(camera_name)
    camera = bpy.data.objects.new(camera_name, camera_data)
    camera.location = location
    camera.rotation_euler = (Vector(target) - Vector(location)).to_track_quat('-Z', 'Y').to_euler()
    scene.collection.objects.link(camera)
    if camera_name == 'Camera A':
        scene.camera = camera

world = bpy.data.worlds.new('World')
world.use_nodes = True
world.node_tree.nodes['Background'].inputs['Color'].default_value = (0.5, 0.6, 0.75, 1)
world.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.6
scene.world = world
bpy.ops.wm.save_as_mainfile(filepath=out_path)
print('saved', out_path)
