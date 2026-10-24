import sys, os
from PIL import Image, ImageDraw, ImageFont
# usage: sheet.py out.jpg cols width paths...
out = sys.argv[1]; cols = int(sys.argv[2]); W = int(sys.argv[3]); paths = sys.argv[4:]
H = int(W * 1920 / 1080)
rows = (len(paths) + cols - 1) // cols
pad = 6; lab = 22
sheet = Image.new('RGB', (cols * (W + pad) + pad, rows * (H + lab + pad) + pad), (20, 20, 20))
d = ImageDraw.Draw(sheet)
try:
    font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 16)
except Exception:
    font = ImageFont.load_default()
for i, p in enumerate(paths):
    im = Image.open(p).convert('RGB').resize((W, H), Image.LANCZOS)
    x = pad + (i % cols) * (W + pad); y = pad + (i // cols) * (H + lab + pad)
    sheet.paste(im, (x, y + lab))
    name = os.path.splitext(os.path.basename(p))[0]
    if name.startswith('s') and name[1:].isdigit():
        t = int(name[1:]); name = f"{t//60}:{t%60:02d} ({t}s)"
    d.text((x + 2, y + 2), name, fill=(255, 220, 120), font=font)
sheet.save(out, quality=88)
print(out, sheet.size)
