import sys
from PIL import Image, ImageDraw
paths = sys.argv[2:]; out = sys.argv[1]
ims = [Image.open(p).convert('RGB') for p in paths]
w = max(i.width for i in ims); h = max(i.height for i in ims)
W = w * len(ims); sheet = Image.new('RGB', (W, h + 18), (20, 20, 20))
d = ImageDraw.Draw(sheet)
for k, (p, im) in enumerate(zip(paths, ims)):
    sheet.paste(im, (k * w, 18)); d.text((k * w + 4, 3), p.split('/')[-1], fill=(255, 255, 255))
sheet.save(out, quality=88)
