import numpy as np, sys, cv2
W=sys.argv[1]
G=[]
idx=list(range(266,360))
for i in idx:
    G.append(cv2.imread(f"{W}/all/f{i:03d}.png").astype(np.float32).mean(2))
G=np.array(G)
s=G[:,1170:1220,430:480].mean(axis=(1,2))
imax=idx[int(s.argmax())]; imin=idx[int(s.argmin())]
print("max glow frame",imax,s.max(),"min glow frame",imin,s.min())
D=G[idx.index(imax)]-G[idx.index(imin)]
D=cv2.GaussianBlur(D,(0,0),3)
# horizontal profile at y=1200 from x=250 to 560
row=D[1200,250:560]
print("profile y=1200 (x: diff)")
print(" ".join(f"{250+k}:{row[k]:.1f}" for k in range(0,310,10)))
# vertical profile at x=450 from y=850 to 1500
col=D[850:1500,450]
print("profile x=450 (y: diff)")
print(" ".join(f"{850+k}:{col[k]:.1f}" for k in range(0,650,25)))
cv2.imwrite(f"{W}/crops/glow_diff.png",np.clip(D*12+20,0,255).astype(np.uint8))
# single frame: brightness profile along y=1200 in max frame
r2=cv2.GaussianBlur(G[idx.index(imax)],(0,0),3)[1200,250:560]
print("max-frame brightness along y=1200:"," ".join(f"{250+k}:{r2[k]:.0f}" for k in range(0,310,10)))
