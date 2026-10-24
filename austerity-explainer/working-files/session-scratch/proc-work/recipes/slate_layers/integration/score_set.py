# What this does (plain words): scores a colour picture + a height picture (16-bit) against the slate reference with the project's "same kind of surface"
# tool, making the normal map from the height the same way the harness does (slope of the height, strength fitted to the reference's slope spread).
# Prints the group scores. Use: python3 -I score_set.py COLOUR.png HEIGHT.png [--keep FOLDER]
import json, os, subprocess, sys, tempfile, shutil
import cv2, numpy as np
PROC = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work'
colour, height_path = sys.argv[1], sys.argv[2]
h = cv2.imread(height_path, cv2.IMREAD_UNCHANGED).astype(np.float64)
h = (h[..., 0] if h.ndim == 3 else h) / 65535.0
ref_n = cv2.imread(PROC + '/reference/slate/normal.png')[..., ::-1].astype(np.float64) / 255 * 2 - 1
target = (ref_n[..., 0].std() + ref_n[..., 1].std()) / 2
def sobel(strength):
    hx = (np.roll(h, -1, 1) - np.roll(h, 1, 1)) / 2; hy = (np.roll(h, -1, 0) - np.roll(h, 1, 0)) / 2
    nx, ny, nz = -strength * hx, strength * hy, np.ones_like(h); l = np.sqrt(nx * nx + ny * ny + nz * nz)
    return np.stack([nx / l, ny / l, nz / l], -1)
lo, hi = 0.01, 400.0
for _ in range(40):
    m = np.sqrt(lo * hi); n = sobel(m); sp = (n[..., 0].std() + n[..., 1].std()) / 2
    lo, hi = (m, hi) if sp < target else (lo, m)
strength = float(np.sqrt(lo * hi)); n = sobel(strength)
d = tempfile.mkdtemp(dir=PROC + '/recipes/slate_layers/integration')
shutil.copy(colour, d + '/colour.png'); shutil.copy(height_path, d + '/height.png')
cv2.imwrite(d + '/normal.png', ((n * 0.5 + 0.5) * 255).round().astype(np.uint8)[..., ::-1])
subprocess.run(['python3', '-I', PROC + '/lib/texture_compare.py', 'slate', d, '--json', d + '/score.json'], capture_output=True)
s = json.load(open(d + '/score.json'))
print('overall', s['overall'], 'groups', s['groups'], 'sobel strength %.1f' % strength)
print('  ', {k: round(v, 3) for k, v in s['scores'].items() if k.startswith('height') or k.startswith('normal')})
if '--keep' in sys.argv:
    shutil.copytree(d, sys.argv[sys.argv.index('--keep') + 1], dirs_exist_ok=True)
shutil.rmtree(d)
