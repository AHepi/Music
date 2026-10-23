"""What this does: builds the small test scene for the place audit's four lessons-round checks (place: film frame, place: world, place: sun,
place: lettering), inside Blender, in a FAULTY or a MENDED version:
  faulty  render size 1200 x 800 although the settings say "for_film": true; a 24 m ground whose edge the camera sees over the wall; the clip end
          50 m with hills 400 m away; far hills with the role backdrop that cast shadows, and a 30 m mill 200 m away that casts shadows; a sun only
          9 degrees up behind a 4 m wall, so most of the ground the camera sees is shadowed; a shop sign with no lettering.
  mended  1080 x 1920; a 4 km ground; clip end 2000 m; the backdrop and the mill cast no shadow; the sun 50 degrees up from the side; the sign
          carries a text object.
Both have a ledger book with a text object on it (a lettered thing that passes) and a floor board (a "board" that is not a sign).
Run: blender -b --disable-autoexec --python make_world_scene.py -- OUT.blend faulty|mended
"""
import math
import sys

import bmesh
import bpy
from mathutils import Vector

arguments = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
if len(arguments) < 2 or arguments[1] not in ('faulty', 'mended'):
    print('usage: blender -b --python make_world_scene.py -- OUT.blend faulty|mended')
    sys.exit(2)
out_path, version = arguments[0], arguments[1]
mended = version == 'mended'

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene


def material(name, colour):
    made = bpy.data.materials.new(name)
    made.use_nodes = True
    made.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = colour
    return made


def box(name, size, location, colour, role):
    mesh = bpy.data.meshes.new(name)
    builder = bmesh.new()
    bmesh.ops.create_cube(builder, size=1.0)
    bmesh.ops.scale(builder, vec=Vector(size), verts=builder.verts)
    builder.to_mesh(mesh)
    builder.free()
    obj = bpy.data.objects.new(name, mesh)
    obj.location = location
    obj.data.materials.append(material(f'{name} colour', colour))
    obj['place_role'] = role
    scene.collection.objects.link(obj)
    return obj


def ground(name, half):
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata([(-half, -half, 0), (half, -half, 0), (half, half, 0), (-half, half, 0)], [], [(0, 1, 2, 3)])
    obj = bpy.data.objects.new(name, mesh)
    obj.data.materials.append(material('ground colour', (0.3, 0.27, 0.2, 1)))
    obj['place_role'] = 'ground.earth'
    scene.collection.objects.link(obj)
    return obj


def lettering(name, body, on, offset):
    curve = bpy.data.curves.new(name, 'FONT')
    curve.body = body
    curve.size = 0.2
    curve.extrude = 0.005
    obj = bpy.data.objects.new(name, curve)
    obj.location = on.location + Vector(offset)
    obj.rotation_euler = (math.radians(90), 0, 0)
    obj['place_role'] = 'prop.generic'
    scene.collection.objects.link(obj)
    return obj


ground('Ground yard', 2000.0 if mended else 12.0)
box('Wall north', (40.0, 0.4, 4.0), (0, 6.0, 2.0), (0.5, 0.25, 0.2, 1), 'wall.brick')
sign = box('Shop sign', (1.2, 0.05, 0.4), (1.5, 1.0, 1.4), (0.2, 0.3, 0.2, 1), 'prop.wood')
if mended:
    lettering('Shop sign lettering', 'GROCER', sign, (-0.5, -0.04, -0.08))
book = box('Ledger book', (0.3, 0.22, 0.05), (-1.2, 1.0, 0.85), (0.4, 0.1, 0.1, 1), 'prop.generic')
lettering('Ledger book title', 'LEDGER', book, (-0.12, -0.12, 0.0))
box('Floor board 1', (1.0, 0.15, 0.03), (-2.5, -1.0, 0.015), (0.4, 0.3, 0.2, 1), 'timber.plank')
hills = box('Far hills', (600.0, 40.0, 60.0), (0, 400.0, 30.0), (0.45, 0.5, 0.6, 1), 'backdrop')
mill = box('Distant mill', (12.0, 12.0, 30.0), (150.0, 140.0, 15.0), (0.4, 0.3, 0.25, 1), 'wall.brick')
hills.visible_shadow = not mended
mill.visible_shadow = not mended

camera_data = bpy.data.cameras.new('Camera A')
camera_data.lens = 24
camera_data.clip_end = 2000.0 if mended else 50.0
camera = bpy.data.objects.new('Camera A', camera_data)
camera.location = (0, -8.0, 6.0)
camera.rotation_euler = (math.radians(75), 0, 0)          # looking along +y, 15 degrees down, over the 4 m wall (faulty: past the ground's edge)
scene.collection.objects.link(camera)
scene.camera = camera
scene.render.resolution_x, scene.render.resolution_y = (1080, 1920) if mended else (1200, 800)

sun_data = bpy.data.lights.new('Sun', 'SUN')
sun_data.energy = 3.0
sun = bpy.data.objects.new('Sun', sun_data)
compass, height = (0.0, 50.0) if mended else (90.0, 9.0)     # faulty: low behind the wall (the sun stands toward +y)
toward = Vector((math.cos(math.radians(compass)) * math.cos(math.radians(height)), math.sin(math.radians(compass)) * math.cos(math.radians(height)),
                 math.sin(math.radians(height))))
sun.rotation_euler = (-toward).to_track_quat('-Z', 'Y').to_euler()
scene.collection.objects.link(sun)
bpy.ops.wm.save_as_mainfile(filepath=out_path)
print(f'saved {out_path} ({version})')
