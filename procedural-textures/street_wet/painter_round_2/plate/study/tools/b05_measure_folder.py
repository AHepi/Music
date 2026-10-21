# What this file does (plain words)
# ------------------------------------------------------------------------------------------------------------------------------------------------
# After a run of b03_render_jobs.py: measures the joint visibility (b04_measure_joints.py) of every new picture in a folder, adds the result to the folder's
# measurements.json, and (with --convert) turns the picture into a smaller JPEG for looking and deletes the big PNG (the folder budget is small).
# A picture's mask is found through the job file(s): each job names its camera and size, and the mask is mask_<camera>_<w>x<h>.png in the same folder.
# Run: python3 -I b05_measure_folder.py FOLDER JOB_FILE [JOB_FILE ...] [--convert]
import json
import os
import sys

import cv2

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.dont_write_bytecode = True
from b04_measure_joints import measure, table  # noqa: E402

args = [a for a in sys.argv[1:] if not a.startswith('--')]
convert = '--convert' in sys.argv
folder, job_files = args[0], args[1:]
jobs = {}
for jf in job_files:
    for j in json.load(open(jf))['jobs']:
        jobs[j['name']] = j
out_path = os.path.join(folder, 'measurements.json')
store = json.load(open(out_path)) if os.path.exists(out_path) else {}
new_rows = []
for name, job in jobs.items():
    if name.endswith('_puddlemask'):
        continue                      # the checking pictures of the puddle masks stay as they are (PNG, tiny)
    png = os.path.join(folder, name + '.png')
    if not os.path.exists(png):
        continue
    mask = os.path.join(folder, f"mask_{job['camera']}_{job['w']}x{job['h']}.png")
    # puddles: the puddle mask of the same camera and state, if the run drew one (name <label>_A_<state>_puddlemask.png, label = the first word of the picture's name)
    label = name.split('_')[0]
    puddle_file = os.path.join(folder, f"{label}_A_{job['state']}_puddlemask.png")
    result = measure(png, mask, puddles=puddle_file if os.path.exists(puddle_file) else None)
    result['job'] = {k: job.get(k) for k in ('camera', 'light', 'state', 'variant', 'args', 'w', 'h', 'samples')}
    store[name] = result
    new_rows.append((name, result))
    if convert:
        image = cv2.imread(png)
        cv2.imwrite(os.path.join(folder, name + '.jpg'), image, [cv2.IMWRITE_JPEG_QUALITY, 92])
        os.remove(png)
json.dump(store, open(out_path, 'w'), indent=1)
table(new_rows)
