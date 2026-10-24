# What this does: measures how much No. 2's lit windows change between stills (page 4's "busy"). The windows are the
# warm, bright pixels inside a box (left, top, right, bottom, in film pixels) of the first still; prints, for every
# other still, the windows' average brightness and how far it moved from the first (mean and mean of the size of the
# change), and the doorway room's too if a second box is given.
# Use: python3 window_change.py "L,T,R,B" ["L,T,R,B" doorway] FIRST.jpg OTHER.jpg ...
import sys
import numpy as np
from PIL import Image

args = sys.argv[1:]
boxes = []
while args and ',' in args[0]:
    boxes.append(tuple(int(v) for v in args.pop(0).split(',')))
stills = [np.asarray(Image.open(f).convert('RGB')).astype(float) for f in args]
for name, (l, t, r, b) in zip(['windows', 'doorway'], boxes):
    first = stills[0][t:b, l:r]
    luma = first @ [0.2126, 0.7152, 0.0722]
    mask = (luma > 120) & (first[..., 0] > first[..., 2] + 15)
    print(f'{name}: {mask.sum()} pixels, first still {luma[mask].mean():.1f}')
    for f, s in zip(args[1:], stills[1:]):
        l2 = s[t:b, l:r] @ [0.2126, 0.7152, 0.0722]
        d = (l2 - luma)[mask]
        print(f'  {f.split("/")[-1]}: {l2[mask].mean():.1f}  change {d.mean():+.1f}  size of change {abs(d).mean():.1f}')
