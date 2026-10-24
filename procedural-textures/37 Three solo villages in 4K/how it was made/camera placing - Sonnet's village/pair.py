import sys
from PIL import Image, ImageDraw
out = sys.argv[1]; ims = [Image.open(p).convert('RGB') for p in sys.argv[2:]]
w = sum(i.width for i in ims) + 8 * (len(ims) - 1); h = max(i.height for i in ims)
c = Image.new('RGB', (w, h + 22), (20, 20, 20)); d = ImageDraw.Draw(c); x = 0
for p, i in zip(sys.argv[2:], ims):
    c.paste(i, (x, 22)); d.text((x + 4, 5), p.rsplit('/', 1)[-1], fill=(255, 255, 255)); x += i.width + 8
c.save(out, quality=90)
