import sys, json
sys.path.insert(0,'/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/kits/weathering/harness')
sys.path.insert(0,'/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/kits/weathering')
import measure_common as mc, numpy as np, cv2
K='/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/'
settings=mc.load_set(K+'kits/weathering/sets/pit_village_street.json'); cls=mc.classes(settings)
B=K+'kits/weathering/harness/baseline/maps/'; P=K+'street_wet/grime_and_growth/integrated/plates/'
def rgb(p): return cv2.resize(cv2.imread(p)[...,::-1].astype(np.float32)/255,(540,960),interpolation=cv2.INTER_AREA)
out={}
for scene,camera,names in [('street','main',['final_main_A_dry','final_main_A_wet']),('lockout','lockout',['final_lockout_B_dry','final_lockout_B_wet'])]:
    cmap=mc.read_class(B+f'class_{camera}_540x960.png')
    for n in names:
        b=rgb(P+f'{scene}/{n}_base.png'); k=rgb(P+f'{scene}/{n}_kit.png'); d=np.abs(k-b).max(axis=2)
        r={}
        for c in ['walls','trims','road','pavement','kerb_gutter','iron']:
            m=mc.class_mask(cmap,cls[c]); r[c]=dict(over3=round(float((d[m]>3/255).mean()),3),over10=round(float((d[m]>10/255).mean()),3),over25=round(float((d[m]>25/255).mean()),3))
        out[f'{scene}_{n.split("_")[-1]}']=r
print(json.dumps(out,indent=0))
json.dump(out,open('meas_E.json','w'),indent=1)
