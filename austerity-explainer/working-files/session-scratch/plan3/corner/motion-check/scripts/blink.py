import numpy as np, sys, cv2
W=sys.argv[1]
T=40
def g(i): return cv2.imread(f"{W}/all/f{i:03d}.png").astype(np.float32).mean(2)
prev=g(0); cur=g(1)
res=[]
for i in range(1,389):
    nxt=g(i+1)
    d=np.abs(cur-(prev+nxt)/2)
    h,w=d.shape
    td=d[:h//T*T,:w//T*T].reshape(h//T,T,w//T,T).mean(axis=(1,3))
    res.append(td)
    prev,cur=cur,nxt
R=np.array(res)  # frames 1..388
# exclude fire/smoke/sparks region and title band
ny,nx=R.shape[1:]
ys=(np.arange(ny)+.5)*T/1920; xs=(np.arange(nx)+.5)*T/1080
mask=np.ones((ny,nx),bool)
mask[np.ix_((ys>0.40)&(ys<0.67),(xs>0.42)&(xs<0.82))]=False
mask[np.ix_(ys<0.13,xs<0.7)]=False
# score relative to the tile's median over time
med=np.median(R,axis=0)+0.5
S=R/med
S[:,~mask]=0
flat=np.argsort(S.ravel())[::-1][:20]
for k in flat:
    f,y,x=np.unravel_index(k,S.shape)
    print(f"frame {f+1} t={(f+1)/30:.2f} at ({xs[x]:.2f},{ys[y]:.2f}) value {R[f,y,x]:.2f} vs typical {med[y,x]-0.5:.2f} ratio {S[f,y,x]:.1f}")
