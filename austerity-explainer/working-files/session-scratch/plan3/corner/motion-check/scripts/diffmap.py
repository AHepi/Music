import numpy as np, sys
from PIL import Image
W=sys.argv[1]; a=int(sys.argv[2]); b=int(sys.argv[3]); gain=float(sys.argv[4]); out=sys.argv[5]
A=np.asarray(Image.open(f"{W}/all/f{a:03d}.png").convert('RGB')).astype(np.float32)
B=np.asarray(Image.open(f"{W}/all/f{b:03d}.png").convert('RGB')).astype(np.float32)
d=np.abs(A-B).mean(axis=2)
print("mean",d.mean(),"p99",np.percentile(d,99),"max",d.max())
# band stats by rows of 10% height
for k in range(10):
    s=d[k*192:(k+1)*192]
    print(f"y {k/10:.1f}-{(k+1)/10:.1f}: mean {s.mean():.2f}")
Image.fromarray(np.clip(d*gain,0,255).astype(np.uint8)).save(out)
