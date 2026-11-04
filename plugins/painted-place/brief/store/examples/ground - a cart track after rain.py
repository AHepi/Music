"""
What this file does: the store's worked example for its ground tools: a cart track after rain, at dusk. A lane of brown
earth runs away from the eye through an open gateway in a wire fence, between grassy verges. A horse and cart have been
along it several times since the rain: the iron tyres cut two narrow wet ruts with water standing in them, deepest at
the gateway where the wheels turned, with potholes pounded out there, and the horse's hooves pocked the strip between
them; an older car's ruts beside them have softened and gathered grit. A trodden footpath crosses the lane before the
gate, and fresh footprints go from the lane to the open door of a hut and back. Stones lie in the verges and between
the ruts, leaves and twigs near the eye. It is drawn from a builder's eye height, 540 x 960, and finished.

    python3 "ground - a cart track after rain.py" [WIDTH HEIGHT SAMPLES OUT.png]     (defaults 540 960 64, in the folder you run it from)

The order of the steps is the point of the example:
    1. ground.make (with the lane's camber) and ground.wet (how wet the place is: it sets how deep every mark goes)
    2. the tracks tool: old ruts first, then the newer ones over them, potholes, the path, the footprints
    3. ground.detail where the eye is near (real lumps from the soil's photographs), then grass.grow, stones.scatter
       and litter.scatter, after the tracks (no grass in a rut, no stone floating over a groove)
    4. the parts, each stood on the ground with ground.height_at
    5. ground.fill(yard, ground.spots(yard)): the water, in every dip the tracks made too
"""

import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), 'tools'))

import bpy  # noqa: E402
import numpy  # noqa: E402
from mathutils import Vector  # noqa: E402

import store  # noqa: E402
import ground  # noqa: E402
import tracks  # noqa: E402
import stones  # noqa: E402
import grass  # noqa: E402
import litter  # noqa: E402
import sky_and_haze  # noqa: E402
import finish  # noqa: E402
import _lines  # noqa: E402

WIDTH = int(sys.argv[1]) if len(sys.argv) > 1 else 540
HEIGHT = int(sys.argv[2]) if len(sys.argv) > 2 else 960
SAMPLES = int(sys.argv[3]) if len(sys.argv) > 3 else 64
OUT = os.path.abspath(sys.argv[4]) if len(sys.argv) > 4 else os.path.join(os.getcwd(), 'ground - a cart track after rain.png')

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene

# ----------------------------------------------------------------------------------------------- 1. the ground, wet
LANE = [(0.5, -6.0, 0.0), (0.1, 4.0, 0.0), (-0.4, 12.0, 0.0), (-0.2, 22.0, 0.0), (0.8, 33.0, 0.0)]
yard = ground.make(size=(18.0, 42.0), location=(0.0, 14.0, 0.0), relief=0.07, camber=(LANE, 3.6, 0.05), seed=11)
ground.wet(yard, wetness=0.7)                                  # after rain: the dips wet, the crowns damp

way = _lines.Path(_lines.line_points(LANE)).smooth(0.05)
GATE_Y = 9.0
gate_along = float(way.project([[way.at(15.0).x, GATE_Y]])[0][0])
gate = way.at(gate_along)

# ----------------------------------------------------------------------------------------------- 2. the tracks
older = [(x + 0.42, y, z) for x, y, z in LANE]                 # a motor car went by days ago, a little to the right
tracks.ruts(yard, older, vehicle='car', passes=2, age=0.85, seed=5)
tracks.ruts(yard, LANE, vehicle='cart', passes=4, age=0.35, seed=2)
tracks.potholes(yard, LANE, at=[gate_along - 0.9, gate_along + 0.7], size=0.6, age=0.7, which='both', seed=3)
tracks.potholes(yard, LANE, at=[24.5], size=0.5, age=0.6, which='middle', seed=4)    # where the horse walks
tracks.path(yard, [(-8.5, 5.0, 0.0), (-3.0, 6.0, 0.0), (0.0, 6.4, 0.0), (4.0, 6.1, 0.0), (8.5, 5.0, 0.0)], width=0.5, age=0.7, seed=1)
HUT_AT, HUT_TURN = (7.7, 15.0), -90.0                          # its front, with the door, faces the lane
door = Vector((HUT_AT[0] - 2.5 - 0.45, HUT_AT[1], 0.0))       # the ground just in front of its step
tracks.footprints(yard, [(0.4, 10.4, 0.0), (1.7, 12.6, 0.0), (3.3, 14.3, 0.0), (door.x, door.y - 0.1, 0.0)], age=0.1, seed=4)
tracks.footprints(yard, [(door.x, door.y + 0.25, 0.0), (3.1, 14.9, 0.0), (1.3, 13.0, 0.0), (0.1, 11.2, 0.0)], age=0.15, seed=6, start='right')

# ----------------------------------------------------------------------------------------------- 3. stones
def from_lane(xy):
    along, across, _ = way.project(xy)
    return along, numpy.abs(across)


def verges(xy):
    along, across = from_lane(xy)
    return ((across > 1.8) & (across < 5.5) & (along < 30.0)).astype(float) * numpy.clip((across - 1.8) / 0.6, 0.0, 1.0)


def middle_strip(xy):
    along, across = from_lane(xy)
    return ((across < 0.38) & (along < 30.0)).astype(float)


def off_the_lane(xy):
    """Grass on the verges, and a little in the strip between the ruts (the horse's hooves keep most of it bare)."""
    along, across = from_lane(xy)
    return numpy.clip((across - 1.5) / 0.5, 0.0, 1.0) + 0.5 * (across < 0.3)


def near_the_eye(xy):
    along, across = from_lane(xy)
    return ((along < 12.0) & (across < 3.5)).astype(float)


ground.detail(yard, area=near_the_eye, cell=0.015)             # real lumps from the soil's photographs where the eye is near
grass.grow(yard, area=off_the_lane, layers=('turf', 'tussocks'), amount=1.3, seed=2)
grass.grow(yard, area=verges, layers=('weeds',), amount=1.5, seed=8)
stones.scatter(yard, area=verges, layers=('rocks', 'pebbles', 'grit'), amount=0.9, where='hollows', seed=3)
stones.scatter(yard, area=middle_strip, layers=('pebbles', 'grit'), amount=0.8, where='crowns', seed=7)
litter.scatter(yard, area=near_the_eye, amount=1.2, seed=5)

# ----------------------------------------------------------------------------------------------- 4. the parts, on the ground
def stand(name, x, y, turn=0.0, **options):
    return store.add_part(name, location=(x, y, ground.height_at(yard, x, y)), turn=turn, **options)


wood = store.material('SURFACE • rough_wood')
for side in (-1.0, 1.0):                                       # two gateposts, the gate swung away out of sight
    x = gate.x + side * 2.1
    bpy.ops.mesh.primitive_cylinder_add(vertices=10, radius=0.1, depth=1.75, location=(x, GATE_Y, ground.height_at(yard, x, GATE_Y) + 0.8))
    post = bpy.context.object
    post.name = 'gatepost'
    post.rotation_euler = (math.radians(2.0 * side), math.radians(-1.5), 0.0)
    store.use_material(post, wood)
    stand('barbed_wire_fence', gate.x + side * (2.15 + 3.9), GATE_Y, length=7.8, seed=2 if side < 0 else 5)
lantern = store.add_part('hurricane_lantern', location=(gate.x - 2.1 + 0.16, GATE_Y - 0.1, ground.height_at(yard, gate.x - 2.1, GATE_Y) + 1.18))
bpy.data.objects['hurricane_lantern light'].data.energy = 70.0
stand('timber_hut', HUT_AT[0], HUT_AT[1], turn=HUT_TURN, door_open=True, seed=3)
stand('coal_cart', -3.1, 19.5, turn=12.0)
stand('milk_churn', gate.x + 2.55, GATE_Y - 0.55, turn=20.0)
stand('milk_churn', gate.x + 2.95, GATE_Y - 0.35, turn=-35.0, seed=1)

# ----------------------------------------------------------------------------------------------- 5. the water
ground.fill(yard, ground.spots(yard), seed=1)

# ----------------------------------------------------------------------------------------------- sky, lamps, camera
sky_and_haze.sky(scene, strength=0.75, clouds=1.0, low_band=(0.24, 0.15, 0.11), high_band=(0.045, 0.1, 0.12), top=(0.01, 0.03, 0.05))
sky_and_haze.haze(low=(-60, -12, 0), high=(60, 120, 30), density=0.003)


def lamp(name, kind, location, energy, colour, size=0.1):
    light = bpy.data.lights.new(name, kind)
    light.energy = energy
    light.color = colour
    if kind == 'AREA':
        light.size = size
    else:
        light.shadow_soft_size = size
    obj = bpy.data.objects.new(name, light)
    scene.collection.objects.link(obj)
    obj.location = location
    return obj


lamp('door spill', 'POINT', (door.x + 0.9, door.y, 1.6), 90.0, (1.0, 0.6, 0.28), 0.3)
lamp('sky fill', 'AREA', (0.0, 8.0, 8.0), 420.0, (0.5, 0.64, 1.0), 10.0)
moon = bpy.data.objects.new('moon fill', bpy.data.lights.new('moon fill', 'SUN'))
moon.data.energy = 0.5
moon.data.color = (0.45, 0.6, 1.0)
moon.rotation_euler = (math.radians(58), 0.0, math.radians(-25))
scene.collection.objects.link(moon)

camera = bpy.data.objects.new('camera', bpy.data.cameras.new('camera'))
camera.data.lens = 28
camera.data.shift_y = -0.05
camera.location = (0.9, -5.4, 1.62)                            # a builder's eye height, standing in the lane
camera.rotation_euler = (Vector((-0.3, 14.0, 0.5)) - camera.location).to_track_quat('-Z', 'Y').to_euler()
scene.collection.objects.link(camera)
scene.camera = camera

# ----------------------------------------------------------------------------------------------- draw and finish
store.prepare_for_render(scene)
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.samples = SAMPLES
scene.cycles.use_adaptive_sampling = True
scene.cycles.use_denoising = True
scene.cycles.max_bounces = 6
scene.cycles.sample_clamp_indirect = 8
scene.render.resolution_x, scene.render.resolution_y = WIDTH, HEIGHT
scene.view_settings.view_transform = 'Standard'
scene.render.image_settings.file_format = 'OPEN_EXR'
scene.render.image_settings.color_depth = '32'
raw = os.path.join(os.path.dirname(OUT), 'raw - ' + os.path.splitext(os.path.basename(OUT))[0] + '.exr')
scene.render.filepath = raw
bpy.ops.render.render(write_still=True)
finish.finish(raw, OUT, bloom=1.0, veil=0.3, soften=0.5)
print('drew', OUT)
