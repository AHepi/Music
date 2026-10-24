# What this does: first quick look at the wood height map: row averages and wrap-around jumps. Plain numbers printed on screen.
import numpy as np
from PIL import Image
P='/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/reference/wood/'
h=np.asarray(Image.open(P+'height_as_uploaded.png')).astype(float)/255
c=np.asarray(Image.open(P+'colour.png')).astype(float)/255
print(h.shape,h.min(),h.max(),h.mean())
# row mean and row darkest-fraction
rm=h.mean(1)
dark=(h<0.15).mean(1)
for y in range(0,1254,6):
    print(y, round(rm[y:y+6].mean(),3), round(dark[y:y+6].mean(),3))
