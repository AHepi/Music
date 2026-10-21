import cv2, numpy as np, json
K='proc-work/'
B=K+'kits/weathering/harness/baseline/maps/'
P=K+'street_wet/grime_and_growth/integrated/plates/street/'
W,H=540,960
def lum(p):
    a=cv2.imread(p)[...,::-1].astype(np.float32)/255
    L=0.2126*a[...,0]+0.7152*a[...,1]+0.0722*a[...,2]
    return cv2.resize(L,(W,H),interpolation=cv2.INTER_AREA)
jm=cv2.imread(B+'jmask_main_540x960.png',cv2.IMREAD_UNCHANGED).astype(np.float32)/65535
cl=cv2.imread(B+'class_main_540x960.png',cv2.IMREAD_UNCHANGED)
pud=cv2.imread(B+'puddle_main_wet.png',cv2.IMREAD_UNCHANGED)[...,2]>32768
Lb=lum(P+'final_main_A_wet_base.png')
for c in (0,1,2):
    m=jm[...,c]>0.5
    print('channel',c,'share',round(float(m.mean()),3),'mean base lum on/off',round(float(Lb[m].mean()),3),round(float(Lb[~m].mean()),3))
print('--- my joint contrast (1 - joint/sett mean luminance) in bands of the 540x960 main plate, puddle dots left out')
joint=jm[...,2]>0.5; sett=(jm[...,1]>0.5)&~joint
res={}
for st in ('dry','wet'):
    Lb=lum(P+f'final_main_A_{st}_base.png'); Lk=lum(P+f'final_main_A_{st}_kit.png')
    ok=~pud if st=='wet' else np.ones_like(pud)
    for band,(y0,y1) in {'near(rows 800-960)':(800,960),'mid(rows 700-800)':(700,800),'far(rows 600-700)':(600,700)}.items():
        mm=np.zeros_like(ok); mm[y0:y1]=True
        j=joint&mm&ok; s=sett&mm&ok
        if j.sum()<30 or s.sum()<30: continue
        cb=1-Lb[j].mean()/Lb[s].mean(); ck=1-Lk[j].mean()/Lk[s].mean()
        res[f'{st} {band}']=dict(joint_dots=int(j.sum()),base=round(float(cb),3),kit=round(float(ck),3),ratio=round(float(ck/cb),3),sett_lum_base=round(float(Lb[s].mean()),3),sett_lum_kit=round(float(Lk[s].mean()),3))
print(json.dumps(res,indent=1)); json.dump(res,open('meas_D.json','w'),indent=1)
