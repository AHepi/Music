import sys; sys.path.insert(0,'/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/redesign/people-paint/check-painter-faults/tools')
from common import *
import cv2
I=imgs()
def lab(a): 
    x=cv2.cvtColor(a,cv2.COLOR_RGB2LAB).astype(np.float32); x[...,0]*=100/255; x[...,1:]-=128; return x
P=lab(I['plate']); Q=lab(I['paint'])
bb=cv2.blur(P[...,2],(7,7))
for yf in [0.64,0.68,0.72,0.76,0.80,0.84,0.88,0.92,0.96,0.99]:
    y=int(yf*2730)
    cand=bb[y]<-1.8
    cand=np.convolve(cand.astype(float),np.ones(9)/9,'same')>0.5
    best=(0,0,0); s=None
    for x in range(0,1100):
        if cand[x] and s is None: s=x
        if (not cand[x]) and s is not None:
            if x-s>best[0]: best=(x-s,s,x)
            s=None
    w,x0,x1=best
    prof=cv2.GaussianBlur(Q[y-2:y+3,:,0].mean(0).reshape(1,-1),(0,0),1.0).ravel()
    def ink_near(x):
        lo,hi=max(0,x-40),x+40; seg=prof[lo:hi]; i=int(np.argmin(seg)); return lo+i
    l=ink_near(x0); r=ink_near(x1)
    print('row %.2f: plate gutter x %4d-%4d (width %3d) | painting ink line near left edge %4d (%+3d), near right edge %4d (%+3d) -> width %3d (%.0f%%)'%(yf,x0,x1,w,l,l-x0,r,r-x1,r-l,100*(r-l)/max(w,1)))
