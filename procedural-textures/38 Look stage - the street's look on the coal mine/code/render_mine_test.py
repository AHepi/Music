"""
What this file does:
The transfer test. It opens the coal-mine scene (built by other sessions, never seen by the street bundle),
draws it once as it is, then drops the look stage on it and draws it again with the same camera, so the
two pictures differ only by the look. A third picture adds the standing-person camera rule.

    python3 render_mine_test.py [variant ...]      variants: as_is, look, look_person  (default: all)

Writes mine-A-as-is.png, mine-B-look.png, mine-C-look-person.png and a times.json next to this file.
"""

import json
import os
import sys
import time

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import look_stage  # noqa: E402

SCENE_FILE = os.path.join(HERE, 'mine-as-is.blend')
WIDTH, HEIGHT = 540, 960
SAMPLES = 32
variants = sys.argv[1:] or ['as_is', 'look', 'look_person']
times = {}
if os.path.exists(os.path.join(HERE, 'times.json')):
    times = json.load(open(os.path.join(HERE, 'times.json')))


def open_scene():
    bpy.ops.wm.open_mainfile(filepath=SCENE_FILE)
    return bpy.context.scene


def render_to(path):
    scene = bpy.context.scene
    scene.render.filepath = path
    started = time.time()
    bpy.ops.render.render(write_still=True)
    return time.time() - started


if 'as_is' in variants:
    scene = open_scene()
    scene.render.resolution_x, scene.render.resolution_y = WIDTH, HEIGHT
    scene.cycles.samples = SAMPLES
    scene.cycles.use_denoising = True
    seconds = render_to(os.path.join(HERE, 'mine-A-as-is.png'))
    times['A as is'] = round(seconds, 1)
    print('A as is:', round(seconds, 1), 's')
    json.dump(times, open(os.path.join(HERE, 'times.json'), 'w'), indent=2)

if 'look' in variants:
    scene = open_scene()
    report = look_stage.apply_look(scene, samples=SAMPLES, resolution=(WIDTH, HEIGHT))
    print('look report:', json.dumps(report, default=str))
    seconds = render_to(os.path.join(HERE, 'mine-B-look.png'))
    times['B look'] = round(seconds, 1)
    print('B look:', round(seconds, 1), 's')
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'mine-B-look.blend'))
    json.dump(times, open(os.path.join(HERE, 'times.json'), 'w'), indent=2)

if 'look_person' in variants:
    scene = open_scene()
    report = look_stage.apply_look(scene, samples=SAMPLES, resolution=(WIDTH, HEIGHT), camera_like_a_person=True)
    print('look+person report:', json.dumps(report, default=str))
    seconds = render_to(os.path.join(HERE, 'mine-C-look-person.png'))
    times['C look + person camera'] = round(seconds, 1)
    print('C look + person camera:', round(seconds, 1), 's')
    json.dump(times, open(os.path.join(HERE, 'times.json'), 'w'), indent=2)
