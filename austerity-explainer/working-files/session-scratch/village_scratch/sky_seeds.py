import sys, math
sys.path.insert(0, '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/mine-work/modules')
import numpy as np
from PIL import Image
import village_and_sky as vs
exec(open('sky_try.py').read().split("def camera_view")[1].join(["def camera_view",""]).split("view=camera_view")[0]) if False else None
src=open('sky_try.py').read()
cv=src[src.index("def camera_view"):src.index("view=camera_view")]
exec(cv)
tiles=[]
for seed in [11,3,7,21,5,42]:
    pic=vs.paint_sky(2048,1024,seed=seed)
    v=camera_view(pic,W=270,H=480)
    tiles.append((np.clip(v,0,1)*255).astype(np.uint8))
Image.fromarray(np.concatenate(tiles,axis=1)).save('sky_seeds.png')
