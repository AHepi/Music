"""What this does: builds the small made-up scenes that test_place_fixes.py runs the place kit on, one Blender file each, into a folder. Every scene is a trap a smoke check found in
the kit: objects with no material at all, a curved lane strip, a lane with a trench cut in it and steps in the trench, curves and text and instances that are drawn but are not meshes,
a lettered sign whose material carries its own picture, a mirrored wall, an empty scene, a scene lit by its world colour alone, a quay with water beside it.
Run inside Blender: blender -b --python make_fix_scenes.py -- OUTPUT_FOLDER   (it writes lazy.blend, lanes.blend, trench.blend, kinds.blend, sign.blend, empty.blend, world.blend, quay.blend,
part.blend, turned.blend).
A concrete example: lanes.blend holds a 50 x 40 m ground and a curved lane ribbon of 20 big faces called "Dirt road ribbon" lying on it.
"""
import math
import os
import sys

import bmesh
import bpy

arguments = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
if not arguments:
    print('give the output folder: blender -b --python make_fix_scenes.py -- OUTPUT_FOLDER')
    sys.exit(2)
out_folder = os.path.abspath(arguments[0])
os.makedirs(out_folder, exist_ok=True)


def fresh():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def box(name, size, location, rotation_z=0.0, scale=None, collection=None):
    mesh = bpy.data.meshes.new(name)
    builder = bmesh.new()
    bmesh.ops.create_cube(builder, size=1.0)
    for vertex in builder.verts:
        vertex.co.x *= size[0]
        vertex.co.y *= size[1]
        vertex.co.z *= size[2]
    builder.to_mesh(mesh)
    builder.free()
    obj = bpy.data.objects.new(name, mesh)
    (collection or bpy.context.scene.collection).objects.link(obj)
    obj.location = location
    obj.rotation_euler = (0.0, 0.0, rotation_z)
    if scale:
        obj.scale = scale
    return obj


def quad(name, x0, x1, y0, y1, z):
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata([(x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z)], [], [(0, 1, 2, 3)])
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    return obj


def sun(name='Sun', location=(0, 0, 10)):
    lamp = bpy.data.objects.new(name, bpy.data.lights.new(name, 'SUN'))
    lamp.location = location
    bpy.context.scene.collection.objects.link(lamp)
    return lamp


def save(name):
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(out_folder, name + '.blend'))


# ---- lazy: objects with NO material at all. The bevels and the shape damage are put on by hand, so that the only thing the audit can still object to is the missing surfaces
fresh()
quad('Ground', -6, 6, -6, 6, 0.0)
for index in range(4):
    wall = box(f'Cottage wall {index + 1}', (2.2 + 0.1 * index, 0.3, 2.4), (-4.0 + 2.6 * index, 0.0, 1.2))
    wall.modifiers.new('Hand bevel', 'BEVEL')
    wall['pk_shape_damage'] = 1
barrel = box('Prop barrel 1', (0.7, 0.7, 0.9), (3.0, 3.0, 0.45))
barrel.modifiers.new('Hand bevel', 'BEVEL')
barrel['pk_shape_damage'] = 1
sun()
save('lazy')

# ---- lanes: a big flat ground and a CURVED lane ribbon (20 big faces, about 170 square metres) lying on it
fresh()
quad('Ground', -5, 55, -20, 20, 0.0)
mesh = bpy.data.meshes.new('Dirt road ribbon')
vertices, faces = [], []
count = 20
for k in range(count + 1):
    x = 50.0 * k / count
    y = 6.0 * math.sin(x / 8.0)
    slope = 6.0 / 8.0 * math.cos(x / 8.0)
    length = math.hypot(1.0, slope)
    nx, ny = -slope / length, 1.0 / length
    vertices += [(x + nx * 1.6, y + ny * 1.6, 0.02), (x - nx * 1.6, y - ny * 1.6, 0.02)]
for k in range(count):
    a = 2 * k
    faces.append((a, a + 1, a + 3, a + 2))
mesh.from_pydata(vertices, [], faces)
mesh.update()
ribbon = bpy.data.objects.new('Dirt road ribbon', mesh)
bpy.context.scene.collection.objects.link(ribbon)
sun()
save('lanes')

# ---- trench: a towpath strip of 0.1 m squares (14 x 2.4 m) with a trench cut through it, a floor 1 m below, and three solid step blocks standing on that floor
fresh()
builder = bmesh.new()
columns, rows, cell = 140, 24, 0.1
grid = [[builder.verts.new((c * cell, r * cell - 1.2, 0.0)) for c in range(columns + 1)] for r in range(rows + 1)]
for r in range(rows):
    for c in range(columns):
        centre_x, centre_y = (c + 0.5) * cell, (r + 0.5) * cell - 1.2
        if 5.0 <= centre_x <= 6.2 and -0.5 <= centre_y <= 0.5:
            continue                                    # the trench: no faces here
        builder.faces.new((grid[r][c], grid[r][c + 1], grid[r + 1][c + 1], grid[r + 1][c]))
bmesh.ops.delete(builder, geom=[v for v in builder.verts if not v.link_faces], context='VERTS')
mesh = bpy.data.meshes.new('Towpath')
builder.to_mesh(mesh)
builder.free()
towpath = bpy.data.objects.new('Towpath', mesh)
bpy.context.scene.collection.objects.link(towpath)
towpath['place_role'] = 'ground.gravel'
quad('Trench floor', 5.0, 6.2, -0.5, 0.5, -1.0)['place_role'] = 'ground.earth'
for index in range(3):
    height = 0.17 * (index + 1)
    step = box(f'Stone step {index + 1}', (0.35, 1.0, height), (5.2 + 0.35 * index, 0.0, -1.0 + height / 2.0))      # solid blocks standing on the trench floor, each 17 cm higher than the one before
    step['place_role'] = 'stone.step'
sun()
save('trench')

# ---- kinds: things drawn that are not meshes: a bevelled curve (a rope), a text sign, an empty that instances a collection (a barrel), and a hidden helper curve
fresh()
quad('Ground', -6, 6, -6, 6, 0.0)
curve = bpy.data.curves.new('Rope 1', 'CURVE')
curve.dimensions = '3D'
curve.bevel_depth = 0.03
curve.bevel_resolution = 2
spline = curve.splines.new('BEZIER')
spline.bezier_points.add(2)
for point, location in zip(spline.bezier_points, ((-2, 0, 0.03), (0, 0.4, 0.03), (2, 0, 0.03))):         # a rope lying on the ground
    point.co = location
    point.handle_left_type = point.handle_right_type = 'AUTO'
rope = bpy.data.objects.new('Rope 1', curve)
rope['place_role'] = 'prop.rope'
bpy.context.scene.collection.objects.link(rope)
text = bpy.data.curves.new('Sign text', 'FONT')
text.body = 'INN'
text.extrude = 0.02
sign = bpy.data.objects.new('Sign text', text)
sign.location = (0, 3, 0.02)                                 # letters lying flat on the ground (the extrusion goes 2 cm both ways)
sign['place_role'] = 'prop.wood'
bpy.context.scene.collection.objects.link(sign)
source = bpy.data.collections.new('barrel source')
barrel_mesh = box('barrel source mesh', (0.7, 0.7, 0.9), (0, 0, 0.45), collection=source)
instance = bpy.data.objects.new('Prop barrel instance', None)
instance.instance_type = 'COLLECTION'
instance.instance_collection = source
instance.location = (3, -2, 0)
bpy.context.scene.collection.objects.link(instance)
helper_curve = bpy.data.curves.new('Helper line', 'CURVE')
helper_curve.bevel_depth = 0.01
helper_spline = helper_curve.splines.new('POLY')
helper_spline.points.add(1)
helper_spline.points[0].co = (0, 0, 0, 1)
helper_spline.points[1].co = (1, 1, 1, 1)
helper = bpy.data.objects.new('Helper line', helper_curve)
helper['place_role'] = 'never.helper'
bpy.context.scene.collection.objects.link(helper)
sun()
save('kinds')

# ---- sign: a sign board whose material carries its own picture (kept as it is), on a ground
fresh()
quad('Ground', -6, 6, -6, 6, 0.0)
board = box('Prop sign board', (1.2, 0.08, 0.6), (0, 0, 0.3))
board['place_role'] = 'prop.wood'
painted = bpy.data.materials.new('lettered sign')
painted.use_nodes = True
texture = painted.node_tree.nodes.new('ShaderNodeTexImage')
picture = bpy.data.images.new('sign_picture', 16, 16)
texture.image = picture
painted.node_tree.links.new(texture.outputs['Color'], painted.node_tree.nodes['Principled BSDF'].inputs['Base Color'])
board.data.materials.append(painted)
sun()
save('sign')

# ---- empty: nothing in it
fresh()
save('empty')

# ---- world: a box and a world colour, no lamp
fresh()
quad('Ground', -6, 6, -6, 6, 0.0)
box('Cottage wall 1', (4.0, 0.3, 2.4), (0, 0, 1.2))
world = bpy.data.worlds.new('Sky colour')
world.use_nodes = True
world.node_tree.nodes['Background'].inputs['Color'].default_value = (0.4, 0.5, 0.8, 1.0)
bpy.context.scene.world = world
save('world')

# ---- quay: a paved quay, a seabed and a sea box beside it (for the plan masks)
fresh()
box('Quay paving', (8.0, 12.0, 0.5), (4.0, 0.0, -0.25))
box('Seabed', (16.0, 12.0, 0.5), (16.0, 0.0, -3.25))
box('Sea', (16.0, 12.0, 2.4), (16.0, 0.0, -1.8))
sun()
save('quay')
# ---- part: a ground owned by 'roads' and three cottage walls owned by 'cottages' (what a part builder's finish-part works on)
fresh()
ground = quad('Ground', -8, 8, -8, 8, 0.0)
ground['place_owner'] = 'roads'
ground['place_role'] = 'ground.earth'
for index in range(3):
    wall = box(f'Cottage wall {index + 1}', (2.0 + 0.2 * index, 0.3, 2.4), (-4.0 + 4.0 * index, 0.0, 1.2))
    wall['place_owner'] = 'cottages'
    wall['place_role'] = 'wall.plaster'
sun()
save('part')

# ---- turned: a wall 4 m long and 0.3 m thick turned 45 degrees (its box along the world axes is about 3 m by 3 m)
fresh()
quad('Ground', -8, 8, -8, 8, 0.0)
box('Cottage wall 1', (4.0, 0.3, 2.4), (0, 0, 1.2), rotation_z=math.radians(45.0))
sun()
save('turned')
print('FIX SCENES DONE', out_folder)
