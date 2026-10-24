import sys; sys.path.insert(0,'/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/redesign/people-paint/check-painter-faults/tools')
from common import *
import cv2
I=imgs()
def warm(a, lthr):
    lab=cv2.cvtColor(a,cv2.COLOR_RGB2LAB).astype(np.float32)
    Lx=lab[...,0]*100/255; b=lab[...,2]-128
    return (Lx>lthr)&(b>12), Lx
for nm,thr in [('plate',55),('paint',60),('behind',60)]:
    m,Lx=warm(I[nm],thr)
    m=cv2.morphologyEx(m.astype(np.uint8),cv2.MORPH_OPEN,np.ones((2,2),np.uint8))
    n,lab,st,cen=cv2.connectedComponentsWithStats(m)
    blobs=[(cen[i][0]/1536,cen[i][1]/2730,st[i,4]) for i in range(1,n) if st[i,4]>=25]
    blobs.sort(key=lambda t:(round(t[0],2),t[1]))
    print(nm,'warm bright blobs >=25 px:',len(blobs),'total px',int(sum(b[2] for b in blobs)))
    print('   ',' '.join('(%.3f,%.3f,%d)'%b for b in blobs))
