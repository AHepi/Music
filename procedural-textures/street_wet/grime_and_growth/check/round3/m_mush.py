import sys, json, numpy as np, cv2
KIT='proc-work/kits/weathering'
sys.path.insert(0,KIT); sys.path.insert(0,KIT+'/harness'); sys.dont_write_bytecode=True
import measure_common as mc
G='proc-work/street_wet/grime_and_growth/'
B=KIT+'/harness/baseline/maps/'
S=mc.load_set('pit_village_street'); CL=mc.classes(S)
def rd(p):
    a=cv2.imread(p,cv2.IMREAD_UNCHANGED); a=a.astype(np.float32)/(65535 if a.dtype==np.uint16 else 255); return a[...,:3][...,::-1]
def lum(a): return 0.2126*a[...,0]+0.7152*a[...,1]+0.0722*a[...,2]
cmap=mc.read_class(B+'class_main_540x960.png'); dep=mc.read_depth(B+'depth_main_540x960.png')
for st in ('dry','wet'):
    base=cv2.resize(rd(G+f'integrated/plates/street/final_main_A_{st}_base.png'),(540,960),interpolation=cv2.INTER_AREA)
    k=cv2.resize(rd(G+f'fix/plates/street/final_main_A_{st}_kit.png'),(540,960),interpolation=cv2.INTER_AREA)
    Lb,Lk=lum(base),lum(k)
    print(st,'plate mean ratio',round(float(Lk.mean()/Lb.mean()),4),'plate mean base',round(float(Lb.mean()),3))
    for c in ('walls','trims','road','pavement','kerb_gutter','iron','colliery'):
        if c not in CL: continue
        m=mc.class_mask(cmap,CL[c])
        sel=m&(Lb>=0.03)
        dark3=float(((Lk<=2/3*Lb)&sel).sum()/max(1,sel.sum()))
        print('  %-12s n=%6d mean ratio %.3f  darkened-third %.3f  under0.10 base %.3f -> kit %.3f  base median %.3f -> %.3f'%(c,m.sum(),Lk[m].mean()/Lb[m].mean(),dark3,(Lb[m]<0.10).mean(),(Lk[m]<0.10).mean(),np.median(Lb[m]),np.median(Lk[m])))
    # left terrace brick colour
    H,W=Lb.shape
    wl=mc.class_mask(cmap,CL['walls']); wl[:, W//2:]=False
    rb=lambda a:float((a[...,0][wl].mean())/(a[...,2][wl].mean()))
    sat=lambda a:float(np.median(cv2.cvtColor((np.clip(a,0,1)*255).astype(np.uint8),cv2.COLOR_RGB2HSV)[...,1][wl])/255)
    print('  left walls r/b base %.2f kit %.2f ; sat base %.3f kit %.3f'%(rb(base),rb(k),sat(base),sat(k)))
