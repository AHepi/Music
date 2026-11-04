"""
What this file does: the store's second worked example for its ground tools: deep motor ruts in a wet field, under a
stormy evening sky, after the owner's picture of a muddy field track (4 November 2026). A heavy vehicle with deep tread
has been along a gently curving line five times in the wet: two ruts a third of a metre deep with lumpy, torn walls,
mud smeared along them and the tread's ridges across their floors holding water between them; the strip between them
and the verges grassy, with tall dry weeds; leaves and twigs in the mud and on the water; rain ringing the puddles. It
is drawn low over the strip, looking along the ruts, 960 x 720 (landscape, like the owner's picture), and finished.

    python3 "ground - deep ruts in a wet field.py" [WIDTH HEIGHT SAMPLES OUT.png [day]]     (defaults 960 720 64, in the folder you run it from)

With "day" at the end it is drawn under a grey daylight like the owner's picture instead of the stormy evening.

The order of the steps, the same for every ground:
    1. ground.make and ground.wet (how wet the place is: it sets how deep the ruts go and how much water stands)
    2. tracks.ruts (here a heavy vehicle, five passes)
    3. ground.detail near the camera: the ground finely divided and pushed up and down by its soil photographs' heights
       (real lumps and clods, photographed churned mud in the ruts)
    4. grass.grow, then stones.scatter and litter.scatter (after the ground's final shape: nothing grows or lies in mid-air)
    5. ground.fill(yard, ground.spots(yard), rain=...): the water, with rain rings
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
import grass  # noqa: E402
import stones  # noqa: E402
import litter  # noqa: E402
import sky_and_haze  # noqa: E402
import finish  # noqa: E402
import _lines  # noqa: E402

WIDTH = int(sys.argv[1]) if len(sys.argv) > 1 else 960
HEIGHT = int(sys.argv[2]) if len(sys.argv) > 2 else 720
SAMPLES = int(sys.argv[3]) if len(sys.argv) > 3 else 64
OUT = os.path.abspath(sys.argv[4]) if len(sys.argv) > 4 else os.path.join(os.getcwd(), 'ground - deep ruts in a wet field.png')
DAY = len(sys.argv) > 5 and sys.argv[5] == 'day'

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene

# ----------------------------------------------------------------------------------------------- 1. the ground, soaked
LINE = [(0.0, -4.0, 0.0), (0.1, 4.0, 0.0), (0.9, 11.0, 0.0), (2.8, 18.0, 0.0), (6.0, 26.0, 0.0)]
yard = ground.make(size=(16.0, 34.0), location=(1.0, 11.0, 0.0), relief=0.06, seed=8, soil='dry dirt')    # brown earth, soaked
ground.wet(yard, wetness=0.85)

# ----------------------------------------------------------------------------------------------- 2. the ruts
tracks.ruts(yard, LINE, vehicle='tractor', passes=5, age=0.25, seed=3)

way = _lines.Path(_lines.line_points(LINE)).smooth(0.05)

# ----------------------------------------------------------------------------------------------- 3. real lumps near the eye
def close_ground(xy):
    along, across, _ = way.project(xy)
    return ((along < 10.0) & (numpy.abs(across) < 3.0)).astype(float)


ground.detail(yard, area=close_ground, cell=0.015)

# ----------------------------------------------------------------------------------------------- 4. grass, stones, litter


def near_the_camera(xy):
    """Litter and stones show only near the eye: a band along the ruts for the first dozen metres."""
    along, across, _ = way.project(xy)
    return ((along < 13.0) & (numpy.abs(across) < 2.6)).astype(float)


grass.grow(yard, layers=('turf', 'tussocks'), amount=1.6, seed=2)
grass.grow(yard, layers=('weeds',), amount=2.5, seed=9)
stones.scatter(yard, area=near_the_camera, layers=('rocks',), amount=0.25, seed=6)
stones.scatter(yard, area=near_the_camera, layers=('pebbles', 'grit'), amount=0.9, seed=7)
litter.scatter(yard, area=near_the_camera, amount=2.2, seed=4)

# ----------------------------------------------------------------------------------------------- 5. the water, raining
ground.fill(yard, ground.spots(yard), seed=1, rain=0.7)

# ----------------------------------------------------------------------------------------------- sky, light, camera
if DAY:                                                         # grey daylight under heavy cloud, like the owner's picture
    sky_and_haze.photo_sky(scene, 'overcast_soil_puresky', strength=1.0, turn=200.0)
else:
    sky_and_haze.sky(scene, strength=1.1, clouds=1.0, low_band=(0.26, 0.22, 0.19), high_band=(0.09, 0.1, 0.115), top=(0.035, 0.04, 0.05))
sky_and_haze.haze(low=(-50, -10, 0), high=(50, 90, 18), density=0.006, colour=(0.62, 0.66, 0.7))
cloud_light = bpy.data.objects.new('cloud light', bpy.data.lights.new('cloud light', 'AREA'))
cloud_light.data.energy = 0.0 if DAY else 600.0             # by day the photographed sky does all the lighting
cloud_light.data.size = 16.0
cloud_light.data.color = (0.92, 0.92, 0.94)
cloud_light.location = (0.0, 8.0, 10.0)
scene.collection.objects.link(cloud_light)
gap = bpy.data.objects.new('gap in the cloud', bpy.data.lights.new('gap in the cloud', 'SUN'))
gap.data.energy = 0.0 if DAY else 0.5
gap.data.color = (1.0, 0.82, 0.62)
gap.data.angle = math.radians(10.0)
gap.rotation_euler = (math.radians(72.0), 0.0, math.radians(125.0))       # low, ahead and to the left: glints on the wet
scene.collection.objects.link(gap)

camera = bpy.data.objects.new('camera', bpy.data.cameras.new('camera'))
camera.data.lens = 24
camera.location = (0.2, -2.2, 0.62)                            # low over the strip between the ruts
camera.rotation_euler = (Vector((0.9, 9.0, -0.25)) - camera.location).to_track_quat('-Z', 'Y').to_euler()
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
finish.finish(raw, OUT, bloom=0.6, veil=0.2, soften=0.25)
print('drew', OUT)
