"""What this does: measures, frame by frame, how strongly a label's words show in the filmed pages: the share of
near-white pixels (all three colours above 200) inside a box of the frame, for a stretch of chapter frames, so the
time a label is readable (from its first frame at full strength to the cut) can be read off.
Use: python3 -I label_strength.py FILM.mp4 FIRST_CHAPTER_FRAME FROM_FRAME TO_FRAME x0 y0 x1 y1 (box in shares of the frame)
"""
import subprocess
import sys

import numpy as np

film, first, a, b = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4])
x0, y0, x1, y1 = (float(v) for v in sys.argv[5:9])
W, H = 1080, 1920
cx, cy, cw, ch = (2 * round(v / 2) for v in (x0 * W, y0 * H, (x1 - x0) * W, (y1 - y0) * H))
raw = subprocess.run(['ffmpeg', '-v', 'error', '-ss', f'{(a - first) / 30:.4f}', '-i', film, '-frames:v', str(b - a + 1),
                      '-vf', f'crop={cw}:{ch}:{cx}:{cy}', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], capture_output=True, check=True).stdout
frames = np.frombuffer(raw, np.uint8).reshape(-1, ch, cw, 3)
values = [(f[..., 0] > 200) & (f[..., 1] > 200) & (f[..., 2] > 200) for f in frames]
top = max(v.mean() for v in values) or 1
for i, v in enumerate(values):
    print(f'frame {a + i} ({(a + i) / 30:.2f} s): {100 * v.mean():5.2f}% white, {100 * v.mean() / top:5.1f}% of the most')
