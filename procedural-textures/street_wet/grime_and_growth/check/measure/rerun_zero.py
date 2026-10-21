# Checker: do the master dial at 0 and every layer's own amount at 0 give the old (base) picture? Same view, same size, same samples; PNG numbers.
import sys, json, os
KIT='proc-work/kits/weathering'
sys.path.insert(0,KIT+'/harness'); sys.path.insert(0,KIT); sys.dont_write_bytecode=True
import numpy as np, cv2
H=os.path.dirname(os.path.abspath(__file__))
def rd(p):
    a=cv2.imread(p,cv2.IMREAD_UNCHANGED); return a.astype(np.float32)/(65535.0 if a.dtype==np.uint16 else 255.0)
def cmp(a,b):
    d=np.abs(a-b).max(axis=2)
    return dict(over1=float((d>1.5/255).mean()),over3=float((d>3.5/255).mean()),mx=float(d.max()),mean=float(d.mean()))
out={}
for scene,base_name in (('street','main_A_wet'),('lockout','lockout_B_wet')):
    kit=H+'/redraw/'+scene; base=H+'/redraw/'+scene+'_base'
    if not os.path.exists(base+'/'+base_name+'.png'): continue
    ref=rd(kit+'/zero_base_again.png')
    print('==',scene,'reference = zero_base_again (drawn right beside them)',base_name,ref.shape)
    rows={}
    for n in sorted(f[:-4] for f in os.listdir(kit) if f.endswith('.png') and (f.startswith('zero_') or f.startswith('on_solo_'))):
        c=cmp(ref,rd(kit+'/'+n+'.png')); rows[n]=c
        print('  %-34s dots >1 step %.5f  >3 steps %.5f  max diff %.4f  mean diff %.6f'%(n,c['over1'],c['over3'],c['mx'],c['mean']))
    out[scene]=rows
json.dump(out,open(H+'/zero_rerun.json','w'),indent=0)
