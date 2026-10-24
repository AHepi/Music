import sys; sys.path.insert(0,'/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/redesign/people-paint/check-painter-faults/tools')
from common import *
from tolerant import tol_diff
import cv2
I=imgs()
ba=np.array(Image.open(S+'/behind-1-aligned.png').convert('RGB'))
d=tol_diff(I['paint'],ba,r=1,blur=1.0)
painted=(cv2.GaussianBlur(d,(0,0),1.5)>14).astype(np.uint8)
painted=cv2.morphologyEx(painted,cv2.MORPH_CLOSE,np.ones((5,5),np.uint8))
painted=cv2.morphologyEx(painted,cv2.MORPH_OPEN,np.ones((3,3),np.uint8))>0
np.save(O+'/painted_people_mask.npy',painted)
G=group_masks()
allp=np.zeros_like(painted)
for g,m in G.items():
    if g.startswith('man') or g.startswith('walker'): allp|=m
allp=cv2.morphologyEx(allp.astype(np.uint8),cv2.MORPH_CLOSE,np.ones((5,5),np.uint8))>0
print('%-18s %8s %8s %6s %8s %8s %10s'%('figure','plate px','painted','IoU','added','lost','centre shift (dx,dy) px'))
for g,m in G.items():
    if not(g.startswith('man') or g.startswith('walker')) or m.sum()==0: continue
    m=cv2.morphologyEx(m.astype(np.uint8),cv2.MORPH_CLOSE,np.ones((5,5),np.uint8))>0
    ys,xs=np.nonzero(m); pad=40
    y0,y1,x0,x1=max(ys.min()-pad,0),ys.max()+pad,max(xs.min()-pad,0),xs.max()+pad
    win=np.zeros_like(m); win[y0:y1,x0:x1]=True
    # painted pixels in this window that are nearest to this figure (not to another figure)
    other=allp&~m
    dist_this=cv2.distanceTransform((~m).astype(np.uint8),cv2.DIST_L2,3)
    dist_other=cv2.distanceTransform((~other).astype(np.uint8),cv2.DIST_L2,3)
    pm=painted&win&(dist_this<=dist_other)
    inter=(pm&m).sum(); uni=(pm|m).sum()
    py,px=np.nonzero(pm)
    print('%-18s %8d %8d %6.2f %8d %8d   (%+.1f, %+.1f)'%(g,m.sum(),pm.sum(),inter/uni,(pm&~m).sum(),(m&~pm).sum(),px.mean()-xs.mean(),py.mean()-ys.mean()))
# visual
v=I['paint'].copy().astype(np.float32)
e1=cv2.Canny(allp.astype(np.uint8)*255,50,100)>0
e2=cv2.Canny(painted.astype(np.uint8)*255,50,100)>0
v[e2]=[255,60,60]; v[e1]=[0,255,255]
Image.fromarray(v.astype(np.uint8)).crop((100,1150,1300,1950)).save(O+'/men-outlines-plate-cyan-painted-red.jpg',quality=92)
