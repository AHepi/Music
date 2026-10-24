import sys, json, numpy as np, cv2
KIT='/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/kits/weathering'
sys.path.insert(0,KIT); sys.path.insert(0,KIT+'/harness'); sys.dont_write_bytecode=True
import measure_common as mc
G='/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/street_wet/grime_and_growth/'
B=KIT+'/harness/baseline/maps/'
S=mc.load_set('pit_village_street'); CL=mc.classes(S)
def rd(p):
    a=cv2.imread(p,cv2.IMREAD_UNCHANGED); a=a.astype(np.float32)/(65535 if a.dtype==np.uint16 else 255); return a[...,:3][...,::-1]
def lum(a): return 0.2126*a[...,0]+0.7152*a[...,1]+0.0722*a[...,2]
sc=0.45; W,H=int(1536*sc),int(2730*sc)
cm=cv2.resize(cv2.imread(B+'class_main_540x960.png',cv2.IMREAD_UNCHANGED),(W,H),interpolation=cv2.INTER_NEAREST)
import os
cmap=mc.read_class(B+'class_main_540x960.png'); cmap=cv2.resize(cmap.astype(np.uint8),(W,H),interpolation=cv2.INTER_NEAREST)
for st in ('dry','wet'):
    base=cv2.resize(rd(G+f'integrated/plates/street/final_main_A_{st}_base.png'),(W,H),interpolation=cv2.INTER_AREA)
    for tag,p in (('old',G+f'integrated/plates/street/final_main_A_{st}_kit.png'),('fix',G+f'fix/plates/street/final_main_A_{st}_kit.png')):
        k=cv2.resize(rd(p),(W,H),interpolation=cv2.INTER_AREA)
        dL=lum(k)-lum(base)
        out={}
        for c in ('walls','road','pavement','kerb_gutter','iron'):
            m=mc.class_mask(cmap,CL[c])
            area=int(m.sum())
            for sign,name in ((-1,'dark'),(1,'pale')):
                bw=((sign*dL>=0.04)&m).astype(np.uint8)
                bw=cv2.morphologyEx(bw,cv2.MORPH_OPEN,np.ones((2,2),np.uint8))
                n,lab,stt,cen=cv2.connectedComponentsWithStats(bw,connectivity=8)
                big=[i for i in range(1,n) if stt[i,4]>=30]
                out[f'{c}_{name}']=(len(big),round(float(sum(stt[i,4] for i in big))/area,4))
        print(st,tag,json.dumps(out))
