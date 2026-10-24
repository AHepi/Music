# Contact sheet: one row per view, pass 1 left, pass 2 right. args: OUT ROWS_JSON
# ROWS_JSON: [[label, pass1_jpg, pass2_jpg], ...]
import sys, json
from PIL import Image, ImageDraw, ImageFont
out, rows = sys.argv[1], json.load(open(sys.argv[2]))
W, H, PAD, LAB = 600, 400, 8, 26
try:
    font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 17)
    bold = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 20)
except Exception:
    font = bold = ImageFont.load_default()
head = 40
sheet = Image.new('RGB', (PAD + 2 * (W + PAD), head + len(rows) * (LAB + H + PAD)), (24, 24, 24))
d = ImageDraw.Draw(sheet)
d.text((PAD, 10), 'First pass (village_pass1)', fill=(235, 235, 235), font=bold)
d.text((PAD + W + PAD, 10), 'Second pass (village)', fill=(235, 235, 235), font=bold)
y = head
for label, p1, p2 in rows:
    for i, p in enumerate((p1, p2)):
        x = PAD + i * (W + PAD)
        d.text((x, y + 4), label, fill=(255, 220, 120), font=font)
        try:
            im = Image.open(p).convert('RGB').resize((W, H), Image.LANCZOS)
            sheet.paste(im, (x, y + LAB))
        except Exception as e:
            d.text((x + 10, y + LAB + 10), 'missing: %s' % e, fill=(255, 80, 80), font=font)
    y += LAB + H + PAD
sheet.save(out, quality=88)
print('sheet', sheet.size)
