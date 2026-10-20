# What this does (plain words): looks at all the rivets found in the reference and builds the "typical rivet": for rings around the centre and
# 8 slices (sectors) round the circle, the middle colour over all rivets. The middle value ignores rust drips that sit on only a few of them.
# Also refines each rivet centre by sliding the typical rivet a few dots. Analysis only (reads the reference). Writes rivet_template.json.
import cv2, numpy as np, json, math
PROC='proc-work'
c=cv2.imread(PROC+'/reference/metal/colour.png')[...,::-1].astype(np.float32)
H,W=c.shape[:2]; P=80
cp=cv2.copyMakeBorder(c,P,P,P,P,cv2.BORDER_WRAP)
rivets=[r for r in json.load(open('rivets_found.json')) if r[2]>=0.68 and not (abs(r[0]-1061)<3 and abs(r[1]-23)<3) and not (abs(r[0]-472)<3 and abs(r[1]-624)<3)]
rivets.append([840,683,0.67])
def polar(cx,cy,radii,sectors,first=0.0):
    out=np.zeros((len(radii),sectors,3),np.float32)
    for si in range(sectors):
        for ri,r in enumerate(radii):
            a=math.radians(first)+2*math.pi*(si+0.5)/sectors
            xs=cx+r*np.cos(a)+P; ys=cy+r*np.sin(a)+P
            out[ri,si]=cv2.remap(cp,np.array([[xs]],np.float32),np.array([[ys]],np.float32),cv2.INTER_LINEAR)[0,0]
    return out
radii=np.arange(0,34,2.0)
stack=np.array([polar(x,y,radii,8) for x,y,_ in rivets])   # (n, ring, sector, 3)
med=np.median(stack,axis=0)
g=med@np.array([.299,.587,.114])
np.set_printoptions(linewidth=200,precision=0,suppress=True)
print('radius  sector grey medians (8 sectors, first at angle 22.5 deg from +x, clockwise on screen since y is down)')
for r,row in zip(radii,g): print('%4.0f'%r,row)
# radial mean over sectors and spread: where is the rivet edge? largest drop
rad=g.mean(axis=1); print('radial mean',rad)
