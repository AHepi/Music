import sys; sys.path.insert(0,'/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/redesign/people-paint/check-painter-faults/tools')
from common import *
import cv2
I=imgs()
def lum(a): return cv2.cvtColor(a,cv2.COLOR_RGB2LAB)[...,0].astype(np.float32)
Lp=lum(I['plate']); Lq=lum(I['paint'])
sig=6
bp=cv2.GaussianBlur(Lp,(0,0),sig); bq=cv2.GaussianBlur(Lq,(0,0),sig)
# monotonic mapping plate->painting by matching the blurred histograms
qs=np.linspace(0,100,201)
xp=np.percentile(bp,qs); xq=np.percentile(bq,qs)
xp=np.maximum.accumulate(xp+np.arange(len(xp))*1e-4)
mp=np.interp(bp,xp,xq)
d=bq-mp
np.save(O+'/tonediff.npy',d)
print('tone-matched L diff (painting minus plate mapped), LAB L units 0-100: median %.1f, p1 %.1f, p99 %.1f'%(np.median(d),np.percentile(d,1),np.percentile(d,99)))
print('share of frame darker by >12: %.2f%%, lighter by >12: %.2f%%'%(100*(d<-12).mean(),100*(d>12).mean()))
v=np.clip(d/25,-1,1)
rgb=np.zeros(d.shape+(3,),np.float32)
base=Lq/100*0.5
rgb[...,0]=base+np.clip(v,0,1)*0.8
rgb[...,1]=base
rgb[...,2]=base+np.clip(-v,0,1)*0.8
out=(np.clip(rgb,0,1)*255).astype(np.uint8)
Image.fromarray(out).resize((768,1365)).save(O+'/tonediff-map.jpg',quality=90)
# grid of blobs
for thr,name in [(-14,'darker'),(14,'lighter')]:
    m=((d<thr) if thr<0 else (d>thr)).astype(np.uint8)
    n,lab,st,cen=cv2.connectedComponentsWithStats(m)
    idx=[i for i in range(1,n) if st[i,4]>1500]
    idx.sort(key=lambda i:-st[i,4])
    print(name,'blobs >1500 px:',len(idx))
    for i in idx[:25]:
        x,y,w,h,a=st[i]; print('   box frac (%.3f,%.3f)-(%.3f,%.3f) area %d mean %.1f'%(x/1536,y/2730,(x+w)/1536,(y+h)/2730,a,d[lab==i].mean()))
