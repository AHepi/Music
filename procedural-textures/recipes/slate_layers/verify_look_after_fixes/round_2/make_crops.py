# What this does (plain words): cuts matching squares out of the reference, the BEFORE tile and the AFTER tile (or any three pictures)
# and puts them side by side as one JPEG so a person can compare them at close range. Same idea as the round 1 checker's make_crops.py.
# Use: python3 -I make_crops.py OUT.jpg zoom size  refx refy  bx by  ax ay [which]   (each pair = top-left corner of the square in that picture)
#   which = colour (default) or normal or height
import sys
from PIL import Image, ImageDraw
P = 'proc-work/'
which = sys.argv[10] if len(sys.argv) > 10 else 'colour'
paths = [P + 'reference/slate/%s.png' % ('height_as_uploaded' if which == 'height' else which),
         P + 'recipes/slate_layers/outputs/default_before_look_fixes/%s.png' % which,
         P + 'recipes/slate_layers/outputs/default/%s.png' % which]
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
