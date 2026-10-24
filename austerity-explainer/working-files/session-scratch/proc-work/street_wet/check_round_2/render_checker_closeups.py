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
    'low_far': aw.make_camera('checker_low_far', (-1.5, 14.0, 0.45), look_at=(1.0, 21.0, 0.3), fov_vertical=40.0),
}
scene.render.engine = 'BLENDER_EEVEE'
scene.render.image_settings.file_format = 'PNG'
scene.render.image_settings.color_mode = 'RGB'
scene.eevee.use_raytracing = True
scene.eevee.shadow_ray_count, scene.eevee.shadow_step_count = 4, 16
scene.eevee.taa_render_samples = 24
scene.render.resolution_x, scene.render.resolution_y = 800, 600
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
