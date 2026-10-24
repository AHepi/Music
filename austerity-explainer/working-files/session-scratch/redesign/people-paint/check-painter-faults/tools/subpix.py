import sys; sys.path.insert(0,'/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/redesign/people-paint/check-painter-faults/tools')
from common import *
import cv2
I=imgs()
ba=np.array(Image.open(S+'/behind-1-aligned.png').convert('RGB'))
A=cv2.cvtColor(I['paint'],cv2.COLOR_RGB2GRAY).astype(np.float32)
B=cv2.cvtColor(ba,cv2.COLOR_RGB2GRAY).astype(np.float32)
people=np.load(O+'/people_mask.npy')
pz=cv2.dilate(people.astype(np.uint8),np.ones((61,61),np.uint8))>0
m=I['mask'].astype(np.float32)/255
win=cv2.createHanningWindow((96,96),cv2.CV_32F)
res=[]
for y in range(0,2730-96,48):
    for x in range(0,1536-96,48):
        if pz[y:y+96,x:x+96].any(): continue
        a=A[y:y+96,x:x+96]; b=B[y:y+96,x:x+96]
        if a.std()<6: continue
        (dx,dy),resp=cv2.phaseCorrelate(a,b,win)
        res.append((x,y,dx,dy,resp,m[y:y+96,x:x+96].mean(),np.abs(a-b).mean()))
res=np.array(res)
for nm,sel in [('outside mask',res[:,5]<0.01),('inside mask (no people)',res[:,5]>0.99),('mask edge',(res[:,5]>=0.01)&(res[:,5]<=0.99))]:
    r=res[sel&(res[:,4]>0.2)]
    if len(r)==0: continue
    sh=np.hypot(r[:,2],r[:,3])
    print('%-24s patches %4d: shift median dx %+.2f dy %+.2f px, |shift| median %.2f, p90 %.2f, max %.2f; mean grey diff %.1f'%(nm,len(r),np.median(r[:,2]),np.median(r[:,3]),np.median(sh),np.percentile(sh,90),sh.max(),r[:,6].mean()))
big=res[(res[:,4]>0.2)&(np.hypot(res[:,2],res[:,3])>1.5)]
print('patches shifted >1.5 px:',len(big))
for r in big[:20]: print('   at (%.3f,%.3f) dx %+.2f dy %+.2f resp %.2f mask %.2f'%((r[0]+48)/1536,(r[1]+48)/2730,r[2],r[3],r[4],r[5]))
