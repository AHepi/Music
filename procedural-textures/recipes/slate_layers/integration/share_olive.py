# What this does (plain words): prints the share of olive-green (moss-like) dots of baked colour pictures, the same way for the reference
# (the reference has 8.7 percent by this rule). Use: python3 -I share_olive.py PICTURE ...
import sys, cv2, numpy as np
for p in sys.argv[1:]:
    img=cv2.imread(p); rgb=img[...,::-1].astype(np.float32); r,g,b=rgb[...,0],rgb[...,1],rgb[...,2]; br=rgb.mean(2)
    m=(g>=b+10)&(r>=b+6)&(br>35)&(br<115)&(np.abs(r-g)<25)
    print(p.split('looks/')[-1], 'olive share %.1f%%'%(m.mean()*100))
