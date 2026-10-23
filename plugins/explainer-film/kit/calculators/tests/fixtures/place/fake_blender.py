#!/usr/bin/env python3
# What this does: a STAND-IN for Blender, used by the variations tests when no Blender is needed. It is started the way the real program is started for one variations job
#   fake_blender.py -b --disable-autoexec --python-exit-code 1 SCENE.blend --python .../blender_run.py -- variations-worker --job JOB.json --where on-card
# and it writes what the real worker writes (place_kit/variations/worker.py): one small picture for each camera of each variation, NN_<name>.json for each variation and job-result.json.
# The pictures are made from the variation's settings: every number changes the brightness, the numbers of dials.rubbish.* and amount.rubbish change nothing (so the tests have a setting
# that "does not show"), and a variation called "broken" fails. No Blender, no bpy: Python with Pillow only.
import json
import os
import sys
import time

from PIL import Image

arguments = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
job = json.load(open(arguments[arguments.index('--job') + 1], encoding='utf-8'))
kit_folder = os.environ.get('FAKE_BLENDER_KIT')
if kit_folder:
    sys.path.insert(0, kit_folder)
from place_kit.variations import keys  # noqa: E402

store = os.environ.get('FAKE_CARD_STORE')


def mapped(path):
    """/workspace means the fake card's store folder (the same mapping the fake command client uses). Without a store the stand-in refuses to write there: a test must never make /workspace."""
    if path.startswith('/workspace'):
        if not store:
            sys.exit('the fake worker refuses to write under /workspace: set FAKE_CARD_STORE to a temporary folder')
        return path.replace('/workspace', store, 1)
    return path


out = mapped(job['out_folder'])
os.makedirs(out, exist_ok=True)
width, height = job.get('size') or [96, 64]
cameras = job.get('cameras') or ['Camera A']
results = []
for position, entry in enumerate(job['entries'], 1):
    shown = {k: v for k, v in entry['set'].items() if not k.startswith(('dials.rubbish', 'amount.rubbish'))}
    brightness = 90 + 60 * sum(float(v) for v in shown.values() if isinstance(v, (int, float)))
    brightness += 25 * sum(1 for v in shown.values() if v == 'wet') + 10 * sum(float(v) for v in (entry.get('args') or {}).values() if isinstance(v, (int, float)))
    ok = entry['name'] != 'broken'
    pictures = []
    for slot, camera in enumerate(cameras):
        if not ok:
            break
        image = Image.new('RGB', (width, height))
        pixels = image.load()
        for x in range(width):
            for y in range(height):
                shade = max(0, min(255, int(brightness + 40 * ((x + 7 * slot) % 16) / 16.0 + 30 * y / height)))
                pixels[x, y] = (shade, max(0, shade - 20), max(0, shade - 40))
        name = f'{keys.file_label(position, entry["name"])}__{keys.file_word(camera)}.jpg'
        image.save(os.path.join(out, name), 'JPEG', quality=90)
        pictures.append({'camera': camera, 'file': name, 'engine': 'CYCLES', 'width': width, 'height': height, 'samples': 4, 'seconds': 0.1, 'bytes': os.path.getsize(os.path.join(out, name)), 'ok': True, 'mean_luminance': 0.4})
    result = {'name': entry['name'], 'is_baseline': entry.get('is_baseline', False), 'set': entry['set'], 'args': entry.get('args') or {}, 'script': entry.get('script'), 'notes': [] if ok else ['the fake worker was told to fail'],
              'pictures': pictures, 'ok': ok, 'reset': 'restored exactly', 'seconds_apply': 0.0, 'seconds_draw': 0.1, 'seconds_reset': 0.0}
    json.dump(result, open(os.path.join(out, keys.file_label(position, entry['name']) + '.json'), 'w'), indent=1)
    results.append(result)
summary = {'job': job.get('job'), 'scene': os.path.basename(job['scene']), 'blender': 'fake', 'device': 'fake card', 'engine': 'CYCLES', 'engine_reasons': ['the fake worker'], 'size': [width, height], 'samples': 4,
           'where': 'card', 'cameras': cameras, 'seconds_in_all': 0.5, 'reopened': 0, 'entries': [r['name'] for r in results], 'ok': all(r['ok'] for r in results)}
json.dump(summary, open(os.path.join(out, 'job-result.json'), 'w'), indent=1)
print('PASS fake worker: job', job.get('job'), len(results), 'variation(s)')
sys.exit(0 if summary['ok'] else 1)
