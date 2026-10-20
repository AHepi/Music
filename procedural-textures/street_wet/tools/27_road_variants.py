# What this does (plain words)
# ------------------------------------------------------------------------------------------------------------------------------------------------
# Round 2: draws the main camera view with EEVEE (the plate's renderer, ray tracing on, the round 2 shadow cure: shadow_ray_count 4 / shadow_step_count 16) for the street as it is
# today and for several wet settings of the road and pavement, so their brightness and speckle can be compared (tools/22b_numbers.py). The checker's aims: wet road about 1.5
# times today's brightness (round 1 had 2.0 in Cycles), speckle (grain) under 0.008 on the road's left, middle and right thirds, pavement flags that still catch the lamp glow.
# Each variant sets, for the road (street_setts) and the pavement (pavement_flags): Wet Roughness, Specular Boost, Film Coat. The variants are written in VARIANTS below.
# Run: xvfb-run -a blender -b --disable-autoexec -t 2 set_copy/street.blend --python tools/27_road_variants.py -- OUT_FOLDER SAMPLES [variant ...]
# Writes OUT_FOLDER/main_<variant>.png (variant 'today' = nothing added) and seconds.txt
import os
import sys
import time

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.dont_write_bytecode = True
import apply_wetness_to_set as aw  # noqa: E402

# name: {material: (wet roughness, specular boost, film coat)}
VARIANTS = {
    'wet_a': {'street_setts': (0.30, 0.25, 0.30), 'pavement_flags': (0.35, 0.25, 0.30)},      # round 2 as first set up
    'wet_b': {'street_setts': (0.40, 0.15, 0.20), 'pavement_flags': (0.35, 0.20, 0.25)},      # calmer road
    'wet_c': {'street_setts': (0.35, 0.20, 0.25), 'pavement_flags': (0.35, 0.20, 0.25)},      # in between
}
args = sys.argv[sys.argv.index('--') + 1:]
out_folder, samples = args[0], int(args[1])
wanted = args[2:] or ['today', 'wet_a', 'wet_b']
os.makedirs(out_folder, exist_ok=True)
scene = bpy.context.scene
aw.cameras()
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x, scene.render.resolution_y = 540, 960
scene.render.image_settings.file_format = 'PNG'
scene.render.image_settings.color_mode = 'RGB'
scene.eevee.taa_render_samples = samples
scene.eevee.use_raytracing = True
scene.eevee.shadow_ray_count, scene.eevee.shadow_step_count = 4, 16
seconds = {}
applied = False
for variant in wanted:
    if variant != 'today' and not applied:
        aw.apply(wetness=0.85, puddles=0.5)
        applied = True
    if variant in VARIANTS:
        for material_name, (rough, boost, coat) in VARIANTS[variant].items():
            node = aw.APPLIED[material_name][0]
            node.inputs['Wet Roughness'].default_value, node.inputs['Specular Boost'].default_value, node.inputs['Film Coat'].default_value = rough, boost, coat
        aw.set_state(0.85, 0.5)
    elif variant == 'dry':
        aw.set_state(0.0, 0.0)
    scene.render.filepath = os.path.join(out_folder, f'main_{variant}.png')
    started = time.time()
    bpy.ops.render.render(write_still=True)
    seconds[variant] = round(time.time() - started, 1)
    print('DRAWN', variant, seconds[variant], 's', flush=True)
open(os.path.join(out_folder, 'seconds.txt'), 'w').write(str(seconds) + '\n')
