import sys
from PIL import Image, ImageDraw, ImageFont
# usage: sheet.py OUT COLS WIDTH file1 [file2 ...]  ; label = file stem
out, cols, w = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
files = sys.argv[4:]
ims = [Image.open(f).convert('RGB') for f in files]
h = int(w * ims[0].height / ims[0].width)
rows = (len(ims) + cols - 1) // cols
pad = 26
sheet = Image.new('RGB', (cols * w, rows * (h + pad)), (20, 20, 20))
d = ImageDraw.Draw(sheet)
try:
    font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 18)
except Exception:
    font = ImageFont.load_default()
for i, (im, f) in enumerate(zip(ims, files)):
    r, c = divmod(i, cols)
    x, y = c * w, r * (h + pad)
    sheet.paste(im.resize((w, int(w * im.height / im.width))), (x, y + pad))
    lab = f.split('/')[-1].rsplit('.', 1)[0]
    d.text((x + 6, y + 3), lab, fill=(255, 230, 120), font=font)
sheet.save(out, quality=88)
print(out, sheet.size)
