# What this file does (plain words)
# ------------------------------------------------------------------------------------------------------------------------------------------------
# Small helpers that write JOB FILES for rubbish_runner.py (the list of pictures one Blender run draws). A job file is plain JSON; these helpers only save typing.
# Cameras are named by a short LABEL: main (the street camera, 540 x 960 in the test set), close (the low view, 640 x 480), lockout (the lockout plate camera, 540 x 960).
# Use inside another script:  import write_jobs as wj; wj.write('/path/out', 'street', pictures=[wj.pic('main', 'A', 'wet', 'rubbish')], ...)
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
STUDY_TOOLS = os.path.abspath(os.path.join(HERE, '..', '..', 'study', 'tools'))
sys.path.insert(0, STUDY_TOOLS)
sys.dont_write_bytecode = True
from b09_lighting_test_set import CAMERAS, SETS  # noqa: E402

CAMERA_NAME = {'main': 'main', 'close': 'close_road', 'lockout': 'lockout', 'gutter': 'gutter_close', 'wall': 'wall_close', 'doorstep': 'doorstep_close', 'leftgutter': 'left_gutter_close', 'drum': 'drum_close'}
SIZES = {'main': (540, 960, 16), 'close': (640, 480, 24), 'lockout': (540, 960, 16), 'gutter': (960, 720, 24), 'wall': (960, 720, 24), 'doorstep': (960, 720, 24), 'leftgutter': (960, 720, 24), 'drum': (960, 720, 24)}
PLATE = {'main': (1536, 2730, 48), 'close': (1920, 1440, 48), 'lockout': (1536, 2730, 48)}


def pic(label, light, state, look, dials=None, size=None, name=None, view='beauty', dirt=None, **extra):
    w, h, samples = size or SIZES[label]
    job = dict(name=name or f'{label}_{light}_{state}_{look}', camera=CAMERA_NAME[label], light=light, state=state, w=w, h=h, samples=samples, look=look, view=view)
    if dials:
        job['dials'] = dials
    if dirt is None:
        dirt = (look == 'rubbish' and view == 'beauty')
    if dirt:
        job['dirt'] = True
    job.update(extra)
    return job


def write(folder, kind, pictures, joint_masks=(), ground_masks=(), puddle_masks=True, filename=None):
    """pictures: list of jobs (see pic). joint_masks / ground_masks: lists of (label, w, h) for the joint measuring masks (Cycles) and the ground masks. With puddle_masks, a puddle mask picture is
    added for every (camera label, wet state, size) of a beauty picture, named <label>_A_<state>_puddlemask (the name the study's measure expects)."""
    os.makedirs(folder, exist_ok=True)
    jobs = list(pictures)
    seen = set()
    if puddle_masks:
        for p in pictures:
            if p.get('view', 'beauty') == 'beauty' and p['state'] != 'dry':
                key = (p['camera'], p['state'], p['w'], p['h'])
                if key in seen:
                    continue
                seen.add(key)
                label = {v: k for k, v in CAMERA_NAME.items()}[p['camera']]
                jobs.append(dict(name=f"{label}_A_{p['state']}_{p['w']}x{p['h']}_puddlemask", camera=p['camera'], light='A', state=p['state'], w=p['w'], h=p['h'], samples=4, look='joints', view='puddles'))
    masks = [[CAMERA_NAME[l], w, h] for l, w, h in joint_masks]
    grounds = [[CAMERA_NAME[l], w, h] for l, w, h in ground_masks]
    path = os.path.join(folder, filename or f'jobs_{kind}.json')
    json.dump(dict(kind=kind, masks=masks, ground_masks=grounds, jobs=jobs), open(path, 'w'), indent=1)
    return path
