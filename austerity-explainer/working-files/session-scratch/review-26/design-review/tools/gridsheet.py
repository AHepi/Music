import sys, os
from PIL import Image, ImageDraw, ImageFont
out = sys.argv[1]; cols = int(sys.argv[2]); W = int(sys.argv[3]); paths = sys.argv[4:]
H = int(W * 1920 / 1080)
rows = (len(paths) + cols - 1) // cols
pad = 30; lab = 22
sheet = Image.new('RGB', (cols * (W + pad) + pad, rows * (H + lab + pad) + pad), (20, 20, 20))
d = ImageDraw.Draw(sheet)
font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 15)
small = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 11)
for i, p in enumerate(paths):
    im = Image.open(p).convert('RGB').resize((W, H), Image.LANCZOS)
    dd = ImageDraw.Draw(im, 'RGBA')
    for k in range(1, 10):
        y = int(H * k / 10)
        dd.line([(0, y), (W, y)], fill=(0, 255, 255, 110), width=1)
    for k in (1, 2):
        y = int(H * k / 3)
        dd.line([(0, y), (W, y)], fill=(255, 0, 255, 170), width=2)
    x = pad + (i % cols) * (W + pad); y0 = pad + (i // cols) * (H + lab + pad)
    sheet.paste(im, (x, y0 + lab))
    for k in range(1, 10):
        d.text((x - 24, y0 + lab + int(H * k / 10) - 6), f"{k*10}", fill=(0, 220, 220), font=small)
    name = os.path.splitext(os.path.basename(p))[0]
    if name.startswith('s') and name[1:].isdigit():
        t = int(name[1:]); name = f"{t//60}:{t%60:02d}"
    d.text((x + 2, y0 + 2), name, fill=(255, 220, 120), font=font)
sheet.save(out, quality=88); print(out, sheet.size)
