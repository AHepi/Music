# What this does (plain words): the "half-tile shift test" for seamless tiles. It bakes a description twice: once normally, once with every shape moved
# half a tile right and down (wrapping round). If the tile is truly seamless, the second picture must equal the first picture rolled by half a tile
# (what leaves on one side comes back on the other). It prints how many dots differ by more than 40 levels (of 255) and the mean difference; a wrongly
# rolled control (rolled by an unrelated amount) is printed for comparison. Also writes a 2 x 2 tiling picture to look at.
# Use (system python):  python3 -I seam_test.py DESCRIPTION.json OUT_FOLDER [size]
import json, os, subprocess, sys
import numpy as np, cv2
HERE = os.path.dirname(os.path.abspath(__file__))
BLENDER = '/home/user/work/blender-app/blender-5.2.2-linux-x64/blender'
description_path, out = sys.argv[1], sys.argv[2]
size = int(sys.argv[3]) if len(sys.argv) > 3 else 1254
d = json.load(open(description_path))
d.pop('grain', None)           # the grain is a fixed pattern in the picture's own dots, it does not move with the shapes: leave it out of this test
tmp = os.path.join(out, 'seam_description.json')
os.makedirs(out, exist_ok=True)
json.dump(d, open(tmp, 'w'), separators=(',', ':'))
half = size // 2
for name, shift in (('plain', 0), ('shifted', half * float(d.get('tile', 1254)) / size)):
    subprocess.run([BLENDER, '-b', '--disable-autoexec', '-t', '2', '--python', os.path.join(HERE, 'brick_generator.py'), '--', tmp, os.path.join(out, name), '--size', str(size), '--samples', '8', '--shift', str(shift)], capture_output=True, text=True)
a = cv2.imread(os.path.join(out, 'plain', 'colour.png')).astype(float)
b = cv2.imread(os.path.join(out, 'shifted', 'colour.png')).astype(float)
rolled = np.roll(a, (half, half), axis=(0, 1))
wrong = np.roll(a, (half + 137, half + 71), axis=(0, 1))
def stats(x, y):
    diff = np.abs(x - y).max(axis=2)
    return {'share_over_40_levels': round(float((diff > 40).mean()), 5), 'mean_abs_difference': round(float(np.abs(x - y).mean()), 3)}
result = {'seamless_test': stats(rolled, b), 'wrongly_rolled_control': stats(wrong, b)}
tiled = np.tile(a.astype(np.uint8), (2, 2, 1))
cv2.imwrite(os.path.join(out, 'tiled_2x2.png'), cv2.resize(tiled, None, fx=0.5, fy=0.5, interpolation=cv2.INTER_AREA))
json.dump(result, open(os.path.join(out, 'seam_result.json'), 'w'), indent=1)
print(json.dumps(result))
