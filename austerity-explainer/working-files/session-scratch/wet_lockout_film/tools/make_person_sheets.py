"""What this file does (plain words): makes the two sheets for the person from the dry and the wet clip (JPEG, under 400 KB each):
  "27 Before and after - dry and wet lockout, same moments.jpg"   six moments, the dry street on the top row, the wet street under it
  "27 Every half second - wet lockout.jpg"                         the wet clip at every half second (24 frames)
Frames are read from the finished clips (so the sheets show what the clips show). Run: python3 -I make_person_sheets.py DRY.mp4 WET.mp4 OUT_FOLDER
"""
import os, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
dry, wet, out = sys.argv[1:4]
os.makedirs(out, exist_ok=True)
def frame(clip, t, size):
    n = int(round(t * 30))
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', clip, '-vf', f'select=eq(n\\,{n}),scale={size[0]}:{size[1]}:flags=area', '-frames:v', '1', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], capture_output=True, check=True).stdout
    return Image.fromarray(np.frombuffer(raw, np.uint8).reshape(size[1], size[0], 3))
def font(size):
    for f in ('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', '/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf'):
        if os.path.exists(f): return ImageFont.truetype(f, size)
    return ImageFont.load_default()
def save_under(img, path, limit=395_000):
    for q in (86, 82, 78, 74, 70, 66, 62, 58):
        img.save(path, quality=q, optimize=True)
        if os.path.getsize(path) <= limit: return q, os.path.getsize(path)
    return q, os.path.getsize(path)
# 1. before and after, six moments
moments = [(1.5, 'title, before the move'), (3.0, 'the move begins'), (4.5, 'half way'), (6.0, 'nearly there'), (7.1, 'the move ends'), (9.5, 'the notice')]
cw, ch = 292, 520; gap = 6; left = 70; top = 44
W_ = left + 6 * (cw + gap); H_ = top + 2 * (ch + gap) + 4
sheet = Image.new('RGB', (W_, H_), (18, 18, 20)); d = ImageDraw.Draw(sheet)
d.text((8, 10), 'Dry street (the film so far) above, wet street (now in the film) below, the same moment of the 12-second clip', fill=(235, 235, 235), font=font(15))
for row, (clip, label) in enumerate(((dry, 'DRY'), (wet, 'WET'))):
    y = top + row * (ch + gap)
    d.text((10, y + ch // 2 - 8), label, fill=(255, 210, 120) if row else (170, 200, 255), font=font(18))
    for i, (t, _) in enumerate(moments):
        sheet.paste(frame(clip, t, (cw, ch)), (left + i * (cw + gap), y))
for i, (t, text) in enumerate(moments):
    d.text((left + i * (cw + gap) + 4, top - 17), f'{t:.1f} s  {text}', fill=(235, 235, 235), font=font(13))
print('before and after', save_under(sheet, os.path.join(out, '27 Before and after - dry and wet lockout, same moments.jpg')))
# 2. every half second, wet
cols, rows = 8, 3; cw, ch = 226, 402
sheet = Image.new('RGB', (cols * (cw + 4) + 4, rows * (ch + 4) + 4), (18, 18, 20)); d = ImageDraw.Draw(sheet)
for k in range(24):
    t = k * 0.5
    x, y = 4 + (k % cols) * (cw + 4), 4 + (k // cols) * (ch + 4)
    sheet.paste(frame(wet, t, (cw, ch)), (x, y))
    d.rectangle([x, y, x + 46, y + 15], fill=(0, 0, 0)); d.text((x + 3, y + 1), f'{t:4.1f} s', fill=(255, 235, 120), font=font(12))
print('every half second', save_under(sheet, os.path.join(out, '27 Every half second - wet lockout.jpg')))
