# What this does (plain words): STUDY ONLY, saves nothing in the scene. Draws the saved Japanese courtyard three ways on the rented machine:
#   1. Cycles (the courtyard's own slow renderer, the way the final photo was made), 2. EEVEE (the fast renderer the film's plates use) as it is,
#   3. EEVEE after the generic do-nothing hook (see c6_hook_test.py) is put in front of every weatherable material.
# It answers: does the courtyard draw in EEVEE, does it look like the Cycles photo, how long does it take, and does the hook still change nothing in EEVEE?
# Run (on the rented machine): /workspace/blender/blender -b --disable-autoexec courtyard_final.blend --python c9_eevee_courtyard.py -- OUT_FOLDER WIDTH SAMPLES
import os, sys, time
import bpy
args = sys.argv[sys.argv.index('--') + 1:]
OUT, WIDTH, SAMPLES = args[0], int(args[1]), int(args[2]); KEEP = (OUT, WIDTH, SAMPLES)
os.makedirs(OUT, exist_ok=True)
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, 'c6_hook_test.py')).read().split('# ---------------------------------------------------------------- render settings')[0]
sys.argv = [sys.argv[0], '--', os.path.join(OUT, 'x')]          # c6's header reads its own arguments
exec(compile(src, 'c6_hook_part', 'exec'))
OUT, WIDTH, SAMPLES = KEEP        # (c6's header reused these names for its own small defaults; put ours back)
scene = bpy.context.scene
r = scene.render; r.resolution_x = WIDTH; r.resolution_y = int(WIDTH * 2 / 3); r.resolution_percentage = 100
r.image_settings.file_format = 'PNG'; r.image_settings.color_mode = 'RGB'; r.image_settings.color_depth = '8'
def draw(name):
    t = time.time(); r.filepath = os.path.join(OUT, name + '.png'); bpy.ops.render.render(write_still=True)
    open(os.path.join(OUT, name + '_seconds.txt'), 'w').write('%.1f' % (time.time() - t))
# 1. Cycles on the card
scene.render.engine = 'CYCLES'; scene.cycles.samples = SAMPLES; scene.cycles.use_denoising = True
try: scene.cycles.device = 'GPU'
except Exception: pass
draw('cycles')
# 2. EEVEE as it is (the same settings the street's plate script uses)
scene.render.engine = 'BLENDER_EEVEE'
scene.eevee.taa_render_samples = SAMPLES; scene.eevee.use_raytracing = True
scene.eevee.shadow_ray_count, scene.eevee.shadow_step_count = 4, 16
if hasattr(scene.eevee, 'shadow_pool_size') and WIDTH > 1080:
    scene.eevee.shadow_pool_size = '1024'; scene.eevee.shadow_resolution_scale = min(1.0, 1080 / WIDTH)
draw('eevee_plain')
# 3. EEVEE after the hook
apply_hook(True)
draw('eevee_hooked')
print('C9 DONE', {k: len(v) for k, v in stats.items()})
