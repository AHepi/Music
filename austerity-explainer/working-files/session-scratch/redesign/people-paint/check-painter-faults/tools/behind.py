import sys; sys.path.insert(0,'/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/redesign/people-paint/check-painter-faults/tools')
from common import *
import cv2, json
I=imgs()
F=json.load(open(S+'/plate-facts/facts.json'))
ids=np.array(Image.open(S+'/plate-facts/ids.png').convert('RGB').resize((1536,2730),Image.NEAREST))
people=np.zeros(ids.shape[:2],bool)
for g in F['groups']:
    if g.startswith('man') or g.startswith('walker'):
        people|=np.all(ids==np.array(F['groups'][g]['colour']),-1)
def L(a): return cv2.cvtColor(a,cv2.COLOR_RGB2LAB)[...,0].astype(np.float32)*100/255
# people + their shadows/light changes in the plate: where plate differs from helper plate
dp=np.abs(L(I['plate'])-L(I['helper']))
dpb=cv2.GaussianBlur(dp,(0,0),2)
plate_change=(dpb>2.0)
print('plate vs helper: people pixels %.2f%% of frame; plate differs from helper (>2 L) on %.2f%%'%(100*people.mean(),100*plate_change.mean()))
print('   of which outside the people: %.2f%% (their shadows and blocked light)'%(100*(plate_change&~people).mean()))
np.save(O+'/people_mask.npy',people); np.save(O+'/plate_change.npy',plate_change)
# painting vs behind
a=I['paint'].astype(np.float32); b=I['behind'].astype(np.float32)
lab_a=cv2.cvtColor(I['paint'],cv2.COLOR_RGB2LAB).astype(np.float32); lab_b=cv2.cvtColor(I['behind'],cv2.COLOR_RGB2LAB).astype(np.float32)
dE=np.sqrt(((lab_a-lab_b)**2).sum(-1))
dEb=cv2.GaussianBlur(dE,(0,0),3)
np.save(O+'/dE_paint_behind.npy',dEb)
expected=cv2.dilate((people|plate_change).astype(np.uint8),np.ones((15,15),np.uint8))>0
print('painting vs people-out: mean colour difference (LAB units, 0-255 scale) whole %.1f; inside people+shadow zone %.1f; outside %.1f'%(dE.mean(),dE[expected].mean(),dE[~expected].mean()))
for t in [10,20,30]:
    big=dEb>t
    print('  changed by >%d: %.2f%% of frame; of that, %.1f%% inside the expected zone; outside zone: %.2f%% of frame'%(t,100*big.mean(),100*(big&expected).sum()/max(1,big.sum()),100*(big&~expected).mean()))
# map
v=np.clip(dEb/40,0,1)
base=cv2.cvtColor(I['behind'],cv2.COLOR_RGB2GRAY).astype(np.float32)/255*0.5
rgb=np.stack([base+v*0.9,base+v*0.3,base],-1)
ed=cv2.Canny(expected.astype(np.uint8)*255,50,100)>0
rgb[ed]=[0.2,0.6,1.0]
Image.fromarray((np.clip(rgb,0,1)*255).astype(np.uint8)).resize((768,1365)).save(O+'/diff-paint-vs-behind.jpg',quality=90)
# outside blobs
m=((dEb>20)&~expected).astype(np.uint8)
n,lab,st,cen=cv2.connectedComponentsWithStats(m)
idx=sorted([i for i in range(1,n) if st[i,4]>400],key=lambda i:-st[i,4])
print('blobs changed >20 outside people+shadow zone (>400 px):',len(idx))
for i in idx[:30]:
    x,y,w,h,ar=st[i]; print('   (%.3f,%.3f)-(%.3f,%.3f) %d px mean dE %.1f'%(x/1536,y/2730,(x+w)/1536,(y+h)/2730,ar,dEb[lab==i].mean()))
