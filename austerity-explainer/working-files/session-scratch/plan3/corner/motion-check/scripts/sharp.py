import numpy as np, sys, cv2
W=sys.argv[1]
for i in range(305,330):
    g=cv2.imread(f"{W}/all/f{i:03d}.png").astype(np.float32).mean(2)
    lap=cv2.Laplacian(g,cv2.CV_32F)
    n=lap[1000:1200,780:950].var(); road=lap[1300:1700,0:400].var(); sky=lap[300:500,100:400].var(); wall=lap[800:1100,950:1080].var()
    print(f"{i} t={i/30:.2f} notice {n:7.1f} road {road:6.1f} sky {sky:5.1f} wall {wall:6.1f} mean {g.mean():.2f}")
