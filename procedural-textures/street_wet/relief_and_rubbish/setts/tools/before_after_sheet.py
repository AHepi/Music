# What this file does (plain words)
# ------------------------------------------------------------------------------------------------------------------------------------------------
# Makes the BEFORE / AFTER sheet of the lighting test set (plain Python, no Blender): for every one of the 22 conditions, the round 2 picture ("before") next to the picture
# with the JOINTS layer ("after"), cropped to the road, with the joint visibility numbers written over each picture (near contrast / share of joint dots "seen", and PASS or FAIL).
# The study's pass line and measure are used unchanged (study/tools/b09_lighting_test_set.py, b04_measure_joints.py).
# Use:  python3 -I before_after_sheet.py FOLDER OUT.jpg [--before before] [--after after] [--cell 400] [--only main,close,lockout] [--heading "text"]
#   FOLDER holds the pictures (JPEG, named <camera>_<light>_<state>_<variant tag>.jpg, for example main_A_wet_before.jpg) and measurements.json made by the runner;
#   --before and --after are the variant tags (default before and after). Any two tags can be put side by side (for example mild and strong).
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
STUDY_TOOLS = os.path.abspath(os.path.join(HERE, '..', '..', 'study', 'tools'))
sys.path.insert(0, STUDY_TOOLS)
sys.dont_write_bytecode = True
from b08_sheets import sheet  # noqa: E402
from b09_lighting_test_set import FULL, judge  # noqa: E402

# the part of each picture that holds the road (box in the picture's own dots)
CROPS = {'main': (0, 500, 540, 960), 'close': (0, 0, 640, 480), 'lockout': (0, 560, 540, 960)}
LIGHT_NAMES = {'A': 'dusk lamps', 'B': 'brazier', 'C': 'side light', 'D': 'overhead', 'E': 'from behind'}
STATE_NAMES = {'dry': 'dry', 'wet': 'wet', 'heavy': 'heavy'}
CAMERA_NAMES = {'main': 'street', 'close': 'close', 'lockout': 'lockout'}


def note(measure, label):
    if measure is None:
        return 'not drawn'
    ok, _ = judge(measure, label)
    n, m = measure['near'], measure['middle']
    f = lambda e, k: 'n/a' if e[k] is None else f'{e[k]:.2f}'   # noqa: E731
    return f"near {f(n, 'contrast')}/{f(n, 'seen')}  mid {f(m, 'contrast')}/{f(m, 'seen')}  {'PASS' if ok else 'FAIL'}"


def build(folder, out, before='before', after='after', cell=400, only=None, heading=None):
    store = json.load(open(os.path.join(folder, 'measurements.json')))
    cells = []
    for label, rows in FULL.items():
        if only and label not in only:
            continue
        for light, states in rows:
            for state in states:
                for tag in (before, after):
                    name = f'{label}_{light}_{state}_{tag}'
                    path = os.path.join(folder, name + '.jpg')
                    if not os.path.exists(path):
                        continue
                    title = f"{CAMERA_NAMES[label]} {LIGHT_NAMES[light]} {STATE_NAMES[state]} {'BEFORE' if tag == before else 'AFTER'}"
                    cells.append((title, note(store.get(name), label), path, CROPS[label]))
    sheet(out, cells, columns=4, cell_width=cell, heading=heading or 'Joints between the setts, every picture of the lighting test set: round 2 (before) and with the JOINTS layer (after). '
          'Numbers: joint contrast / share of joint dots seen, near and middle road (puddle dots left out); PASS / FAIL against the study pass line')


if __name__ == '__main__':
    argv = sys.argv[1:]
    opt = lambda key, default=None: argv[argv.index(key) + 1] if key in argv else default   # noqa: E731
    build(argv[0], argv[1], before=opt('--before', 'before'), after=opt('--after', 'after'), cell=int(opt('--cell', 400)), only=opt('--only').split(',') if opt('--only') else None,
          heading=opt('--heading'))
