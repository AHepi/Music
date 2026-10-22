import sys
from PIL import Image, ImageDraw
# usage: contact.py OUT.jpg COLS TILEW img1 img2 ...   (label = file stem)
out, cols, tw = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
paths = sys.argv[4:]
ims = []
for p in paths:
    im = Image.open(p).convert('RGB')
    h = int(im.height * tw / im.width)
    ims.append((p.rsplit('/', 1)[-1].rsplit('.', 1)[0], im.resize((tw, h), Image.LANCZOS)))
rows = (len(ims) + cols - 1) // cols
th = max(i.height for _, i in ims)
sheet = Image.new('RGB', (cols * tw, rows * (th + 16)), (30, 30, 30))
d = ImageDraw.Draw(sheet)
for k, (n, im) in enumerate(ims):
    x, y = (k % cols) * tw, (k // cols) * (th + 16)
    sheet.paste(im, (x, y + 16))
    d.text((x + 4, y + 2), n, fill=(255, 255, 255))
sheet.save(out, quality=88)
print(out, sheet.size)
