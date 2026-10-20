# What this does (plain words): the strictest seamless test. For each description: bake it normally, then bake it again with the whole picture slid by
# half a tile in both directions (the generator's --shift 0.5 0.5), and compare the second picture with the first one rolled by half its size.
# If the tile really repeats, they are the same picture. Prints the average difference, the share of dots that differ by more than 40 of 255 (these
# are only the soft edges that land a little differently after the slide), and, for contrast, the same numbers when rolled by a wrong amount.
# Use: python3 -I half_tile_test.py DESCRIPTION.json [DESCRIPTION.json ...]   (writes ../scores/half_tile_test.json)
import json, os, subprocess, sys
import cv2
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); GRAVEL = os.path.abspath(os.path.join(HERE, '..'))
BLENDER = '/home/user/work/blender-app/blender-5.2.2-linux-x64/blender'
size = 512
results = {}
for path in sys.argv[1:]:
    name = os.path.splitext(os.path.basename(path))[0]
    folders = {}
    for tag, extra in (('a', []), ('b', ['--shift', '0.5', '0.5'])):
        out = os.path.join(GRAVEL, 'scores', 'half_tile', f'{name}_{tag}')
        subprocess.run([BLENDER, '-b', '--disable-autoexec', '-t', '2', '--python', os.path.join(GRAVEL, 'generator', 'gravel_generator.py'), '--', path, out, '--size', str(size), *extra], capture_output=True, text=True)
        folders[tag] = out
    a = cv2.imread(os.path.join(folders['a'], 'colour.png')).astype(float); b = cv2.imread(os.path.join(folders['b'], 'colour.png')).astype(float)
    rolled = np.roll(a, (size // 2, size // 2), axis=(0, 1))
    d = np.abs(rolled - b).mean(axis=2)
    wrong = np.abs(np.roll(a, (size // 2 + 9, size // 2 - 7), axis=(0, 1)) - b).mean(axis=2)
    ha = cv2.imread(os.path.join(folders['a'], 'height.png'), cv2.IMREAD_UNCHANGED).astype(float) / 257.0
    hb = cv2.imread(os.path.join(folders['b'], 'height.png'), cv2.IMREAD_UNCHANGED).astype(float) / 257.0
    ha = ha[..., 0] if ha.ndim == 3 else ha; hb = hb[..., 0] if hb.ndim == 3 else hb
    hd = np.abs(np.roll(ha, (size // 2, size // 2), axis=(0, 1)) - hb)
    results[name] = {'colour_mean_difference_levels': round(float(d.mean()), 3), 'colour_share_over_40': round(float((d > 40).mean()), 4),
                     'wrong_roll_mean_difference': round(float(wrong.mean()), 3), 'wrong_roll_share_over_40': round(float((wrong > 40).mean()), 4),
                     'height_mean_difference_levels': round(float(hd.mean()), 3)}
    print(name, results[name], flush=True)
json.dump(results, open(os.path.join(GRAVEL, 'scores', 'half_tile_test.json'), 'w'), indent=1)
