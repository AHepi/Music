# What this does: puts several pictures side by side at a chosen scale, with a small caption each, for looking.
import sys
from PIL import Image, ImageDraw
out = sys.argv[1]; scale = float(sys.argv[2]); files = sys.argv[3:]
ims = [Image.open(f).convert('RGB') for f in files]
ims = [im.resize((int(im.width*scale), int(im.height*scale)), Image.LANCZOS) for im in ims]
W = sum(im.width for im in ims) + 6*(len(ims)-1); H = max(im.height for im in ims) + 24
sheet = Image.new('RGB', (W, H), (255,255,255)); d = ImageDraw.Draw(sheet); x = 0
for f, im in zip(files, ims):
    sheet.paste(im, (x, 24)); d.text((x+4, 4), f.split('/')[-1], fill=(0,0,0)); x += im.width + 6
sheet.save(out, quality=92)
