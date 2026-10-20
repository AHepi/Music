# What this does (plain words): cuts matching zoomed-in squares out of the reference, the BEFORE tile and the AFTER tile and puts them
# side by side (reference | before | after) as one JPEG, so a person can compare them at close range.
# Use: python3 -I make_crops.py OUT.jpg zoom size  refx refy  bx by  ax ay   (each pair is the top-left corner of the square in that picture)
import sys
from PIL import Image, ImageDraw
P = 'proc-work/'
paths = [P + 'reference/slate/colour.png', P + 'recipes/slate_layers/outputs/default_before_look_fixes/colour.png', P + 'recipes/slate_layers/outputs/default/colour.png']
out, zoom, size = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
pts = [(int(sys.argv[4 + 2 * i]), int(sys.argv[5 + 2 * i])) for i in range(3)]
tiles = []
for path, (x, y) in zip(paths, pts):
    im = Image.open(path).convert('RGB').crop((x, y, x + size, y + size)).resize((size * zoom, size * zoom), Image.LANCZOS)
    tiles.append(im)
W = size * zoom
sheet = Image.new('RGB', (W * 3 + 20, W + 22), (255, 255, 255))
d = ImageDraw.Draw(sheet)
for i, (im, name) in enumerate(zip(tiles, ['REFERENCE', 'BEFORE', 'AFTER'])):
    sheet.paste(im, (i * (W + 10), 22))
    d.text((i * (W + 10) + 4, 5), name, fill=(0, 0, 0))
sheet.save(out, quality=90)
