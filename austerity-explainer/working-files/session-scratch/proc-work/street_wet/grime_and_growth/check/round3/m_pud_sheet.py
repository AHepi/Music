import numpy as np, cv2
from PIL import Image
G='/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/street_wet/grime_and_growth/'
B='/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/kits/weathering/harness/baseline/maps/'
def rd(p):
    a=cv2.imread(p,cv2.IMREAD_UNCHANGED); a=a.astype(np.float32)/(65535 if a.dtype==np.uint16 else 255); return a[...,:3][...,::-1]
base=rd(G+'integrated/plates/street/final_main_A_wet_base.png'); k=rd(G+'fix/plates/street/final_main_A_wet_kit.png'); h,w=k.shape[:2]
hsv=cv2.cvtColor((k*255).astype(np.uint8),cv2.COLOR_RGB2HSV_FULL).astype(np.float32); H,S=hsv[...,0]/255*360,hsv[...,1]/255
d=np.abs(k-base).max(axis=2)
green=(k[...,1]>k[...,0]*1.08)&(k[...,1]>k[...,2]*1.15)&(S>0.3)&(d>0.04)&(H>60)&(H<170); green[:int(h*0.55)]=False
pud=cv2.imread(B+'puddle_main_wet.png',cv2.IMREAD_UNCHANGED)[...,2]>32768; pud=cv2.resize(pud.astype(np.uint8),(w,h),interpolation=cv2.INTER_NEAREST)>0
gd=cv2.dilate(green.astype(np.uint8),np.ones((9,9),np.uint8)); n2,lab2,st2,cen2=cv2.connectedComponentsWithStats(gd,connectivity=8)
tiles=[]
for i in range(1,n2):
    m=green&(lab2==i)
    if m.sum()<20: continue
    ys,xs=np.where(m); yr=ys.max(); xr=int(np.median(xs[ys>=yr-3]))
    if pud[min(h-1,yr+4),xr]:
        cx,cy=int(xs.mean()),int(ys.mean()); x0=max(0,min(w-100,cx-50)); y0=max(0,min(h-100,cy-50))
        t=k[y0:y0+100,x0:x0+100]; b=base[y0:y0+100,x0:x0+100]
        tt=np.concatenate([b,t],axis=0); tiles.append((np.clip(tt,0,1)*255).astype(np.uint8))
        print(cx,cy,int(m.sum()))
row=np.concatenate([cv2.resize(t,None,fx=2,fy=2,interpolation=cv2.INTER_NEAREST) for t in tiles[:8]],axis=1)
Image.fromarray(row).save(G+'check/round3/puddle_clusters_base_over_fix.jpg',quality=82); print(row.shape)
