# What this file does (plain words): makes a contact sheet of ground crops from a list of pictures, with a label above each, for the checker's own looking. Use: python3 -I make_my_sheet.py OUT.jpg COLUMNS CROP_TOP_SHARE PICTURE [PICTURE ...]
import sys
from PIL import Image, ImageDraw
out, cols, top = sys.argv[1], int(sys.argv[2]), float(sys.argv[3])
paths = sys.argv[4:]
tiles = []
for p in paths:
    im = Image.open(p).convert('RGB')
    w, h = im.size
    im = im.crop((0, int(h * top), w, h))
    tiles.append((p.split('/')[-1].replace('.jpg', ''), im))
tw = max(t[1].size[0] for t in tiles); th = max(t[1].size[1] for t in tiles)
rows = (len(tiles) + cols - 1) // cols
sheet = Image.new('RGB', (cols * (tw + 4), rows * (th + 22)), (20, 20, 20))
d = ImageDraw.Draw(sheet)
for i, (name, im) in enumerate(tiles):
    x, y = (i % cols) * (tw + 4), (i // cols) * (th + 22)
    d.text((x + 3, y + 5), name, fill=(235, 235, 160))
    sheet.paste(im, (x, y + 20))
sheet.save(out, quality=90)
print(sheet.size)
