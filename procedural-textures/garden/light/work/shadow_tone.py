import sys, numpy as np
from PIL import Image
for p in sys.argv[1:]:
    a=np.asarray(Image.open(p).convert('RGB').resize((960,640))).astype(float)/255
    Y=0.2126*a[...,0]+0.7152*a[...,1]+0.0722*a[...,2]
    lower=np.zeros(Y.shape,bool); lower[300:,:]=True      # ground and stones, not sky/hills
    sh=lower&(Y>0.04)&(Y<0.18)                             # shadows
    lit=lower&(Y>0.45)
    def tone(m): 
        r,g,b=[a[...,i][m].mean() for i in range(3)]; return (round(r,3),round(g,3),round(b,3),'B/R=%.2f'%(b/r))
    print(p.split('/')[-1],'shadow',tone(sh),'sunlit',tone(lit), 'n', int(sh.sum()), int(lit.sum()))
