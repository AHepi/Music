# Verifier script: half-tile-shift test at 1254 dots on S_v4: bake A (normal) vs bake B (generator --shift 0.5 0.5); B should equal A rolled by half.
import cv2, numpy as np
G = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/recipes/gravel/verify'
a = cv2.imread(G + '/S_v4/colour.png').astype(float); b = cv2.imread(G + '/S_v4_shifted/colour.png').astype(float)
n = a.shape[0]; h = n // 2
print('size', n, 'bake times', open(G + '/S_v4_shifted/bake.json').read().count('total_s'))
for name, shift in (('half roll (h,h)', (h, h)), ('wrong roll (h+9,h-7)', (h + 9, h - 7)), ('no roll', (0, 0)), ('roll (h, 0)', (h, 0))):
    d = np.abs(np.roll(a, shift, axis=(0, 1)) - b).mean(axis=2)
    print('%-22s mean diff %.3f  share over 40: %.4f' % (name, d.mean(), (d > 40).mean()))
# where does the difference concentrate? looks at the seam lines of the rolled picture (the original tile edge sits at the middle of B)
d = np.abs(np.roll(a, (h, h), axis=(0, 1)) - b).mean(axis=2)
print('diff on the lines that were the tile edge (x=h or y=h, band 3 dots): %.3f vs elsewhere %.3f' % (np.concatenate([d[h - 3:h + 3].ravel(), d[:, h - 3:h + 3].ravel()]).mean(), d.mean()))
ha = cv2.imread(G + '/S_v4/height.png', cv2.IMREAD_UNCHANGED).astype(float) / 257; hb = cv2.imread(G + '/S_v4_shifted/height.png', cv2.IMREAD_UNCHANGED).astype(float) / 257
ha = ha[..., 0] if ha.ndim == 3 else ha; hb = hb[..., 0] if hb.ndim == 3 else hb
print('height half-roll mean diff %.3f' % np.abs(np.roll(ha, (h, h), axis=(0, 1)) - hb).mean())
na = cv2.imread(G + '/S_v4/normal.png').astype(float); nb = cv2.imread(G + '/S_v4_shifted/normal.png').astype(float)
print('normal half-roll mean diff %.3f' % np.abs(np.roll(na, (h, h), axis=(0, 1)) - nb).mean())
