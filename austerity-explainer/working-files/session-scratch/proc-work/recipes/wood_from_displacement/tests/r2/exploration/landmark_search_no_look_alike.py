# What this does (plain words): the first, exploratory search of round 2 for 'places of the source map that have no look-alike elsewhere' (flipped copies included): for every 132-dot patch of the height and colour maps (stepped by 18 dots) it finds the most similar other patch and reports the patches with the LARGEST smallest distance. Result: no place stands out (median distance 0.099, 90th percent 0.114, largest 0.146), so the landmarks were chosen by eye instead (see the guide, section 9, round 2, item 2). Kept for the record; written to the scratch folder, not needed by the recipe. Run with python3 -I (numpy and PIL only); it writes landmarks_coarse.json and landmarks_overlay.jpg next to itself.
import numpy as np, json, time
from PIL import Image, ImageDraw
P='/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/'
h=np.asarray(Image.open(P+'reference/wood/height_as_uploaded.png').convert('L'),dtype=np.float32)/255
c=np.asarray(Image.open(P+'reference/wood/colour.png').convert('RGB'),dtype=np.float32)/255
f=6
n=1254//f*f
def down(a): return a[:n,:n].reshape(n//f,f,n//f,f).mean((1,3))
Hh=down(h); Cc=np.stack([down(c[...,i]) for i in range(3)],-1)
Fm=np.concatenate([Hh[...,None],Cc],-1)   # 209x209x4
m=Fm.shape[0]
ps=22 # 132 dots
step=3 # 18 dots
ys=list(range(0,m-ps+1,step)); xs=ys
pos=[(y,x) for y in ys for x in xs]
N=len(pos); print(N)
X=np.stack([Fm[y:y+ps,x:x+ps].reshape(-1) for y,x in pos]).astype(np.float32)
sq=(X*X).sum(1)
def fl(k):
    out=[]
    for y,x in pos:
        p=Fm[y:y+ps,x:x+ps]
        if k&1:p=p[:,::-1]
        if k&2:p=p[::-1]
        out.append(p.reshape(-1))
    return np.stack(out).astype(np.float32)
py=np.array([p[0] for p in pos]); px=np.array([p[1] for p in pos])
near=(np.abs(py[:,None]-py[None])<ps*1.05)&(np.abs(px[:,None]-px[None])<ps*1.05)
dmin=np.full(N,1e9,dtype=np.float32)
for k in range(4):
    Y=fl(k); D=sq[:,None]+(Y*Y).sum(1)[None]-2*X@Y.T; D[near]=1e9; dmin=np.minimum(dmin,D.min(1))
d=np.sqrt(np.maximum(dmin,0)/X.shape[1])
print('median',np.median(d),'p90',np.percentile(d,90),'max',d.max())
order=np.argsort(-d); picked=[]
for i in order:
    cy=(pos[i][0]+ps/2)*f; cx=(pos[i][1]+ps/2)*f
    if all((cy-q[1])**2+(cx-q[0])**2>150**2 for q in picked):
        picked.append((float(cx),float(cy),float(d[i])))
    if len(picked)>=22: break
json.dump(picked,open('landmarks_coarse.json','w'))
im=Image.open(P+'reference/wood/colour.png').convert('RGB'); dr=ImageDraw.Draw(im)
for k,(cx,cy,v) in enumerate(picked):
    dr.ellipse((cx-66,cy-66,cx+66,cy+66),outline=(255,255,0),width=3); dr.text((cx-6,cy-6),str(k),fill=(255,255,0))
    print(k,round(cx),round(cy),round(v,3))
im.save('landmarks_overlay.jpg',quality=88)
