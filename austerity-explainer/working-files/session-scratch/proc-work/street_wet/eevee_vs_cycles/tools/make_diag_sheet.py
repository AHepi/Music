# What this file does (plain words): makes the extra sheet "why the two pictures differ": four pictures of the main street, wet, side by side (EEVEE as drawn, EEVEE with the lamps allowed to reach further,
# Cycles as drawn, Cycles with the sky-dome mesh taken out of the lighting). A test sheet, not a pair: these four are NOT the same settings. Plain Python (Pillow).
import os, json
import numpy as np
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__)); E = os.path.abspath(os.path.join(HERE, '..')); W = E + '/work/'
OUT = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/26 EEVEE and Cycles side by side - pictures/26 Extra - why the pictures differ - four tests on the wet main street.jpg'
F = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'; FB = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
def sec(p): return float(open(p).read().strip())
def L(path):
    a = np.asarray(Image.open(path).convert('RGB'), dtype=np.float32) / 255
    return float((0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2]).mean())
panels = [
    ('EEVEE as the plates are drawn', W + 'runA/out/main_wet_eevee.png', sec(W + 'runA/out/main_wet_eevee_seconds.txt'), (120, 190, 255)),
    ('EEVEE, light threshold 0.01 -> 0.0001', W + 'runD/out/dg_main_eevee_threshold_0001.png', sec(W + 'runD/out/dg_main_eevee_threshold_0001_seconds.txt'), (120, 190, 255)),
    ('Cycles as drawn', W + 'runA/out/main_wet_cycles.png', sec(W + 'runA/out/main_wet_cycles_seconds.txt'), (255, 190, 110)),
    ('Cycles, sky-dome mesh out of the light', W + 'runD/out/dg_main_cycles_domedark.png', sec(W + 'runD/out/dg_main_cycles_domedark_seconds.txt'), (255, 190, 110)),
]
w = 400; h = 711; pad = 14; gap = 10; head = 70; foot = 74
Wd = pad * 2 + 4 * w + 3 * gap; Hd = head + h + foot
c = Image.new('RGB', (Wd, Hd), (24, 24, 26)); d = ImageDraw.Draw(c)
d.text((pad, 10), 'Why the two pictures differ: four tests on the wet main street (1080 x 1920, shown at 37 %)', font=ImageFont.truetype(FB, 19), fill=(235, 235, 235))
d.text((pad, 40), 'These four are NOT a pair (settings differ on purpose, to find the cause). Nothing in the layers was changed.', font=ImageFont.truetype(F, 13), fill=(170, 170, 175))
for i, (label, path, secs, col) in enumerate(panels):
    x = pad + i * (w + gap)
    c.paste(Image.open(path).convert('RGB').resize((w, h), Image.LANCZOS), (x, head))
    d.text((x, head + h + 6), label, font=ImageFont.truetype(FB, 13), fill=col)
    d.text((x, head + h + 26), f'brightness {L(path):.3f}   drawn in {secs:.1f} s', font=ImageFont.truetype(F, 13), fill=(235, 235, 235))
d.text((pad + 1 * (w + gap), head + h + 46), 'lamps reach the road', font=ImageFont.truetype(F, 12), fill=(170, 170, 175))
d.text((pad + 3 * (w + gap), head + h + 46), 'sky reflection on the road changes', font=ImageFont.truetype(F, 12), fill=(170, 170, 175))
for q in range(92, 40, -2):
    c.save(OUT, 'JPEG', quality=q, optimize=True, progressive=True)
    if os.path.getsize(OUT) <= 390_000:
        break
print(os.path.basename(OUT), c.size, q, os.path.getsize(OUT) // 1024, 'KB')
