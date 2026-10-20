# What this file does (plain words)
# ------------------------------------------------------------------------------------------------------------------------------
# The independence test of COLOUR AND FADE inside the WHOLE recipe (all the layers that exist at the time you run it, through
# recipe/slate_recipe.py): change this layer's Seed, or switch it off with Amount 0, and see WHERE the finished colour changes.
# The rule being tested: this layer is the bottom of the stack, so the other layers paint OVER it. Therefore the finished colour must not
# change (a) in the joints, (b) wherever another layer's Mask is 1 (it fully covers the paint below), and (c) the other layers' own
# masks must be exactly the same picture (this layer must not move damage, moss or outline). The Height and Roughness sums may change
# wherever this layer's own tone relief changes (that is what a height sum is), and nowhere else.
# Use (plain python): python3 -I full_stack_independence.py [SIZE]      -> full_stack_independence.json / .md next to this file
import json
import os
import subprocess
import sys

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
SIZE = int(sys.argv[1]) if len(sys.argv) > 1 else 384
OUT = os.path.join(HERE, 'full_stack_pictures')
BLENDER = ['/home/user/work/blender-app/blender-5.2.2-linux-x64/blender', '-b', '--disable-autoexec', '-t', '2', '--python']
RECIPE = os.path.abspath(os.path.join(HERE, '..', '..', 'recipe', 'slate_recipe.py'))
BAKE_TOOLS = os.path.join(HERE, '..', 'bake_tools.py')
P = 'colour_and_fade.'
OTHERS = ['damage', 'moss', 'outline_and_shadow']


def bake(name, views, channels):
    folder = os.path.join(OUT, name)
    subprocess.run(BLENDER + [BAKE_TOOLS, '--', RECIPE, folder, str(SIZE), '4', json.dumps(views), '{}', channels], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return folder


def load(folder, name, kind):
    image = cv2.imread(os.path.join(folder, f'{name}_{kind}.png'), cv2.IMREAD_UNCHANGED).astype(np.float64)
    return image / (65535.0 if image.max() > 255 else 255.0)


def main():
    maps = bake('maps', {'base': {}, 'seed12': {P + 'seed': 12.0}, 'amount0': {P + 'amount': 0.0}}, 'Colour,Height,Roughness')
    numbers = {'piece_mask': {'debug_view': 'bundle.joints'}}
    for layer in OTHERS:
        numbers[f'{layer}_mask'] = {'debug_view': f'{layer}.mask'}
    masks = bake('masks', numbers, 'Height')
    masks_seed = bake('masks_seed12', {f'{layer}_mask': {'debug_view': f'{layer}.mask', P + 'seed': 12.0} for layer in OTHERS}, 'Height')
    piece_mask = load(masks, 'piece_mask', 'height')[..., 0]
    joints = cv2.erode((piece_mask < 0.01).astype(np.uint8), np.ones((3, 3), np.uint8)).astype(bool)
    slates = cv2.erode((piece_mask > 0.99).astype(np.uint8), np.ones((5, 5), np.uint8)).astype(bool)
    results = {'size': SIZE, 'joint dots': int(joints.sum()), 'slate dots (3+ dots from a joint)': int(slates.sum())}
    base_c = load(maps, 'base', 'colour')
    for variant in ('seed12', 'amount0'):
        delta = np.abs(base_c - load(maps, variant, 'colour')).max(axis=2) > 2 / 255.0
        row = {'colour changed in joints (% of joint dots)': round(float(delta[joints].mean() * 100), 4),
               'colour changed on slates (% of slate dots)': round(float(delta[slates].mean() * 100), 2)}
        for layer in OTHERS:
            covered = slates & (load(masks, f'{layer}_mask', 'height')[..., 0] > 0.99)
            row[f'colour changed where {layer} fully covers (% of {int(covered.sum())} dots)'] = round(float(delta[covered].mean() * 100), 4) if covered.any() else 'no such dots (layer empty here)'
        height_delta = np.abs(load(maps, 'base', 'height') - load(maps, variant, 'height'))[..., 0]
        row['height changed in joints (% of joint dots, > 0.0005)'] = round(float((height_delta[joints] > 0.0005).mean() * 100), 4)
        row['height changed on slates (% of slate dots, > 0.0005)'] = round(float((height_delta[slates] > 0.0005).mean() * 100), 2)
        results[variant] = row
    results['the other layers\' masks after changing this layer\'s seed: largest difference (must be 0; 16 bit)'] = {
        layer: round(float(np.abs(load(masks, f'{layer}_mask', 'height') - load(masks_seed, f'{layer}_mask', 'height')).max()), 6) for layer in OTHERS}
    with open(os.path.join(HERE, 'full_stack_independence.json'), 'w') as handle:
        json.dump(results, handle, indent=1)
    lines = ['# COLOUR AND FADE - independence inside the whole recipe (written by full_stack_independence.py)', '']
    for key, value in results.items():
        if isinstance(value, dict):
            lines.append(f'## {key}')
            lines += [f'* {k}: {v}' for k, v in value.items()]
            lines.append('')
        else:
            lines.append(f'* {key}: {value}')
    with open(os.path.join(HERE, 'full_stack_independence.md'), 'w') as handle:
        handle.write('\n'.join(lines))
    print(json.dumps(results, indent=1))


if __name__ == '__main__':
    main()
