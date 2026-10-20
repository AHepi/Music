# What this does (plain words): puts several of the quick 512-dot "view" pictures of a tuning round side by side in one JPEG with a name under each,
# so they can be looked at together. Use: python3 -I look_sheet.py OUT.jpg FOLDER name1 name2 ... [--cols N] [--size PIXELS]
# (each name is a picture FOLDER/<name>_colour.png).
import os
import sys

from PIL import Image, ImageDraw

args = sys.argv[1:]
cols = int(args[args.index('--cols') + 1]) if '--cols' in args else 4
size = int(args[args.index('--size') + 1]) if '--size' in args else 400
clean = [a for i, a in enumerate(args) if a not in ('--cols', '--size') and (i == 0 or args[i - 1] not in ('--cols', '--size'))]
out, folder, names = clean[0], clean[1], clean[2:]
rows = (len(names) + cols - 1) // cols
sheet = Image.new('RGB', (cols * (size + 6), rows * (size + 24)), (30, 30, 30))
draw = ImageDraw.Draw(sheet)
for index, name in enumerate(names):
    path = os.path.join(folder, name + '_colour.png')
    if not os.path.exists(path):
        path = os.path.join(folder, name + '.png')
    image = Image.open(path).convert('RGB').resize((size, size), Image.LANCZOS)
    x, y = (index % cols) * (size + 6), (index // cols) * (size + 24)
    sheet.paste(image, (x, y))
    draw.text((x + 4, y + size + 4), name, fill=(235, 235, 235))
sheet.save(out, quality=90)
print('wrote', out, sheet.size)
