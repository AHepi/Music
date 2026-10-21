"""What brightness does a plate value turn into in the painting (and then in the film)?  Per region, from lined-up pairs."""
import sys; sys.path.insert(0,'scripts')
from common import *
from stage_curve import *
import json
BINS=[0,0.02,0.04,0.06,0.08,0.10,0.13,0.17,0.22,0.30,0.45,0.7,1.01]
out={}
import sys as _s
ONLY=_s.argv[1:] 
for name,(p,q) in PAIRS.items():
    if ONLY and name not in ONLY: continue
    A=gauss(lum(load_rgb(p)),2.0); Bf=load_rgb(WORK+f"/{name}_painting_registered.png"); B=gauss(lum(Bf),2.0)
    if name.startswith('lockout'):
        M=lockout_masks()
        regs={'ground':erode(M['road']|M['pavement']|M['kerb']|M['gutter'],7),'walls+roofs':erode(M['walls']|M['roofs']|M['colliery'],7),'sky':erode(M['sky'],9),'everything':np.ones((H,W),bool)}
    else:
        yy=np.arange(H)[:,None]*np.ones((1,W))
        regs={'lower half':yy>=H*0.5,'upper half':yy<H*0.5,'everything':np.ones((H,W),bool)}
    out[name]={}
    print("=====",name)
    for rn,m in regs.items():
        rows=[]
        for a,b in zip(BINS[:-1],BINS[1:]):
            s=m&(A>=a)&(A<b)
            if s.sum()<2000: continue
            q=B[s]
            rows.append({'plate_lo':a,'plate_hi':b,'n':int(s.sum()),'plate_mean':float(A[s].mean()),'paint_mean':float(q.mean()),'paint_p10':float(np.percentile(q,10)),'paint_p90':float(np.percentile(q,90)),
                         'film_of_paint_mean':float(stage_grey(q.mean()))})
        out[name][rn]=rows
        print(" ",rn)
        for r in rows: print("    plate %.2f-%.2f (%.0f%% of region)  mean %.3f -> painting mean %.3f  [p10 %.3f, p90 %.3f]  -> film %.3f"%(r['plate_lo'],r['plate_hi'],100*r['n']/m.sum(),r['plate_mean'],r['paint_mean'],r['paint_p10'],r['paint_p90'],r['film_of_paint_mean']))
        # region darkness shares
        sh={}
        for thr in (0.05,0.08,0.10,0.13,0.17):
            sh[str(thr)]={'plate':float((A[m]<thr).mean()),'painting':float((B[m]<thr).mean())}
        out[name][rn+'_dark_shares']=sh
        print("    share darker than: "+"  ".join(f"<{t}: plate {v['plate']*100:.0f}% painting {v['painting']*100:.0f}%" for t,v in sh.items()))
json.dump(out,open(NUM+('/d1_tone_map_'+'_'.join(ONLY)+'.json' if ONLY else '/d1_tone_map.json'),'w'),indent=1)
