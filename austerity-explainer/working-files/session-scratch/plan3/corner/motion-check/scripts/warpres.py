import numpy as np, sys, cv2
W=sys.argv[1]; pairs=[(int(a),int(b)) for a,b in (s.split(':') for s in sys.argv[2:])]
dis=cv2.DISOpticalFlow_create(cv2.DISOPTICAL_FLOW_PRESET_ULTRAFAST if False else cv2.DISOPTICAL_FLOW_PRESET_MEDIUM)
dis.setFinestScale(0)
def load(i):
    a=cv2.imread(f"{W}/all/f{i:03d}.png").astype(np.float32)
    g=min(i/30,1.0) if i<30 else 1.0
    if i>360: g=max(1-(i/30-12),1e-3)
    return a/max(g,1e-3)
for a,b in pairs:
    A=load(a); B=load(b)
    ga=cv2.cvtColor(np.clip(A,0,255).astype(np.uint8),cv2.COLOR_BGR2GRAY); gb=cv2.cvtColor(np.clip(B,0,255).astype(np.uint8),cv2.COLOR_BGR2GRAY)
    flow=dis.calc(gb,ga,None)  # for each pixel in B, where it is in A
    h,w=gb.shape
    gx,gy=np.meshgrid(np.arange(w),np.arange(h))
    mapx=(gx+flow[...,0]).astype(np.float32); mapy=(gy+flow[...,1]).astype(np.float32)
    Aw=cv2.remap(A,mapx,mapy,cv2.INTER_LINEAR)
    r=np.abs(Aw-B).mean(2)
    r=cv2.GaussianBlur(r,(0,0),3)
    cv2.imwrite(f"{W}/crops/res_{a:03d}_{b:03d}.png",np.clip(r*10,0,255).astype(np.uint8))
    T=60; td=r[:h//T*T,:w//T*T].reshape(h//T,T,w//T,T).mean(axis=(1,3))
    top=np.argsort(td.ravel())[::-1][:8]
    print(a,b, f"mean {r.mean():.2f}", " ".join(f"({(k%td.shape[1]+.5)*T/1080:.2f},{(k//td.shape[1]+.5)*T/1920:.2f}):{td.ravel()[k]:.1f}" for k in top))
