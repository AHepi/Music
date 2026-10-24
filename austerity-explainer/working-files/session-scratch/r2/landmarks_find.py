import numpy as np, json, time
from PIL import Image
P='/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/'
h=np.asarray(Image.open(P+'reference/wood/height_as_uploaded.png').convert('L'),dtype=np.float32)/255
c=np.asarray(Image.open(P+'reference/wood/colour.png').convert('RGB'),dtype=np.float32)/255
# half resolution by 2x2 mean
def half(a): 
    return a[:1254//2*2:2,:1254//2*2:2]*0.25+a[1::2,:1254//2*2:2]*0.25+a[:1254//2*2:2,1::2]*0.25+a[1::2,1::2]*0.25
H=half(h); C=np.stack([half(c[...,i]) for i in range(3)],-1)
F=np.concatenate([H[...,None],C],-1)  # 627x627x4
n=F.shape[0]
ps=48; step=12
pos=[(y,x) for y in range(0,n-ps+1,step) for x in range(0,n-ps+1,step)]
N=len(pos); print(N)
X=np.stack([F[y:y+ps,x:x+ps].reshape(-1) for y,x in pos]).astype(np.float32)
def flipped(y,x,k):
    p=F[y:y+ps,x:x+ps]
    if k&1: p=p[:,::-1]
    if k&2: p=p[::-1]
    return p.reshape(-1)
sq=(X*X).sum(1)
dmin=np.full(N,1e9,dtype=np.float32)
py=np.array([p[0] for p in pos]); px=np.array([p[1] for p in pos])
near=(np.abs(py[:,None]-py[None])<ps*1.1)&(np.abs(px[:,None]-px[None])<ps*1.1)
t=time.time()
for k in range(4):
    Y=np.stack([flipped(y,x,k) for y,x in pos]).astype(np.float32)
    D=sq[:,None]+(Y*Y).sum(1)[None]-2*X@Y.T
    D[near]=1e9
    dmin=np.minimum(dmin,D.min(1))
    print('flip',k,time.time()-t,flush=True)
d=np.sqrt(np.maximum(dmin,0)/X.shape[1])  # rms difference
order=np.argsort(-d)
picked=[]
for i in order:
    cy=(pos[i][0]+ps/2)*2; cx=(pos[i][1]+ps/2)*2
    if all((cy-q[1])**2+(cx-q[0])**2>130**2 for q in picked):
        picked.append((cx,cy,float(d[i])))
    if len(picked)>=24: break
json.dump({'picked':picked,'median_distinctness':float(np.median(d)),'p90':float(np.percentile(d,90))},open('/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/r2/landmarks_raw.json','w'),indent=1)
np.save('/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/r2/distinct_grid.npy',d.reshape(len(range(0,n-ps+1,step)),-1))
for p in picked: print([round(v,3) if isinstance(v,float) else v for v in p])
print('median',np.median(d),'p90',np.percentile(d,90))
