# What this does: builds the whole coal-mine scene by running the build() of every part in modules/ (ground, engine house,
# headframe, chimney and smoke, track and carts, village and sky), then points the camera, sets the photo settings, and
# takes a portrait photo. It also writes a small report (how long each part took, how many objects and triangles) next to
# the photo. Parts can be left out with --skip or built alone with --only, which is handy for quick checks.
# Use: blender -b --disable-autoexec --python assemble_mine.py -- OUT_PREFIX [--quick] [--samples N] [--width W] [--height H]
#        [--camera x,y,z,tx,ty,tz] [--lens L] [--exposure E] [--only a,b] [--skip a,b] [--save-blend] [--no-render]
import importlib
import json
import math
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, 'lib'))
sys.path.insert(0, os.path.join(HERE, 'modules'))
import bpy
import mine_common as mc

PART_ORDER = ['ground_and_yard', 'engine_house', 'headframe', 'chimney_and_smoke', 'track_and_carts', 'village_and_sky']

arguments = sys.argv[sys.argv.index('--') + 1:]
out_prefix = arguments[0]


def option(name, default=None, cast=str):
    if name in arguments:
        return cast(arguments[arguments.index(name) + 1])
    return default


QUICK = '--quick' in arguments
SAMPLES = option('--samples', 24 if QUICK else 160, int)
WIDTH = option('--width', 540 if QUICK else 1080, int)
HEIGHT = option('--height', int(round(WIDTH * 16 / 9)), int)
LENS = option('--lens', 26.0, float)
EXPOSURE = option('--exposure', 0.4, float)
CAMERA = [float(v) for v in option('--camera', '-14,-25,2.4,0,0,10').split(',')]
ONLY = option('--only', '').split(',') if option('--only') else None
SKIP = option('--skip', '').split(',') if option('--skip') else []

mc.clear_scene()
report = {'parts': {}}
started_all = time.time()
for part in PART_ORDER:
    if (ONLY and part not in ONLY) or part in SKIP:
        continue
    path = os.path.join(HERE, 'modules', part + '.py')
    if not os.path.exists(path):
        mc.say(f'part {part}: file missing, skipped')
        continue
    started = time.time()
    module = importlib.import_module(part)
    try:
        info = module.build('Mine ' + part.replace('_', ' '))
    except Exception as problem:
        import traceback
        traceback.print_exc()
        report['parts'][part] = {'error': str(problem)}
        mc.say(f'part {part}: FAILED {problem}')
        continue
    seconds = time.time() - started
    report['parts'][part] = {'seconds': round(seconds, 1), 'objects': len((info or {}).get('objects', [])), 'notes': (info or {}).get('notes', '')}
    mc.say(f'part {part}: built in {seconds:.1f} s, {report["parts"][part]["objects"]} objects')

def add_engine_house_floor():
    """The ground part digs 7 cm out under the engine house and the engine house builds no floor, so lay a dark plank floor
    just under the sleepers; otherwise the doorway looks onto the void."""
    if ONLY and 'engine_house' not in ONLY:
        return
    floor_material = mc.surface_material('wood', tint=(0.30, 0.26, 0.24), variation=0.2, splash=0.0)
    builder = mc.MeshBuilder('Engine house floor', [floor_material])
    builder.add_polygon([(-3.8, 0.1, -0.02), (3.8, 0.1, -0.02), (3.8, 10.9, -0.02), (-3.8, 10.9, -0.02)], slot=0)
    builder.finish('Mine engine house')


add_engine_house_floor()


def add_front_fill_light():
    """A big, soft, warm light from the camera's side (low in the sky), so the fronts of the buildings and the mud show their
    own warm colours the way the painted reference does, instead of only the cool sky light."""
    if ONLY and len(ONLY) < 3:
        return
    mc.set_sun(38, 35, strength=0.9, colour=(1.0, 0.72, 0.5), name='Warm front fill', angle_degrees=18.0)


add_front_fill_light()
scene = bpy.context.scene
if scene.world is None:
    mc.set_flat_world((0.4, 0.5, 0.6), 1.0)
    mc.set_sun(8, 40, strength=3.0, colour=(1.0, 0.6, 0.35))
    mc.say('no world from the parts: used a plain fallback')

# camera
camera = mc.make_camera(CAMERA[:3], CAMERA[3:6], lens=LENS, name='Photo camera')
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.samples = SAMPLES
scene.cycles.use_adaptive_sampling = True
scene.cycles.adaptive_threshold = 0.015
scene.cycles.use_denoising = True
try:
    scene.cycles.denoiser = 'OPENIMAGEDENOISE'
except Exception:
    pass
scene.cycles.max_bounces = 6
scene.cycles.diffuse_bounces = 3
scene.cycles.glossy_bounces = 4
scene.cycles.transmission_bounces = 4
scene.cycles.sample_clamp_indirect = 8.0
scene.cycles.dicing_rate = 1.0
scene.cycles.offscreen_dicing_scale = 4.0
scene.render.resolution_x, scene.render.resolution_y = WIDTH, HEIGHT
scene.render.resolution_percentage = 100
scene.view_settings.view_transform = 'AgX'
try:
    scene.view_settings.look = 'AgX - Punchy'
except Exception:
    pass
scene.view_settings.exposure = EXPOSURE
scene.render.image_settings.file_format = 'PNG'
scene.render.image_settings.color_depth = '8'
scene.render.filepath = out_prefix + '.png'

triangles = 0
for obj in bpy.data.objects:
    if obj.type == 'MESH':
        triangles += sum(len(p.vertices) - 2 for p in obj.data.polygons)
report['total_objects'] = len(bpy.data.objects)
report['total_triangles_before_displacement'] = triangles
report['build_seconds'] = round(time.time() - started_all, 1)
mc.say(f'built: {report["total_objects"]} objects, {triangles} triangles in {report["build_seconds"]} s')

if '--save-blend' in arguments:
    bpy.ops.wm.save_as_mainfile(filepath=out_prefix + '.blend', compress=True)
    mc.say('saved ' + out_prefix + '.blend')
if '--no-render' not in arguments:
    started = time.time()
    bpy.ops.render.render(write_still=True)
    report['render_seconds'] = round(time.time() - started, 1)
    mc.say(f'rendered {WIDTH}x{HEIGHT} at {SAMPLES} samples in {report["render_seconds"]} s -> {out_prefix}.png')
with open(out_prefix + '.report.json', 'w') as handle:
    json.dump(report, handle, indent=1)
