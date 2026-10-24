import sys; sys.path.insert(0,'/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/redesign/people-paint/check-painter-faults/tools')
from common import *
from peaks import dark_lines
import cv2
I=imgs()
def L(a): return cv2.cvtColor(a,cv2.COLOR_RGB2LAB)[...,0].astype(np.float32)*100/255
Lp,Lq=L(I['plate']),L(I['paint'])
x0,x1=int(0.478*1536),int(0.612*1536)
for yf in [0.437,0.440,0.444,0.449,0.455,0.460]:
    y=int(yf*2730)
    out=[]
    for nm,Lx,d in [('plate',Lp,1.0),('painting',Lq,3.0)]:
        prof=Lx[y-2:y+3,x0:x1].mean(0)
        pos,w=dark_lines(prof,d,4)
        out.append('%s %d bars, median width %.1f px'%(nm,len(pos),np.median(w) if w else 0))
    print('row %.3f (y=%d): '%(yf,y)+' | '.join(out))
