import sys, json
sys.path.insert(0,'/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/kits/weathering/harness')
sys.path.insert(0,'/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/kits/weathering')
import measure_common as mc
import numpy as np, cv2
K='/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/'
settings=mc.load_set(K+'kits/weathering/sets/pit_village_street.json')
cls=mc.classes(settings)
B=K+'kits/weathering/harness/baseline/maps/'
P=K+'street_wet/grime_and_growth/integrated/plates/'
def lumsmall(path,w,h):
    rgb=mc.read_rgb(path); L=mc.lum(rgb)
    return cv2.resize(L,(w,h),interpolation=cv2.INTER_AREA)
out={}
for scene,camera,pairs in [('street','main',[('final_main_A_dry','dry'),('final_main_A_wet','wet')]),('lockout','lockout',[('final_lockout_B_dry','dry'),('final_lockout_B_wet','wet')])]:
    cmap=mc.read_class(B+f'class_{camera}_540x960.png')
    for name,state in pairs:
        Lb=lumsmall(P+f'{scene}/{name}_base.png',540,960); Lk=lumsmall(P+f'{scene}/{name}_kit.png',540,960)
        res={'plate_mean_ratio':round(float(Lk.mean()/Lb.mean()),4)}
        for c,ids in cls.items():
            m=mc.class_mask(cmap,ids)
            if m.sum()<200: continue
            b=Lb[m]; k=Lk[m]
            sel=b>=0.03
            res[c]=dict(n=int(m.sum()),mean_ratio=round(float(k.mean()/b.mean()),3),
                 darkened_third=round(float(((k<=2/3*b)&sel).sum()/max(1,sel.sum())),3),
                 under010_base=round(float((b<0.10).mean()),3),under010_kit=round(float((k<0.10).mean()),3),
                 under012_kit=round(float((k<0.12).mean()),3),
                 p10=round(float(np.percentile(k,10)),3),p50_base=round(float(np.median(b)),3),p50_kit=round(float(np.median(k)),3))
        out[f'{scene}_{state}']=res
print(json.dumps(out,indent=1))
json.dump(out,open('meas_A.json','w'),indent=1)
