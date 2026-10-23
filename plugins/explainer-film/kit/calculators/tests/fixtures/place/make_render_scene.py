"""What this does: builds the tiniest scene the render tests draw, inside Blender: a ground plane, one box and one camera named "Camera A", and (by option) a lamp.
Run: blender -b --python make_render_scene.py -- OUT.blend [--lamp] [--dark] [--no-camera] [--glow]
  --lamp       adds a point lamp (the renderer rule must then pick Cycles)
  --dark       no sun, a black world: the picture comes out nearly black (the check for a scene with no light must say so)
  --no-camera  leaves the camera out (the render must say there is no camera)
  --glow       the box uses a glowing material and there is no lamp (the rule must pick Cycles for a glowing material alone)
Without --lamp, --dark and --glow it adds a sun and a grey world, so the picture is lit by daylight alone (the rule must pick EEVEE).
"""
import sys

import bpy
from mathutils import Vector

arguments = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
if not arguments or arguments[0].startswith('-'):
    print('usage: blender -b --python make_render_scene.py -- OUT.blend [--lamp] [--dark] [--no-camera] [--glow]')
    sys.exit(2)
out_path = arguments[0]
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
world = bpy.data.worlds.new('World')
world.use_nodes = True
background = world.node_tree.nodes['Background']
background.inputs['Color'].default_value = (0.0, 0.0, 0.0, 1.0) if '--dark' in arguments else (0.5, 0.5, 0.55, 1.0)
scene.world = world


def material(name, colour, glow=False):
    made = bpy.data.materials.new(name)
    made.use_nodes = True
    node = made.node_tree.nodes['Principled BSDF']
    node.inputs['Base Color'].default_value = colour
    if glow:
        node.inputs['Emission Color'].default_value = (1.0, 0.6, 0.2, 1.0)
        node.inputs['Emission Strength'].default_value = 5.0
    return made


bpy.ops.mesh.primitive_plane_add(size=6, location=(0, 0, 0))
bpy.context.object.name = 'Ground'
bpy.context.object.data.materials.append(material('Ground material', (0.35, 0.3, 0.25, 1.0)))
bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, 0.5))
bpy.context.object.name = 'Box'
bpy.context.object.data.materials.append(material('Box material', (0.6, 0.5, 0.4, 1.0), glow='--glow' in arguments))
if '--lamp' in arguments:
    lamp = bpy.data.lights.new('Lamp', 'POINT')
    lamp.energy = 400.0
    obj = bpy.data.objects.new('Lamp', lamp)
    obj.location = (1.5, -1.5, 2.5)
    scene.collection.objects.link(obj)
elif '--dark' not in arguments and '--glow' not in arguments:
    sun = bpy.data.lights.new('Sun', 'SUN')
    sun.energy = 3.0
    obj = bpy.data.objects.new('Sun', sun)
    obj.rotation_euler = (0.9, 0.2, 0.6)
    scene.collection.objects.link(obj)
if '--no-camera' not in arguments:
    data = bpy.data.cameras.new('Camera A')
    camera = bpy.data.objects.new('Camera A', data)
    camera.location = (3.5, -3.5, 2.5)
    camera.rotation_euler = (Vector((0, 0, 0.4)) - Vector(camera.location)).to_track_quat('-Z', 'Y').to_euler()
    scene.collection.objects.link(camera)
    scene.camera = camera
bpy.ops.wm.save_as_mainfile(filepath=out_path)
print('SAVED', out_path)
