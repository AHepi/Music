# What this does (plain words): measures a few general-character numbers of the moss (olive dots) of a colour picture so that the moss of a test bake
# can be compared with the reference's moss: the average olive colour, how yellow it is, and how big the olive pieces are. It copies nothing.
# Use: python3 -I moss_character.py reference|PICTURE.png ...
import os, sys
import cv2
import numpy as np
PROC = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..'))
def lab(p):
    l = cv2.cvtColor(p, cv2.COLOR_BGR2LAB).astype(np.float64)
    return l[...,0]*100/255, l[...,1]-128, l[...,2]-128
for name in sys.argv[1:]:
    path = os.path.join(PROC, 'reference', 'slate', 'colour.png') if name == 'reference' else name
    pic = cv2.imread(path)
    if pic.shape[0] != 900: pic = cv2.resize(pic, (900, 900), interpolation=cv2.INTER_AREA)
    L, a, b = lab(pic)
    olive = (b > 6) & (a < 1)
    n = olive.sum()
    chroma = np.hypot(a, b)
    closed = cv2.morphologyEx(olive.astype(np.uint8), cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)))
    cnt, lbl, stats, _ = cv2.connectedComponentsWithStats(closed, connectivity=8)
    areas = np.sort(stats[1:, cv2.CC_STAT_AREA])[::-1]
    tot = areas.sum()
    big = areas[areas >= 400].sum() / max(tot, 1)
    # greenish-grey wash (olive-ish but weaker): b* 2..6 and a* < 0
    wash = ((b > 2) & (b <= 6) & (a < 0)).mean() * 100
    # edge crispness: median gradient magnitude of L on olive boundary pixels
    edge = cv2.morphologyEx(olive.astype(np.uint8), cv2.MORPH_GRADIENT, np.ones((3,3), np.uint8)).astype(bool)
    gx = cv2.Sobel(L, cv2.CV_64F, 1, 0, ksize=3); gy = cv2.Sobel(L, cv2.CV_64F, 0, 1, ksize=3)
    grad = np.hypot(gx, gy)
    print(os.path.basename(os.path.dirname(path)) + '/' + os.path.basename(path) if name != 'reference' else 'reference',
          'olive%%=%.1f' % (olive.mean()*100), 'meanLab=%.1f/%.1f/%.1f' % (L[olive].mean(), a[olive].mean(), b[olive].mean()),
          'chroma=%.1f' % chroma[olive].mean(), 'pieces=%d' % (len(areas)), 'median_piece=%d' % np.median(areas), 'share_in_pieces>=400=%.0f%%' % (big*100),
          'weak_green_wash%%=%.1f' % wash, 'edge_grad=%.1f' % np.median(grad[edge]), 'olive_inner_grad=%.1f' % np.median(grad[olive]))
