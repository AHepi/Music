# What this file does (plain words): finds WHICH part of the moss layer makes the half-tile test show a few mismatching dots, by switching parts off one at a time
# (damage avoid, lichen, ...) and measuring the half-tile mismatch of the moss mask each time. Uses the frozen copy of the stack. Use: python3 -I half_tile_probe.py [SIZE]
import json, os, subprocess, sys
import cv2
import numpy as np
here = os.path.dirname(os.path.abspath(__file__)); work = os.path.abspath(os.path.join(here, '..'))
size = int(sys.argv[1]) if len(sys.argv) > 1 else 384
recipe = os.path.join(work, 'frozen', 'recipe', 'slate_recipe.py')
variants = {'all on': {}, 'damage avoid 0': {'moss.damage_avoid': 0.0}, 'damage avoid 0, lichen 0': {'moss.damage_avoid': 0.0, 'moss.lichen_amount': 0.0},
            'damage avoid 0, lichen 0, edge raggedness 0, fringe 0': {'moss.damage_avoid': 0.0, 'moss.lichen_amount': 0.0, 'moss.edge_raggedness': 0.0, 'moss.fringe_amount': 0.0}}
def bake(tag, params):
    views = {'mask': {'debug_view': 'moss.mask'}}
    folder = os.path.join(work, 'dev', 'probe_' + tag)
    subprocess.run(['/home/user/work/blender-app/blender-5.2.2-linux-x64/blender', '-b', '--disable-autoexec', '-t', '2', '--python', os.path.join(work, '..', 'tests', 'bake_tools.py'), '--', recipe, folder, str(size), '4', json.dumps(views), json.dumps(params), 'Height'], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    im = cv2.imread(os.path.join(folder, 'mask_height.png'), -1).astype(np.float64) / 65535.0
    return im.max(axis=2)
for i, (name, params) in enumerate(variants.items()):
    a, b = bake(f'{i}a', params), bake(f'{i}b', dict(params, shift=[0.5, 0.5]))
    right = (np.abs(np.roll(a, (size // 2, size // 2), axis=(0, 1)) - b) > 0.1).mean() * 100
    wrong = (np.abs(np.roll(a, (size // 2 + 7, size // 2 + 7), axis=(0, 1)) - b) > 0.1).mean() * 100
    print(f'{name:60s} right roll {right:6.3f} %   wrong roll {wrong:6.3f} %   (moss share {100 * (a > 0.5).mean():.1f} %)', flush=True)
