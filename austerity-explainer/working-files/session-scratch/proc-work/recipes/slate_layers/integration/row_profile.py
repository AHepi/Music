# What this does (plain words): draws the average brightness of every picture row (one number per row of dots, averaged across the whole width) for the
# reference and for baked pictures, so the dark joint bands and the dark-to-light run down a slate can be compared. Use: python3 -I row_profile.py OUT.png PICTURE ...
import sys, cv2, numpy as np
PROC = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work'
out = sys.argv[1]
pics = [('reference', PROC + '/reference/slate/colour.png', (0, 0, 255))] + [(p.split('/')[-1], p, c) for p, c in zip(sys.argv[2:], [(255, 120, 0), (0, 160, 0), (200, 0, 200)])]
canvas = np.full((420, 1254, 3), 255, np.uint8)
stats = []
for name, path, colour in pics:
    img = cv2.imread(path); img = cv2.resize(img, (1254, 1254), interpolation=cv2.INTER_AREA)
    L = cv2.cvtColor(img, cv2.COLOR_BGR2LAB).astype(np.float32)[..., 0] * 100 / 255
    prof = L.mean(1)
    pts = np.stack([np.arange(1254), 400 - prof * 5.5], 1).astype(np.int32)
    cv2.polylines(canvas, [pts], False, colour, 1)
    stats.append((name, float(prof.std()), float(prof.min()), float(prof.max())))
for i, (n, s, lo, hi) in enumerate(stats):
    cv2.putText(canvas, f'{n}: profile std {s:.1f} min {lo:.1f} max {hi:.1f}', (10, 20 + 18 * i), cv2.FONT_HERSHEY_SIMPLEX, 0.5, pics[i][2], 1)
cv2.imwrite(out, canvas)
for s in stats: print(s)
