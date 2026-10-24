"""What this does (scratch, round 6 set): compares two pictures of the same view (a state before and after), e.g. W1 quiet
and W1 working: the mean level (0-255, the brightest channel... here the mean of R, G, B) of the whole frame, of its bottom
30%, and the share of the frame that changed by more than 6 levels (2-pixel blur, largest channel) or 3 levels (10-pixel
blur), as make_state_picture.py counts it. Optionally the mean of a box given as fractions x0,y0,x1,y1.
Use: python3 measure_pair.py BEFORE AFTER [--box x0,y0,x1,y1 ...]"""
import sys
import cv2
import numpy as np

a, b = cv2.imread(sys.argv[1]).astype(np.float32), cv2.imread(sys.argv[2]).astype(np.float32)
if a.shape != b.shape:
    b = cv2.resize(b, (a.shape[1], a.shape[0]), interpolation=cv2.INTER_AREA)
h, w = a.shape[:2]
unit = w / 1536
blur = lambda p, s: cv2.GaussianBlur(p, (0, 0), s * unit)
diff = np.abs(blur(a, 2) - blur(b, 2)).max(axis=2)
smooth = np.abs(blur(a, 10) - blur(b, 10)).max(axis=2)
changed = (diff > 6) | (smooth > 3)
print(f'frame mean {a.mean():.1f} -> {b.mean():.1f}; bottom 30% mean {a[int(h*0.7):].mean():.1f} -> {b[int(h*0.7):].mean():.1f}; '
      f'changed (6 / faint 3): {changed.mean()*100:.1f}% of the frame; bottom 30% changed {changed[int(h*0.7):].mean()*100:.1f}%')
args = sys.argv[3:]
for k, arg in enumerate(args):
    if arg == '--box':
        x0, y0, x1, y1 = [float(v) for v in args[k + 1].split(',')]
        box = (slice(int(y0 * h), int(y1 * h)), slice(int(x0 * w), int(x1 * w)))
        print(f'  box {args[k+1]}: {a[box].mean():.1f} -> {b[box].mean():.1f}')
