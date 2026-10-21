# What this file does (plain words)
# ------------------------------------------------------------------------------------------------------------------------------------------------
# Measures the finished pictures of a folder AGAIN, this time leaving out the dots that lie under a puddle (water at a grazing angle hides what is under it, see section 6 of the study note).
# It needs the pictures (JPEG or PNG) and the joint / stone / road masks of the folder, and the puddle mask pictures (the checking view, names <label>_A_<state>_puddlemask.png) from any
# of the folders given. It writes FOLDER/measurements_nopuddle.json, the same layout as measurements.json plus 'puddle_share' (the share of the road that is puddle).
# Run: python3 -I b15_remeasure_with_puddles.py FOLDER PUDDLE_FOLDER [PUDDLE_FOLDER ...] [--rename-lockout]
#   --rename-lockout: the baseline's lockout pictures are called lockout_A_* (A = the plate lighting): give them the test set's name lockout_B_* too
import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.dont_write_bytecode = True
from b04_measure_joints import measure  # noqa: E402

args = [a for a in sys.argv[1:] if not a.startswith('--')]
folder, puddle_folders = args[0], args[1:]
store = json.load(open(os.path.join(folder, 'measurements.json')))
mask_folders = [folder, os.path.join(folder, '..', 'r03')]
out = {}
for name, old in store.items():
    job = old.get('job') or {}
    picture = next((p for p in (os.path.join(folder, name + '.jpg'), os.path.join(folder, name + '.png')) if os.path.exists(p)), None)
    if picture is None or not job.get('camera') or name.endswith('_puddlemask'):
        continue
    camera = job['camera']
    label = name.split('_')[0]
    mask = next((os.path.join(d, f"mask_{camera}_{job['w']}x{job['h']}.png") for d in mask_folders if os.path.exists(os.path.join(d, f"mask_{camera}_{job['w']}x{job['h']}.png"))), None)
    if label == 'lockout':
        camera_mask_name = f"mask_lockout_{job['w']}x{job['h']}.png"
        mask = next((os.path.join(d, camera_mask_name) for d in mask_folders if os.path.exists(os.path.join(d, camera_mask_name))), mask)
    puddle = None
    if job.get('state') != 'dry':
        for d in puddle_folders:
            candidate = os.path.join(d, f"{label}_A_{job['state']}_puddlemask.png")
            if os.path.exists(candidate):
                puddle = candidate
                break
    if mask is None:
        print('no mask for', name)
        continue
    result = measure(picture, mask, puddles=puddle)
    result['job'] = job
    out[name] = result
    if '--rename-lockout' in sys.argv and name.startswith('lockout_A_'):
        out['lockout_B_' + name.split('_')[2]] = result
json.dump(out, open(os.path.join(folder, 'measurements_nopuddle.json'), 'w'), indent=1)
print('wrote', os.path.join(folder, 'measurements_nopuddle.json'), len(out), 'pictures')
