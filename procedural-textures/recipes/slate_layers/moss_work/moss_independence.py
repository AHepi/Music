# What this file does (plain words)
# ------------------------------------------------------------------------------------------------------------------------------
# Proves that the MOSS layer is independent of the other layers, using the REAL recipe (recipe/slate_recipe.py, all layers). Two kinds of check:
#   A. Change MOSS (switch it off with Amount 0, or give it another Seed) and look at the finished picture (colour, exact height, roughness): the only dots
#      that may change are the dots where moss is in the picture before OR after the change. Everything outside must be exactly the same.
#   B. Change ANOTHER layer (colour and fade seed, damage seed, outline seed, layout seed) and look at what MOSS itself makes (its Mask and its Colour,
#      baked alone through the recipe's debug views): moss must not change, except through the one declared link (it reads DAMAGE's Mask, so a new damage
#      seed may change moss, but only on dots where damage is, before or after) and through the layout (every layer reads the layout bundle).
# Output: moss_independence_table.md and moss_independence.json in the folder given. The work pictures go into a sub folder.
# Use (plain python):  python3 -I moss_independence.py [SIZE] [OUT_FOLDER]
import json
import os
import subprocess
import sys

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
SIZE = int(sys.argv[1]) if len(sys.argv) > 1 else 384
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, 'independence')
BLENDER = ['/home/user/work/blender-app/blender-5.2.2-linux-x64/blender', '-b', '--disable-autoexec', '-t', '2', '--python']
TOOLS = os.path.join(HERE, '..', 'tests', 'bake_tools.py')
RECIPE = os.path.join(HERE, 'frozen', 'recipe', 'slate_recipe.py') if os.environ.get('MOSS_FROZEN') else os.path.join(HERE, '..', 'recipe', 'slate_recipe.py')      # MOSS_FROZEN=1: use the frozen copy of the whole stack
VIEWS = {'final': {}, 'moss_mask': {'debug_view': 'moss.mask'}, 'moss_colour': {'debug_view': 'moss.colour'}, 'damage_mask': {'debug_view': 'damage.mask'}}


def bake(name, params):
    folder = os.path.join(OUT, 'work', name)
    subprocess.run(BLENDER + [TOOLS, '--', RECIPE, folder, str(SIZE), '4', json.dumps(VIEWS), json.dumps(params), 'Colour,Height,Roughness'],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return folder


def load(folder, view, kind):
    suffix = {'colour': '_colour.png', 'height': '_height.png', 'roughness': '_roughness.png'}[kind]
    path = os.path.join(folder, view + suffix)
    image = cv2.imread(path, cv2.IMREAD_UNCHANGED)
    if image is None:
        return None
    image = image.astype(np.float64)
    return image / (65535.0 if image.max() > 255 else 255.0)


def exact_number(folder, view):
    """The exact (16 bit) number a debug view shows, from its Height picture: one number per dot."""
    data = load(folder, view, 'height')
    return data.max(axis=2)


def picture_changed(a_folder, b_folder):
    out = {}
    for kind, limit in (('colour', 2 / 255), ('height', 0.002), ('roughness', 0.005)):
        a, b = load(a_folder, 'final', kind), load(b_folder, 'final', kind)
        out[kind] = np.abs(a - b).max(axis=2) > limit
    return out


if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    base = bake('base', {})
    base_moss, base_damage = exact_number(base, 'moss_mask') > 0.01, exact_number(base, 'damage_mask') > 0.01
    rows_a, rows_b = [], []
    # ---- A. change MOSS
    for label, params in (('Amount 0', {'moss.amount': 0.0}), ('Seed + 1', {'moss.seed': 32.0}), ('Coverage 0.5', {'moss.coverage': 0.5})):
        folder = bake('moss_' + label.replace(' ', '_').replace('+', 'plus').replace('.', 'p'), params)
        variant_moss = exact_number(folder, 'moss_mask') > 0.01
        allowed = base_moss | variant_moss
        changes = picture_changed(base, folder)
        row = {'what was changed': 'moss ' + label, 'moss dots before %': round(100 * base_moss.mean(), 2), 'moss dots after %': round(100 * variant_moss.mean(), 2)}
        for kind, d in changes.items():
            row[f'{kind} changed %'] = round(100 * d.mean(), 3)
            row[f'{kind} changed outside moss before/after %'] = round(100 * (d & ~allowed).mean(), 3)
        rows_a.append(row)
    # ---- B. change ANOTHER layer and look at what moss makes
    for label, params, link_allowed in (('colour_and_fade seed + 1', {'colour_and_fade.seed': 12.0}, 'none'),
                                         ('outline_and_shadow seed + 1', {'outline_and_shadow.seed': 42.0}, 'none'),
                                         ('damage seed + 1', {'damage.seed': 22.0}, 'damage'),
                                         ('damage amount 0', {'damage.amount': 0.0}, 'damage'),
                                         ('layout seed + 1', {'layout.seed': 2.0}, 'layout')):
        folder = bake('other_' + label.replace(' ', '_').replace('+', 'plus'), params)
        mask_a, mask_b = exact_number(base, 'moss_mask'), exact_number(folder, 'moss_mask')
        colour_a, colour_b = load(base, 'moss_colour', 'colour'), load(folder, 'moss_colour', 'colour')
        mask_changed = np.abs(mask_a - mask_b) > 0.002
        colour_changed = (np.abs(colour_a - colour_b).max(axis=2) > 2 / 255) & ((mask_a > 0.01) | (mask_b > 0.01))      # colour only counts where moss is
        damage_before_after = base_damage | (exact_number(folder, 'damage_mask') > 0.01)
        row = {'what was changed': label, 'allowed through': {'none': 'nothing', 'damage': 'the declared link (damage mask)', 'layout': 'the layout bundle (all layers read it)'}[link_allowed],
               'moss mask dots changed %': round(100 * mask_changed.mean(), 3), 'moss colour dots changed %': round(100 * colour_changed.mean(), 3)}
        if link_allowed == 'damage':
            row['moss mask changed outside damage before/after %'] = round(100 * (mask_changed & ~damage_before_after).mean(), 3)
        rows_b.append(row)
    with open(os.path.join(OUT, 'moss_independence.json'), 'w') as handle:
        json.dump({'A_change_moss': rows_a, 'B_change_another_layer': rows_b}, handle, indent=1)
    lines = ['## A. Change MOSS, look at the finished picture', '',
             '| what was changed | moss dots before % | moss dots after % | colour changed % | colour changed outside moss % | height changed % | height outside moss % | roughness changed % | roughness outside moss % |', '|---|---|---|---|---|---|---|---|---|']
    for r in rows_a:
        lines.append(f"| {r['what was changed']} | {r['moss dots before %']} | {r['moss dots after %']} | {r['colour changed %']} | {r['colour changed outside moss before/after %']} | "
                     f"{r['height changed %']} | {r['height changed outside moss before/after %']} | {r['roughness changed %']} | {r['roughness changed outside moss before/after %']} |")
    lines += ['', '## B. Change ANOTHER layer, look at what MOSS makes (its own mask and colour, baked alone)', '',
              '| what was changed | allowed to reach moss through | moss mask dots changed % | moss colour dots changed % | moss mask changed outside damage % |', '|---|---|---|---|---|']
    for r in rows_b:
        lines.append(f"| {r['what was changed']} | {r['allowed through']} | {r['moss mask dots changed %']} | {r['moss colour dots changed %']} | {r.get('moss mask changed outside damage before/after %', '-')} |")
    with open(os.path.join(OUT, 'moss_independence_table.md'), 'w') as handle:
        handle.write('\n'.join(lines) + '\n')
    print('\n'.join(lines))
