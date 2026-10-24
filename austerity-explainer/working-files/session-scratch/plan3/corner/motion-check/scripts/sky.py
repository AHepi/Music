import numpy as np, sys
W=sys.argv[1]; f=sys.argv[2]
a=np.load(f"{W}/{f}"); p0,p1,al=a[0],a[1],a[2][:,0]>0
d=p1-p0
for (x0,x1,y0,y1) in [(0,0.45,0,0.13),(0.2,0.45,0.13,0.25),(0.55,0.8,0,0.18),(0.4,0.55,0.05,0.1)]:
    m=al&(p0[:,0]>=x0*1080)&(p0[:,0]<x1*1080)&(p0[:,1]>=y0*1920)&(p0[:,1]<y1*1920)
    print((x0,x1,y0,y1),m.sum())
    for k in np.where(m)[0][:25]:
        print(f"   at ({p0[k,0]/1080:.3f},{p0[k,1]/1920:.3f}) moved ({d[k,0]:+.1f},{d[k,1]:+.1f})")
