# What this does (plain words): looks ONCE at the general colour character of a slate picture (reference or baked): the average colour of
# slate dots in three brightness bands, how far from neutral grey (blue-teal-ness), and the share of olive (moss) and tan (damage) dots.
# This is a measurement used to choose default settings by hand. Nothing is copied slate by slate.
import sys
import cv2
import numpy as np
PROC = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work'
def report(name, path):
    img = cv2.imread(path)
    rgb = img[..., ::-1].astype(np.float32)
    bright = rgb.mean(axis=2)
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB).astype(np.float32)
    a, b = lab[..., 1] - 128, lab[..., 2] - 128
    slate = bright > 30
    print(name)
    for lo, hi in ((30, 50), (50, 70), (70, 90), (90, 255)):
        m = (bright >= lo) & (bright < hi)
        if m.sum():
            print(f'   brightness {lo}-{hi}: share {m.mean()*100:5.1f}%  mean rgb {tuple(int(v) for v in rgb[m].mean(axis=0))}  Lab a {a[m].mean():5.1f} b {b[m].mean():5.1f}')
    # olive: red and green above blue clearly (b of Lab > 4) ; tan: red > green > blue and bright
    r, g, bl = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    olive = (g >= bl + 8) & (r >= bl + 4) & (bright < 110) & (bright > 35) & (np.abs(r - g) < 22)
    tan = (r > bl + 14) & (r >= g) & (bright > 70)
    print(f'   share olive-ish dots {olive.mean()*100:.1f}%   share tan/pale-warm dots {tan.mean()*100:.1f}%   share very dark (<30) {np.mean(bright<30)*100:.1f}%')
report('reference', PROC + '/reference/slate/colour.png')
for p in sys.argv[1:]:
    report(p, p)
