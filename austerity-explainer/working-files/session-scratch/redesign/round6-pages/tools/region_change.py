# What this does: measures how much named regions of filmed stills brighten or darken against the first still (round 6:
# page 4's "busy" must brighten No. 2's doorway and windows; the people at work inside must stay dark). For each region
# (a box in film pixels) it prints, for every still, the region's average brightness (levels 0 to 255) and its change
# from the first still; and the same for the region's dark pixels (below 40 in the first still: the people at work).
# Use: python3 -I region_change.py "NAME:L,T,R,B" ["NAME:L,T,R,B" ...] FIRST.jpg OTHER.jpg ...
import os
import sys

import numpy as np
from PIL import Image

args = sys.argv[1:]
regions = []
while args and ':' in args[0] and not os.path.exists(args[0]):
    name, box = args.pop(0).split(':')
    regions.append((name, tuple(int(v) for v in box.split(','))))
lumas = [np.asarray(Image.open(f).convert('RGB')).astype(float) @ [0.2126, 0.7152, 0.0722] for f in args]
for name, (l, t, r, b) in regions:
    first = lumas[0][t:b, l:r]
    dark = first < 40
    print(f'{name} ({l},{t} to {r},{b}): first still {first.mean():.1f}, its dark pixels {first[dark].mean() if dark.any() else 0:.1f} ({dark.mean() * 100:.0f}% of the box)')
    for f, luma in zip(args[1:], lumas[1:]):
        part = luma[t:b, l:r]
        print(f'  {os.path.basename(f)}: {part.mean():6.1f}  change {part.mean() - first.mean():+6.1f}   dark pixels {part[dark].mean() - first[dark].mean() if dark.any() else 0:+5.1f}')
