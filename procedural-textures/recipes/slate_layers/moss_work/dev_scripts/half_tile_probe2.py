# What this file does (plain words): the half-tile mismatch of OTHER hard-edged numbers, for comparison with moss: the layout's piece_mask (joints) and moss with parts of its logic off.
# Use: python3 -I half_tile_probe2.py [SIZE]
import json, os, subprocess, sys
import cv2
import numpy as np
here = os.path.dirname(os.path.abspath(__file__)); work = os.path.abspath(os.path.join(here, '..'))
size = int(sys.argv[1]) if len(sys.argv) > 1 else 384
recipe = os.path.join(work, 'frozen', 'recipe', 'slate_recipe.py')
cases = {'layout piece_mask (joints)': ('bundle.piece_mask', {}), 'layout top_edge_distance': ('bundle.top_edge_distance', {}), 'moss mask, coverage 1 (almost all moss)': ('moss.mask', {'moss.coverage': 1.0, 'moss.damage_avoid': 0.0, 'moss.lichen_amount': 0.0})}
def bake(tag, view, params):
    folder = os.path.join(work, 'dev', 'probe2_' + tag)
    subprocess.run(['/home/user/work/blender-app/blender-5.2.2-linux-x64/blender', '-b', '--disable-autoexec', '-t', '2', '--python', os.path.join(work, '..', 'tests', 'bake_tools.py'), '--', recipe, folder, str(size), '4', json.dumps({'v': {'debug_view': view}}), json.dumps(params), 'Height'], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return (cv2.imread(os.path.join(folder, 'v_height.png'), -1).astype(np.float64) / 65535.0).max(axis=2)
for i, (name, (view, params)) in enumerate(cases.items()):
    a, b = bake(f'{i}a', view, params), bake(f'{i}b', view, dict(params, shift=[0.5, 0.5]))
    d = np.abs(np.roll(a, (size // 2, size // 2), axis=(0, 1)) - b)
    print(f'{name:45s} dots differing by more than 0.1: {100 * (d > 0.1).mean():6.3f} %   by more than 0.5: {100 * (d > 0.5).mean():6.3f} %', flush=True)
