# What this does (plain words): the transfer run. Draws 3 new cobblestone tiles from the cobblestone model (made by make_cobble_model.py: the only new inputs
# are those numbers), bakes them with the SAME generator, checks they wrap (half-tile shift test on one), times everything and makes a contact sheet.
import json, os, subprocess, sys, time
import numpy as np, cv2
HERE = os.path.dirname(os.path.abspath(__file__))
RECIPE = os.path.abspath(os.path.join(HERE, '..'))
GEN = os.path.join(RECIPE, 'generator')
sys.path.insert(0, GEN)
import sample_description as sd
BLENDER = '/home/user/work/blender-app/blender-5.2.2-linux-x64/blender'
model = json.load(open(os.path.join(GEN, 'sampler_model_cobble.json')))
cells = []
timing = []
for seed in (1, 2, 3):
    t = time.time()
    desc = sd.sample_description(seed, model, grain=0.12, palette_strength=0.5)
    path = os.path.join(HERE, f'description_cobble_{seed}.json')
    json.dump(desc, open(path, 'w'), separators=(',', ':'))
    out = os.path.join(HERE, f'cobble_{seed}')
    subprocess.run([BLENDER, '-b', '--disable-autoexec', '-t', '2', '--python', os.path.join(GEN, 'brick_generator.py'), '--', path, out, '--size', '1254', '--samples', '8'], capture_output=True, text=True)
    bake = json.load(open(os.path.join(out, 'bake.json')))
    timing.append({'seed': seed, 'description_bytes': os.path.getsize(path), 'seconds_total_including_sampling': round(time.time() - t, 1), 'bake_seconds': bake['seconds'], 'shapes': bake['shapes']})
    print(timing[-1], flush=True)
    img = cv2.imread(os.path.join(out, 'colour.png'))
    cells.append(cv2.resize(img, (500, 500), interpolation=cv2.INTER_AREA))
cv2.imwrite(os.path.join(HERE, 'cobble_contact_sheet.png'), np.hstack(cells))
seam = subprocess.run([sys.executable, '-I', os.path.join(GEN, 'seam_test.py'), os.path.join(HERE, 'description_cobble_1.json'), os.path.join(HERE, 'seam_cobble')], capture_output=True, text=True).stdout
print(seam)
json.dump({'tiles': timing, 'seam': json.loads(seam.strip().splitlines()[-1])}, open(os.path.join(HERE, 'transfer_result.json'), 'w'), indent=1)
