"""What this does: makes a close-up sheet from filmed stills: each listed part of a still (a box in shares of the
frame's width and height) cut out, enlarged to the same height and laid side by side with a label under it, so a
small thing in the film (the men at the gate, a word on a drum, the smoke) can be looked at closely.
Use: python3 -I close_ups.py SPEC.json OUT.jpg [HEIGHT=600]
  SPEC.json: [{"still": "/path/still-54.70.jpg", "box": [x0, y0, x1, y1], "label": "W3 labels"}, ...]
"""
import json
import sys
import textwrap

from PIL import Image, ImageDraw, ImageFont

spec, out = json.load(open(sys.argv[1])), sys.argv[2]
height = int(sys.argv[3]) if len(sys.argv) > 3 else 600
font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 16)
parts = []
for item in spec:
    picture = Image.open(item['still']).convert('RGB')
    w, h = picture.size
    x0, y0, x1, y1 = item['box']
    crop = picture.crop((round(x0 * w), round(y0 * h), round(x1 * w), round(y1 * h)))
    if item.get('brighter'):
        crop = crop.point(lambda v: min(255, int(v * item['brighter'])))
    scale = height / crop.height
    parts.append((crop.resize((max(1, round(crop.width * scale)), height), Image.LANCZOS), item['label']))
label = 64
total = sum(p.width for p, _ in parts) + 8 * (len(parts) + 1)
sheet = Image.new('RGB', (total, height + label + 16), (24, 24, 26))
draw = ImageDraw.Draw(sheet)
x = 8
for picture, text in parts:
    sheet.paste(picture, (x, 8))
    for k, line in enumerate(textwrap.wrap(text, width=max(12, picture.width // 9))[:3]):
        draw.text((x + 4, height + 12 + k * 19), line, fill=(230, 230, 230), font=font)
    x += picture.width + 8
sheet.save(out, quality=90)
print(out, sheet.size)
