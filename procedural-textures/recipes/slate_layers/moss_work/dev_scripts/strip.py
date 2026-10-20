# What this file does (plain words)
# ------------------------------------------------------------------------------------------------------------------------------
# Makes ONE "what does this setting do" strip for the MOSS layer: it bakes the moss layer (alone on a flat slate colour, or with the real colour layer
# under it and the damage layer over it) once for each of several values of one setting, and joins the small pictures into one labelled strip.
# It can also print the share of slate dots the moss covers for each picture (bakes the Mask as well).
# With --real the REAL recipe (all layers) is baked instead: then --paint, --damage and the 'view' key of a variant have no meaning.
# Use (plain python, not Blender):
#   python3 -I strip.py OUT_PNG TITLE SIZE 'JSON {label: {setting: value, ...}}' [--base 'JSON'] [--columns N] [--cell 384] [--paint] [--damage] [--share] [--crop x0 y0 x1 y1]
# Settings are named like the recipe's: moss.coverage, moss.drip_length ... Extra recipe parameters: damage (true), base ('flat' or 'paint'), order ('moss_on_top').
import json, os, subprocess, sys, shutil, tempfile
import cv2
import numpy as np
here = os.path.dirname(os.path.abspath(__file__))
work = os.path.abspath(os.path.join(here, '..'))
args = sys.argv[1:]
def take(flag, default=None, count=1):
    if flag in args:
        i = args.index(flag)
        vals = args[i + 1:i + 1 + count]
        del args[i:i + 1 + count]
        return vals if count != 1 else vals[0]
    return default
def take_flag(flag):
    if flag in args:
        args.remove(flag)
        return True
    return False
base = json.loads(take('--base', '{}'))
columns = int(take('--columns', 0) or 0)
cell = int(take('--cell', 384))
crop = take('--crop', None, 4)
paint, damage, share = take_flag('--paint'), take_flag('--damage'), take_flag('--share')
real = take_flag('--real')          # use the real recipe (all layers, recipe/slate_recipe.py) instead of the moss-only test recipe
out_png, title, size, variants = args[0], args[1], int(args[2]), json.loads(args[3])
if paint and not real: base['base'] = 'paint'
if damage and not real: base['damage'] = True
os.makedirs(os.path.join(work, 'dev'), exist_ok=True)
folder = tempfile.mkdtemp(prefix='moss_strip_', dir=os.path.join(work, 'dev'))
keys = {label: f'v{i:02d}' for i, label in enumerate(variants)}
views = {f'{keys[l]}_colour': (dict(extra) if real else dict({'view': 'colour'}, **extra)) for l, extra in variants.items()}
blender = [os.path.join(work, '..', 'tests', 'blender.sh'), os.path.join(work, '..', 'tests', 'bake_tools.py'), '--',
           os.path.join(work, '..', 'recipe', 'slate_recipe.py') if real else os.path.join(work, 'moss_only_recipe.py'), folder, str(size), '4']
subprocess.run(blender + [json.dumps(views), json.dumps(base), 'Colour'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
shares = {}
if share:
    extra_views = {f'{keys[l]}_mask': dict(extra, view='mask') for l, extra in variants.items()}
    extra_views['joints'] = dict(view='joints')
    subprocess.run(blender + [json.dumps(extra_views), json.dumps(base), 'Colour'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    joints = cv2.imread(f'{folder}/joints_colour.png', 0)
    for l in variants:
        m = cv2.imread(f'{folder}/{keys[l]}_mask_colour.png', 0)
        shares[l] = (m[joints > 127] > 127).mean()
cells = []
for l in variants:
    pic = cv2.imread(f'{folder}/{keys[l]}_colour_colour.png')
    if pic is None:
        print('MISSING', l); continue
    if crop:
        x0, y0, x1, y1 = [int(float(v) * size) for v in crop]
        pic = pic[y0:y1, x0:x1]
    scale = cell / pic.shape[1]
    pic = cv2.resize(pic, (cell, int(pic.shape[0] * scale)), interpolation=cv2.INTER_AREA)
    banner = np.full((30, cell, 3), 245, np.uint8)
    text = l + (f'   ({shares[l] * 100:.0f}% covered)' if l in shares else '')
    cv2.putText(banner, text[:46], (6, 21), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (20, 20, 20), 1, cv2.LINE_AA)
    cells.append(np.vstack([banner, pic]))
columns = columns or len(cells)
blank = np.full_like(cells[0], 255)
while len(cells) % columns:
    cells.append(blank)
rows = [np.hstack(cells[i:i + columns]) for i in range(0, len(cells), columns)]
grid = np.vstack(rows)
header = np.full((38, grid.shape[1], 3), 255, np.uint8)
cv2.putText(header, title, (8, 27), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 0, 0), 2, cv2.LINE_AA)
os.makedirs(os.path.dirname(out_png), exist_ok=True)
cv2.imwrite(out_png, np.vstack([header, grid]))
shutil.rmtree(folder, ignore_errors=True)
print(out_png)
