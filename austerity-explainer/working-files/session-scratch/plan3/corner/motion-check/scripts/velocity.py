import numpy as np, sys, cv2
W=sys.argv[1]
def g(i): return cv2.cvtColor(cv2.imread(f"{W}/all/f{i:03d}.png"),cv2.COLOR_BGR2GRAY)
# track features in the lower-left cobbles (near, fast moving, no effects) and the left houses
start=9
g0=g(start)
mask=np.zeros_like(g0); mask[1300:1850,40:450]=255
p=cv2.goodFeaturesToTrack(g0,400,0.01,10,mask=mask)
mask2=np.zeros_like(g0); mask2[500:1000,20:300]=255
q=cv2.goodFeaturesToTrack(g0,300,0.01,10,mask=mask2)
prev=g0; rows=[]
for i in range(start+1,262):
    gi=g(i)
    out=[]
    for pts in (p,q):
        n,st,_=cv2.calcOpticalFlowPyrLK(prev,gi,pts,None,winSize=(31,31),maxLevel=3)
        ok=st.ravel()==1
        d=(n-pts).reshape(-1,2)[ok]
        out.append(np.median(d,0))
        pts[:]=n
    prev=gi
    rows.append((i,out))
for i,(a,b) in rows:
    print(f"{i:3d} t={i/30:5.2f} cobbles=({a[0]:+.3f},{a[1]:+.3f}) |v|={np.hypot(*a):.3f}  houses=({b[0]:+.3f},{b[1]:+.3f}) |v|={np.hypot(*b):.3f}")
