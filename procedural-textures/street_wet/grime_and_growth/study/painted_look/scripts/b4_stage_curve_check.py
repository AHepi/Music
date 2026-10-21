import sys; sys.path.insert(0,'scripts')
from common import *
from stage_curve import *
import json
ST=SW+"/painter_test/stage/stills/"
SWd,SHd=1080,1920
sc=1.281
Mp=lockout_masks()
M=np.array([[sc,0,768-sc*540],[0,sc,1365-sc*960]],np.float32)
out={}
for k,st in (('dry',ST+"dry_projector/still-6.00.jpg"),('wet',ST+"wet_projector/still-6.00.jpg")):
    P=load_rgb(WORK+f"/stage_{k}_painting_on_stage_grid.png",(SWd,SHd)); S=load_rgb(st,(SWd,SHd))
    Pb=np.stack([gauss(P[...,i],2.0) for i in range(3)],-1); Sb=np.stack([gauss(S[...,i],2.0) for i in range(3)],-1)
    Lp=lum(Pb); Ls=lum(Sb)
    yy,xx=np.mgrid[0:SHd,0:SWd]; cx=(xx/SWd-0.5); cy=(yy/SHd-0.5)
    edge=smoothstep(0.85,0.2,np.sqrt((cx*0.9)**2+cy**2)*1.25)
    pred=np.zeros_like(Pb)
    for i in range(0,SHd,240): pred[i:i+240]=stage_rgb(Pb[i:i+240],LOOK_LOCKOUT,edge[i:i+240,:,None])
    Lm=lum(pred)
    wm={}
    for nm in ['props near','props far','windows','road','pavement','walls','roofs','sky']:
        wm[nm]=cv2.warpAffine(Mp[nm].astype(np.uint8)*255,M,(SWd,SHd),flags=cv2.INTER_NEAREST|cv2.WARP_INVERSE_MAP)>127
    keep=(edge>0.97)&~wm['props near']&~wm['props far']&~wm['windows']&(gauss(Lp,8)<0.6)&(wm['road']|wm['pavement']|wm['walls']|wm['roofs'])
    bins=[0,0.03,0.06,0.09,0.12,0.15,0.18,0.21,0.25,0.3,0.4,0.5,0.6]
    rows=[]
    for a,b in zip(bins[:-1],bins[1:]):
        m=keep&(Lp>=a)&(Lp<b)
        if m.sum()<500: continue
        rows.append(dict(a=a,b=b,n=int(m.sum()),painted=float(Lp[m].mean()),stage=float(Ls[m].mean()),model=float(Lm[m].mean())))
    out[k]=rows
    print(k,"mean abs err model %.4f, mean signed (stage-model) %.4f"%(np.abs(Lm-Ls)[keep].mean(),(Ls-Lm)[keep].mean()))
    for r in rows: print("   painted %.2f-%.2f n=%7d  painted %.3f -> stage %.3f   (my model %.3f)"%(r['a'],r['b'],r['n'],r['painted'],r['stage'],r['model']))
    # per region
    for nm in ['road','pavement','walls','roofs']:
        m=keep&wm[nm]
        print("   region",nm,"painted mean %.3f stage mean %.3f model %.3f ratio stage/painted %.2f"%(Lp[m].mean(),Ls[m].mean(),Lm[m].mean(),Ls[m].mean()/Lp[m].mean()))
json.dump(out,open(NUM+'/b4_stage_curve_check.json','w'),indent=1)
