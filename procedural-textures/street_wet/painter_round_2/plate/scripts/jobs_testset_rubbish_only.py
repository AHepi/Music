# What this does (plain words): writes the job files for the LIGHTING TEST SET (the study's 22 fixed pictures) drawn ONE way only: the final look (JOINTS and the new rubbish at the new defaults).
# It is rubbish/tools/jobs_testset.py with the look list cut down to "rubbish" (the earlier two looks, round 2 and joints-only, were measured in round 1 and are not needed again).
# Use: python3 -I jobs_testset_rubbish_only.py FOLDER_NAME [dial=value ...]
import os, sys
sys.path.insert(0, 'proc-work/street_wet/painter_round_2/plate/rubbish/tools')
import write_jobs as wj
from b09_lighting_test_set import SETS, CAMERAS
BASE = 'proc-work/street_wet/painter_round_2/plate/rubbish/work/'
name = sys.argv[1]
dials = {k: float(v) for k, v in (a.split('=') for a in sys.argv[2:] if '=' in a)}
OUT = BASE + name
count = 0
for kind in ('street', 'lockout'):
    pictures, sizes = [], set()
    for label, rows in SETS['full'].items():
        if CAMERAS[label]['file'] != kind:
            continue
        for light, states in rows:
            for state in states:
                pictures.append(wj.pic(label, light, state, 'rubbish', dials=dials or None))
                count += 1
        sizes.add((label, CAMERAS[label]['w'], CAMERAS[label]['h']))
    print(wj.write(OUT, kind, pictures, joint_masks=sorted(sizes), ground_masks=sorted(sizes)))
print('pictures', count)
