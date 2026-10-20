# What this does (plain words): makes ONE bigger picture (2508 x 2508 dots = 2 x 2 tiles' worth of wall) of NEW, non-repeating bricks from the same
# generator (24 courses of 8 bricks, every patch new), and measures whether it repeats or has seams:
#   repeat test: how well the picture matches a copy of itself moved by any amount (autocorrelation of brightness). A tile simply copied 2 x 2 matches
#                itself perfectly (1.0) when moved by one tile; a truly new picture should have no strong match anywhere except at zero.
#   seam test:   how big the jump is across the wrap-around edge and across the middle lines (where tile edges would be) compared with a normal jump
#                between neighbouring dots (1.0 = no seam). The same numbers for the reference tile copied 2 x 2 are shown for comparison.
# Use (system python):  python3 -I run_area.py [seed] [grain]
import json, os, subprocess, sys
import numpy as np, cv2
HERE = os.path.dirname(os.path.abspath(__file__))
PROC = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(PROC, 'lib'))
import sample_description as sd
import texture_compare as tc
BLENDER = '/home/user/work/blender-app/blender-5.2.2-linux-x64/blender'
seed = int(sys.argv[1]) if len(sys.argv) > 1 else 101
grain = float(sys.argv[2]) if len(sys.argv) > 2 else 0.12
out = os.path.join(PROC, 'recipes', 'brick', 'area')
os.makedirs(out, exist_ok=True)
model = json.load(open(os.path.join(HERE, 'sampler_model_brick.json')))
desc = sd.sample_description(seed, model, tile=2508, grain=grain)
path = os.path.join(out, 'description_area.json')
json.dump(desc, open(path, 'w'), separators=(',', ':'))
subprocess.run([BLENDER, '-b', '--disable-autoexec', '-t', '2', '--python', os.path.join(HERE, 'brick_generator.py'), '--', path, os.path.join(out, 'picture'), '--size', '2508', '--samples', '8'], capture_output=True, text=True)
bake = json.load(open(os.path.join(out, 'picture', 'bake.json')))
img = cv2.imread(os.path.join(out, 'picture', 'colour.png'))
ref = cv2.imread(os.path.join(PROC, 'reference', 'brick', 'colour.png'))
copied = np.tile(ref, (2, 2, 1))
def grey(x):
    return cv2.cvtColor(x, cv2.COLOR_BGR2GRAY).astype(np.float64)
def repeat_peak(g, min_shift=400):
    g = g - g.mean()
    f = np.fft.rfft2(g)
    ac = np.fft.irfft2(f * np.conj(f), s=g.shape)
    ac /= ac[0, 0]
    h, w = g.shape
    ys = np.minimum(np.arange(h), h - np.arange(h))[:, None]
    xs = np.minimum(np.arange(w), w - np.arange(w))[None, :]
    far = (ys >= min_shift) | (xs >= min_shift)
    # ignore the wide ridge of "moved by a few brick rows/columns" being similar: report the top value far from zero
    idx = np.unravel_index(np.argmax(np.where(far, ac, -1)), ac.shape)
    return float(ac[idx]), [int(idx[0]), int(idx[1])]
def seam_numbers(g):
    h, w = g.shape
    typical = (np.abs(np.diff(g, axis=1)).mean() + np.abs(np.diff(g, axis=0)).mean()) / 2
    wrap = (np.abs(g[:, 0] - g[:, -1]).mean() + np.abs(g[0, :] - g[-1, :]).mean()) / 2
    mid = (np.abs(g[:, w // 2] - g[:, w // 2 - 1]).mean() + np.abs(g[h // 2, :] - g[h // 2 - 1, :]).mean()) / 2
    return {'wrap_edge_jump_ratio': round(float(wrap / typical), 3), 'middle_lines_jump_ratio': round(float(mid / typical), 3)}
gi, gc = grey(img), grey(copied)
pk_new, where_new = repeat_peak(gi)
pk_copy, where_copy = repeat_peak(gc)
result = {'seed': seed, 'description_bytes': os.path.getsize(path), 'bake_seconds': bake['seconds'], 'shapes': bake['shapes'],
          'new_picture': {'best_match_when_moved': round(pk_new, 3), 'at_shift': where_new, **seam_numbers(gi)},
          'reference_tile_copied_2x2': {'best_match_when_moved': round(pk_copy, 3), 'at_shift': where_copy, **seam_numbers(gc)}}
# the same texture score on the middle 1254 x 1254 piece (a tile-sized look) and on the whole
cv2.imwrite(os.path.join(out, 'picture', 'middle_tile.png'), img[627:627 + 1254, 627:627 + 1254])
os.makedirs(os.path.join(out, 'middle'), exist_ok=True)
for name in ('colour', 'height', 'normal'):
    src = cv2.imread(os.path.join(out, 'picture', name + '.png'), cv2.IMREAD_UNCHANGED)
    cv2.imwrite(os.path.join(out, 'middle', name + '.png'), src[627:627 + 1254, 627:627 + 1254])
result['texture_overall_of_middle_piece'] = tc.score_set('brick', os.path.join(out, 'middle'))['overall']
json.dump(result, open(os.path.join(out, 'area_result.json'), 'w'), indent=1)
print(json.dumps(result, indent=1))
cv2.imwrite(os.path.join(out, 'area_preview.png'), cv2.resize(img, (1254, 1254), interpolation=cv2.INTER_AREA))
