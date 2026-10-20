# What this does: TEST of the "drop the stones and let physics settle them" way of making gravel (a polygoniq tip and several tutorials describe it):
# ~160 lumpy stones of random size and turn are dropped from random heights into a 1 x 1 tray (four invisible walls and a floor, all passive rigid bodies),
# the rigid-body simulation is stepped for 120 frames, then the heap is photographed from straight above (colour = random blue-grey per stone, height = Z).
# It measures: how long the simulation took, and whether the result repeats at the tile edges (it does not: the walls stop stones at the edge).
# Run: blender -b --disable-autoexec -t 2 --python geo_physics_gravel.py -- OUT_FOLDER [--size 512] [--stones 160]
import json
import math
import os
import random
import sys
import time

import bmesh
import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import geo_helpers as gh  # noqa: E402

args = sys.argv[sys.argv.index('--') + 1:]
out = args[0]
size = int(args[args.index('--size') + 1]) if '--size' in args else 512
count = int(args[args.index('--stones') + 1]) if '--stones' in args else 160
os.makedirs(out, exist_ok=True)
random.seed(7)
scene = gh.new_overhead_scene(size)

# one lumpy stone mesh, shared by all stones
bm = bmesh.new()
bmesh.ops.create_icosphere(bm, subdivisions=1, radius=0.5)
for vertex in bm.verts:
    vertex.co += __import__('mathutils').Vector((random.uniform(-0.15, 0.15), random.uniform(-0.15, 0.15), random.uniform(-0.15, 0.15)))
    vertex.co.z *= 0.7
mesh = bpy.data.meshes.new('stone')
bm.to_mesh(mesh)
bm.free()
colour_material = gh.object_random_colour_material([(0.0, '#16181c'), (0.2, '#1f2228'), (0.4, '#2a2f38'), (0.55, '#38414e'), (0.7, '#4b5967'), (0.85, '#5e7080'), (0.93, '#7d5a3d')], 'stone colour')
mesh.materials.append(colour_material)

bpy.ops.rigidbody.world_add()
world = scene.rigidbody_world
world.point_cache.frame_start = 1
world.point_cache.frame_end = 130
scene.frame_start, scene.frame_end = 1, 130


def passive_box(name, location, size_xyz):
    box_mesh = bpy.data.meshes.new(name)
    box_mesh.from_pydata([(-0.5, -0.5, -0.5), (0.5, -0.5, -0.5), (0.5, 0.5, -0.5), (-0.5, 0.5, -0.5), (-0.5, -0.5, 0.5), (0.5, -0.5, 0.5), (0.5, 0.5, 0.5), (-0.5, 0.5, 0.5)], [],
                         [(0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)])
    obj = bpy.data.objects.new(name, box_mesh)
    obj.location = location
    obj.scale = size_xyz
    scene.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.rigidbody.object_add(type='PASSIVE')
    obj.rigid_body.collision_shape = 'BOX'
    obj.select_set(False)
    return obj


floor = passive_box('floor', (0.5, 0.5, -0.05), (1.0, 1.0, 0.1))
walls = [passive_box('wall_left', (-0.05, 0.5, 0.25), (0.1, 1.2, 0.5)), passive_box('wall_right', (1.05, 0.5, 0.25), (0.1, 1.2, 0.5)),
         passive_box('wall_bottom', (0.5, -0.05, 0.25), (1.2, 0.1, 0.5)), passive_box('wall_top', (0.5, 1.05, 0.25), (1.2, 0.1, 0.5))]
for obj in walls + [floor]:
    obj.hide_render = True
ground_view = bpy.data.objects.new('ground picture', bpy.data.meshes.new('ground picture'))
ground_view.data.from_pydata([(-1, -1, 0), (2, -1, 0), (2, 2, 0), (-1, 2, 0)], [], [(0, 1, 2, 3)])
scene.collection.objects.link(ground_view)

stones = []
for index in range(count):
    obj = bpy.data.objects.new('s%03d' % index, mesh)
    s = random.uniform(0.04, 0.09)
    obj.scale = (s * random.uniform(0.8, 1.3), s * random.uniform(0.8, 1.2), s)
    obj.rotation_euler = (random.uniform(0, 6.28), random.uniform(0, 6.28), random.uniform(0, 6.28))
    obj.location = (random.uniform(0.04, 0.96), random.uniform(0.04, 0.96), 0.12 + 0.012 * index)
    scene.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.rigidbody.object_add(type='ACTIVE')
    obj.rigid_body.collision_shape = 'CONVEX_HULL'
    obj.rigid_body.friction = 0.8
    obj.rigid_body.mass = 1.0
    obj.select_set(False)
    stones.append(obj)

start = time.time()
for frame in range(1, 131):
    scene.frame_set(frame)
simulation_seconds = time.time() - start
bpy.context.view_layer.update()
heights = [obj.matrix_world.translation.z for obj in stones]
gh.set_material(ground_view, gh.constant_colour_material('soil', (0.1, 0.045, 0.02, 1.0)))
gh.render_picture(scene, os.path.join(out, 'colour.png'))
height_material = gh.height_material(0.0, 0.12)
for obj in stones:
    obj.data.materials.clear()
    obj.data.materials.append(height_material)
gh.set_material(ground_view, height_material)
gh.render_picture(scene, os.path.join(out, 'height.png'), True, True)
inside = sum(1 for obj in stones if 0 <= obj.matrix_world.translation.x <= 1 and 0 <= obj.matrix_world.translation.y <= 1)
facts = {'stones': count, 'frames_simulated': 130, 'simulation_seconds': round(simulation_seconds, 1), 'stones_still_inside_the_tray': inside,
         'highest_stone_centre_z': round(max(heights), 3), 'mean_stone_centre_z': round(sum(heights) / len(heights), 3)}
json.dump(facts, open(os.path.join(out, 'facts.json'), 'w'), indent=1)
print('FACTS', json.dumps(facts))
