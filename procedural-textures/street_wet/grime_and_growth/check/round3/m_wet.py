import sys, numpy as np, cv2
KIT='proc-work/kits/weathering'
sys.path.insert(0,KIT); sys.path.insert(0,KIT+'/harness'); sys.dont_write_bytecode=True
import measure_common as mc
G='proc-work/street_wet/grime_and_growth/'
B=KIT+'/harness/baseline/maps/'
S=mc.load_set('pit_village_street'); CL=mc.classes(S)
def rd(p):
    a=cv2.imread(p,cv2.IMREAD_UNCHANGED); a=a.astype(np.float32)/(65535 if a.dtype==np.uint16 else 255); return a[...,:3][...,::-1]
def lum(a): return 0.2126*a[...,0]+0.7152*a[...,1]+0.0722*a[...,2]
for scene,cam,nm in (('street','main','final_main_A'),('lockout','lockout','final_lockout_B')):
    cmap=mc.read_class(B+f'class_{cam}_540x960.png')
    L={}
    for st in ('dry','wet'):
        for tag,p in (('base',G+f'integrated/plates/{scene}/{nm}_{st}_base.png'),('fix',G+f'fix/plates/{scene}/{nm}_{st}_kit.png')):
            L[(st,tag)]=lum(cv2.resize(rd(p),(540,960),interpolation=cv2.INTER_AREA))
    for c in ('walls','trims','road','pavement'):
        m=mc.class_mask(cmap,CL[c])
        rb=L[('wet','base')][m].mean()/L[('dry','base')][m].mean(); rf=L[('wet','fix')][m].mean()/L[('dry','fix')][m].mean()
        p95b=np.percentile(L[('wet','base')][m],95); p95f=np.percentile(L[('wet','fix')][m],95)
        print(scene,c,'wet/dry base %.3f fix %.3f (diff %.3f) | wet p95 base %.3f fix %.3f'%(rb,rf,rf-rb,p95b,p95f))
