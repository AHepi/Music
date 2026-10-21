import json, os, numpy as np, cv2, glob
kit='/workspace/wk_out/chk3_street'
def rd(p):
    a=cv2.imread(p,cv2.IMREAD_UNCHANGED); return a.astype(np.float32)/(65535.0 if a.dtype==np.uint16 else 255.0)
ref=rd(kit+'/zero_base_again.png'); rows={}
for n in sorted(f[:-4] for f in os.listdir(kit) if f.endswith('.png') and f.startswith('zero_')):
    d=np.abs(ref-rd(kit+'/'+n+'.png')).max(axis=2)
    rows[n]=(round(float((d>1.5/255).mean()),5),round(float((d>3.5/255).mean()),5),round(float(d.max()),4))
print('ZERO',json.dumps(rows))
t={}
for f in sorted(glob.glob(kit+'/time_*.json')):
    d=json.load(open(f)); t[os.path.basename(f)[:-5]]=(d['seconds'],d['seconds_look_change'])
print('TIME',json.dumps(t))
