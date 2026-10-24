import numpy as np, cv2, sys
W=sys.argv[1]
def gray(i):
    return cv2.cvtColor(cv2.imread(f"{W}/all/f{i:03d}.png"),cv2.COLOR_BGR2GRAY)
start=int(sys.argv[2]); end=int(sys.argv[3])
g0=gray(start)
# features in chosen regions
pts=cv2.goodFeaturesToTrack(g0,maxCorners=3000,qualityLevel=0.005,minDistance=12)
p=pts.copy(); alive=np.ones(len(p),bool)
prev=g0
for i in range(start+1,end+1):
    g=gray(i)
    nxt,st,err=cv2.calcOpticalFlowPyrLK(prev,g,p,None,winSize=(21,21),maxLevel=3)
    back,st2,_=cv2.calcOpticalFlowPyrLK(g,prev,nxt,None,winSize=(21,21),maxLevel=3)
    fb=np.linalg.norm(back-p,axis=2).ravel()
    alive&=(st.ravel()==1)&(st2.ravel()==1)&(fb<0.5)
    p=nxt; prev=g
p0=pts.reshape(-1,2); p1=p.reshape(-1,2)
np.save(f"{W}/track_{start}_{end}.npy",np.stack([p0,p1,np.repeat(alive[:,None],2,1)],0))
d=p1-p0
print("alive",alive.sum(),"of",len(alive))
# grid summary
for gy in np.arange(0,1,0.1):
    row=[]
    for gx in np.arange(0,1,0.2):
        m=alive&(p0[:,0]>=gx*1080)&(p0[:,0]<(gx+0.2)*1080)&(p0[:,1]>=gy*1920)&(p0[:,1]<(gy+0.1)*1920)
        if m.sum()>=3:
            dd=np.median(d[m],0); row.append(f"({dd[0]:+6.1f},{dd[1]:+6.1f})n{m.sum():3d}")
        else: row.append(" "*19)
    print(f"y{gy:.1f}: "+" ".join(row))
