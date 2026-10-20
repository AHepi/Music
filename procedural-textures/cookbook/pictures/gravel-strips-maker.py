# What this does (plain words): makes the extra "what does this setting do?" strips for the gravel guides, WITHOUT Blender and without
# changing anything in recipes/gravel. Two kinds:
#  (1) RELABELLED copies of five gravel strips whose labels did not match what was run (the checker's findings in
#      recipes/gravel/verifier_answer.json): the same tile pictures from recipes/gravel/guide_pictures/sweeps_big/, joined again with lib/make_strip.py
#      under corrected labels.
#  (2) TWO NEW strips for settings that had none:
#      - normal strength: the baked S_v4 height picture turned into a normal map at strengths 0, 5, 10, 20, 40 with the generator's own rule
#        (slope of the 8-bit height x strength, central differences, as in recipes/gravel/generator/gravel_generator.py derive_normal_from_height),
#        and each one scored against the reference with lib/pixel_compare.py (normal error in degrees);
#      - height stretch: the pebble transfer tile's colour, the height the GRAVEL stretch would give it (worked out here in plain Python with the
#        generator's height rule), and the height the generator really baked with the pebbles' own stretch.
# Every crop is the top-left 320 x 320 dots of a 1254-dot picture (the relabelled strips are 320 x 320 crops of a 640-dot picture of the whole tile).
# The numbers it measures go to gravel-strips-numbers.json next to this file. Pictures are saved as JPEG (quality 85) to keep them small.
# Use: python3 -I gravel_strips_maker.py
import json
import os
import shutil
import subprocess
import sys

import cv2
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
PROC = os.path.abspath(os.path.join(HERE, '..', '..'))
GRAVEL = os.path.join(PROC, 'recipes', 'gravel')
SWEEPS = os.path.join(GRAVEL, 'guide_pictures', 'sweeps_big')
WORK = os.path.join(os.path.dirname(PROC), 'gravel-strip-work')          # temporary folder outside proc-work, removed at the end
sys.path.insert(0, os.path.join(PROC, 'lib'))
import pixel_compare as pc  # noqa: E402

CROP = 320
numbers = {}


def join_strip(folder, title, out_name):
    """Runs lib/make_strip.py on a folder holding tile_XX.png + sweep.json, then saves the strip as a small JPEG in this folder."""
    temporary_png = os.path.join(WORK, out_name + '.png')
    subprocess.run([sys.executable, '-I', os.path.join(PROC, 'lib', 'make_strip.py'), folder, temporary_png, '--title', title], check=True)
    out = os.path.join(HERE, out_name + '.jpg')
    Image.open(temporary_png).convert('RGB').save(out, quality=85, optimize=True)
    print(out, os.path.getsize(out) // 1024, 'KB')


def relabel(sweep_name, labels, title, out_name):
    folder = os.path.join(WORK, sweep_name)
    os.makedirs(folder, exist_ok=True)
    original = json.load(open(os.path.join(SWEEPS, sweep_name, 'sweep.json')))
    for file_name in original['files']:
        target = os.path.join(folder, file_name)
        if not os.path.exists(target):
            os.symlink(os.path.join(SWEEPS, sweep_name, file_name), target)
    json.dump({'files': original['files'], 'labels': labels, 'title': title}, open(os.path.join(folder, 'sweep.json'), 'w'))
    join_strip(folder, title, out_name)


def normal_from_height(height01, strength):
    """The generator's rule (central differences on the height rounded to 8 bits), green pointing up the picture."""
    h = np.round(height01 * 255.0)
    hx = (np.roll(h, -1, axis=1) - np.roll(h, 1, axis=1)) / 2.0
    hy = (np.roll(h, -1, axis=0) - np.roll(h, 1, axis=0)) / 2.0
    nx, ny, nz = -strength * hx / 255.0, strength * hy / 255.0, np.ones_like(h)
    length = np.sqrt(nx * nx + ny * ny + nz * nz)
    return np.stack([nx / length, ny / length, nz / length], axis=-1)


def load_height01(path):
    image = cv2.imread(path, cv2.IMREAD_UNCHANGED)
    image = image[..., 0] if image.ndim == 3 else image
    return image.astype(np.float64) / (65535.0 if image.dtype == np.uint16 else 255.0)


os.makedirs(WORK, exist_ok=True)

# ---------------------------------------------------------------- (1) the five relabelled strips
relabel('stone_chip', ['0 (smooth)', '0.05', '0.12 (S_v4 uses 0.10)', '0.25', '0.4'],
        'Edge chipping (share of the stone radius)', 'gravel-strip-stone-chip')
relabel('stone_packing', ['0.35', '0.5', '0.65 (3 of 5 classes)', '0.8', '1.0'],
        'Packing: spacing x sum of radii (one value for all classes)', 'gravel-strip-stone-packing')
relabel('layers_stage', ['ground only', '+ soil lumps, specks', '+ tiny stones', '+ small + medium', '+ large + biggest'],
        'Layers added one by one', 'gravel-strip-layers')
relabel('height_filter_width', ['box (no blur)', 'width 1 (used here)', 'width 2', 'width 4', 'width 8'],
        'Height blur: Cycles Gaussian filter width (tile at 640 dots)', 'gravel-strip-height-blur')
relabel('light_direction', ['from the top (used)', 'top left', 'right', 'bottom right', 'from the bottom'],
        'Light direction (stones only; soil lumps stay lit from the top)', 'gravel-strip-light-direction')

# ---------------------------------------------------------------- (2a) normal strength
s_v4 = os.path.join(GRAVEL, 'outputs', 'S_v4')
height = load_height01(os.path.join(s_v4, 'height.png'))
folder = os.path.join(WORK, 'normal_strength')
os.makedirs(folder, exist_ok=True)
score_folder = os.path.join(WORK, 'normal_score')
os.makedirs(score_folder, exist_ok=True)
shutil.copy(os.path.join(s_v4, 'colour.png'), os.path.join(score_folder, 'colour.png'))
shutil.copy(os.path.join(s_v4, 'height.png'), os.path.join(score_folder, 'height.png'))
strengths = [0, 5, 10, 20, 40]
files, labels, normal_numbers = [], [], {}
for index, strength in enumerate(strengths):
    normal = normal_from_height(height, strength) * 0.5 + 0.5
    rgb8 = np.clip(np.round(normal * 255.0), 0, 255).astype(np.uint8)
    cv2.imwrite(os.path.join(score_folder, 'normal.png'), rgb8[..., ::-1])
    report = pc.pixel_report('gravel', score_folder)
    normal_numbers[str(strength)] = {'normal_mean_angle_degrees': round(report['normal_mean_angle_degrees'], 2),
                                     'normal_median_angle_degrees': round(report['normal_median_angle_degrees'], 2)}
    name = f'tile_{index:02d}.png'
    cv2.imwrite(os.path.join(folder, name), rgb8[:CROP, :CROP, ::-1])
    files.append(name)
    label = 'flat (0)' if strength == 0 else str(strength) + (' (used)' if strength == 10 else '')
    labels.append(label + ': %.1f deg' % report['normal_mean_angle_degrees'])
    print('normal strength', strength, normal_numbers[str(strength)], flush=True)
numbers['normal_strength_on_S_v4'] = {'what': 'normal map made from outputs/S_v4/height.png at each strength (central differences on the 8-bit height), '
                                              'scored against reference/gravel/normal.png with lib/pixel_compare.py', 'by_strength': normal_numbers}
json.dump({'files': files, 'labels': labels, 'title': 'Normal strength (label: error against the reference normal)'}, open(os.path.join(folder, 'sweep.json'), 'w'))
join_strip(folder, 'Normal strength (label: error against the reference normal)', 'gravel-strip-normal-strength')

# ---------------------------------------------------------------- (2b) height stretch on the pebble transfer tile
pebbles = os.path.join(GRAVEL, 'transfer', 'out', 'pebbles_1254')
colour = cv2.imread(os.path.join(pebbles, 'colour.png'))
rgb = colour[..., ::-1].astype(np.float64)
gravel_rule = json.load(open(os.path.join(GRAVEL, 'description', 'S_v4.json')))['maps']['height']
pebble_rule = json.load(open(os.path.join(GRAVEL, 'description', 'transfer_pebbles.json')))['maps']['height']


def height_by_rule(rule):
    mix = np.asarray(rule['mix'], np.float64) / 255.0
    return np.clip(rgb @ mix + rule['offset'], 0.0, 255.0)


gravel_height = height_by_rule(gravel_rule)
pebble_height_computed = height_by_rule(pebble_rule)
baked_pebble_height = load_height01(os.path.join(pebbles, 'height.png')) * 255.0
numbers['height_stretch_on_pebbles'] = {
    'what': 'height made from transfer/out/pebbles_1254/colour.png with the gravel rule (S_v4 maps.height) and with the pebble rule '
            '(transfer_pebbles maps.height), no blur; plus the height the generator baked',
    'gravel_rule_share_of_dots_at_full_white': round(float((gravel_height >= 254.5).mean()), 3),
    'gravel_rule_mean_height_0_to_255': round(float(gravel_height.mean()), 1),
    'pebble_rule_share_of_dots_at_full_white': round(float((pebble_height_computed >= 254.5).mean()), 3),
    'pebble_rule_mean_height_0_to_255': round(float(pebble_height_computed.mean()), 1),
    'baked_pebble_height_share_at_full_white': round(float((baked_pebble_height >= 254.5).mean()), 3),
    'baked_pebble_height_mean_0_to_255': round(float(baked_pebble_height.mean()), 1)}
print(numbers['height_stretch_on_pebbles'], flush=True)
folder = os.path.join(WORK, 'height_stretch')
os.makedirs(folder, exist_ok=True)
grey = lambda values: cv2.cvtColor(np.clip(np.round(values), 0, 255).astype(np.uint8), cv2.COLOR_GRAY2BGR)
tiles = [colour[:CROP, :CROP], grey(gravel_height[:CROP, :CROP]), grey(baked_pebble_height[:CROP, :CROP])]
files = []
for index, tile in enumerate(tiles):
    cv2.imwrite(os.path.join(folder, f'tile_{index:02d}.png'), tile)
    files.append(f'tile_{index:02d}.png')
labels = ['pebble colour', 'height, gravel stretch', 'height, own stretch']
json.dump({'files': files, 'labels': labels, 'title': 'Height stretch on a new surface'}, open(os.path.join(folder, 'sweep.json'), 'w'))
join_strip(folder, 'Height stretch on a new surface', 'gravel-strip-height-stretch')

json.dump(numbers, open(os.path.join(HERE, 'gravel-strips-numbers.json'), 'w'), indent=1)
shutil.rmtree(WORK)
print('done')
