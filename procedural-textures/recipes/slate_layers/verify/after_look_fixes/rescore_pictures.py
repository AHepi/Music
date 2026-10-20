# What this does (plain words): the honesty checker's own copy of integration/score_set.py. It takes a colour picture and a height picture,
# makes a normal map from the height the way the harness does (strength fitted to the reference) AND the way the reference was made
# (3 x 3 slope, strength 7, integration/make_normal.py), scores both with lib/texture_compare.py against the slate reference, and prints the
# group scores as one line of JSON. It writes only into a temporary folder inside the checker's own folder, which it removes afterwards.
# Use: python3 -I rescore_pictures.py COLOUR.png HEIGHT.png [LABEL]
import json, os, shutil, subprocess, sys, tempfile
import cv2, numpy as np
PROC = 'proc-work'
HERE = PROC + '/recipes/slate_layers/verify/after_look_fixes'
colour, height_path = sys.argv[1], sys.argv[2]
label = sys.argv[3] if len(sys.argv) > 3 else os.path.basename(colour)
h = cv2.imread(height_path, cv2.IMREAD_UNCHANGED).astype(np.float64)
h = (h[..., 0] if h.ndim == 3 else h) / 65535.0
ref_n = cv2.imread(PROC + '/reference/slate/normal.png')[..., ::-1].astype(np.float64) / 255 * 2 - 1
target = (ref_n[..., 0].std() + ref_n[..., 1].std()) / 2


def sobel(strength):
    hx = (np.roll(h, -1, 1) - np.roll(h, 1, 1)) / 2
    hy = (np.roll(h, -1, 0) - np.roll(h, 1, 0)) / 2
    nx, ny, nz = -strength * hx, strength * hy, np.ones_like(h)
    l = np.sqrt(nx * nx + ny * ny + nz * nz)
    return np.stack([nx / l, ny / l, nz / l], -1)


lo, hi = 0.01, 400.0
for _ in range(40):
    m = np.sqrt(lo * hi)
    n = sobel(m)
    sp = (n[..., 0].std() + n[..., 1].std()) / 2
    lo, hi = (m, hi) if sp < target else (lo, m)
strength = float(np.sqrt(lo * hi))
n_harness = sobel(strength)
result = {'label': label, 'harness_strength': round(strength, 2)}


def score(normal_png_path_writer, tag):
    d = tempfile.mkdtemp(dir=HERE)
    shutil.copy(colour, d + '/colour.png')
    shutil.copy(height_path, d + '/height.png')
    normal_png_path_writer(d + '/normal.png')
    subprocess.run(['python3', '-I', PROC + '/lib/texture_compare.py', 'slate', d, '--json', d + '/score.json'], capture_output=True)
    s = json.load(open(d + '/score.json'))
    shutil.rmtree(d)
    result[tag] = {'overall': s['overall'], 'groups': s['groups']}


score(lambda p: cv2.imwrite(p, ((n_harness * 0.5 + 0.5) * 255).round().astype(np.uint8)[..., ::-1]), 'harness_style_normal')
# strength-7 normal made by the project's own make_normal.py
def strength7(p):
    subprocess.run(['python3', '-I', PROC + '/recipes/slate_layers/integration/make_normal.py', height_path, p, '7'], capture_output=True, check=True)
score(strength7, 'strength7_normal')
print(json.dumps(result))
