"""What this does: looks through a finished film for sudden jumps between frames (a painting switching over, a
prop popping, a flash) and makes a contact sheet of two frames a second to look at the motion. Each frame is
compared with the one before; a frame whose change is far bigger than its neighbours' (more than JUMP times the
middle value of the 5 frames either side, and over a small floor) is listed with its time. A planned cut shows
up too: say which times are cuts and they are reported as planned.

Use: python3 -I find_jumps.py FILM.mp4 SHEET.jpg [JUMP=4] [PLANNED_CUT_SECONDS ...]
"""
import json
import subprocess
import sys

import numpy as np
from PIL import Image

film, sheet_path = sys.argv[1], sys.argv[2]
jump = float(sys.argv[3]) if len(sys.argv) > 3 else 4.0
planned = [float(t) for t in sys.argv[4:]]
probe = json.loads(subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=width,height,r_frame_rate',
                                   '-of', 'json', film], capture_output=True, text=True, check=True).stdout)['streams'][0]
num, den = (int(v) for v in probe['r_frame_rate'].split('/'))
fps = num / den
width, height = 270, 480   # small and grey is enough to see a jump
raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', film, '-vf', f'scale={width}:{height},format=gray', '-f', 'rawvideo', '-'],
                     capture_output=True, check=True).stdout
frames = np.frombuffer(raw, np.uint8).reshape(-1, height, width).astype(np.float32)
change = np.abs(np.diff(frames, axis=0)).mean(axis=(1, 2))   # change[i]: from frame i to frame i + 1
print(f'{len(frames)} frames at {fps:g} a second; change between frames: middle {np.median(change):.2f}, largest {change.max():.2f} '
      f'(into frame {change.argmax() + 1}, {(change.argmax() + 1) / fps:.2f} s)')
found = []
for i, c in enumerate(change):
    around = np.concatenate([change[max(0, i - 5):i], change[i + 1:i + 6]])
    if len(around) and c > jump * max(np.median(around), 0.05) and c > 1.0:
        t = (i + 1) / fps
        kind = 'planned cut' if any(abs(t - p) < 1.5 / fps for p in planned) else 'JUMP'
        found.append(f'{kind} into frame {i + 1} ({t:.2f} s): change {c:.2f}, around it {np.median(around):.2f}')
print('\n'.join(found) if found else 'no jumps')
# the contact sheet: two frames a second, in rows of eight
colour = subprocess.run(['ffmpeg', '-v', 'error', '-i', film, '-vf', f'fps=2,scale={width // 2}:{height // 2}', '-f', 'rawvideo',
                         '-pix_fmt', 'rgb24', '-'], capture_output=True, check=True).stdout
thumbs = np.frombuffer(colour, np.uint8).reshape(-1, height // 2, width // 2, 3)
per_row = 8
rows = (len(thumbs) + per_row - 1) // per_row
sheet = Image.new('RGB', (per_row * (width // 2 + 4), rows * (height // 2 + 4)), (15, 15, 15))
for k, thumb in enumerate(thumbs):
    sheet.paste(Image.fromarray(thumb), ((k % per_row) * (width // 2 + 4), (k // per_row) * (height // 2 + 4)))
sheet.save(sheet_path, quality=88)
print(f'sheet of {len(thumbs)} frames (two a second): {sheet_path}')
