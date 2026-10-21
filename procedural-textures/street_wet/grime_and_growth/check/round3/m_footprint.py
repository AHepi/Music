import sys, json, numpy as np, cv2
KIT='proc-work/kits/weathering'
sys.path.insert(0,KIT); sys.path.insert(0,KIT+'/harness'); sys.dont_write_bytecode=True
import measure_common as mc
G='proc-work/street_wet/grime_and_growth/'
B=KIT+'/harness/baseline/maps/'
S=mc.load_set('pit_village_street'); CL=mc.classes(S)
def rd(p):
    a=cv2.imread(p,cv2.IMREAD_UNCHANGED); a=a.astype(np.float32)/(65535 if a.dtype==np.uint16 else 255); return a[...,:3][...,::-1]
for scene,cam,nm,ids in (('street','main','final_main_A',('dry','wet')),('lockout','lockout','final_lockout_B',('dry','wet'))):
    cmap=mc.read_class(B+f'class_{cam}_540x960.png')
    for st in ids:
        sc='street' if scene=='street' else 'lockout'
        bp=G+f'integrated/plates/{sc}/{nm}_{st}_base.png'
        base=cv2.resize(rd(bp),(540,960),interpolation=cv2.INTER_AREA)
        for tag,p in (('old',G+f'integrated/plates/{sc}/{nm}_{st}_kit.png'),('fix',G+f'fix/plates/{sc}/{nm}_{st}_kit.png')):
            k=cv2.resize(rd(p),(540,960),interpolation=cv2.INTER_AREA)
            d=np.abs(k-base).max(axis=2)
            row={'all>3':float((d>3/255).mean()),'all>10':float((d>10/255).mean())}
            for c in ('walls','trims','road','pavement','kerb_gutter','iron'):
                if c in CL:
                    m=mc.class_mask(cmap,CL[c])
                    if m.sum()>200: row[c+'>3']=float((d[m]>3/255).mean()); row[c+'>10']=float((d[m]>10/255).mean())
            print(scene,st,tag,{a:round(b,3) for a,b in row.items()})
