"""What this does: makes a tiny props-only scene (one crate on a 3 m square of ground, one sun, one view camera close to the crate,
tilted down a little so the top of its frame shows the horizon) to see what the place audit's new check "place: world" says about a
prop built alone. A verify-step scratch file; it writes only the .blend it is given.
Run: blender -b --disable-autoexec --python make_prop_scene.py -- OUT.blend [far]
  far: the same scene with the ground made 4 km wide (the "mended" case)
"""
import math
import sys

import bmesh
import bpy
from mathutils import Vector

arguments = sys.argv[sys.argv.index('--') + 1:]
out_path = arguments[0]
far_ground = len(arguments) > 1 and arguments[1] == 'far'

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.render.resolution_x, scene.render.resolution_y = 1200, 800


def plain_material(name, colour):
    made = bpy.data.materials.new(name)
    made.use_nodes = True
    made.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = colour
    return made


half = 2000.0 if far_ground else 1.5
ground_mesh = bpy.data.meshes.new('Ground')
ground_mesh.from_pydata([(-half, -half, 0), (half, -half, 0), (half, half, 0), (-half, half, 0)], [], [(0, 1, 2, 3)])
ground = bpy.data.objects.new('Ground', ground_mesh)
ground.data.materials.append(plain_material('ground colour', (0.3, 0.27, 0.2, 1)))
ground['place_role'] = 'ground.earth'
scene.collection.objects.link(ground)

crate_mesh = bpy.data.meshes.new('Crate')
builder = bmesh.new()
bmesh.ops.create_cube(builder, size=0.6)
builder.to_mesh(crate_mesh)
builder.free()
crate = bpy.data.objects.new('Crate', crate_mesh)
crate.location = (0, 0, 0.3)
crate.data.materials.append(plain_material('crate colour', (0.4, 0.25, 0.1, 1)))
crate['place_role'] = 'prop.crate'
scene.collection.objects.link(crate)

sun_data = bpy.data.lights.new('Sun', 'SUN')
sun_data.energy = 3.0
sun = bpy.data.objects.new('Sun', sun_data)
sun.rotation_euler = (math.radians(40), 0, math.radians(30))
scene.collection.objects.link(sun)

camera_data = bpy.data.cameras.new('View crate')
camera_data.lens = 35
camera = bpy.data.objects.new('View crate', camera_data)
camera.location = (0, -2.5, 1.2)
camera.rotation_euler = (math.radians(78), 0, 0)     # tilted 12 degrees down: the top of the frame sees past the horizon
scene.collection.objects.link(camera)
scene.camera = camera
bpy.ops.wm.save_as_mainfile(filepath=out_path)
print('saved', out_path)
