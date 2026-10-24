# What this is (plain words): the independent checker's own re-draw of the wet street, from two camera spots the builder never used.
# It opens the builder's street copy (set_copy/street.blend, read only; nothing is saved), draws each spot first as the street is "today" (no wetness layer),
# then puts the builder's wetness layer on (the builder's own tools/apply_wetness_to_set.py, imported, not changed) and draws it wet at the builder's usual
# setting (wetness 0.85, puddles 0.5). EEVEE (the film's plate renderer), ray tracing on, shadow rays 4 / steps 16, like the builder's plate.
# Run: xvfb-run -a blender -b --disable-autoexec -t 2 set_copy/street.blend --python check_round_2/render_checker_closeups.py -- OUT_FOLDER
import os
import sys
import time

import bpy

HERE = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/street_wet/tools'
sys.path.insert(0, HERE)
sys.dont_write_bytecode = True
import apply_wetness_to_set as aw  # noqa: E402

out = sys.argv[sys.argv.index('--') + 1]
os.makedirs(out, exist_ok=True)
scene = bpy.context.scene
spots = {
    # standing in the road, looking at the foot of the LEFT (brick) cottages, pavement, kerb and gutter
    'brick_side': aw.make_camera('checker_brick_side', (1.0, 8.0, 0.9), look_at=(-3.5, 12.0, 0.7), fov_vertical=42.0),
    # crouched low in the left lane, looking up the road toward the colliery gate: puddles and sett shine at a grazing angle
    # (first try used look_at and came out upside down; this one sets the angles by hand, like the film's own main camera)
    'low_far': aw.make_camera('checker_low_far2', (-1.2, 12.0, 0.5), quaternion_wxyz=None, look_at=None, fov_vertical=40.0) if False else None,
    'pavement_graze': None,
}
import math
cam = aw.make_camera('checker_low_far2', (-1.2, 12.0, 0.5), look_at=(0.0, 30.0, 0.3), fov_vertical=40.0)
cam.rotation_mode = 'XYZ'
cam.rotation_euler = (math.radians(91.5), 0.0, math.radians(-3.0))
spots['low_far'] = cam
cam2 = aw.make_camera('checker_pavement_graze', (2.0, 5.0, 0.6), look_at=(3.4, 10.0, 0.1), fov_vertical=45.0)
cam2.rotation_mode = 'XYZ'
cam2.rotation_euler = (math.radians(86.0), 0.0, math.radians(-14.0))
spots['pavement_graze'] = cam2
for k, c in spots.items():
    print('CAMERA', k, tuple(round(v, 2) for v in c.location), 'up vector', tuple(round(v, 2) for v in (c.matrix_world.to_quaternion() @ __import__('mathutils').Vector((0, 1, 0)))), flush=True)
del spots['brick_side']
scene.render.engine = 'BLENDER_EEVEE'
scene.render.image_settings.file_format = 'PNG'
scene.render.image_settings.color_mode = 'RGB'
scene.eevee.use_raytracing = True
scene.eevee.shadow_ray_count, scene.eevee.shadow_step_count = 4, 16
scene.eevee.taa_render_samples = 24
scene.render.resolution_x, scene.render.resolution_y = 720, 540
log = open(os.path.join(out, 'seconds.txt'), 'a')


def draw(name, state):
    scene.camera = spots[name]
    scene.render.filepath = os.path.join(out, f'{name}_{state}.png')
    started = time.time()
    bpy.ops.render.render(write_still=True)
    log.write(f'{name} {state}: {round(time.time() - started, 1)} s\n')
    log.flush()


for name in spots:
    draw(name, 'today')
aw.apply(wetness=0.0, puddles=0.0)
aw.set_state(0.85, 0.5)
for name in spots:
    draw(name, 'wet')
log.write('ALL DONE\n')
log.close()
