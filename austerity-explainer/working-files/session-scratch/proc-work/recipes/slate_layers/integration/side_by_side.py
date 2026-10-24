# What this does (plain words): puts a crop of the reference next to the same crop of a baked picture (or two baked pictures), so a person can
# compare the look by eye. The reference is a guide only; the slates are of course not the same slates.
# Use: python3 -I side_by_side.py OUT.png X Y W H [scale] PICTURE_A [PICTURE_B ...]   ('ref' means the slate reference colour picture)
import sys
import cv2
import numpy as np
PROC = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work'
out = sys.argv[1]; x, y, w, h = map(int, sys.argv[2:6]); scale = float(sys.argv[6])
pics = sys.argv[7:]
tiles = []
for p in pics:
    path = PROC + '/reference/slate/colour.png' if p == 'ref' else p
    img = cv2.imread(path)
    s = img.shape[0] / 1254.0
    crop = img[int(y*s):int((y+h)*s), int(x*s):int((x+w)*s)]
    crop = cv2.resize(crop, (int(w*scale), int(h*scale)), interpolation=cv2.INTER_NEAREST if scale > 1 else cv2.INTER_AREA)
    cv2.putText(crop, 'reference' if p == 'ref' else p.split('/')[-2] if '/' in p else p, (8, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    tiles.append(crop)
    tiles.append(np.full((crop.shape[0], 6, 3), 255, np.uint8))
cv2.imwrite(out, np.hstack(tiles[:-1]))
