"""Plain note: our own small checker. Compares two same-size 8-bit pictures dot by dot and prints the average error in brightness
steps (0-255), the share of dots that differ by more than 2 steps, and the same numbers away from picture edges."""
import sys, numpy as np, cv2
a = cv2.imread(sys.argv[1], cv2.IMREAD_UNCHANGED)[..., :3].astype(float)
b = cv2.imread(sys.argv[2], cv2.IMREAD_UNCHANGED)[..., :3].astype(float)
assert a.shape == b.shape, (a.shape, b.shape)
d = np.abs(a - b)
grey = a.mean(axis=2).astype(np.uint8)
edges = cv2.dilate(cv2.Canny(grey, 20, 60), np.ones((5,5),np.uint8)) > 0
print('mean abs error %.3f steps | share >2 steps %.2f%% | share >8 steps %.2f%% | max %.0f' % (d.mean(), 100*(d.max(axis=2)>2).mean(), 100*(d.max(axis=2)>8).mean(), d.max()))
print('   interior (away from edges): mean %.3f, share >2 steps %.2f%%   | on edges: mean %.3f' % (d[~edges].mean(), 100*(d[~edges].max(axis=1)>2).mean(), d[edges].mean() if edges.any() else 0))
print('   mean of A %.2f, mean of B %.2f' % (a.mean(), b.mean()))
