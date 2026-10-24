import sys; sys.path.insert(0,'/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/redesign/people-paint/check-painter-faults/tools')
from common import *
import cv2, json
I=imgs()
F=json.load(open(S+'/plate-facts/facts.json'))
ids=np.array(Image.open(S+'/plate-facts/ids.png').convert('RGB').resize((1536,2730),Image.NEAREST))
def LAB(a): 
    x=cv2.cvtColor(a,cv2.COLOR_RGB2LAB).astype(np.float32); x[...,0]*=100/255; x[...,1:]-=128; return x
P,Hh,Q,B=[cv2.GaussianBlur(LAB(I[k]),(0,0),5) for k in ['plate','helper','paint','behind']]
r=np.load(O+'/ratio_plate_helper.npy')
people=np.load(O+'/people_mask.npy')
pz=cv2.dilate(people.astype(np.uint8),np.ones((25,25),np.uint8))>0
# fit plate->painting lightness and warmth mapping on the lower half where plate==helper lighting (r~1), away from people
H,W=r.shape; yy,xx=np.mgrid[0:H,0:W]
fitm=(np.abs(r-1)<0.05)&~pz&(yy>0.40*H)
qs=np.linspace(1,99,99)
xp=np.percentile(P[...,0][fitm],qs); xq=np.percentile(Q[...,0][fitm],qs)
def mapL(v): return np.interp(v,xp,xq)
# warmth (b*) linear fit
A=np.vstack([P[...,2][fitm],np.ones(fitm.sum())]).T
cb=np.linalg.lstsq(A,Q[...,2][fitm],rcond=None)[0]
res=Q[...,0][fitm]-mapL(P[...,0][fitm])
print('mapping check on fit area: painting L minus mapped plate L: mean %+.1f, spread (sd) %.1f'%(res.mean(),res.std()))
print('%-20s %7s | %-24s | %-24s'%('where a person stood','pixels','lightness L: expected / people-out','warmth b*: expected / people-out'))
for g in F['groups']:
    if not(g.startswith('man') or g.startswith('walker')): continue
    m=np.all(ids==np.array(F['groups'][g]['colour']),-1)
    m=cv2.morphologyEx(m.astype(np.uint8),cv2.MORPH_CLOSE,np.ones((5,5),np.uint8)); m=cv2.erode(m,np.ones((7,7),np.uint8))>0
    if m.sum()<50: continue
    eL=mapL(Hh[...,0][m]).mean(); aL=B[...,0][m].mean()
    eb=(cb[0]*Hh[...,2][m]+cb[1]).mean(); ab=B[...,2][m].mean()
    print('%-20s %7d | %6.1f / %6.1f (%+5.1f)       | %6.1f / %6.1f (%+5.1f)'%(g,m.sum(),eL,aL,aL-eL,eb,ab,ab-eb))
