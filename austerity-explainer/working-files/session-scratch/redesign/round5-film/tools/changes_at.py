"""What this does: prints how much each frame changes from the one before (the jump finder's measure: small grey
frames, the average difference in levels) for the chapter frames asked about, so a planned moment (a cut, the first
frames of a page turn, the run-on) can be checked frame by frame in the joined film.
Use: python3 -I changes_at.py FILM.mp4 FIRST_CHAPTER_FRAME FROM_FRAME-TO_FRAME ... (chapter frames)"""
import subprocess
import sys

import numpy as np

film, first = sys.argv[1], int(sys.argv[2])
for span in sys.argv[3:]:
    a, b = (int(v) for v in span.split('-'))
    start = (a - 1 - first) / 30
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-ss', f'{start:.4f}', '-i', film, '-frames:v', str(b - a + 2), '-vf', 'scale=270:480,format=gray',
                          '-f', 'rawvideo', '-'], capture_output=True, check=True).stdout
    frames = np.frombuffer(raw, np.uint8).reshape(-1, 480, 270).astype(np.float32)
    change = np.abs(np.diff(frames, axis=0)).mean(axis=(1, 2))
    print(f'frames {a}-{b}: ' + ', '.join(f'{a + i} ({(a + i) / 30:.2f} s) {c:.2f}' for i, c in enumerate(change)))
