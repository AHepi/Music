import numpy as np, sys, cv2
W=sys.argv[1]; a=int(sys.argv[2]); b=int(sys.argv[3]); out=sys.argv[4]
acc=None; acc2=None; n=0
for i in range(a,b):
    g=cv2.imread(f"{W}/all/f{i:03d}.png").astype(np.float32).mean(2)
    g=cv2.GaussianBlur(g,(0,0),2)
    if acc is None: acc=np.zeros_like(g); acc2=np.zeros_like(g)
    acc+=g; acc2+=g*g; n+=1
m=acc/n; s=np.sqrt(np.maximum(acc2/n-m*m,0))
print("std percentiles",np.percentile(s,[50,90,99,99.9]))
cv2.imwrite(out,np.clip(s*12,0,255).astype(np.uint8))
