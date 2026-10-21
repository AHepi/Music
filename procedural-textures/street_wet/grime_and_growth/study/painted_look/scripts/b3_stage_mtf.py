"""What does the film stage do to fine detail of the painting (lens blur, grain, scale)?  Plate-view still of the film's lockout scene (stage, 1080 x 1920)
against its painting, lined up with a similarity transform (the film's lens is 40 degrees, the plate's 44)."""
import sys; sys.path.insert(0,'scripts')
from common import *
import json
ST=SW+"/painter_test/stage/stills/"
pairs={'dry':(PV+"/lockout-painted.jpg",ST+"dry_projector/still-6.00.jpg"),'wet':(SW+"/painter_test/pictures/wet_painting_lined_up.png",ST+"wet_projector/still-6.00.jpg")}
SW_,SH_=1080,1920
out={}
for k,(pa,st) in pairs.items():
    Pfull=load_rgb(pa)                      # 1536 x 2730
    S=load_rgb(st,(SW_,SH_))
    Ls=lum(S)
    # painting at about the stage's scale to start the search: crop of the middle 0.9 -> 1080
    # the film's start frame is the plate camera with a 40 degree lens (plate 44): stage px -> plate px is a pure scale 1.281 about the middle
    # (edge correlation peaks at 1.28 with no shift, scripts/b3a_stage_align.py)
    sc=1.281
    M=np.array([[sc,0,768-sc*540],[0,sc,1365-sc*960]],np.float32)
    Pw=np.stack([cv2.warpAffine(Pfull[...,i],M,(SW_,SH_),flags=cv2.INTER_AREA|cv2.WARP_INVERSE_MAP,borderMode=cv2.BORDER_REFLECT) for i in range(3)],-1)
    Lp=lum(Pw)
    cv2.imwrite(WORK+f"/stage_{k}_painting_on_stage_grid.png",cv2.cvtColor((Pw*255+.5).astype(np.uint8),cv2.COLOR_RGB2BGR))
    M0=lockout_masks((SW_,SH_))
    ys=np.nonzero(M0['road'].any(axis=1))[0]; y0,y1=ys.min(),ys.max(); th=[y0,y0+(y1-y0)//3,y0+2*(y1-y0)//3,y1+1]
    def rb(m,a,b): r=np.zeros_like(m); r[a:b]=m[a:b]; return r
    # the masks are for the plate camera; the stage frame is the 40-degree crop -> use the warped masks
    def wmask(m):
        mm=cv2.warpAffine(m.astype(np.uint8)*255,np.hstack([np.linalg.inv(np.vstack([M,[0,0,1]]))[:2,:2],np.zeros((2,1))]) if False else M,(SW_,SH_),flags=cv2.INTER_NEAREST|cv2.WARP_INVERSE_MAP) 
        return mm>127
    # masks are at plate size: warp from the plate size 1536x2730
    Mp=lockout_masks()
    regs={}
    for nm in ['road','pavement','walls','roofs']:
        mm=cv2.warpAffine(Mp[nm].astype(np.uint8)*255,M,(SW_,SH_),flags=cv2.INTER_NEAREST|cv2.WARP_INVERSE_MAP)>127
        regs[nm]=erode(mm,9)
    ys=np.nonzero(regs['road'].any(axis=1))[0]; y0,y1=ys.min(),ys.max(); th=[y0,y0+(y1-y0)//3,y0+2*(y1-y0)//3,y1+1]
    regs2={'road far':rb(regs['road'],th[0],th[1]),'road middle':rb(regs['road'],th[1],th[2]),'road near':rb(regs['road'],th[2],th[3]),'pavement':regs['pavement'],'walls':regs['walls']}
    # glow and fire spoil the comparison near lights: drop the brightest areas
    ok=(gauss(Lp,6)<0.6)
    res={}
    for sg in [0.8,1.0,1.4,2.0,2.8,4.0,5.6,8.0,11.0,16.0]:
        da=dog(Lp,sg); db=dog(Ls,sg)
        for rn,m in regs2.items():
            m=m&ok
            if m.sum()<4000: continue
            ra=float(da[m].std()); rbb=float(db[m].std())
            best_c=-1
            for dy in (-1,0,1):
                for dx in (-1,0,1):
                    c=np.corrcoef(da[m],np.roll(np.roll(db,dy,0),dx,1)[m])[0,1]; best_c=max(best_c,c)
            res.setdefault(rn,[]).append({'sigma_film_px':sg,'width_film_px':round(3*sg,1),'painting_rms':ra,'stage_rms':rbb,'ratio':rbb/max(ra,1e-9),'corr':float(best_c)})
    out[k]=res
    for rn,rows in res.items():
        print(" ",k,rn)
        print("   width_film_px: "+" ".join("%5.1f"%r['width_film_px'] for r in rows))
        print("   stage/painting rms: "+" ".join("%5.2f"%r['ratio'] for r in rows))
        print("   correlation      : "+" ".join("%5.2f"%r['corr'] for r in rows))
json.dump(out,open(NUM+'/b3_stage_mtf.json','w'),indent=1)
