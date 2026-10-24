import numpy as np, sys, cv2
W=sys.argv[1]
# patches as (name, x0,x1,y0,y1) in pixels (start positions; camera moves slowly here)
patches=[("right of pail",900,1000,1440,1490),("left of pail under chair",700,780,1400,1440),("below drum",620,720,1420,1460),("far ground control",300,400,1500,1550)]
for i in range(30,130,3):
    a=cv2.imread(f"{W}/all/f{i:03d}.png").astype(np.float32).mean(2)
    print(f"{i:3d} t={i/30:4.2f} "+" ".join(f"{n[:12]}={a[y0:y1,x0:x1].mean():6.1f}" for n,x0,x1,y0,y1 in patches))
