# What this does (plain words): measures how the brightness variation of a slate picture splits up: how much of it is "the same on every
# column" (up-and-down structure: joints, shadow bands, the dark-to-light run inside a row) and how much is sideways variation
# (different slates, different streaks). Used once to find out why the "feature size along x" number of the first full bake was far
# from the reference. It only measures; nothing is copied from the reference into the recipe.
import sys
import cv2
import numpy as np
PROC = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work'
def lightness(path):
    img = cv2.imread(path)
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB).astype(np.float32)
    return lab[..., 0] * 100.0 / 255.0
for name, path in (('reference', PROC + '/reference/slate/colour.png'), ('candidate', sys.argv[1])):
    L = lightness(path)
    total = L.var()
    rowprofile = L.mean(axis=1, keepdims=True) * np.ones((1, L.shape[1]))
    rest = L - rowprofile
    # upper-slate-only part: ignore joints (very dark dots)
    slate = L > 14
    print(f'{name}: mean {L.mean():.1f}  std {L.std():.1f}  share of variance that is the same along each row: {rowprofile.var()/total:.2f}  '
          f'share dark joints (L<14): {1-slate.mean():.3f}  slate-only mean {L[slate].mean():.1f} std {L[slate].std():.1f}')
    # horizontal autocorrelation of slate-only picture at a few lags (rows of dots)
    c = L - L.mean()
    ac = np.fft.ifft2(np.abs(np.fft.fft2(c))**2).real; ac /= ac[0,0]
    print('   x-autocorr at lag 8,16,32,64,128,256:', [round(float(ac[0, k]), 2) for k in (8,16,32,64,128,256)], ' y lags 8,16,32,64:', [round(float(ac[k,0]),2) for k in (8,16,32,64)])
