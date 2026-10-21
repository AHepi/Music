# What this does (plain words): plain Python (no Blender). Builds the picture sheet "surface families of the courtyard": the final photo, the flat family map and a legend with the share
# of the photo each family covers and which kind of weathering it takes.
# Run: python3 c7b_family_sheet.py PHOTO.jpg MAP.png OUT.jpg
import sys
from PIL import Image, ImageDraw
photo, fmap, out = sys.argv[1:4]
COL = {'ground': (0.30, 0.55, 0.18), 'add-on moss and pebbles': (0.62, 0.88, 0.32), 'raked gravel': (0.88, 0.78, 0.48), 'water': (0.15, 0.40, 0.85), 'wood': (0.80, 0.40, 0.10),
       'plaster': (0.97, 0.97, 0.88), 'wall cap tiles': (0.10, 0.10, 0.55), 'roof tiles': (0.45, 0.25, 0.70), 'add-on stones': (0.62, 0.62, 0.66), 'plain stone': (0.32, 0.34, 0.45),
       'bamboo': (0.85, 0.92, 0.15), 'bark': (0.45, 0.22, 0.08), 'leaves, needles, lilies': (0.05, 0.28, 0.07), 'hills and glow (backdrop)': (0.22, 0.22, 0.26)}
ROWS = [('ground', 15.4, 'moss, grime film, stains, bare earth, weeds'), ('add-on moss and pebbles', 0.8, 'already grown by the add-on: do not double'), ('raked gravel', 7.4, 'leaf litter, finer dust, weeds at edges, moss islands'),
        ('wood', 10.3, 'grey weathering, mildew, rot at feet, end checks, moss at plank ends'), ('plaster', 5.1, 'run-off streaks, splash band, cracks, mildew'), ('wall cap tiles', 0.5, 'moss and lichen on top, drip stain below'),
        ('roof tiles', 5.3, 'moss and lichen on lower edges and shaded side, tile stains'), ('add-on stones', 9.7, 'moss on top and shaded side, lichen, water line, chips'), ('plain stone', 1.8, 'same as stones'),
        ('bamboo', 0.5, 'left alone for now'), ('bark', 0.4, 'left alone for now'), ('water', 5.9, 'own water layer later; not weathered'), ('leaves, needles, lilies', 12.4, 'never weathered'), ('hills and glow (backdrop)', 13.9, 'never weathered'), ('sky', 10.5, 'never')]
W = 1200
a = Image.open(photo).convert('RGB').resize((600, 400)); b = Image.open(fmap).convert('RGB').resize((600, 400))
sh = Image.new('RGB', (W, 400 + 28 + 22 * len(ROWS) + 40), (24, 24, 24)); sh.paste(a, (0, 0)); sh.paste(b, (600, 0))
d = ImageDraw.Draw(sh)
d.text((8, 408), 'Left: the final golden-hour photo (Cycles, 2400 x 1600). Right: the same view, every material swapped for a flat family colour. Shares = share of the photo, one ray per dot of a 240 x 160 grid (about 0.25 points).', fill=(235, 235, 235))
y = 428
for name, share, note in ROWS:
    c = COL.get(name, (0, 0, 0)); d.rectangle([8, y + 2, 24, y + 16], fill=tuple(int(v * 255) for v in c), outline=(200, 200, 200))
    d.text((34, y + 2), f'{name}', fill=(240, 240, 240)); d.text((250, y + 2), f'{share:4.1f} %', fill=(240, 240, 140)); d.text((320, y + 2), note, fill=(200, 200, 200)); y += 22
d.text((8, y + 6), 'Weatherable share of the photo: about 57 % (ground, gravel, wood, plaster, caps, roof, stones, plinth, bamboo, bark). Roof tiles are 688 copies of one tile, so a layer must read the surface, not the object.', fill=(235, 235, 235))
sh.save(out, quality=80); print(sh.size)
