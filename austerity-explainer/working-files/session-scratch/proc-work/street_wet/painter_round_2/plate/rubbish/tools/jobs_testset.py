# What this file does (plain words)
# ------------------------------------------------------------------------------------------------------------------------------------------------
# Writes the job files for the LIGHTING TEST SET (the study's 22 fixed pictures: 3 cameras x 5 lightings x dry / wet / heavy, see study/tools/b09_lighting_test_set.py) drawn THREE ways each:
#     round2   the street as round 2 left it (no JOINTS, no rubbish)         joints   with the JOINTS layer (the setts' round)         rubbish   joints plus the rubbish (dials as given)
# plus everything the measuring needs: the joint measuring masks (Cycles), the ground masks, the puddle masks, and for every rubbish picture its rubbish mask ("_dirt").
# Use: python3 -I jobs_testset.py FOLDER_NAME [dial=value ...]       (dials given are used for the rubbish pictures; folder = rubbish/work/FOLDER_NAME)
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import write_jobs as wj
from b09_lighting_test_set import SETS, CAMERAS
BASE = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/street_wet/painter_round_2/plate/rubbish/work/'
name = sys.argv[1]
dials = {k: float(v) for k, v in (a.split('=') for a in sys.argv[2:] if '=' in a)}
OUT = BASE + name
for kind in ('street', 'lockout'):
    pictures, sizes = [], set()
    for label, rows in SETS['full'].items():
        if CAMERAS[label]['file'] != kind:
            continue
        for light, states in rows:
            for state in states:
                for look in ('round2', 'joints', 'rubbish'):
                    pictures.append(wj.pic(label, light, state, look, dials=dials if look == 'rubbish' else None))
        sizes.add((label, CAMERAS[label]['w'], CAMERAS[label]['h']))
    print(wj.write(OUT, kind, pictures, joint_masks=sorted(sizes), ground_masks=sorted(sizes)))
