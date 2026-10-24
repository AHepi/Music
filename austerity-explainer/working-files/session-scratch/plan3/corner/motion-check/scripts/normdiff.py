import numpy as np, sys, cv2
W=sys.argv[1]
ref=cv2.imread(f"{W}/all/f045.png").astype(np.float32)
out=[]
for i in [9,12,15,18,21,24,27,30,36,45]:
    a=cv2.imread(f"{W}/all/f{i:03d}.png").astype(np.float32)
    g=min(i/30,1.0)
    n=a/g
    cv2.imwrite(f"{W}/crops/norm_{i:03d}.png",np.clip(n,0,255).astype(np.uint8))
    d=np.abs(n-ref).mean(2)
    # tiles 60
    T=60; h,w=d.shape
    td=d[:h//T*T,:w//T*T].reshape(h//T,T,w//T,T).mean(axis=(1,3))
    top=np.argsort(td.ravel())[::-1][:6]
    print(i, f"mean {d.mean():.2f}", " ".join(f"({(k%td.shape[1]+.5)*T/1080:.2f},{(k//td.shape[1]+.5)*T/1920:.2f}):{td.ravel()[k]:.1f}" for k in top))
    cv2.imwrite(f"{W}/crops/normdiff_{i:03d}_vs045.png",np.clip(d*8,0,255).astype(np.uint8))
