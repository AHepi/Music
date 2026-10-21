import sys, os
from PIL import Image
import numpy as np
d = sys.argv[1]; tag = sys.argv[2]; out = sys.argv[3]
names = sys.argv[4:]
b = np.asarray(Image.open(f'{d}/{tag}_photo_before.jpg').convert('RGB')).astype(np.float32)
tiles = []
for n in names:
    a = np.asarray(Image.open(f'{d}/{tag}_photo_solo_{n}.jpg').convert('RGB')).astype(np.float32)
    diff = np.clip(np.abs(a - b).max(axis=2) * 6, 0, 255).astype(np.uint8)
    im = Image.fromarray(diff).convert('RGB').resize((600, 400))
    tiles.append(im)
cols = 3
rows = (len(tiles) + cols - 1) // cols
sheet = Image.new('RGB', (600 * cols, 400 * rows), (30, 30, 30))
for i, t in enumerate(tiles):
    sheet.paste(t, ((i % cols) * 600, (i // cols) * 400))
sheet.save(out, quality=80)
print(out)
