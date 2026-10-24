import sys; sys.path.insert(0,'/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/redesign/people-paint/check-painter-faults/tools')
from common import *
import cv2
I=imgs()
def L(a): return cv2.cvtColor(a,cv2.COLOR_RGB2LAB)[...,0].astype(np.float32)*100/255
Lp,Lh,Lq,Lb,Ls=[cv2.GaussianBlur(L(I[k]),(0,0),3) for k in ['plate','helper','paint','behind','state']]
people=np.load(O+'/people_mask.npy')
pz=cv2.dilate(people.astype(np.uint8),cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(31,31)))>0
mask=I['mask'].astype(np.float32)/255
# men's cast shadows: plate darker than helper by > 3 L (relative: >20% darker), outside the people
rel=(Lh-Lp)/(Lh+1)
sh=(Lh-Lp>3)&(rel>0.2)&~pz
sh=cv2.morphologyEx(sh.astype(np.uint8),cv2.MORPH_OPEN,np.ones((5,5),np.uint8))>0
n,lab,st,cen=cv2.connectedComponentsWithStats(sh.astype(np.uint8))
keep=np.zeros_like(sh)
for i in range(1,n):
    if st[i,4]>3000: keep|=lab==i
sh=keep
np.save(O+'/men_shadow_mask.npy',sh)
ring=(cv2.dilate(sh.astype(np.uint8),np.ones((41,41),np.uint8))>0)&~sh&~pz
# restrict ring to the same lit surfaces: where helper plate within 30% of shadow-area helper mean
print('cast-shadow area (plate darker than helper plate by >20%%, outside the men): %.2f%% of frame, %d px'%(100*sh.mean(),sh.sum()))
ys,xs=np.nonzero(sh); print('  spans x %.3f-%.3f, y %.3f-%.3f'%(xs.min()/1536,xs.max()/1536,ys.min()/2730,ys.max()/2730))
for nm,Lx in [('plate',Lp),('helper plate',Lh),('painting',Lq),('people-out',Lb),('state picture',Ls)]:
    a=Lx[sh].mean(); b=Lx[ring].mean()
    print('  %-14s L in shadow %.1f, just around it %.1f, shadow depth %.1f L (%.0f%% darker)'%(nm,a,b,b-a,100*(b-a)/b))
print('  state mask over the shadow area: fully (>0.99) %.0f%%, partly %.0f%%, not at all %.0f%%'%(100*(mask[sh]>0.99).mean(),100*((mask[sh]>0.01)&(mask[sh]<=0.99)).mean(),100*(mask[sh]<=0.01).mean()))
print('  painting vs people-out inside shadow area: mean |dL| %.2f'%np.abs(Lq[sh]-Lb[sh]).mean())
# Overlay picture
vis=I['behind'].copy().astype(np.float32)
e=cv2.Canny(sh.astype(np.uint8)*255,50,100)>0
e=cv2.dilate(e.astype(np.uint8),np.ones((3,3),np.uint8))>0
vis[e]=[0,220,255]
Image.fromarray(vis.astype(np.uint8)).crop((0,1300,1150,2200)).resize((690,540)).save(O+'/shadows-left-in-people-out.jpg',quality=90)
