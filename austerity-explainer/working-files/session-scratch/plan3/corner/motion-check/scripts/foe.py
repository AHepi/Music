import numpy as np, sys
W=sys.argv[1]; f=sys.argv[2]
a=np.load(f"{W}/{f}"); p0,p1,al=a[0],a[1],a[2][:,0]>0
p=p0[al]; d=(p1-p0)[al]
mag=np.linalg.norm(d,axis=1)
def fit(r):
    dd=d-r
    A=np.stack([dd[:,1],-dd[:,0]],1); b=p[:,0]*dd[:,1]-p[:,1]*dd[:,0]
    wts=1/np.maximum(np.linalg.norm(dd,axis=1),1)  # normalise
    F,res,_,_=np.linalg.lstsq(A*wts[:,None],b*wts,rcond=None)
    # angular residual
    v=p-F; cr=(v[:,0]*dd[:,1]-v[:,1]*dd[:,0])/np.maximum(np.linalg.norm(v,axis=1)*np.linalg.norm(dd,axis=1),1e-6)
    dot=(v*dd).sum(1)
    return F,np.median(np.abs(cr)),np.mean(dot<0)
F,res,neg=fit(np.zeros(2))
print("no rotation: FOE at",F/[1080,1920],"median |sin angle|",res,"frac inward",neg)
best=None
for rx in np.arange(-10,10.5,1):
    for ry in np.arange(-10,10.5,1):
        F2,res2,neg2=fit(np.array([rx,ry]))
        if best is None or res2<best[0]: best=(res2,rx,ry,F2,neg2)
print("best uniform shift",best[1],best[2],"FOE",best[3]/[1080,1920],"res",best[0],"inward",best[4])
# far points: small flows
m=mag<20
v=p[m]-F
for k in np.argsort(mag[m])[:15]:
    print(f"far pt ({p[m][k,0]/1080:.3f},{p[m][k,1]/1920:.3f}) flow ({d[m][k,0]:+.1f},{d[m][k,1]:+.1f}) radial dir ({v[k,0]/np.linalg.norm(v[k]):+.2f},{v[k,1]/np.linalg.norm(v[k]):+.2f})")
