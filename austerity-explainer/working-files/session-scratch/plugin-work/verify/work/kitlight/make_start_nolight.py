"""What this does: makes the empty starting scene for the canal lock side: metric units, a hero camera ("Camera A") and a close-up camera ("Camera B"), a plain grey-blue world as the soft fill, and one low sun that grazes the walls.
Run: blender -b --disable-autoexec --python make_start.py -- start.blend
"""
import math
import sys

import bpy
from mathutils import Vector

out = sys.argv[sys.argv.index('--') + 1]
bpy.ops.wm.read_homefile(use_empty=True)
scene = bpy.context.scene
scene.unit_settings.system = 'METRIC'
scene.render.resolution_x, scene.render.resolution_y = 1200, 800


def camera(name, location, target, lens):
    data = bpy.data.cameras.new(name)
    data.lens = lens
    obj = bpy.data.objects.new(name, data)
    scene.collection.objects.link(obj)
    obj.location = location
    direction = Vector(target) - Vector(location)
    obj.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
    return obj


camera('Camera A', (-4.8, 3.4, 1.3), (0.9, -0.4, -0.75), 24)       # the hero view: from behind the far wall, across the channel to the near wall, the steps and the gate
camera('Camera B', (1.2, 1.9, -0.1), (3.6, 0.5, -0.8), 28)         # the close-up: the gate leaf, the brick wall at the waterline
scene.camera = bpy.data.objects['Camera A']
world = bpy.data.worlds.new('World')
world.use_nodes = True
background = world.node_tree.nodes.get('Background')
background.inputs[0].default_value = (0.42, 0.50, 0.58, 1.0)
background.inputs[1].default_value = 1.0
scene.world = None
bpy.ops.wm.save_as_mainfile(filepath=out)
print('saved', out)
