"""How does the painter treat hue and colour strength?  Plate pixels grouped by hue (blurred 2 px), painting hue/saturation/brightness for the same pixels."""
import sys; sys.path.insert(0,'scripts')
from common import *
import json
def hsv(rgb):
    x=(rgb*255).astype(np.uint8); h=cv2.cvtColor(x,cv2.COLOR_RGB2HSV_FULL).astype(np.float32)
    return h[...,0]*360/255, h[...,1]/255, h[...,2]/255
out={}
SECT=[('red/orange',(-30,40)),('yellow-brown',(40,75)),('green',(75,150)),('teal/cyan',(150,200)),('blue',(200,260)),('purple/magenta',(260,330))]
for name in PAIRS:
    p,q=PAIRS[name]
    A=load_rgb(p); B=load_rgb(WORK+f"/{name}_painting_registered.png")
    A=np.stack([gauss(A[...,i],2.0) for i in range(3)],-1); B=np.stack([gauss(B[...,i],2.0) for i in range(3)],-1)
    ha,sa,va=hsv(A); hb,sb,vb=hsv(B)
    ha=np.where(ha>330,ha-360,ha)
    print("=====",name)
    out[name]={}
    for nm,(lo,hi) in SECT:
        m=(ha>=lo)&(ha<hi)&(sa>0.18)&(va>0.10)
        if m.sum()<3000: print("  ",nm,"too few (",int(m.sum()),")"); continue
        hbb=np.where(hb>330,hb-360,hb)
        # circular mean hue of painting for these pixels
        ang=np.deg2rad(hbb[m]); mh=np.rad2deg(np.arctan2(np.sin(ang).mean(),np.cos(ang).mean()))
        # share of the painting pixels that stay in the same sector / saturation > .12
        stay=((hbb[m]>=lo)&(hbb[m]<hi)&(sb[m]>0.12)).mean()
        r=dict(n=int(m.sum()),plate_hue=float(np.rad2deg(np.arctan2(np.sin(np.deg2rad(ha[m])).mean(),np.cos(np.deg2rad(ha[m])).mean()))),paint_hue=float(mh),plate_sat=float(sa[m].mean()),paint_sat=float(sb[m].mean()),plate_val=float(va[m].mean()),paint_val=float(vb[m].mean()),stay_in_sector=float(stay))
        out[name][nm]=r
        print("   %-15s n=%8d plate hue %5.0f -> painting hue %5.0f | saturation %.2f -> %.2f | brightness(V) %.2f -> %.2f | stay in the same colour family: %3.0f%%"%(nm,r['n'],r['plate_hue'],r['paint_hue'],r['plate_sat'],r['paint_sat'],r['plate_val'],r['paint_val'],100*stay))
json.dump(out,open(NUM+'/e1_hue.json','w'),indent=1)
