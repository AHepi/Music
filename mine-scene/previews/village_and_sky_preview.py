# What this does: builds ONLY the village, hills, sky and lights (modules/village_and_sky.py) on top of a plain stand-in ground
# (the real ground comes from another part), and takes small test photos from several angles, then writes
# out/village_and_sky_report.json (object count, triangle count, build time, known flaws).
# Views: standard (the tall 9:16 finished-look camera), detail (close on the houses), back (from behind the village looking at the mine side),
# side (from the left across the yard), street (down the lamp-lit street), plan (from high above), sky (wide view of the hills and sky).
# Use: blender -b --disable-autoexec -t 2 --python village_and_sky_preview.py -- [quick] [view view ...]
#   with no view names it takes standard, detail and back. "quick" makes tiny fast photos.
import json
import math
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, 'lib'))
sys.path.insert(0, os.path.join(ROOT, 'modules'))
import numpy as np
import bpy
import mine_common as mc
import village_and_sky

arguments = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
quick = 'quick' in arguments
no_village = 'novillage' in arguments
wanted = [a for a in arguments if a not in ('quick', 'novillage')] or ['standard', 'detail', 'back']

VIEWS = {
    # name: (camera location, look-at point, lens, picture size, samples)
    'standard': ((-9.5, -21.0, 1.7), (1.0, 2.0, 5.5), 28, (506, 900), 40),
    'detail': ((8.0, 2.0, 2.2), (28.0, 22.0, 5.0), 40, (900, 700), 36),
    'back': ((46.0, 68.0, 22.0), (25.0, 22.0, 4.0), 30, (900, 700), 36),
    'side': ((-14.0, 14.0, 2.6), (26.0, 24.0, 4.5), 28, (900, 640), 36),
    'street': ((20.0, 3.0, 2.0), (30.0, 22.0, 3.5), 30, (700, 900), 36),
    'plan': ((29.0, 22.0, 110.0), (29.0, 22.0, 0.0), 40, (800, 800), 24),
    'sky': ((0.0, -10.0, 2.0), (60.0, 60.0, 14.0), 22, (1200, 600), 30),
    'wide': ((-9.5, -21.0, 1.7), (1.0, 2.0, 5.5), 18, (900, 900), 30),
    'left': ((-9.5, -21.0, 1.7), (-70.0, 30.0, 8.0), 24, (900, 640), 24),
    'behind': ((-9.5, -21.0, 1.7), (30.0, 100.0, 8.0), 24, (900, 640), 24),
}


def stand_in_ground():
    """A plain muddy floor that follows the shared ground_height, standing in for the real ground."""
    xs = np.arange(-60.0, 70.0, 2.0)
    ys = np.arange(-60.0, 70.0, 2.0)
    vertices = [(x, y, mc.ground_height(x, y) - 0.03 if math.hypot(x - 4.0, y - 4.0) < 60.0 else mc.ground_height(4.0 + 60.0 * (x - 4.0) / math.hypot(x - 4.0, y - 4.0), 4.0 + 60.0 * (y - 4.0) / math.hypot(x - 4.0, y - 4.0)) - 0.03) for y in ys for x in xs]
    faces = []
    for j in range(len(ys) - 1):
        for i in range(len(xs) - 1):
            a = j * len(xs) + i
            faces.append((a, a + 1, a + 1 + len(xs), a + len(xs)))
    mesh = bpy.data.meshes.new('Stand-in ground')
    mesh.from_pydata(vertices, [], faces)
    obj = bpy.data.objects.new('Stand-in ground', mesh)
    bpy.context.scene.collection.objects.link(obj)
    mesh.materials.append(mc.plain_material('Stand-in mud', (0.16, 0.11, 0.08), roughness=0.9))
    return obj


mc.clear_scene()
started = time.time()
stand_in_ground()
result = village_and_sky.build('Village and sky', with_village=not no_village)
build_seconds = time.time() - started
mc.say(f'build finished in {build_seconds:.1f} s: ' + result['notes'])

report = {'object_count': len(result['objects']), 'triangle_count': result['triangle_count'], 'uses_real_displacement': [],
          'build_seconds': round(build_seconds, 1), 'known_flaws': village_and_sky.KNOWN_FLAWS}
os.makedirs(os.path.join(ROOT, 'out'), exist_ok=True)
scene = bpy.context.scene
exposure = village_and_sky.RECOMMENDED_EXPOSURE
for name in wanted:
    location, target, lens, size, samples = VIEWS[name]
    for obj in list(bpy.data.objects):
        if obj.type == 'CAMERA':
            bpy.data.objects.remove(obj)
    if quick:
        size = (size[0] // 2, size[1] // 2)
        samples = 12
    scene.view_settings.exposure = exposure
    try:
        scene.view_settings.look = 'AgX - Punchy'
    except Exception:
        pass
    path = os.path.join(ROOT, 'out', f'village_and_sky_{name}.png')
    mc.render_preview(path, location, target, lens=lens, size=size, samples=samples)
    mc.say('photo ' + path)
with open(os.path.join(ROOT, 'out', 'village_and_sky_report.json'), 'w') as handle:
    json.dump(report, handle, indent=1)
