"""Does the painter darken the foot of the walls (a dark plinth) by itself?  Foot / middle brightness of the walls, plate vs painting."""
import sys; sys.path.insert(0,'scripts')
from common import *
import json
M=lockout_masks()
walls=M['walls']&~M['props near']
res={}
for name in ('lockout_dry','lockout_wet','lockout_wet_r2'):
    p,q=PAIRS[name]
    A=lum(load_rgb(p)); B=lum(load_rgb(WORK+f"/{name}_painting_registered.png"))
    ysn=np.full(W,-1); ysx=np.full(W,-1)
    cols=np.nonzero(walls.any(axis=0))[0]
    pos=np.full((H,W),np.nan,np.float32)
    for x in cols:
        r=np.nonzero(walls[:,x])[0]
        if len(r)<150: continue
        y0,y1=r.min(),r.max()
        pos[r,x]=(r-y0)/max(1,(y1-y0))
    foot=(pos>0.88); mid=(pos>0.35)&(pos<0.6); top=(pos<0.15)
    f=lambda I,m: float(I[m&walls].mean())
    r={'plate_foot_over_mid':f(A,foot)/f(A,mid),'paint_foot_over_mid':f(B,foot)/f(B,mid),'plate_top_over_mid':f(A,top)/f(A,mid),'paint_top_over_mid':f(B,top)/f(B,mid),
       'plate_foot':f(A,foot),'plate_mid':f(A,mid),'paint_foot':f(B,foot),'paint_mid':f(B,mid),'foot_pixels':int((foot&walls).sum())}
    res[name]=r
    print(name,{k:round(v,3) for k,v in r.items()})
json.dump(res,open(NUM+'/e3_wall_foot.json','w'),indent=1)
