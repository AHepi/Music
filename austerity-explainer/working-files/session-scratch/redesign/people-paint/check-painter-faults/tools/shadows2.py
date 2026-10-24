import sys; sys.path.insert(0,'/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/redesign/people-paint/check-painter-faults/tools')
from common import *
import cv2
I=imgs()
def L(a): return cv2.cvtColor(a,cv2.COLOR_RGB2LAB)[...,0].astype(np.float32)*100/255
r=np.load(O+'/ratio_plate_helper.npy')
people=np.load(O+'/people_mask.npy')
pz=cv2.dilate(people.astype(np.uint8),cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(25,25)))>0
Ls={k:cv2.GaussianBlur(L(I[k]),(0,0),4) for k in ['plate','helper','paint','behind','state']}
deep=(r<0.6)&~pz; lit=(r>0.92)&~pz
H,W=r.shape
yy,xx=np.mgrid[0:H,0:W]
rows=[]
# only the ground in front of the men, left of the right wall
ground=(yy>0.62*H)&(yy<0.80*H)&(xx<0.80*W)
for y0 in range(int(0.62*H),int(0.80*H),40):
    band=ground&(yy>=y0)&(yy<y0+40)
    d=band&deep; l=band&lit
    if d.sum()<500 or l.sum()<500: continue
    rows.append([Ls[k][l].mean()-Ls[k][d].mean() for k in ['plate','helper','paint','behind','state']]+[d.sum()])
rows=np.array(rows)
print('ground strips in front of the men compared:',len(rows),'; deep-shadow pixels',int(rows[:,5].sum()))
for i,k in enumerate(['plate','helper plate','painting','people-out','state picture']):
    print('  %-14s lit minus shadow (same strips): %+.1f L (median over strips %+.1f)'%(k,np.average(rows[:,i],weights=rows[:,5]),np.median(rows[:,i])))
# visual
vis=I['behind'].astype(np.float32)
e=cv2.Canny(((r<0.6)&~pz).astype(np.uint8)*255,50,100)>0
e=cv2.dilate(e.astype(np.uint8),np.ones((3,3),np.uint8))>0
vis[e]=[0,230,255]
Image.fromarray(vis.astype(np.uint8)).crop((0,1250,1300,2250)).resize((780,600)).save(O+'/plate-shadow-outline-on-people-out.jpg',quality=90)
vis=I['paint'].astype(np.float32); vis[e]=[0,230,255]
Image.fromarray(vis.astype(np.uint8)).crop((0,1250,1300,2250)).resize((780,600)).save(O+'/plate-shadow-outline-on-painting.jpg',quality=90)
