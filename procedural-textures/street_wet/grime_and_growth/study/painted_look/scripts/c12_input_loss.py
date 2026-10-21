"""What the painter literally receives: the plate shrunk to 0.53, 0.45, 0.40 (and 0.3) of its size.  How much of a mark's contrast is left in the shrunk picture, by mark width?"""
import sys; sys.path.insert(0,'scripts')
import c7_specific_match as C
from common import *
import json
p,q=PAIRS['lockout_wet_r2']
A=lum(load_rgb(p))
M=lockout_masks()
reg=erode(M['road']|M['pavement']|M['kerb']|M['gutter'],7)|erode(M['walls'],9)
res={}
versions={}
for s in (0.527,0.45,0.40,0.30):
    small=cv2.resize(A,(int(round(W*s)),int(round(H*s))),interpolation=cv2.INTER_AREA)   # how the picture was shrunk before sending (area average)
    versions[s]=cv2.resize(small,(W,H),interpolation=cv2.INTER_CUBIC)
out={}
for dark in (True,False):
    lab,items=C.marks(A,reg,dark,17,0.03)
    rows=[]
    for (i,x,y,w,h,area) in items:
        if x<100 or y<100 or x+w>W-100 or y+h>H-100: continue
        m=12; x0,y0,x1,y1=x-m,y-m,x+w+m,y+h+m
        comp=(lab[y0:y1,x0:x1]==i)
        dt=cv2.distanceTransform(comp.astype(np.uint8),cv2.DIST_L2,3); width=2*dt.max()
        ring=cv2.dilate(comp.astype(np.uint8),C.disc(11))>0; ring&=~(cv2.dilate(comp.astype(np.uint8),C.disc(3))>0)
        if ring.sum()<8: continue
        s0=C.signal(A[y0:y1,x0:x1],comp,ring,dark)
        if s0<0.04: continue
        r={'width':float(width),'plate':float(s0)}
        for s,V in versions.items(): r[str(s)]=float(C.signal(V[y0:y1,x0:x1],comp,ring,dark)/s0)
        rows.append(r)
    out['dark' if dark else 'bright']=rows
    R=rows
    print("dark" if dark else "bright","marks with plate contrast >= 0.04:",len(R))
    Wd=np.array([r['width'] for r in R])
    for (wlo,whi) in [(0,2.5),(2.5,4.5),(4.5,8),(8,16)]:
        sel=(Wd>=wlo)&(Wd<whi)
        if sel.sum()<10: continue
        print("  width %4.1f-%4.1f px (n=%3d): contrast left after shrinking to  0.53: %3.0f%%   0.45: %3.0f%%   0.40: %3.0f%%   0.30: %3.0f%%"%(wlo,whi,sel.sum(),*(100*np.median([r[str(s)] for r,m in zip(R,sel) if m]) for s in (0.527,0.45,0.40,0.30))))
json.dump(out,open(NUM+'/c12_input_loss.json','w'))
