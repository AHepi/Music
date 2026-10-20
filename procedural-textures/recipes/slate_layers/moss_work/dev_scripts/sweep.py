# What this file does (plain words): bakes the moss layer (alone, on flat slate) for several values of ONE setting (or several named variants),
# prints the covered share for each, and joins the colour pictures into one labelled contact sheet.
# Use: python3 -I sweep.py NAME SIZE SETTING v1 v2 v3 ...      (SETTING like moss.coverage)
#   or python3 -I sweep.py NAME SIZE --variants 'JSON {label: {settings...}}'
# Extra: --base 'JSON settings used by all' ; --columns N ; --view colour|mask|moss_only  (default colour) ; --paint (use the real COLOUR AND FADE under the moss) ; --damage
import json, subprocess, sys, os
import cv2
import numpy as np
here = os.path.dirname(os.path.abspath(__file__))
work = os.path.abspath(os.path.join(here, '..'))
args = sys.argv[1:]
def take(flag, default=None, has_value=True):
    if flag in args:
        i = args.index(flag)
        if has_value:
            val = args[i + 1]; del args[i:i + 2]; return val
        del args[i]; return True
    return default
base = json.loads(take('--base', '{}'))
columns = int(take('--columns', 0) or 0)
view_name = take('--view', 'colour')
variants_json = take('--variants')
paint = take('--paint', False, False)
damage = take('--damage', False, False)
name, size = args[0], int(args[1])
if variants_json:
    variants = json.loads(variants_json)
else:
    setting = args[2]
    variants = {f'{setting.split(".")[-1]} {v}': {setting: float(v) if v.replace('.', '', 1).replace('-', '', 1).isdigit() else v} for v in args[3:]}
if paint: base['base'] = 'paint'
if damage: base['damage'] = True
views = {}
for label, extra in variants.items():
    key = label.replace(' ', '_').replace('.', 'p')
    for kind in (view_name, 'joints'):
        views[f'{key}__{kind}'] = dict(extra, view=kind)
out = os.path.join(work, 'dev', name)
subprocess.run([os.path.join(work, '..', 'tests', 'blender.sh'), os.path.join(work, '..', 'tests', 'bake_tools.py'), '--',
                os.path.join(work, 'moss_only_recipe.py'), out, str(size), '4', json.dumps(views), json.dumps(base), 'Colour'],
               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
tiles = []
for label in variants:
    key = label.replace(' ', '_').replace('.', 'p')
    c = cv2.imread(f'{out}/{key}__{view_name}_colour.png')
    j = cv2.imread(f'{out}/{key}__joints_colour.png', 0)
    if c is None:
        print('missing', label); continue
    cover = cv2.imread(f'{out}/{key}__{view_name}_colour.png')
    # share from a mask bake is only meaningful for the mask view; for colour we bake it separately below
    tiles.append((label, c, j))
# share needs the mask view: bake it too
mask_views = {f'{label.replace(" ", "_").replace(".", "p")}__mask': dict(extra, view='mask') for label, extra in variants.items()}
subprocess.run([os.path.join(work, '..', 'tests', 'blender.sh'), os.path.join(work, '..', 'tests', 'bake_tools.py'), '--',
                os.path.join(work, 'moss_only_recipe.py'), out, str(size), '4', json.dumps(mask_views), json.dumps(base), 'Colour'],
               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
cells = []
for label, c, j in tiles:
    key = label.replace(' ', '_').replace('.', 'p')
    m = cv2.imread(f'{out}/{key}__mask_colour.png', 0)
    share = (m[j > 127] > 127).mean()
    print(f'{label:32s} covered share {share:.3f}')
    banner = np.full((30, c.shape[1], 3), 245, np.uint8)
    cv2.putText(banner, f'{label[:28]}  {share*100:.0f}%', (6, 21), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (20, 20, 20), 1, cv2.LINE_AA)
    cells.append(np.vstack([banner, c]))
columns = columns or len(cells)
while len(cells) % columns: cells.append(np.full_like(cells[0], 255))
rows = [np.hstack(cells[i:i + columns]) for i in range(0, len(cells), columns)]
cv2.imwrite(f'{out}/contact.png', np.vstack(rows))
print(f'{out}/contact.png')
