import sys, json, os, numpy as np, cv2
H=os.path.dirname(os.path.abspath(__file__))
def rd(p):
    a=cv2.imread(p,cv2.IMREAD_UNCHANGED); return a.astype(np.float32)/(65535.0 if a.dtype==np.uint16 else 255.0)
scene=sys.argv[1]; kit=H+'/redraw/'+scene
ref=rd(kit+'/zero_base_again.png'); rows={}
for n in sorted(f[:-4] for f in os.listdir(kit) if f.endswith('.png') and (f.startswith('zero_') or f.startswith('on_solo_'))):
    d=np.abs(ref-rd(kit+'/'+n+'.png')).max(axis=2)
    rows[n]=dict(over1=float((d>1.5/255).mean()),over3=float((d>3.5/255).mean()),mx=float(d.max()))
    print('%-34s >1 step %.5f  >3 steps %.5f  max %.4f'%(n,rows[n]['over1'],rows[n]['over3'],rows[n]['mx']))
json.dump(rows,open(H+f'/zero_{scene}.json','w'),indent=0)
