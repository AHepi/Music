import numpy as np, sys, cv2
W=sys.argv[1]
for i in list(range(26,52,2))+list(range(134,166,2))+list(range(252,290,2))+list(range(356,390,3)):
    g=cv2.imread(f"{W}/all/f{i:03d}.png").astype(np.float32).mean(2)
    a=g[80:180,60:560]  # BRITAIN 1926 / LOCKED OUT area
    b=g[160:230,60:480]
    print(f"{i:3d} t={i/30:5.2f} title-area max {a.max():5.0f} p99 {np.percentile(a,99):5.1f}  second-line p99 {np.percentile(b,99):5.1f}")
