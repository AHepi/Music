"""What this does: a contact sheet of a filmed stretch of a chapter, one frame a second: the frame at every whole
chapter second (00:48, 00:49 ...), each about phone-thumbnail size with its chapter time and the shot under it, in
rows of ten, so the whole stretch can be seen at a glance.
Use: python3 -I contact_sheet_seconds.py FILM.mp4 FIRST_CHAPTER_FRAME OUT.jpg [SHOTS.json: [[from, to, "name"], ...]]
"""
import json
import math
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

film, first, out = sys.argv[1], int(sys.argv[2]), sys.argv[3]
shots = json.load(open(sys.argv[4])) if len(sys.argv) > 4 else []
FPS, W, H, PER_ROW, GAP, LABEL = 30, 180, 320, 10, 6, 40
raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', film, '-vf', f'scale={W}:{H}:flags=lanczos', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'],
                     capture_output=True, check=True).stdout
frames = np.frombuffer(raw, np.uint8).reshape(-1, H, W, 3)
picks = [s * FPS - first for s in range(math.ceil(first / FPS), math.floor((first + len(frames) - 1) / FPS) + 1)]
rows = (len(picks) + PER_ROW - 1) // PER_ROW
sheet = Image.new('RGB', (PER_ROW * (W + GAP) + GAP, rows * (H + LABEL + GAP) + GAP), (22, 22, 24))
draw = ImageDraw.Draw(sheet)
try:
    font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 15)
    small = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 12)
except OSError:
    font = small = ImageFont.load_default()
for k, index in enumerate(picks):
    x, y = GAP + (k % PER_ROW) * (W + GAP), GAP + (k // PER_ROW) * (H + LABEL + GAP)
    sheet.paste(Image.fromarray(frames[index]), (x, y))
    seconds = (index + first) / FPS
    shot = next((name for a, b, name in shots if a <= seconds < b), '')
    draw.text((x + 3, y + H + 3), f'{int(seconds) // 60}:{int(seconds) % 60:02d}  ({seconds:.0f} s)', fill=(235, 235, 235), font=font)
    draw.text((x + 3, y + H + 22), shot, fill=(170, 170, 170), font=small)
sheet.save(out, quality=90)
print(f'{out}: {len(picks)} frames, one a second, {sheet.size[0]} x {sheet.size[1]}')
