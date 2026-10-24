# What this does: a frame-to-frame check of a film. It reads every frame (small, grey), measures how
# much each frame differs from the one before, and lists frames that jump far more than their
# neighbours (a sudden pop, flicker or snap), plus a sheet of one frame every half second.
# Use: python3 motion_scan.py FILM.mp4 OUT_FOLDER
import subprocess, sys, os
import numpy as np
from PIL import Image

film, out = sys.argv[1], sys.argv[2]
os.makedirs(out, exist_ok=True)
width, height = 135, 240
raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', film, '-vf', f'scale={width}:{height}', '-f', 'rawvideo', '-pix_fmt', 'gray', '-'],
                     capture_output=True, check=True).stdout
frames = np.frombuffer(raw, np.uint8).reshape(-1, height, width).astype(np.float32)
diffs = np.abs(np.diff(frames, axis=0)).mean(axis=(1, 2))
print(f'{len(frames)} frames; mean change {diffs.mean():.2f}, largest {diffs.max():.2f} at frame {diffs.argmax() + 1}')
flagged = []
for i, d in enumerate(diffs):
    around = np.concatenate([diffs[max(0, i - 4):i], diffs[i + 1:i + 5]])
    usual = np.median(around) if len(around) else 0
    if d > 3 * usual + 1.0:
        flagged.append((i + 1, d, usual))
for frame, d, usual in flagged:
    print(f'  jump at frame {frame} ({frame / 30:.2f} s): change {d:.2f}, around it {usual:.2f}')
# the sheet: one frame every half second
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', film, '-vf', 'fps=2,scale=270:480,tile=8x3', '-frames:v', '1', os.path.join(out, 'sheet.jpg')], check=True)
