import sys
import numpy as np
from PIL import Image, ImageFilter
S, still = sys.argv[1], sys.argv[2]; K='/home/user/work/paper-pop-up-film-kit/assets/reliefs/sam-3d-test'
a=np.asarray(Image.open(S+'/render-a/original/still-190.00.jpg'),float); b=np.asarray(Image.open(still),float)
for n,m in [('red car','mask-1.png'),('pump left','mask-3.png'),('pump middle','mask-4.png'),('pump right','mask-5.png')]:
    mk=np.asarray(Image.open(K+'/'+m).resize((1080,1920)).filter(ImageFilter.MinFilter(21)))>128
    print(f'{n:12s} painting {a[mk].mean(0).round(0)} models {b[mk].mean(0).round(0)} brightness ratio {(a[mk].mean(0).sum()/b[mk].mean(0).sum()):.2f}')
