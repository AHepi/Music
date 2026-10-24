import sys; sys.path.insert(0,'/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/redesign/people-paint/check-painter-faults/tools')
from common import *
import cv2, json
I=imgs()
s=0.5
def grad(a):
    g=cv2.cvtColor(a,cv2.COLOR_RGB2GRAY).astype(np.float32)
    g=cv2.resize(g,None,fx=s,fy=s,interpolation=cv2.INTER_AREA)
    g=cv2.GaussianBlur(g,(0,0),1.5)
    # normalise local contrast
    m=cv2.GaussianBlur(g,(0,0),12); sd=np.sqrt(cv2.GaussianBlur((g-m)**2,(0,0),12))+4
    g=(g-m)/sd
    gx=cv2.Sobel(g,cv2.CV_32F,1,0); gy=cv2.Sobel(g,cv2.CV_32F,0,1)
    return np.hypot(gx,gy)
A=grad(I['plate']); B=grad(I[sys.argv[1] if len(sys.argv)>1 else 'paint'])
H,W=A.shape; P_=48; R=20
res=[]
for y in range(R,H-P_-R,24):
    for x in range(R,W-P_-R,24):
        t=A[y:y+P_,x:x+P_]
        if t.std()<0.15: continue
        reg=B[y-R:y+P_+R,x-R:x+P_+R]
        m=cv2.matchTemplate(reg,t,cv2.TM_CCOEFF_NORMED)
        _,mx,_,loc=cv2.minMaxLoc(m)
        z=m[R,R]
        res.append((x,y,loc[0]-R,loc[1]-R,mx,z,float(t.std())))
res=np.array(res)
np.save(O+'/patchshift_%s.npy'%(sys.argv[1] if len(sys.argv)>1 else 'paint'),res)
sh=np.hypot(res[:,2],res[:,3])/s
print('patches',len(res),'peak ncc median %.2f'%np.median(res[:,4]),'zero-shift ncc median %.2f'%np.median(res[:,5]))
print('shift (full px) median %.1f p75 %.1f p90 %.1f'%(np.median(sh),np.percentile(sh,75),np.percentile(sh,90)))
# reliable moved patches: peak ncc>0.5 and peak-zero>0.15 and shift>=4 full px
mv=(res[:,4]>0.5)&(sh>=6)&(res[:,4]-res[:,5]>0.15)
print('moved reliable patches',mv.sum())
for r,ss in zip(res[mv],sh[mv]):
    print('  at (%.3f,%.3f) shift dx %+d dy %+d full px (%.0f), ncc %.2f vs %.2f at zero'%((r[0]+24)/W,(r[1]+24)/H,r[2]/s,r[3]/s,ss,r[4],r[5]))
