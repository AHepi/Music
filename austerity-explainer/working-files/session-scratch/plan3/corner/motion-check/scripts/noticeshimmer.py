import numpy as np, sys, cv2
W=sys.argv[1]
def g(i): return cv2.cvtColor(cv2.imread(f"{W}/all/f{i:03d}.png"),cv2.COLOR_BGR2GRAY).astype(np.float32)
# notice small-print band region roughly (in each frame the notice grows; use a box that stays on the notice)
x0,x1,y0,y1=800,930,1000,1150
out=[]
for i in list(range(30,256,15))+list(range(270,360,15)):
    A=g(i); B=g(i+1)
    a=A[y0-40:y1+40,x0-40:x1+40]; b=B[y0-40:y1+40,x0-40:x1+40]
    warp=np.eye(2,3,dtype=np.float32)
    try:
        cc,warp=cv2.findTransformECC(a,b,warp,cv2.MOTION_AFFINE,(cv2.TERM_CRITERIA_EPS|cv2.TERM_CRITERIA_COUNT,200,1e-6),None,3)
    except cv2.error as e:
        print(i,"ecc fail"); continue
    bw=cv2.warpAffine(b,warp,(a.shape[1],a.shape[0]),flags=cv2.INTER_LINEAR+cv2.WARP_INVERSE_MAP)
    r=np.abs(bw-a)[40:-40,40:-40]
    # high-frequency residual
    print(f"{i:3d} t={i/30:5.2f} scale={warp[0,0]:.5f} shift=({warp[0,2]:+.2f},{warp[1,2]:+.2f}) resid mean={r.mean():.2f} p95={np.percentile(r,95):.1f}")
