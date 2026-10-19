# What this does: builds ONLY the engine house (modules/engine_house.py) on the plain preview floor and takes small test photos of it
# from several angles, then writes out/engine_house_report.json (object count, triangle count, build time, known flaws).
# Views: standard (the tall 9:16 finished-look camera), detail (doorway, lamp, planks, crate), back (rear and right side),
# side (the left wall at a good angle, windows and shed), roof (from above), inside (looking in through the doorway).
# Use: blender -b --disable-autoexec -t 2 --python engine_house_preview.py -- [quick] [view view ...]
#   with no view names it takes standard, detail, back and side. "quick" makes tiny fast photos.
import json
import math
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, 'lib'))
sys.path.insert(0, os.path.join(ROOT, 'modules'))
import bpy
import mine_common as mc
import engine_house

arguments = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
quick = 'quick' in arguments
wanted = [a for a in arguments if a != 'quick'] or ['standard', 'detail', 'back', 'side']

VIEWS = {
    # name: (camera location, look-at point, lens, picture size, sun azimuth, sun elevation)
    'standard': ((-9.5, -21.0, 1.7), (1.0, 2.0, 5.5), 28, (506, 900), 38, 22),
    'detail': ((-5.2, -7.6, 1.9), (-0.3, 0.0, 2.6), 32, (800, 800), 38, 24),
    'back': ((13.0, 21.0, 5.5), (0.0, 6.0, 3.8), 30, (720, 800), 215, 26),
    'side': ((-15.5, 5.0, 2.6), (-4.0, 5.0, 3.0), 28, (900, 640), 300, 24),
    'roof': ((-10.0, -12.0, 12.5), (0.0, 4.5, 6.0), 32, (800, 700), 38, 24),
    'inside': ((-1.2, -6.0, 1.5), (0.8, 3.0, 2.3), 30, (700, 700), 38, 24),
    'lamp': ((-3.5, -3.6, 4.2), (-1.2, -0.3, 5.3), 40, (700, 700), 38, 24),
    'wallclose': ((-8.2, 1.5, 2.3), (-3.9, 4.9, 2.4), 36, (800, 700), 300, 20),
    'doorclose': ((-3.6, -4.8, 2.0), (1.6, 0.0, 2.4), 36, (800, 700), 38, 24),
    'roofclose': ((-7.5, -3.5, 7.4), (-1.5, 3.0, 6.0), 40, (800, 700), 38, 24),
    'threequarter': ((-13.0, -13.0, 3.2), (0.5, 3.5, 3.6), 30, (900, 800), 38, 20),
    'rightclose': ((9.5, 2.0, 2.4), (3.9, 6.0, 2.5), 34, (800, 700), 215, 22),
    'stackclose': ((-2.5, 0.5, 9.5), (0.0, 4.75, 8.0), 40, (800, 700), 38, 24),
    'smallwindow': ((-7.0, 5.5, 2.3), (-3.9, 7.6, 2.5), 40, (800, 700), 300, 20),
    'eaves': ((-7.2, -2.6, 2.0), (-4.2, 0.4, 4.4), 38, (800, 700), 38, 24),
    'ridgeclose': ((-3.5, -6.0, 7.6), (0.0, 0.0, 7.0), 40, (800, 700), 38, 24),
    'cornerclose': ((-7.0, -3.5, 1.2), (-3.9, 0.3, 1.6), 34, (800, 700), 38, 24),
}

mc.clear_scene()
started = time.time()
mc.preview_stage()
result = engine_house.build('Engine house')
build_seconds = time.time() - started
mc.say(f'build finished in {build_seconds:.1f} s')

report = {'object_count': len(result['objects']), 'triangle_count': result['triangle_count'], 'uses_real_displacement': result['displaced'],
          'build_seconds': round(build_seconds, 1), 'known_flaws': engine_house.KNOWN_FLAWS}

os.makedirs(os.path.join(ROOT, 'out'), exist_ok=True)
for name in wanted:
    dusk = name.endswith('_dusk')
    location, target, lens, size, azimuth, elevation = VIEWS[name.replace('_dusk', '')]
    for obj in list(bpy.data.objects):
        if obj.type in ('CAMERA', 'LIGHT'):
            bpy.data.objects.remove(obj)
    if dusk:
        # a moody dusk set-up to judge the glowing windows and lamp: low orange sun from the front-right, dim blue sky
        mc.set_flat_world((0.10, 0.13, 0.20), 0.6)
        mc.set_sun(7, 300, strength=4.0, colour=(1.0, 0.52, 0.22))
    else:
        mc.set_flat_world((0.55, 0.62, 0.72), 0.9)
        mc.set_sun(elevation, azimuth, strength=3.6, colour=(1.0, 0.84, 0.66))
    path = os.path.join(ROOT, 'out', f'engine_house_{name}.png')
    if quick:
        size = (size[0] // 2, size[1] // 2)
    shot_started = time.time()
    mc.render_preview(path, location, target, lens=lens, size=size, samples=10 if quick else 36)
    mc.say(f'{name}: {time.time() - shot_started:.0f} s -> {path}')

with open(os.path.join(ROOT, 'out', 'engine_house_report.json'), 'w') as handle:
    json.dump(report, handle, indent=2)
