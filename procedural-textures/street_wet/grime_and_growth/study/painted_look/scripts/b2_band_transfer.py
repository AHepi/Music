"""How much of the plate's detail, at each size, is still in the painting? (band-pass pictures of both, compared region by region)
width_px below = rough width of a feature the band picks out, in plate pixels at 1536 x 2730 (about 3 x sigma)."""
import sys; sys.path.insert(0,'scripts')
from common import *
import json
SIG=[0.8,1.0,1.4,2.0,2.8,4.0,5.6,8.0,11.0,16.0,23.0,32.0]
def corr_maxshift(a,b,m,rad=2):
    best=-1;bi=None
    a0=a.copy(); 
    for dy in range(-rad,rad+1):
        for dx in range(-rad,rad+1):
            bs=np.roll(np.roll(b,dy,0),dx,1)
            x=a[m]; y=bs[m]
            c=np.corrcoef(x,y)[0,1]
            if c>best: best=c;bi=(dx,dy)
    return best
out={}
for name,(p,q) in PAIRS.items():
    A=lum(load_rgb(p)); B=lum(load_rgb(WORK+f"/{name}_painting_registered.png"))
    if name.startswith('lockout'):
        M=lockout_masks()
        ys=np.nonzero(M['road'].any(axis=1))[0]; y0,y1=ys.min(),ys.max()
        thirds=[y0,y0+(y1-y0)//3,y0+2*(y1-y0)//3,y1+1]
        def rowband(m,a,b):
            r=np.zeros_like(m); r[a:b]=m[a:b]; return r
        regs={'road far':rowband(M['road'],thirds[0],thirds[1]),'road middle':rowband(M['road'],thirds[1],thirds[2]),'road near':rowband(M['road'],thirds[2],thirds[3]),
              'pavement+kerb+gutter':M['pavement']|M['kerb']|M['gutter'],'walls':M['walls'],'roofs':M['roofs'],'sky':M['sky']}
        regs={k:erode(v,9) for k,v in regs.items()}
    else:
        yy=np.arange(H)[:,None]*np.ones((1,W)); 
        regs={'upper third (sky, roofs, far walls)':yy<H/3,'middle third':(yy>=H/3)&(yy<2*H/3),'lower third (road, pavement, near)':yy>=2*H/3}
    res={}
    for s in SIG:
        da=dog(A,s); db=dog(B,s)
        for rn,m in regs.items():
            if m.sum()<5000: continue
            sa=float(da[m].std()); sb=float(db[m].std())
            c=corr_maxshift(da,db,m,1)
            res.setdefault(rn,[]).append({'sigma':s,'width_px':round(3*s,1),'plate_rms':sa,'paint_rms':sb,'ratio':sb/max(sa,1e-9),'corr':float(c)})
    out[name]=res
    print("=====",name)
    for rn,rows in res.items():
        print(" ",rn)
        print("   width_px: "+" ".join("%5.1f"%r['width_px'] for r in rows))
        print("   corr    : "+" ".join("%5.2f"%r['corr'] for r in rows))
        print("   rms plate: "+" ".join("%5.3f"%r['plate_rms'] for r in rows))
        print("   rms paint: "+" ".join("%5.3f"%r['paint_rms'] for r in rows))
json.dump(out,open(NUM+'/b2_band_transfer.json','w'),indent=1)
