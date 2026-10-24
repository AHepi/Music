import numpy as np, sys, cv2
W=sys.argv[1]; a=int(sys.argv[2]); b=int(sys.argv[3]); out=sys.argv[4]
F=[]
for i in range(a,b):
    g=cv2.imread(f"{W}/all/f{i:03d}.png").astype(np.float32).mean(2)/min(max(i/30,1e-3),1.0)
    F.append(cv2.GaussianBlur(g,(0,0),2))
F=np.array(F)
# remove linear trend per pixel (slow drift from camera creep)
t=np.arange(len(F))[:,None,None]-len(F)/2
slope=(F*t).sum(0)/(t*t).sum(0)
R=F-F.mean(0)-slope*t
s=R.std(0)
print(np.percentile(s,[50,90,99]))
cv2.imwrite(out,np.clip(s*15,0,255).astype(np.uint8))
