import numpy as np, sys, cv2
W=sys.argv[1]
ref=cv2.imread(f"{W}/all/f030.png").astype(np.float32)
# region: far street/top (little motion): x 0.2-0.6, y 0.15-0.45
r=(slice(int(0.15*1920),int(0.45*1920)),slice(int(0.2*1080),int(0.6*1080)))
for i in list(range(0,31,3)):
    a=cv2.imread(f"{W}/all/f{i:03d}.png").astype(np.float32)
    g=(a[r].mean()+1e-3)/ref[r].mean()
    # fit linear a = g*ref + c
    x=ref[r].ravel(); y=a[r].ravel()
    A=np.stack([x,np.ones_like(x)],1); (gg,c),*_=np.linalg.lstsq(A,y,rcond=None)
    print(i, f"t={i/30:.2f} ratio={g:.3f} fit gain={gg:.3f} offset={c:.2f}")
