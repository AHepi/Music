# What this does: lays stills side by side at a chosen width, each labelled with its file name, into one sheet.
# Use: python3 sheet.py OUT.jpg WIDTH_EACH STILL ...
import sys
from PIL import Image, ImageDraw
out, width, files = sys.argv[1], int(sys.argv[2]), sys.argv[3:]
ims = [Image.open(f).convert('RGB') for f in files]
h = round(width * ims[0].height / ims[0].width)
sheet = Image.new('RGB', (width * len(ims), h + 24), (20, 20, 20))
d = ImageDraw.Draw(sheet)
for i, (f, im) in enumerate(zip(files, ims)):
    sheet.paste(im.resize((width, h)), (i * width, 24))
    d.text((i * width + 4, 4), f.split('/')[-1], fill=(255, 255, 255))
sheet.save(out, quality=88)
