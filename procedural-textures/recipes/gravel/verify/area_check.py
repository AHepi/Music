# Verifier script: independent check of the 2508 x 2508 area picture: seams at the middle and wrap lines, quadrant similarity, repeats (shifted self-correlation at all shifts of one quadrant against the rest).
import cv2, numpy as np, os
G = 'proc-work/recipes/gravel'
img = cv2.imread(G + '/area/out/area_2508/colour.png').astype(np.float64)
print('shape', img.shape)
n = img.shape[0]; h = n // 2
dc = np.abs(np.diff(img, axis=1, append=img[:, :1])).mean(axis=(0, 2))   # change between col i and i+1, wrapping
dr = np.abs(np.diff(img, axis=0, append=img[:1])).mean(axis=(1, 2))
for name, arr in (('col', dc), ('row', dr)):
    med = np.median(arr)
    print(name, 'median jump %.2f' % med, 'middle ratio %.3f' % (arr[h - 1] / med), 'wrap ratio %.3f' % (arr[n - 1] / med), 'max ratio over all lines %.3f' % (arr.max() / med),
          'rank of middle line among all lines (0=largest) %d of %d' % ((arr > arr[h - 1]).sum(), n))
g = cv2.cvtColor(img.astype(np.uint8), cv2.COLOR_BGR2GRAY).astype(np.float64)
q = [g[:h, :h], g[:h, h:], g[h:, :h], g[h:, h:]]
def ncc(a, b):
    a = (a - a.mean()) / a.std(); b = (b - b.mean()) / b.std()
    f = np.fft.ifft2(np.fft.fft2(a) * np.conj(np.fft.fft2(b))).real / a.size
    return f
peaks = []
for i in range(4):
    for j in range(i + 1, 4):
        f = ncc(q[i], q[j]); peaks.append(round(float(f.max()), 3))
print('quadrant cross-correlation peaks (wrapped shifts)', peaks)
# self-similarity of the whole picture at half shifts: area vs itself rolled by exactly half
for s in ((h, 0), (0, h), (h, h)):
    r = np.roll(g, s, axis=(0, 1)); print('whole picture vs itself rolled by', s, 'mean abs grey difference %.1f' % np.abs(r - g).mean(), 'correlation %.3f' % np.corrcoef(r.ravel(), g.ravel())[0, 1])
# autocorrelation of the whole picture: any peak other than at zero shift would mean a repeat (period)
f = ncc(g[:1024, :1024], g[:1024, :1024]); f[0, 0] = 0; f[:3, :3] = 0; f[-3:, -3:] = 0; f[:3, -3:] = 0; f[-3:, :3] = 0
print('best non-zero-shift self-correlation inside a 1024 crop: %.3f' % f.max())
# the 1254 S_v4 tile vs a quadrant of the area: any shared content?
s = cv2.cvtColor(cv2.imread(G + '/verify/S_v4/colour.png'), cv2.COLOR_BGR2GRAY).astype(np.float64)
print('S_v4 tile vs area quadrant best correlation: %.3f' % max(float(ncc(s, qq[:1254, :1254] if qq.shape[0] >= 1254 else np.pad(qq, ((0, 1254 - qq.shape[0]),) * 2 + ())).max()) for qq in [g[:1254, :1254], g[1254:, 1254:]]))
