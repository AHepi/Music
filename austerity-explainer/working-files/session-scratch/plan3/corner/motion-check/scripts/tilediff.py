import numpy as np, sys
from PIL import Image
W=sys.argv[1]
N=390
T=60
prev=None
rows=[]
allt=[]
for i in range(N):
    a=np.asarray(Image.open(f"{W}/all/f{i:03d}.png").convert('RGB')).astype(np.float32)
    g=a.mean(axis=2)
    if prev is not None:
        d=np.abs(g-prev)
        h,w=d.shape
        td=d[:h//T*T,:w//T*T].reshape(h//T,T,w//T,T).mean(axis=(1,3))
        allt.append(td)
        k=np.unravel_index(td.argmax(),td.shape)
        rows.append((i,d.mean(),td.max(),k))
    prev=g
np.save(f"{W}/tilediffs.npy",np.array(allt))
for r in rows:
    i,m,mx,k=r
    print(f"{i:3d} t={i/30:5.2f} mean={m:5.2f} tilemax={mx:6.2f} at x={(k[1]+.5)*T/1080:.2f} y={(k[0]+.5)*T/1920:.2f}")
