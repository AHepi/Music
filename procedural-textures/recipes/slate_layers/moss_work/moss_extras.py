# What this file does (plain words)
# ------------------------------------------------------------------------------------------------------------------------------
# Three more checks of the MOSS layer, on the frozen copy of the stack:
#   1. RESOLUTION: the moss mask baked at 512, 1254 and 2508 dots: shrunk to 512 and compared with the 512 picture (same share of moss? same places?). Sizes are in tile
#      units, so the pictures must agree except for edge dots.
#   2. 2 x 2 AREA: the whole finished colour with recipe.tiles_across = 2 (new, non-repeating content): one picture, to look at for seams or repeats.
#   3. TIME: the finished colour at 1254 dots with MOSS in the stack and without it (recipe.stack_order without moss), one after the other, to see what the layer costs.
# Results: ../tests/moss/resolution/, ../tests/moss/area_2x2.png, ../tests/moss/timing.json.   Use: python3 -I moss_extras.py
import json, os, subprocess, sys, time
import cv2
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..'))
BL = ['/home/user/work/blender-app/blender-5.2.2-linux-x64/blender', '-b', '--disable-autoexec', '-t', '2', '--python', os.path.join(ROOT, 'tests', 'bake_tools.py'), '--']
FROZEN = os.path.join(HERE, 'frozen', 'recipe', 'slate_recipe.py')
ONLY = os.path.join(HERE, 'moss_only_recipe.py')
os.makedirs(os.path.join(ROOT, 'tests', 'moss', 'resolution'), exist_ok=True)

def bake(recipe, folder, size, views, params, channels='Colour'):
    t = time.time()
    subprocess.run(BL + [recipe, folder, str(size), '4', json.dumps(views), json.dumps(params), channels], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return time.time() - t

# 1. resolution (moss mask on the flat slate test recipe; the layout and moss are the same code as in the real stack)
work = os.path.join(HERE, 'dev', 'extras')
masks, joints = {}, {}
for size in (512, 1254, 2508):
    seconds = bake(ONLY, os.path.join(work, f'res{size}'), size, {'mask': {'view': 'mask'}, 'joints': {'view': 'joints'}, 'colour': {'view': 'colour'}}, {})
    masks[size] = cv2.imread(os.path.join(work, f'res{size}', 'mask_colour.png'), 0).astype(np.float32) / 255
    joints[size] = cv2.imread(os.path.join(work, f'res{size}', 'joints_colour.png'), 0).astype(np.float32) / 255
    print(f'resolution {size}: baked three views in {seconds:.0f} s', flush=True)
lines = ['| size | share of slate dots that are moss | after shrinking to 512 dots: dots that differ from the 512 bake by more than 0.5 |', '|---|---|---|']
for size in (512, 1254, 2508):
    share = (masks[size][joints[size] > 0.5] > 0.5).mean() * 100
    small = cv2.resize(masks[size], (512, 512), interpolation=cv2.INTER_AREA)
    differ = (np.abs(small - masks[512]) > 0.5).mean() * 100
    lines.append(f'| {size} | {share:.2f} % | {differ:.2f} % |')
text = '\n'.join(lines)
open(os.path.join(ROOT, 'tests', 'moss', 'resolution', 'resolution_table.md'), 'w').write(text + '\n')
print(text, flush=True)
strip = [cv2.resize(cv2.imread(os.path.join(work, f'res{s}', 'colour_colour.png')), (640, 640), interpolation=cv2.INTER_AREA) for s in (512, 1254, 2508)]
labels = ['512 dots', '1254 dots', '2508 dots']
for img, label in zip(strip, labels):
    cv2.putText(img, label, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2, cv2.LINE_AA)
cv2.imwrite(os.path.join(ROOT, 'tests', 'moss', 'resolution', 'resolution_512_1254_2508.png'), np.hstack(strip))

# 2. the 2 x 2 area
seconds = bake(FROZEN, os.path.join(work, 'area'), 1536, {'area': {}}, {'recipe.tiles_across': 2})
img = cv2.imread(os.path.join(work, 'area', 'area_colour.png'))
cv2.imwrite(os.path.join(ROOT, 'tests', 'moss', 'area_2x2.png'), img)
print(f'2 x 2 area at 1536 dots: {seconds:.0f} s', flush=True)

# 3. time with and without moss
timing = {}
for name, params in (('with moss', {}), ('without moss', {'recipe.stack_order': 'colour_and_fade,damage,outline_and_shadow'}), ('with moss again', {})):
    timing[name] = round(bake(FROZEN, os.path.join(work, 'time_' + name.replace(' ', '_')), 1254, {'c': {}}, params), 1)
    print('time', name, timing[name], flush=True)
json.dump(timing, open(os.path.join(ROOT, 'tests', 'moss', 'timing.json'), 'w'), indent=1)
