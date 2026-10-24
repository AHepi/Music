import sys,numpy as np
from PIL import Image
d=sys.argv[1]
prev=None
for i in range(1,361):
    a=np.asarray(Image.open(f"{d}/f{i:03d}.png").convert('L'),dtype=np.float32)
    if prev is not None:
        m=np.abs(a-prev).mean()
        print(f"{i-1:3d} {(i-1)/30:5.2f} {m:6.2f} {a.mean():6.1f}")
    prev=a
