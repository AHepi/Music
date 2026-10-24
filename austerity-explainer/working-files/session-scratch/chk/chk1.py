import numpy as np
from PIL import Image
P='/home/user/work/paper-pop-up-film-kit/assets/reliefs/'
paint=np.asarray(Image.open(P+'inflation-chapter-2/409-bg-petrol-station-1973.jpg').convert('L').resize((1080,1920)),float)
orig=np.asarray(Image.open('render-a/original/still-190.00.jpg').convert('L'),float)
print('paint size', Image.open(P+'inflation-chapter-2/409-bg-petrol-station-1973.jpg').size)
# search scale/shift
import itertools
best=None
for s in [1.0,1.02,1.04,1.06,1.08,1.1]:
  im=Image.open(P+'inflation-chapter-2/409-bg-petrol-station-1973.jpg').convert('L').resize((int(1080*s),int(1920*s)))
  a=np.asarray(im,float)
  for dx in range(-30,31,3):
    for dy in range(-30,31,3):
      ox=(a.shape[1]-1080)//2+dx; oy=(a.shape[0]-1920)//2+dy
      if ox<0 or oy<0 or ox+1080>a.shape[1] or oy+1920>a.shape[0]: continue
      c=a[oy:oy+1920,ox:ox+1080]
      e=np.abs(c[200:1700,100:980]-orig[200:1700,100:980]).mean()
      if best is None or e<best[0]: best=(e,s,dx,dy)
print(best)
